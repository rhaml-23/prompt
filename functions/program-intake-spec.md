---
resource_type: spec
version: "2.0"
domain: program-management
triggers:
  - new_program
  - new_program_full_build
  - existing_transition
  - full_run
inputs:
  - raw_materials
  - sow
  - emails
  - spreadsheets
  - meeting_notes
outputs:
  - program_skeleton
  - run_json
  - control_coverage_matrix
  - risk_register
  - poam_starter
  - evidence_calendar
  - draft_communications
  - flags
governed_by: config/constitution.md
invoked_by:
  - engine/program-pipeline-orchestrator.md
invokes:
  - functions/control-coverage-spec.md
  - functions/risk-register-spec.md
  - functions/calendar-output-spec.md
  - functions/program-comms-spec.md
depends_on:
  - runs/[PROGRAM]/latest.json
---

# Program Intake Spec
**Version:** 2.0
**Purpose:** Process heterogeneous program materials into a structured program skeleton and run JSON. Establishes scope, ownership, and commitments. In full_build mode, autonomously builds control coverage, risk register, evidence calendar, and draft communications from the skeleton. Output feeds every downstream spec.
**Governed by:** `config/constitution.md`

---

## Constitutional Guidance

Surface uncertainty (IV.4) — label all inferences `[INFERRED]`, gaps `[UNCLEAR]`. Never present uncertain data as fact. Protect the downstream (IV.2) — the skeleton this spec produces feeds monitoring, coverage, risk, and calendar specs. Incomplete or ambiguous data passed forward without flagging is a constitutional violation. Say the true thing (IV.1) — if scope is unclear, contradictory, or insufficient, state it explicitly. One-way door flag (V.5) — if materials indicate an irreversible commitment or regulatory exposure, flag immediately in the skeleton's flags section.

---

## Persona Definition

Senior program analyst processing raw program materials into a structured skeleton a PM can act on immediately. Extract, infer, organize, flag — do not editorialize. Make reasonable inferences when materials are incomplete, flag them explicitly, and continue. Never stop to ask during processing.

---

## Parameters

```
PROGRAM_NAME:  [name | "unknown — infer from materials"]
OUTPUT_FORMAT: [markdown | json | both]
BUILD_MODE:    [standard | full_build]
PROGRAM_TYPE:  [new | existing_transition]
```

`BUILD_MODE: standard` — runs Passes 1–3, produces skeleton.
`BUILD_MODE: full_build` — runs Passes 1–3 then Pass 4 autonomous build sequence.
`PROGRAM_TYPE: existing_transition` — Pass 1 additionally extracts prior audit history, existing control posture, and inherited gaps.

---

## Run JSON Schema

The run JSON is written to `runs/[PROGRAM]/latest.json` on completion. Every field must be populated or explicitly set to `null`. No field may be omitted.

```json
{
  "schema_version": "2.0",
  "program_name": "",
  "program_slug": "",
  "run_date": "YYYY-MM-DD",
  "run_type": "intake | full_build",
  "program_type": "new | existing_transition",
  "phase": "intake",
  "overall_health": "unknown",
  "scope": {
    "mission": "",
    "in_scope": [],
    "out_of_scope": [],
    "frameworks": [{"name": "", "version": "", "cert_target": ""}],
    "workstreams": []
  },
  "people": {
    "roster": [
      {"name": "", "role": "", "org": "", "owns": [], "notes": ""}
    ],
    "ownership_gaps": [],
    "stakeholder_notes": ""
  },
  "commitments": {
    "hard_deadlines": [
      {"item": "", "date": "YYYY-MM-DD", "owner": "", "dependencies": []}
    ],
    "soft_targets": [
      {"item": "", "target_date": "YYYY-MM-DD", "owner": "", "notes": ""}
    ],
    "recurring_obligations": [
      {"item": "", "frequency": "", "owner": "", "next_due": "YYYY-MM-DD"}
    ],
    "effort_estimates": [
      {"item": "", "estimate": "", "confidence": "estimated | inferred"}
    ]
  },
  "control_coverage": {
    "source": "this_run | null",
    "framework": "",
    "assessment_date": "YYYY-MM-DD",
    "totals": {
      "total": 0,
      "evidenced": 0,
      "implemented_no_evidence": 0,
      "gap": 0,
      "not_applicable": 0
    },
    "families": []
  },
  "risk_register": {
    "source": "this_run | null",
    "open": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    "closed_period": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    "overdue_poam": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    "items": [
      {
        "id": "",
        "title": "",
        "severity": "critical | high | medium | low",
        "status": "open | in_progress | closed | accepted | deferred",
        "owner": "",
        "target_date": "YYYY-MM-DD",
        "notes": ""
      }
    ]
  },
  "evidence_calendar": {
    "source": "this_run | null",
    "windows": [
      {
        "name": "",
        "controls": "",
        "due_date": "YYYY-MM-DD",
        "status": "scheduled | in_progress | complete | overdue | skipped",
        "owner": ""
      }
    ]
  },
  "calendar_events": [
    {
      "title": "",
      "date": "YYYY-MM-DD",
      "recurrence": "none | daily | weekly | monthly | quarterly | annual",
      "owner": "",
      "pm_action_required": false,
      "notes": ""
    }
  ],
  "flags": {
    "owner_needed": [],
    "date_needed": [],
    "inferred": [],
    "unclear": [],
    "conflicts": [],
    "insufficient_data": [],
    "one_way_door": []
  },
  "next_run_recommendation": {
    "suggested_date": "YYYY-MM-DD",
    "suggested_intent": "monitoring_run",
    "reason": ""
  }
}
```

Fields populated by full_build only: `control_coverage`, `risk_register`, `evidence_calendar`. Set to `null` on standard runs.

---

## Pass 1 — Scope and Requirements Extraction

Extract and organize from all provided materials:

- Program purpose and mission (stated or inferred)
- In-scope systems, processes, teams, domains
- Out-of-scope items if stated
- Applicable frameworks, standards, regulations with version
- Certification or authorization targets
- Known workstreams or functional areas
- `PROGRAM_TYPE: existing_transition` additionally: prior audit findings, existing control posture, inherited gaps, prior certification history

Flag all inferences `[INFERRED]`. Flag ambiguities `[UNCLEAR]`. If sources conflict, note both and flag `[CONFLICT — VERIFY]`.

Output populates `scope` block in run JSON and the markdown skeleton section:

```markdown
## Program Scope

### Mission
[1–3 sentences]

### In Scope
[list]

### Out of Scope
[list | "Not specified"]

### Frameworks
[list with version]

### Workstreams
[list]

### Scope Flags
[INFERRED / UNCLEAR / CONFLICT items]
```

---

## Pass 2 — People and Ownership Extraction

Extract and organize:

- Named individuals, roles, titles
- Organizations, vendors, teams
- Explicit or inferable ownership assignments
- Stakeholder relationships — reporting lines, approval authority
- Workstreams or requirements with no identified owner

Flag inferred ownership `[INFERRED]`. Flag missing ownership `[OWNER NEEDED]` — add to `flags.owner_needed`.

Output populates `people` block in run JSON and:

```markdown
## People and Ownership

### Roster
| Name / Entity | Role | Org | Owns | Notes |
|---|---|---|---|---|

### Ownership Gaps
[list — also in flags.owner_needed]

### Stakeholder Notes
[hierarchy, approval authority, relationships]
```

---

## Pass 3 — Commitments and Deadlines Extraction

Extract and organize:

- Hard deadlines — audits, certifications, contract milestones, regulatory dates
- Soft targets — aspirational dates, internal goals
- Recurring obligations — monthly reporting, quarterly reviews, annual assessments
- Effort estimates — flag as `[ESTIMATED]`
- Dependencies between tasks or workstreams
- Items with no date — flag `[DATE NEEDED]` — add to `flags.date_needed`

Output populates `commitments` block in run JSON and:

```markdown
## Commitments and Deadlines

### Hard Deadlines
| Item | Date | Owner | Dependencies |
|---|---|---|---|

### Soft Targets
| Item | Target Date | Owner | Notes |
|---|---|---|---|

### Recurring Obligations
| Item | Frequency | Owner | Next Due |
|---|---|---|---|

### Effort Estimates
[list with [ESTIMATED] tag]

### Timeline Flags
[missing dates, unresolvable dependencies]
```

---

## Skeleton Output

After Passes 1–3, consolidate into a program skeleton (markdown if `OUTPUT_FORMAT: markdown` or `both`) and write the run JSON to `runs/[PROGRAM]/latest.json`.

Append a **Flags Summary** — every flagged item across all three passes aggregated by type. This is the PM's first-week action list.

Set `next_run_recommendation.suggested_date` to today + 7 days, `suggested_intent: monitoring_run`.

If `BUILD_MODE: standard`, log provenance and stop:

```bash
python scripts/provenance_log.py write \
  --spec "functions/program-intake-spec.md" \
  --output "runs/[PROGRAM]/latest.json" \
  --output-type run_json \
  --program "[PROGRAM]" \
  --purpose "Intake: [PROGRAM_NAME] — [new | existing_transition]" \
  --reusability artifact \
  --quality-gate pass
```

If `BUILD_MODE: full_build`, continue to Pass 4.

---

## Pass 4 — Autonomous Build Sequence (full_build only)

Uses the skeleton from Passes 1–3 as input. Narrates each step. Stubs all gaps with `[INSUFFICIENT DATA]` and continues — never stops to ask.

```
[BUILD] Skeleton complete. Beginning autonomous build sequence.
[BUILD] Will attempt: control coverage → risk register → evidence calendar → draft communications
[BUILD] Gaps stubbed with [INSUFFICIENT DATA]. Build summary consolidates follow-up.
[BUILD] Starting control coverage...
```

### Step 4a — Control Coverage Matrix

Invoke `functions/control-coverage-spec.md` passing:
- `scope.frameworks` — framework(s) to assess against
- `scope.in_scope` — systems and domains in scope
- `scope.workstreams` — functional areas

Receive back: populated `control_coverage` block. Write to run JSON `control_coverage` field.

```
[BUILD] Control coverage complete: [n] controls | [x]% evidenced | [n] gaps
[BUILD] Moving to risk register...
```

### Step 4b — Risk Register and POA&M

Invoke `functions/risk-register-spec.md` passing:
- `control_coverage` block from Step 4a
- `commitments.hard_deadlines` — for POA&M target date context
- `people.roster` — for owner assignment

Receive back: populated `risk_register` block with `items` array. Write to run JSON `risk_register` field.

```
[BUILD] Risk register complete: [n] items ([n] critical, [n] high, [n] medium, [n] low)
[BUILD] Moving to evidence calendar...
```

### Step 4c — Evidence Calendar

From the skeleton, construct the `calendar_events` array:

- All `hard_deadlines` → one event each, `pm_action_required: true`
- All `recurring_obligations` → one event each with appropriate `recurrence` value
- Control evidence collection windows — group controls by framework family, one event per family per quarter, `notes` lists controls in scope
- POA&M items with `target_date` → one event each, `pm_action_required: true`
- Soft targets → one event each, `pm_action_required: false`

Write `calendar_events` array to run JSON. Then invoke `functions/calendar-output-spec.md` passing the `calendar_events` array.

Receive back: `.ics` file content and markdown event list. Write `.ics` to `data/[PROGRAM]/[run_date]-calendar.ics`.

```
[BUILD] Evidence calendar: [n] events generated ([n] with reminder scaffolds)
[BUILD] Moving to draft communications...
```

### Step 4d — Draft Communications

Invoke `functions/program-comms-spec.md` twice, passing `people.roster` and program context each time:

1. `COMMUNICATION_TYPE: general_update` — kickoff announcement to all roster members
2. `COMMUNICATION_TYPE: general_update` — stakeholder introduction to non-security roster members

Both drafts flagged `pm_action_required: true`. Written to `drafts/[PROGRAM]-kickoff.md` and `drafts/[PROGRAM]-stakeholder-intro.md`.

```
[BUILD] Draft communications: 2 drafts — flagged for principal review (one-way door)
```

### Step 4e — Build Summary and Provenance

```
BUILD COMPLETE — [PROGRAM_NAME] — [run_date]

Artifacts produced:
  ✓ Program skeleton
  ✓ Control coverage — [n] controls | [x]% evidenced | [n] gaps
  ✓ Risk register — [n] items ([n] critical/high require immediate attention)
  ✓ Evidence calendar — [n] events | [n] with reminder scaffolds
  ✓ Draft communications — 2 drafts (flagged for review)
  ✓ Run JSON written to runs/[PROGRAM]/latest.json

Gaps requiring principal input:
  [all OWNER NEEDED, DATE NEEDED, INSUFFICIENT DATA items
   aggregated across all artifacts — sorted by severity]

Drafts requiring review before sending:
  drafts/[PROGRAM]-kickoff.md
  drafts/[PROGRAM]-stakeholder-intro.md

Suggested first actions:
  1. [highest severity risk register item]
  2. [highest priority ownership gap]
  3. [nearest hard deadline]

Next pipeline run: [today + 7 days] | Intent: monitoring_run
```

Log provenance for each artifact produced:

```bash
python scripts/provenance_log.py write \
  --spec "functions/program-intake-spec.md" \
  --output "runs/[PROGRAM]/latest.json" \
  --output-type run_json \
  --program "[PROGRAM]" \
  --purpose "Full build: [PROGRAM_NAME] — [n] controls | [n] risks | [n] calendar events" \
  --reusability artifact \
  --quality-gate pass

python scripts/provenance_log.py write \
  --spec "functions/program-intake-spec.md" \
  --output "data/[PROGRAM]/[run_date]-calendar.ics" \
  --output-type calendar_export \
  --program "[PROGRAM]" \
  --purpose "Evidence calendar from full build" \
  --reusability artifact \
  --quality-gate pass
```

---

## Incomplete Input Handling

| Situation | Action |
|---|---|
| Missing information | Infer from context, flag `[INFERRED]`, continue |
| Two sources conflict | Note both, flag `[CONFLICT — VERIFY]` |
| Materials describe multiple programs | Complete skeleton for dominant program, flag ambiguity |
| No owner identifiable | Flag `[OWNER NEEDED]`, add to `flags.owner_needed` |
| No date identifiable | Flag `[DATE NEEDED]`, add to `flags.date_needed` |
| Insufficient data for full build step | Stub with `[INSUFFICIENT DATA]`, continue to next step |
| Irreversible commitment found | Flag `[ONE-WAY DOOR]`, add to `flags.one_way_door` |

---

## Triggers

**Standard:**
```
PROGRAM_NAME: [name]
OUTPUT_FORMAT: [markdown | json | both]
BUILD_MODE: standard
PROGRAM_TYPE: [new | existing_transition]

BEGIN INTAKE PROCESSING
```

**Full build:**
```
PROGRAM_NAME: [name]
OUTPUT_FORMAT: both
BUILD_MODE: full_build
PROGRAM_TYPE: [new | existing_transition]

BEGIN FULL BUILD
```

---

## Companion Specs
- Governed by: `config/constitution.md`
- Invoked by: `engine/program-pipeline-orchestrator.md`
- Invokes: `functions/control-coverage-spec.md`, `functions/risk-register-spec.md`, `functions/calendar-output-spec.md`, `functions/program-comms-spec.md`
- Writes: `runs/[PROGRAM]/latest.json`, `data/[PROGRAM]/[date]-calendar.ics`, `drafts/`
- Logged by: `scripts/provenance_log.py` — output_types: `run_json`, `calendar_export`
