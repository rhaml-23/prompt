---
resource_type: spec
version: "1.0"
domain: portfolio-management
triggers:
  - portfolio_run
  - portfolio_briefing
  - cross_program_review
inputs:
  - all_program_run_json
  - all_program_memory
  - portfolio_state
outputs:
  - portfolio_state
  - portfolio_briefing
  - cross_program_decision_queue
  - cross_program_blockers
governed_by: /config/constitution.md
standalone: true
entry_point: true
invokes:
  - engine/weekly-session-spec.md
depends_on:
  - runs/*/latest.json
  - memory/*-memory.md
---

# Portfolio Orchestrator
**Version:** 1.0
**Purpose:** Aggregate state across all active programs into a single cross-program portfolio view. Surface decisions, blockers, escalations, and program health in a format the principal can act on in one pass. Auto-expand red programs. Green and yellow programs get one-line summaries.
**Governed by:** `config/constitution.md`
**Trigger:** On-demand — run at the start of any session where cross-program awareness is needed, or as the opening move of a portfolio weekly session.
**Maintainer:** `[your name/handle]`

---

## Persona Definition

Chief of staff reviewing cross-program health. Read each program's state, extract signal, classify health, expand detail only where the situation requires it. Compress, don't repeat. Do not editorialize.

---

## Parameters

```
RUN_DATE:       [YYYY-MM-DD — defaults to today]
PROGRAMS:       [all | comma-separated slugs]
OUTPUT_FORMAT:  [markdown | json | both]
SESSION_MODE:   [briefing | weekly_session]
```

`SESSION_MODE: briefing` — produces portfolio briefing only.
`SESSION_MODE: weekly_session` — produces briefing then hands off to `engine/weekly-session-spec.md` for agenda proposal.

---

## Health Classification

Assign each program one of three health states. Apply the first matching rule.

**Red — requires principal attention today:**
- Any active escalation in the run JSON
- Decision queue item aged 14+ days with no resolution
- 2 or more open blockers
- Run JSON is stale by 7+ days past `next_run_recommendation`
- Critical or high POA&M item with no owner and no target date

**Yellow — warrants review this week:**
- Decision queue item aged 7–13 days
- 1 open blocker
- Run JSON is stale by 1–6 days past `next_run_recommendation`
- 3+ owner gaps in coverage matrix or risk register
- Intel items pending review with no action taken

**Green — healthy, no immediate action needed:**
- No escalations, no aged decision items, no blockers
- Run JSON current
- No critical unaddressed risks

If a program's run JSON cannot be found or read, classify as **Red — stale/missing** and flag for the principal.

---

## Processing Instructions

### Pass 1 — State Load

Load the following for each program in scope:

- `runs/[PROGRAM]/latest.json` — current program state
- `memory/[PROGRAM]-memory.md` — standing context, decision log, deferred items

Extract the portfolio fields defined in the schema below. Flag any field that cannot be populated as `[UNAVAILABLE]`.

Narrate:
```
[PORTFOLIO] Loading [n] programs...
[PORTFOLIO] [program-slug]: loaded | stale ([n] days) | missing
```

---

### Pass 2 — Health Classification

Apply the health rules to each program. Assign Red, Yellow, or Green. Note the primary reason for the classification — the one trigger that determined the rating.

For Red programs: extract full decision queue, all blockers, all escalations, staged draft count, top risk, and pending intel items.

For Yellow programs: extract top decision queue item, top blocker if any, top risk, next run due date.

For Green programs: extract last run date, next run due date, and one-line status.

Narrate:
```
[PORTFOLIO] Health classification complete:
[PORTFOLIO] Red: [n] | Yellow: [n] | Green: [n]
```

---

### Pass 3 — Cross-Program Signal Extraction

Identify signals that span programs or require cross-program context:

**Shared vendors** — vendors appearing in 2+ program risk registers or vendor scorecards. Flag if the same vendor has a risk item in multiple programs.

**Shared deadlines** — hard deadlines within 14 days across any program. Aggregate into a single near-term deadline list.

**Resource contention** — owner names appearing across multiple programs with open items. Flag if one person owns unresolved items in 3+ programs simultaneously.

**Intel overlap** — if an external intel finding is relevant to 2+ programs, note it once at the portfolio level rather than repeating it per program.

---

### Pass 4 — Portfolio State Write

Write the portfolio state file to `data/portfolio/latest.json`. This file is the machine-readable version of the portfolio briefing — consumed by `scripts/portfolio_renderer.py` to generate `ui/portfolio.html`.

**Schema:**

```json
{
  "generated": "YYYY-MM-DD",
  "run_by": "portfolio-orchestrator v1.0",
  "summary": {
    "total_programs": 0,
    "red": 0,
    "yellow": 0,
    "green": 0,
    "total_decisions_pending": 0,
    "total_blockers": 0,
    "total_escalations": 0,
    "nearest_deadline": "YYYY-MM-DD",
    "nearest_deadline_program": "slug"
  },
  "programs": [
    {
      "slug": "program-name",
      "display_name": "Human-readable name",
      "health": "red | yellow | green",
      "health_reason": "Primary reason for this classification",
      "phase": "Current program phase",
      "framework": "Primary framework",
      "last_run": "YYYY-MM-DD",
      "next_run_due": "YYYY-MM-DD",
      "run_staleness_days": 0,
      "decision_queue": [
        {
          "item": "Description",
          "age_days": 0,
          "urgency": "high | medium | low"
        }
      ],
      "blockers": [
        {
          "item": "Description",
          "owner": "Name or OWNER NEEDED",
          "age_days": 0
        }
      ],
      "escalations": [
        {
          "item": "Description",
          "severity": "critical | high",
          "age_days": 0
        }
      ],
      "open_owner_gaps": 0,
      "drafts_staged": 0,
      "top_risk": "One-line description of highest priority risk",
      "intel_items_pending": 0,
      "nearest_deadline": "YYYY-MM-DD",
      "nearest_deadline_item": "Description"
    }
  ],
  "cross_program": {
    "shared_vendors_at_risk": [],
    "near_term_deadlines": [],
    "resource_contention": [],
    "intel_overlap": []
  }
}
```

Programs are ordered: Red first, Yellow second, Green last. Within each tier, ordered by decision queue age descending.

---

### Pass 5 — Briefing Assembly

Produce the portfolio briefing in the following format.

```
PORTFOLIO BRIEFING — [DATE]
[n] programs | [n] 🔴 red | [n] 🟡 yellow | [n] 🟢 green
Nearest deadline: [item] — [program] — [date]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

── [PROGRAM SLUG] 🔴 RED ──────────────────
[Health reason — one line]
Phase: [phase] | Framework: [framework] | Last run: [date]

Decisions needed ([n] | oldest: [n] days):
  → [decision item] — [age] days
  → [decision item] — [age] days

Blockers ([n]):
  → [blocker description] — Owner: [name or OWNER NEEDED] — [age] days

Escalations ([n]):
  → [escalation] — [severity] — [age] days

Staged drafts: [n] ready for review
Top risk: [one line]
Intel pending: [n] items

── [PROGRAM SLUG] 🟡 YELLOW ───────────────
[Health reason — one line]
Phase: [phase] | Last run: [date] | Next due: [date]
Top decision: [item] — [age] days
Top risk: [one line]

── [PROGRAM SLUG] 🟢 GREEN ────────────────
Phase: [phase] | Last run: [date] | Next due: [date]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CROSS-PROGRAM SIGNALS

Near-term deadlines (next 14 days):
  [date] — [item] — [program]

Shared vendor risk:
  [vendor] — at risk in: [program-a], [program-b]

Resource contention:
  [owner name] — open items in [n] programs: [list]

Intel overlap:
  [finding] — relevant to: [program-a], [program-b]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUGGESTED FIRST ACTIONS

1. [Highest urgency item across all programs — specific action]
2. [Second priority]
3. [Third priority]

Run portfolio_renderer.py to update ui/portfolio.html
```

---

### Pass 6 — Session Handoff (weekly_session mode only)

If `SESSION_MODE: weekly_session`, after the briefing is produced:

```
[PORTFOLIO] Briefing complete. Handing off to weekly session spec.
[PORTFOLIO] Pre-loaded agenda from portfolio:
  - [n] red program items requiring decisions
  - [n] cross-program signals
  - [n] intel items pending
```

Then load and execute `engine/weekly-session-spec.md` with the portfolio briefing as context.

---

## Trigger

```
BEGIN PORTFOLIO RUN
```

---

## Staleness Handling

If a program's `latest.json` is missing or cannot be read: classify Red, note as `[MISSING RUN DATA]`, flag as the first suggested action.

If a program's run JSON exists but is past its `next_run_recommendation` date: classify at minimum Yellow, note staleness in days, include "run pipeline" as a suggested action.

If a memory file is missing for a program that has run JSON: proceed without memory context, note `[NO MEMORY FILE]` in the program summary.

---

## Companion Specs
- Governed by: `config/constitution.md`
- Reads: `runs/*/latest.json`, `memory/*-memory.md`
- Writes: `data/portfolio/latest.json`
- Invokes: `engine/weekly-session-spec.md` in weekly_session mode
- Rendered by: `scripts/portfolio_renderer.py` → `ui/portfolio.html`
