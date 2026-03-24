---
resource_type: spec
version: "2.0"
domain: program-management
triggers:
  - calendar_export
  - monitoring_run
  - new_program
inputs:
  - pipeline_run_json
  - calendar_events_array
outputs:
  - ics_file
  - markdown_event_list
governed_by: config/constitution.md
invoked_by: engine/program-pipeline-orchestrator.md
depends_on: functions/program-monitoring-spec.md
execution_modes:
  - llm_spec
  - python_script
script: scripts/calendar_exporter.py
---

# Calendar Output Spec
**Version:** 2.0
**Purpose:** Transform the `calendar_events` array from a pipeline run JSON into a portable `.ics` file and human-readable event list. Applies working-day scheduling logic, conflict resolution, intelligent batching, and holiday awareness to produce a calendar that respects the laws of time and can be imported without manual correction.
**Governed by:** `config/constitution.md`

---

## Constitutional Guidance

Protect the downstream (IV.2) — calendar events drive real commitments. A conflicting or weekend-scheduled event imported by a colleague is worse than a flagged gap. Surface uncertainty (IV.4) — inferred classifications or adjusted dates must be labeled. Never silently generate a misleading entry.

---

## Persona Definition

Calendar scheduling engine. Converts structured event data into RFC 5545 iCalendar format with conflict-free, working-day-aware scheduling. Intelligent about density — high-prep activities get time blocks, batched items get collective blocks, informational deadlines become all-day markers. Never schedules on weekends or blocked holidays.

---

## Parameters

```
TIMEZONE:      [IANA timezone string — default: America/New_York]
WORK_START:    [HH:MM — default: 09:00]
WORK_END:      [HH:MM — default: 17:00]
GAP_MINUTES:   [minutes between events — default: 15]
HOLIDAYS:      [us_federal_plus_observed — default, only supported value currently]
```

---

## Working Day Definition

A working day is Monday–Friday, excluding blocked holidays.

### Blocked Holiday List (US Federal + Common Observed)

```
New Year's Day                Jan 1
New Year's Day (observed)     nearest weekday if Jan 1 falls on weekend
MLK Day                       3rd Monday in January
Presidents' Day               3rd Monday in February
Memorial Day                  last Monday in May
Juneteenth                    June 19 (nearest weekday if weekend)
Independence Day              July 4 (nearest weekday if weekend)
Labor Day                     1st Monday in September
Columbus Day                  2nd Monday in October
Veterans Day                  November 11 (nearest weekday if weekend)
Thanksgiving                  4th Thursday in November
Day After Thanksgiving        Friday after Thanksgiving
Christmas Eve                 December 24
Christmas Day                 December 25 (nearest weekday if weekend)
New Year's Eve                December 31
```

### Working Day Check

```
is_working_day(date):
  if date.weekday() in [5, 6]:   # Saturday, Sunday
    return False
  if date in blocked_holidays:
    return False
  return True
```

### Shift-Left Rule

When a calculated date (event date or reminder date) falls on a non-working day, shift to the nearest prior working day:

```
shift_left(date):
  candidate = date - 1 day
  while not is_working_day(candidate):
    candidate = candidate - 1 day
  return candidate
```

Apply shift-left to: all event dates, all reminder dates. Never shift forward — deadlines move earlier, not later.

---

## Output Mode Classification

Before scheduling, assign each event an output mode. This determines whether it gets a time slot, is batched with similar events, or becomes an all-day marker.

### Mode 1 — Time-Blocked
Gets a specific DTSTART and DTEND. Placed sequentially in the working day with gap between events.

Assigned to:
- All `tabletop`, `audit_event`, `access_review`, `policy_review`, `assessment` activity types
- Any event with `pm_action_required: true` regardless of type
- Any `evidence_collection` window (after batching — one block per window, not per item)
- Reminder scaffold events (`[PREP]` events)

### Mode 2 — Batched Block
Multiple events of the same type on the same date collapsed into a single time-blocked event. The batch block gets one DTSTART/DTEND. Individual items appear in the DESCRIPTION field.

Assigned to:
- `vendor_checkin`, `training`, `recurring_sync` when 3+ occur on the same date
- `deadline` events when `pm_action_required: true` and 3+ occur on the same date
- Any same-type cluster of 3+ events that would individually overflow the working day

Batch block duration: base duration for the type + 30 minutes per additional item, capped at 3 hours.
```
batch_duration = min(base_duration + (extra_items * 30min), 180min)
```

Batch block title format:
```
[Activity Type] Block — [n] items — [program]
```

Batch block description lists all individual items.

### Mode 3 — All-Day Marker
Scheduled as a full-day event (no DTSTART time, DATE value only). Appears as a banner in most calendar clients. Does not consume working-day capacity.

Assigned to:
- `deadline` and `milestone` types where `pm_action_required: false`
- Any event that cannot be accommodated in the working day after batching and spillover
- Recurring events that are informational only

---

## Activity Classification

| Activity Type | Output Mode | Base Duration | Reminder Scaffold |
|---|---|---|---|
| `tabletop` | Time-blocked | 3 hours | Yes |
| `access_review` | Time-blocked | 2 hours | Yes |
| `policy_review` | Time-blocked | 2 hours | Yes |
| `evidence_collection` | Time-blocked (batched) | 2 hours | Yes |
| `assessment` | Time-blocked | 2 hours | Yes |
| `audit_event` | Time-blocked | 2 hours | Yes |
| `vendor_checkin` | Batched if 3+ | 1 hour | No |
| `training` | Batched if 3+ | 1 hour | No |
| `recurring_sync` | Batched if 3+ | 1 hour | No |
| `deadline` | All-day (time-blocked if pm_action_required) | 1 hour | No |
| `milestone` | All-day (time-blocked if pm_action_required) | 1 hour | No |
| `other` | Time-blocked | 1 hour | No |

Classification logic:
- Read event `title` and `notes`, match against type examples
- If ambiguous, assign most likely type and mark `[INFERRED]`
- Evidence collection: group all items sharing the same due date into one `evidence_collection` event before classification

---

## Day Scheduling Algorithm

For each unique date in the event set, apply this algorithm:

### Step 1 — Apply shift-left
If the date is not a working day, shift all events on that date to the prior working day.
Note the shift in each event's description: `[RESCHEDULED from YYYY-MM-DD — non-working day]`

### Step 2 — Separate by output mode
```
time_blocked = events where output_mode == Time-Blocked (sorted by priority)
batched      = events where output_mode == Batched Block (grouped by type)
all_day      = events where output_mode == All-Day Marker
```

### Step 3 — Priority sort for time-blocked events
Within time-blocked events, sort by priority descending:

| Priority | Types |
|---|---|
| 1 — Highest | `tabletop`, `audit_event` |
| 2 | `access_review`, `policy_review`, `assessment` |
| 3 | `evidence_collection` |
| 4 | `pm_action_required: true` standard activities |
| 5 | `vendor_checkin`, `recurring_sync`, `other` |
| 6 — Lowest | Reminder scaffold events |

### Step 4 — Fit time-blocked events into working day

```
cursor = WORK_START  # e.g. 09:00

for event in priority_sorted_time_blocked:
  event_end = cursor + event.duration
  if event_end > WORK_END:
    # Day is full — spill to prior working day
    spill_date = shift_left(current_date - 1 day)
    move event to spill_date queue
    note in description: [MOVED to YYYY-MM-DD — day capacity reached]
  else:
    event.DTSTART = current_date + cursor
    event.DTEND   = current_date + event_end
    cursor = event_end + GAP_MINUTES
```

Apply spilled events to their new date using the same algorithm recursively.

### Step 5 — Fit batched blocks
Apply same cursor logic for batched blocks after time-blocked events are placed.
If a batch block doesn't fit, convert it to an all-day marker and note:
`[CONVERTED to all-day — day capacity reached after time-blocked events]`

### Step 6 — All-day markers
Write all all-day markers for the date with `DTSTART;VALUE=DATE:[YYYYMMDD]`. These do not affect cursor position.

### Step 7 — Capacity warning
If any event was spilled or converted during scheduling, add to the run summary:
```
[SCHEDULE NOTE] [n] events were moved or converted on [date] due to day capacity.
See flagged events in markdown summary.
```

---

## Reminder Scaffold

Generate reminder events for time-blocked activities with `Reminder Scaffold: Yes`.

**1-month reminder** (activity date − 30 days, then shift-left if non-working):
```
Title:    [PREP] [original title] — 1 month out
Duration: 30 minutes
Notes:    Preparation checkpoint. Review requirements, confirm participants, identify blockers.
PM action required: true
```

**1-week reminder** (activity date − 7 days, then shift-left if non-working):
```
Title:    [PREP] [original title] — 1 week out
Duration: 30 minutes
Notes:    Final preparation. Confirm readiness, stage materials, send pre-work if needed.
PM action required: true
```

Reminder rules:
- If 1-month reminder date is in the past → skip, generate 1-week only
- If 1-week reminder date is in the past → skip both
- If reminder date equals the activity date after shift-left → skip that reminder
- Reminders are time-blocked events — apply day scheduling algorithm to reminder dates
- Never generate reminders for recurring events

---

## Processing Passes

### Pass 1 — Validation
Validate each event:
- `title` — required. If missing: `Untitled Program Event` + flag
- `date` — required, must be `YYYY-MM-DD`. If missing: flag `[DATE NEEDED]` and skip
- `recurrence` — must be `none | daily | weekly | monthly | quarterly | annual`. Default: `none`
- `pm_action_required` — boolean. Default: `false`

```
Validation: [n] valid, [n] flagged/skipped
Flagged: [list with reason]
```

### Pass 2 — Classification and Batching
1. Classify each valid event into activity type
2. Assign output mode (time-blocked / batched / all-day)
3. Cluster same-date same-type events meeting batch threshold
4. Collapse evidence collection clusters into single windows
5. Mark inferred classifications

### Pass 3 — Reminder Generation
For each qualifying event:
1. Calculate 1-month and 1-week reminder dates
2. Apply shift-left to each
3. Apply reminder rules
4. Add reminder events to the time-blocked queue for their respective dates

### Pass 4 — Working Day Scheduling
For each unique date across all events and reminders:
1. Apply shift-left if non-working day
2. Apply day scheduling algorithm (Steps 1–7 above)
3. Record any spills or conversions for the summary

### Pass 5 — Recurrence Rule Mapping

| Value | RRULE |
|---|---|
| `none` | _(no RRULE)_ |
| `daily` | `RRULE:FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR` |
| `weekly` | `RRULE:FREQ=WEEKLY` |
| `monthly` | `RRULE:FREQ=MONTHLY` |
| `quarterly` | `RRULE:FREQ=MONTHLY;INTERVAL=3` |
| `annual` | `RRULE:FREQ=YEARLY` |

### Pass 6 — .ics Generation

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Program Pipeline//Calendar Export v2.0//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
[VEVENT blocks — time-blocked first by date, then batched, then all-day markers]
END:VCALENDAR
```

**Time-blocked and batched events:**
```
BEGIN:VEVENT
UID:[slugified-title]-[date]-[HHMM]@program-pipeline
DTSTAMP:[current UTC datetime]
DTSTART;TZID=[TIMEZONE]:[YYYYMMDD]T[HHMM]00
DTEND;TZID=[TIMEZONE]:[YYYYMMDD]T[HHMM]00
SUMMARY:[title — append " ✋" if pm_action_required]
DESCRIPTION:[type | duration | owner | notes | any RESCHEDULED or MOVED notices]
[RRULE if recurrence != none]
END:VEVENT
```

**All-day markers:**
```
BEGIN:VEVENT
UID:[slugified-title]-[date]-allday@program-pipeline
DTSTAMP:[current UTC datetime]
DTSTART;VALUE=DATE:[YYYYMMDD]
DTEND;VALUE=DATE:[YYYYMMDD+1]
SUMMARY:[title — append " ✋" if pm_action_required]
DESCRIPTION:[type | owner | notes | any notices]
END:VEVENT
```

### Pass 7 — Markdown Event List

```markdown
## Calendar Events — [program] [run_date]

### Scheduling Summary
- Working days in range: [n]
- Time-blocked events: [n] ([total hours] hrs)
- Batched blocks: [n] (covering [n] individual items)
- All-day markers: [n]
- Reminder events generated: [n]
- Events shifted left (non-working day): [n]
- Events spilled to prior day (capacity): [n]
- Events converted to all-day (capacity): [n]
- Skipped / flagged: [n]

[SCHEDULE NOTES if any spills or conversions occurred]

### Time-Blocked Events (by date)
| Date | Time | Title | Type | Duration | Owner | PM Action | Notes |
|---|---|---|---|---|---|---|---|

### Batched Blocks
| Date | Time | Title | Items | Duration | Types |
|---|---|---|---|---|---|

### All-Day Markers
| Date | Title | Type | Owner | PM Action |
|---|---|---|---|---|

### Reminder Events
| Date | Time | Title | For Activity |
|---|---|---|---|

### Skipped / Flagged
| Original Date | Title | Reason |
|---|---|---|
```

---

## Edge Cases

| Situation | Handling |
|---|---|
| 80+ items due same day | Batch same-type items, convert lowest-priority to all-day, spill remainder to prior working day |
| Event date is a federal holiday | Shift-left to prior working day, note in description |
| Reminder date falls on activity date after shift-left | Skip that reminder |
| Activity is less than 7 days away | Skip 1-month reminder, generate 1-week only if date is future |
| Activity is less than 7 days away and in past | Skip both reminders |
| Recurring event | No reminders generated. Recurrence rule applied. Not batched. |
| Spill chains (spilled event also lands on full day) | Apply algorithm recursively. Cap at 5 prior days — if still unresolved, convert to all-day and flag. |
| Two events share identical title and date | Generate both with distinct UIDs using HHMM suffix |
| Duration extends past WORK_END on spill day | Reduce duration to fit, note: `[DURATION ADJUSTED to fit working day]` |

---

## Two Execution Modes

### Mode A — Script (preferred)
```bash
python scripts/calendar_exporter.py --run path/to/run.json
python scripts/calendar_exporter.py --run path/to/run.json --output path/to/events.ics
python scripts/calendar_exporter.py --run path/to/run.json --markdown-only
python scripts/calendar_exporter.py --run path/to/run.json --timezone America/Chicago
```

### Mode B — LLM
Provide the `calendar_events` array and trigger:
```
BEGIN CALENDAR PROCESSING
```

---

## Companion Specs
- Governed by: `config/constitution.md`
- Invoked by: `engine/program-pipeline-orchestrator.md`
- Reads: `runs/[PROGRAM]/latest.json → calendar_events`
- Writes: `data/[PROGRAM]/[date]-calendar.ics`, markdown event list
- Logged by: `scripts/provenance_log.py` — output_type: `calendar_export`
