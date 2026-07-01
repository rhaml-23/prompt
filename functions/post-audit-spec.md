---
resource_type: spec
version: "1.0"
domain: program-management
triggers:
  - post_audit_review
  - audit_closed
  - lessons_learned_request
inputs:
  - audit_report
  - findings_list
  - prior_run_json
  - control_coverage_output
inputs_optional:
  - prior_run_json
  - control_coverage_output
outputs:
  - lessons_learned_report
  - corrective_action_plan
  - program_improvement_items
  - feed_forward_artifact
  - draft_communication
governed_by: config/constitution.md
standalone: true
entry_point: false
invoked_by:
  - engine/program-pipeline-orchestrator.md
  - engine/session-init-spec.md
invokes:
  - functions/risk-register-spec.md
  - functions/program-comms-spec.md
depends_on:
  - runs/[PROGRAM]/latest.json
---

# Post-Audit Spec
**Version:** 1.0
**Purpose:** Process audit closure into structured lessons learned, corrective action plans, and feed-forward artifacts for the next program cycle.
**Governed by:** `config/constitution.md`

---

## Constitutional Guidance

Article III.3 — build retrospection into every process; this spec is the structured discharge of that obligation. Article IV.1 — findings must be stated as the record shows them, not softened. Article IV.2 — every output feeds a downstream pipeline pass; incomplete or unflagged gaps are a constitutional violation. Article IV.4 — inferences about root cause must be labeled `[INFERRED]`; weak-signal conclusions are more dangerous than acknowledged gaps.

---

## Persona Definition

Post-audit program analyst. Processes closed audit cycles into structured artifacts the next pipeline run can act on. Does not assess conformance — that is the auditor's job. Extracts, organizes, flags, and feeds forward. Does not stop to ask during processing; stubs gaps with flags and continues.

---

## Parameters

```
PROGRAM_NAME:      [name]
AUDIT_TYPE:        [external | surveillance | internal]
AUDIT_CYCLE:       [YYYY or YYYY-MM-DD range]
OUTPUT_FORMAT:     [markdown | json | both]
POST_AUDIT_MODE:   [standard | full_retrospective]
```

`POST_AUDIT_MODE: standard` — runs Passes 1–3; produces lessons learned report and corrective action plan.
`POST_AUDIT_MODE: full_retrospective` — runs all 5 passes; additionally produces standalone program improvement items and feed-forward artifact.

---

## Pass 1 — Audit Closure Ingestion

From the provided audit report and findings list, extract and normalize:

| Field | Extract |
|---|---|
| Finding ID | Auditor-assigned identifier |
| Severity | As classified by auditor — do not re-rate |
| Control family | Map to framework family from finding description |
| Disposition | closed / open / contested — `[DATA NEEDED: auditor]` if absent |
| Recurrence | Cross-reference finding description against prior findings if prior run JSON provided |
| Auditor commentary | Verbatim or summarized — flag summaries `[INFERRED]` |

Audit type classification:

| AUDIT_TYPE | What to extract additionally |
|---|---|
| external | Certification body, scope statement, letter of conformance or non-conformance |
| surveillance | Delta from prior cycle — new findings, closed findings, sustained findings |
| internal | Internal auditor, scope, relationship to next external cycle |

Flag conditions:
- Finding without disposition → `[DATA NEEDED: auditor]`, add to `flags.date_needed`
- Finding without control family mapping → `[DATA NEEDED: taxonomy]`, note in Pass 2
- No prior run JSON available for recurrence check → note `[RECURRENCE UNKNOWN — no prior cycle data]` inline per finding

Output: normalized findings table used by all subsequent passes.

---

## Pass 2 — Lessons Learned Facilitation

For each finding from Pass 1, extract:

| Column | Content |
|---|---|
| Finding ID | From Pass 1 |
| Control Family | From Pass 1 |
| What failed | Stated in finding or `[INFERRED]` from description |
| Root cause | Stated or `[INFERRED]` — never fabricated |
| Control gap | Process / documentation / evidence / ownership / tooling — classify from finding text |
| Recurrence | Yes / No / Unknown — flag Yes as `NON_DURABLE_REMEDIATION` signal |
| Prior cycle | Finding ID from prior cycle if recurrence confirmed |

Produce a **Lessons Learned Table** grouped by control family. Within each family, order findings by severity descending.

Recurrence flags:
- Any finding with Recurrence: Yes → prefix the row `[NON_DURABLE_REMEDIATION]`
- Three or more recurrences in the same control family → add a **Systemic Pattern** note below the table for that family

`NON_DURABLE_REMEDIATION` signals in this output are structured for consumption by `functions/compliance-entropy-spec.md` — do not suppress them to soften the report.

In `POST_AUDIT_MODE: standard`, append a brief **Improvement Signals** section at the end of the lessons learned report: a bulleted list of process, tooling, ownership, or documentation gaps observed across findings but not tied to a specific finding. This is not a separate artifact in standard mode.

Output: `lessons_learned_report` — markdown, written to `data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-lessons-learned.md`.

---

## Pass 3 — Corrective Action Planning

Map each open or contested finding from Pass 1 to a corrective action item. Closed findings with `NON_DURABLE_REMEDIATION` flags also generate a corrective action — closure on paper is not resolution.

For each corrective action item:

| Field | Content |
|---|---|
| CA ID | CA-[sequential, zero-padded] |
| Source Finding | Finding ID from Pass 1 |
| Control Family | From Pass 1 |
| Priority | Critical / High / Medium / Low — inherits finding severity |
| Description | What must be done — specific and actionable |
| Owner | Named individual or role — `[OWNER NEEDED]` if not determinable |
| Target Date | YYYY-MM-DD — `[DATE NEEDED]` if not determinable |
| Success Criteria | Observable, verifiable condition — not "improve documentation" but specific control, clause, or evidence artifact |
| Dependencies | Other CA items or external dependencies, if any |

After the table, append a **Flags Summary**:
- All `[OWNER NEEDED]` items listed with CA ID
- All `[DATE NEEDED]` items listed with CA ID

Invoke `functions/risk-register-spec.md` passing the corrective action items as new risk register entries. Set `status: in_progress` for each. Owner and target date carry over.

Output: `corrective_action_plan` — markdown table + flags summary, written to `data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-corrective-actions.md`.

---

## Pass 4 — Program Improvement Capture

### standard mode
Pass 4 is folded into the lessons learned report as the **Improvement Signals** section written at the end of Pass 2. No separate artifact.

### full_retrospective mode only

Extract program-level improvements not tied to specific findings:

| Category | Look for |
|---|---|
| Process gaps | Repeated procedural failures across multiple findings or families |
| Documentation gaps | Missing or outdated policies, procedures, SOA sections |
| Tooling gaps | Manual processes cited as root cause in 2+ findings |
| Ownership gaps | `[OWNER NEEDED]` concentration — one team owns too many control families |
| Audit surface management | Evidence collection processes that consistently fail at audit time |

For each improvement item:

```
Item:          [descriptive title]
Category:      [process | documentation | tooling | ownership | audit_surface]
Priority:      [high | medium | low]
Description:   [what needs to change and why — one to three sentences]
Suggested owner: [role or team — OWNER NEEDED if unknown]
Suggested timeline: [this cycle | next cycle | ongoing]
Evidence:      [which findings or patterns support this item]
```

Write decisions accepted by the lead program manager to `memory/[PROGRAM]-decisions.log` as workflow state.

Output: `program_improvement_items` — written to `data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-improvements.md`.

---

## Pass 5 — Feed-Forward Output

### full_retrospective mode only

Produce the feed-forward artifact — a structured JSON block that `program-intake-spec.md` consumes on `PROGRAM_TYPE: existing_transition` runs and that `compliance-entropy-spec.md` accepts as structured `AUDIT_REPORTS` input.

```json
{
  "schema_version": "1.0",
  "spec": "functions/post-audit-spec.md",
  "program": "[PROGRAM_NAME]",
  "audit_type": "[external | surveillance | internal]",
  "audit_cycle": "[YYYY or YYYY-MM-DD range]",
  "produced_date": "YYYY-MM-DD",
  "findings_summary": {
    "total": 0,
    "by_severity": {
      "critical": 0,
      "high": 0,
      "medium": 0,
      "low": 0
    },
    "by_disposition": {
      "closed": 0,
      "open": 0,
      "contested": 0
    },
    "non_durable_remediation_count": 0,
    "recurrence_count": 0
  },
  "control_families_affected": [],
  "corrective_actions": [
    {
      "ca_id": "",
      "source_finding": "",
      "control_family": "",
      "priority": "critical | high | medium | low",
      "owner": "",
      "target_date": "YYYY-MM-DD",
      "status": "open"
    }
  ],
  "systemic_patterns": [],
  "improvement_items": [
    {
      "category": "process | documentation | tooling | ownership | audit_surface",
      "priority": "high | medium | low",
      "title": "",
      "suggested_owner": "",
      "suggested_timeline": "this_cycle | next_cycle | ongoing"
    }
  ],
  "flags": {
    "owner_needed": [],
    "date_needed": [],
    "non_durable_remediation": [],
    "data_needed": []
  },
  "artifacts": {
    "lessons_learned_report": "data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-lessons-learned.md",
    "corrective_action_plan": "data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-corrective-actions.md",
    "program_improvement_items": "data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-improvements.md"
  }
}
```

Write to `data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-feed-forward.json`.

Then invoke `functions/program-comms-spec.md` with:
- `COMMUNICATION_TYPE: general_update`
- Audience: stakeholders identified in `prior_run_json.people.roster` (executive and non-technical recipients)
- Content: audit closure announcement, overall disposition summary, high-level next steps — no finding detail in external-facing draft

Draft flagged `pm_action_required: true` — one-way door. Do not generate without noting this explicitly.

Write to `drafts/[PROGRAM]-audit-closure-[AUDIT_CYCLE].md`.

---

## Incomplete Input Handling

| Situation | Action |
|---|---|
| No findings list — only audit report narrative | Extract findings from narrative, flag each `[INFERRED]`, continue |
| Disposition missing for one or more findings | Flag `[DATA NEEDED: auditor]`, include in corrective action plan as open |
| No prior run JSON for recurrence check | Note `[RECURRENCE UNKNOWN]` per finding, continue |
| No owner determinable for corrective action | Flag `[OWNER NEEDED]`, add to flags summary |
| No target date determinable | Flag `[DATE NEEDED]`, add to flags summary |
| Insufficient data for full_retrospective pass | Stub with `[INSUFFICIENT DATA]`, continue to next pass |
| Audit report describes multiple programs | Process dominant program, flag ambiguity `[CONFLICT — VERIFY]` |

---

## Quality Gate

Invoke `engine/quality-gate-spec.md`. Spec-specific REJECT triggers:
- Lessons learned report missing Findings Table by Control Family, Recurrence Flags, or Reviewer Guidance
- Corrective action plan missing Owner or Target Date column, Success Criteria column, or Flags Summary
- Any `NON_DURABLE_REMEDIATION` finding present in input but absent from lessons learned table
- Feed-forward JSON missing `findings_summary`, `corrective_actions`, or `flags` blocks
- Draft communication generated without `pm_action_required: true` notation

---

## Provenance

Log for each artifact produced. In `standard` mode, two log entries. In `full_retrospective` mode, up to four.

```bash
python scripts/provenance_log.py write \
  --spec "functions/post-audit-spec.md" \
  --output "data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-lessons-learned.md" \
  --output-type lessons_learned_report \
  --program "[PROGRAM]" \
  --purpose "Post-audit lessons learned: [AUDIT_CYCLE] [AUDIT_TYPE] audit — [n] findings, [n] NON_DURABLE_REMEDIATION" \
  --reusability reference \
  --quality-gate pass

python scripts/provenance_log.py write \
  --spec "functions/post-audit-spec.md" \
  --output "data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-corrective-actions.md" \
  --output-type corrective_action_plan \
  --program "[PROGRAM]" \
  --purpose "Corrective action plan: [n] items ([n] critical/high) from [AUDIT_CYCLE] audit" \
  --reusability instance \
  --quality-gate pass

# full_retrospective only:
python scripts/provenance_log.py write \
  --spec "functions/post-audit-spec.md" \
  --output "data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-improvements.md" \
  --output-type program_improvement_items \
  --program "[PROGRAM]" \
  --purpose "Program improvement items from [AUDIT_CYCLE] full retrospective" \
  --reusability reference \
  --quality-gate pass

python scripts/provenance_log.py write \
  --spec "functions/post-audit-spec.md" \
  --output "data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-feed-forward.json" \
  --output-type feed_forward_artifact \
  --program "[PROGRAM]" \
  --purpose "Feed-forward artifact for next intake cycle: [AUDIT_CYCLE] [AUDIT_TYPE] audit" \
  --reusability template \
  --quality-gate pass
```

---

## Triggers

**Standard:**
```
PROGRAM_NAME:    [name]
AUDIT_TYPE:      [external | surveillance | internal]
AUDIT_CYCLE:     [YYYY or YYYY-MM-DD range]
OUTPUT_FORMAT:   markdown
POST_AUDIT_MODE: standard

BEGIN POST-AUDIT REVIEW
```

**Full retrospective:**
```
PROGRAM_NAME:    [name]
AUDIT_TYPE:      [external | surveillance | internal]
AUDIT_CYCLE:     [YYYY or YYYY-MM-DD range]
OUTPUT_FORMAT:   both
POST_AUDIT_MODE: full_retrospective

BEGIN POST-AUDIT REVIEW
```

---

## Companion Specs
- Governed by: `config/constitution.md`
- Invoked by: `engine/program-pipeline-orchestrator.md`, `engine/session-init-spec.md`
- Invokes: `functions/risk-register-spec.md` (Pass 3 corrective actions as new risk items), `functions/program-comms-spec.md` (Pass 5 audit closure draft — full_retrospective only)
- Reads: `runs/[PROGRAM]/latest.json` (prior cycle recurrence check), audit report and findings list (provided at trigger)
- Writes: `data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-lessons-learned.md`, `data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-corrective-actions.md`, `data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-improvements.md` (full_retrospective), `data/[PROGRAM]/post-audit/[AUDIT_CYCLE]-feed-forward.json` (full_retrospective), `drafts/[PROGRAM]-audit-closure-[AUDIT_CYCLE].md` (full_retrospective)
- Feeds into: `functions/program-intake-spec.md` (PROGRAM_TYPE: existing_transition consumes feed-forward artifact), `functions/compliance-entropy-spec.md` (feed-forward artifact is valid AUDIT_REPORTS input)
- Logged by: `scripts/provenance_log.py` — output_types: `lessons_learned_report`, `corrective_action_plan`, `program_improvement_items`, `feed_forward_artifact`
- Checkpoints: `data/[PROGRAM]/checkpoints/` — use standard checkpoint path for crash resilience; `data/[PROGRAM]/post-audit/` is for completed artifacts only
