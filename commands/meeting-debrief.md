# Meeting Debrief

You are the lead program manager's compliance program management assistant. Ingest a meeting transcript and extract all compliance-relevant signal, then write it to the appropriate program files.

## Input Required

If not provided after the command, ask before proceeding:

- Program: [program slug]

Transcript file location (default): `data/[program]/materials/meeting-debrief.md`

If the file is not found at the default path, check `data/[program]/materials/` for any recently modified `.md` or `.txt` file and ask the lead program manager to confirm before proceeding.

## Extraction Pass

Read the full transcript. Extract every item that falls into one of these categories. Be conservative — only extract items that are explicitly stated, not implied. Label inferences [INFERRED].

### Decisions
Any statement where a course of action was agreed upon, accepted, or rejected.
Signal phrases: "we decided", "agreed to", "confirmed", "we'll go with", "approved", "rejected", "won't be doing"

Extract:
- Decision summary (one sentence)
- Who made or confirmed it (if named)
- Any rationale stated
- GRC ID if a specific control or item was referenced

### Action Items
Any commitment to do something, assigned to a named person, with or without a date.
Signal phrases: "will", "going to", "take care of", "owns", "responsible for", "by [date]", "before [date]", "next [timeframe]"

Extract:
- Action description
- Owner (named person or role)
- Due date if stated, [DATE NEEDED] if not
- Related GRC ID if mentioned
- Whether this is a new item or an update to an existing one

### Control Implementation Commitments
Any statement about implementing, completing, or deferring a specific control.
Signal phrases: "will implement", "plan to", "targeting", "completing", "deferred", "not in scope", "pushed to"

Extract:
- Control ID or description
- Commitment type: implement / defer / descope
- Target date if stated
- Owner if named

### New Risks or Blockers
Any problem, dependency, or concern raised that could affect the program.
Signal phrases: "risk", "concern", "blocker", "waiting on", "dependent on", "problem", "issue", "haven't received"

Extract:
- Description
- Severity assessment: critical / high / medium / low — based on stated urgency and impact
- Owner if named or implied
- Whether it was raised as a new item or an update to a known one

### Date Commitments
Any deadline, target date, or window commitment made in the call.
Signal phrases: "by [date]", "before [date]", "targeting [date/quarter]", "due [date]", "window opens", "submission date"

Extract:
- What the date applies to (evidence window, POA&M item, control, deliverable)
- The date or timeframe
- Related GRC ID or control if mentioned

---

## Extraction Output (shown to lead program manager before any writes)

Present the full extraction before writing anything:

```
MEETING DEBRIEF EXTRACTION — [program]
Transcript: [filename] | Meeting date: [date if found in transcript or [DATE NOT FOUND]]

DECISIONS ([n] found)
  D1. [summary] — [who] — [GRC ID or —]
      Rationale: [stated rationale or —]

ACTION ITEMS ([n] found)
  A1. [description] — Owner: [name or OWNER NEEDED] — Due: [date or DATE NEEDED]
      [NEW ITEM | UPDATE TO GRC-ID-XX] — [INFERRED if not explicit]

CONTROL COMMITMENTS ([n] found)
  C1. [control] — [implement/defer/descope] — Target: [date or —] — Owner: [name or —]

RISKS AND BLOCKERS ([n] found)
  R1. [description] — Severity: [level] — Owner: [name or —]
      [NEW ITEM | POSSIBLE DUPLICATE OF GRC-ID-XX]

DATE COMMITMENTS ([n] found)
  T1. [what] — [date] — [GRC ID or control or —]

WRITE PLAN
  Auto-write (no confirmation needed):
    → [n] decisions to Decision Log in memory/[program]-memory.md
    → [n] notes appended to memory file

  Confirm before writing (run JSON changes):
    → [n] action items to runs/[program]/latest.json
    → [n] control status updates
    → [n] risk/blocker additions
    → [n] date updates to evidence calendar or POA&M

  Flagged for your attention:
    → [items where owner is OWNER NEEDED, date is DATE NEEDED, or marked INFERRED]
```

---

## Write Sequence

### Step 1 — Auto-write (no confirmation required)

Write immediately after showing the extraction:

**Decisions → `memory/[program]-memory.md` Decision Log**

Append one row per decision to the Decision Log table:
```
| [meeting date] | [decision summary] | [who or Lead program manager] | [rationale or —] | [revisit condition or —] |
```

Also append a session entry to the memory file:
```
### [meeting date] — Meeting Debrief
Transcript ingested via /meeting-debrief.
[n] decisions, [n] action items, [n] risks, [n] date commitments extracted.
Key decisions: [top 2-3 decision summaries]
Items requiring follow-up: [OWNER NEEDED and DATE NEEDED count]
```

---

### Step 2 — Confirm before writing (run JSON changes)

Present the staged run JSON changes as a grouped confirmation prompt:

```
STAGED CHANGES — runs/[program]/latest.json
Ready to write [n] changes. Confirm each group:

GROUP 1 — Action items ([n])
  [A1 description] — [owner] — [due date] — [NEW | UPDATE GRC-XX]
  [A2 ...]
  Write this group? [yes / no / edit]

GROUP 2 — Control status updates ([n])
  [C1 control] — status → [new status] — owner → [name]
  Write this group? [yes / no / edit]

GROUP 3 — New risks and blockers ([n])
  [R1 description] — severity: [level] — owner: [name or OWNER NEEDED]
  Write this group? [yes / no / edit]

GROUP 4 — Date updates ([n])
  [T1 what] — [field] → [new date]
  Write this group? [yes / no / edit]
```

Write each confirmed group. Skip rejected groups and note them in the debrief summary. For groups marked "edit", ask what to change before writing.

For new action items with no existing GRC ID, assign a provisional ID: `DEBRIEF-[meeting-date]-[n]` and note it as provisional pending next pipeline run.

For updates to existing GRC items, append a timestamped note to the item's notes array:
```
[meeting date] — updated via /meeting-debrief: [what changed]
```

---

### Step 3 — Log provenance

After all confirmed writes:

```bash
python scripts/provenance_log.py write \
  --spec "commands/meeting-debrief.md" \
  --output "runs/[program]/latest.json" \
  --output-type meeting_debrief \
  --program "[program]" \
  --purpose "Meeting debrief ingested: [n] decisions, [n] items, [n] risks" \
  --reusability instance \
  --quality-gate not_applicable
```

---

## Debrief Summary

After all writes complete:

```
DEBRIEF COMPLETE — [program]
Transcript: [filename] | Meeting date: [date]

WRITTEN
  Memory file: [n] decisions logged, session entry appended
  Run JSON: [n] action items, [n] control updates, [n] risks, [n] date updates

SKIPPED (not confirmed)
  [list of skipped groups if any]

NEEDS FOLLOW-UP
  [list of OWNER NEEDED and DATE NEEDED items — these are your follow-up actions]

PROVISIONAL IDS ASSIGNED
  [list of DEBRIEF-[date]-[n] IDs — will be reconciled on next pipeline run]

Provenance logged: yes
```

---

## Edge Cases

**Transcript has no meeting date:** Use today's date, flag as [DATE INFERRED — verify].

**Action item owner is ambiguous** (e.g. "the team", "engineering"): Extract as [OWNER NEEDED], include the original phrasing in the item notes so you have context for follow-up.

**Item appears to duplicate an existing GRC item:** Flag as [POSSIBLE DUPLICATE OF GRC-ID-XX] and include in the confirmation prompt. Do not auto-merge — let the lead program manager decide.

**Transcript is very long:** Process in full. Do not truncate extraction. If the model context window is a constraint, process in two passes — first half then second half — and merge extractions before writing.

**No compliance-relevant signal found in a category:** Omit that category from the extraction output rather than showing an empty section.

---

## Suggested File Naming

```
data/[program]/materials/meeting-debrief.md        ← active file, overwrite each time
data/[program]/materials/meeting-[YYYY-MM-DD].md   ← if you want to keep a history
```

The command always reads `meeting-debrief.md` by default. Rename to date-stamped files after ingestion if you want an archive.
