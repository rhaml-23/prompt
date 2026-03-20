---
resource_type: spec
version: "1.0"
domain: session-management
triggers:
  - weekly_session
  - focused_work_session
inputs:
  - session_memory_files
  - latest_run_jsons
  - provenance_log
  - principal_input
outputs:
  - proposed_agenda
  - session_work_products
  - pattern_report
  - session_close_summary
  - staged_deliverables
  - updated_session_memory
governed_by: config/constitution.md
standalone: true
entry_point: true
depends_on:
  - engine/session-init-spec.md
  - engine/program-pipeline-orchestrator.md
  - functions/program-comms-spec.md
  - engine/quality-gate-spec.md
---

# Weekly Session Spec
**Version:** 1.0  
**Purpose:** Defines the structure and behavior of a focused weekly work session. Opens with a memory-informed agenda proposal, runs work with pattern detection and values alignment active, closes with a summary and staged deliverables.  
**Governed by:** `config/constitution.md`  
**Typical duration:** 1–3 hours  

---

## Session Open

### Step 1 — Load memory

Read for every active program:
- `/memory/[program_slug]-memory.md` — full file
- `/runs/[program_slug]/latest.json` — program_state and decision_queue only

If a memory file does not exist for a program, note it and create a blank one from the template at session close.

### Step 2 — Pattern scan

Before proposing anything, scan across all memory files for:

**External intel items** — any items from a recent intel scan staged for the agenda:
```
[INTEL] [n] external findings staged since last session:
  [Critical/High] [finding title] — [program] — [recommended action]
```
If no scan has run since the last session and more than 14 days have passed, note it:
```
[INTEL] No external scan in [n] days. Consider running one before or after this session.
```

**Deferred item aging** — any item deferred 3+ times:
```
[PATTERN] "[item]" has been deferred [n] times across [date range].
Last stated reason: "[reason]". Worth addressing today or explicitly closing.
```

**Flag persistence** — any flag present in 3+ consecutive run JSONs:
```
[PATTERN] "[flag]" has appeared in every run since [date] without resolution.
```

**Decision queue stagnation** — any decision queue item present for 14+ days:
```
[PATTERN] "[item]" has been in the decision queue since [date] — [n] days.
```

**Velocity drop** — if provenance log shows fewer than expected outputs in the past 2 weeks for an active program, note it without judgment:
```
[PATTERN] No pipeline run recorded for "[program]" in [n] days.
Recommended cadence was [cadence].
```

### Step 3 — Propose agenda

Format:

```
GOOD [day]. Here's where things stand and what I'd suggest we work on today.

PROGRAM HEALTH
[program]: [health] — [one-line status]
[program]: [health] — [one-line status]

PATTERNS WORTH NAMING
[list any patterns from Step 2 — skip section if none]

PROPOSED AGENDA
Estimated session: [n] hours

1. [highest priority item] — [why this first] — [~time estimate]
2. [next item] — [brief rationale] — [~time estimate]
3. [next item] — [brief rationale] — [~time estimate]
[continue as needed]

ITEMS I'D SKIP TODAY
[anything in the queue that can wait and why]

What do you want to change?
```

Rules for agenda proposal:
- Lead with the highest-risk or most time-sensitive item — not the easiest
- Maximum 5 agenda items for a 2-hour session — don't overload
- If a pattern was surfaced, include addressing it as an agenda item unless it is clearly low priority
- End with an open question — the principal modifies, approves, or redirects
- Do not start work until the agenda is confirmed

---

## Session Work Mode

### Active behaviors during work

**Values alignment check** — before executing any significant output, briefly cross-reference with the decision log in session memory. If the current action contradicts a prior decision, flag it:
```
[VALUES CHECK] This would [action]. In [prior session] you decided [prior decision].
These are in tension. Proceed as directed or revisit the prior decision?
```

**Progressive staging** — as each agenda item completes, stage its output immediately:
- Save to the appropriate `/runs/` or `/drafts/` location
- Log to provenance
- Note it in the session close list
Do not batch outputs at the end. Stage as you go.

**Pace check** — if the session has been running for 90 minutes and more than 2 agenda items remain, surface it:
```
[PACE] 90 minutes in. [n] items remain: [list].
Options: push through, defer [item], or end here with a clean close.
```

---

## Session Close

### Step 1 — Compile session summary

```
SESSION CLOSE — [YYYY-MM-DD]

WORKED ON
[bullet per agenda item addressed — one sentence each]

PRODUCED
[list each deliverable with file path or description]
[mark each: ready to send | needs review | internal only]

DECISIONS MADE
[any decisions made this session — will be added to memory]

DEFERRED
[anything not addressed — reason and suggested next session priority]

PATTERNS ADDRESSED
[how the principal responded to any patterns raised at open]
[or: no patterns raised / patterns noted but not addressed]

PROGRAM STATE
[program]: [health] — [any change from session open]
```

### Step 2 — Stage deliverables

Organize all outputs produced this session:

```
STAGED DELIVERABLES

Ready to send (requires principal review before sending):
  [file/description] → [recipient/channel]

Ready to use:
  [file/description] → [purpose]

Saved to repo:
  [file path] → [what it is]
```

Everything in "ready to send" is flagged for one-way door review. Nothing goes out without the principal's explicit sign-off.

### Step 3 — Write session memory

Append to `memory/[program_slug]-memory.md` for each program touched this session:

```markdown
### [YYYY-MM-DD]

**Worked on:** [summary]
**Produced:** [deliverables]
**Decisions made:** [any — also add to Decision Log table]
**Deferred:** [any — also add to Deferred Items table if 2+ deferrals]
**Patterns noticed:** [any surfaced this session]
**Principal direction on patterns:** [response or "acknowledged, no action"]
**State at close:** [one sentence]
**Next session priority:** [agent recommendation]
```

Update Standing Context if anything fundamental changed about the program this session.

Update Decision Log table if decisions were made.

Update Deferred Items table if items were explicitly pushed out — increment "times deferred" for existing entries.

### Step 4 — Log provenance

For each deliverable produced this session, write a provenance log entry.

### Step 5 — Close

```
Session logged. Deliverables staged.

Next session I'd suggest starting with: [top priority from memory]
```

---

## Companion Specs
- Governed by: `config/constitution.md`
- Reads: `memory/*.md`, `runs/*/latest.json`, `logs/provenance.jsonl`
- Invokes: `engine/program-pipeline-orchestrator.md`, `functions/program-comms-spec.md`, `engine/quality-gate-spec.md`
- Writes: `memory/*.md`, `logs/provenance.jsonl`, `drafts/`, `runs/`
