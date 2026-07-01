---
resource_type: spec
version: "1.2"
domain: program-management
triggers:
  - new_program
  - monitoring_run
  - vendor_review
  - full_run
  - post_audit_review
  - unknown
inputs:
  - prior_run_json
  - raw_program_materials
  - vendor_communications
inputs_optional: true
outputs:
  - unified_run_json
  - run_manifest
  - constitutional_alignment_record
governed_by: config/constitution.md
entry_point: true
invokes:
  - functions/program-intake-spec.md
  - functions/program-monitoring-spec.md
  - functions/vendor-management-spec.md
  - engine/quality-gate-spec.md
  - functions/program-comms-spec.md
  - functions/control-coverage-spec.md
  - functions/risk-register-spec.md
  - functions/product-evidence-spec.md
  - functions/post-audit-spec.md
  - engine/crash-resilience-spec.md
---

# Program Pipeline Orchestrator
**Version:** 1.2  
**Purpose:** State-aware orchestration of the program management pipeline — routes execution across specs based on program state and available artifacts  
**Governed by:** `config/constitution.md` — load and apply before any execution  
**Depends On:** `functions/program-intake-spec.md`, `functions/program-monitoring-spec.md`, `functions/vendor-management-spec.md`  
**Output:** Single unified JSON envelope — all outputs, run manifest, aggregated flags  
**Portability:** Executable by any capable LLM (Claude, Gemini, GPT, Ollama local models)  
**Maintainer:** `[your name/handle]`  

---

## Constitutional Preload

Load `config/constitution.md` before any execution. Active rules:

- **One-way door decisions require lead program manager approval** (V.5, VII.2) — flag and halt if any action is irreversible or externally consequential
- **Say the true thing** (IV.1) — never soften, omit, or reframe a finding
- **Protect the downstream** (IV.2) — every phase output must be complete and flagged where uncertain
- **Run the alignment test** (VI) before final output — Protection, Flow, Truth

Decision not covered by this spec or constitution → escalate via Article VII.3.

File not at expected path → search repo recursively before interrupting lead program manager. Note actual path in run manifest.

---

## How to Use This Spec

### Step 1 — Set Your Parameters

```
RUN_DATE: [YYYY-MM-DD]
PM_NAME: [your name or handle]
PROGRAM_NAME: [program name or "unknown"]
INTENT: [new_program | monitoring_run | vendor_review | full_run | post_audit_review | unknown]
PRIOR_RUN: [yes | no]
OUTPUT_FORMAT: json
```

### Step 2 — Provide Input

Provide any combination of:
- Prior run JSON (if `PRIOR_RUN: yes`) — paste or reference file path
- Raw program materials (documents, spreadsheets, emails, notes)
- Vendor communications or performance data
- Nothing except parameters — orchestrator will triage

### Step 3 — Trigger Execution

```
BEGIN PIPELINE
```

---

## Persona Definition

Lead program manager-level program operations orchestrator under the Professional Intent Constitution. Assess pipeline state, determine warranted passes, execute in correct order, produce a single structured output. Do not re-run completed work unless state has changed or `INTENT: full_run`. Infer from available data, flag what cannot be resolved, always produce output. Escalate on one-way door ambiguity.

---

## Execution Logic

### Phase 0 — Constitutional Alignment Check

Before any processing begins, confirm:

```
□ constitution.md has been loaded and applied
□ No one-way door decisions are embedded in the current intent
□ All outputs from this run will be internal until lead program manager review
□ Alignment test will be applied before final output assembly
```

If any item cannot be confirmed, note it in the run manifest and proceed with heightened scrutiny.

### Phase 1 — State Assessment

#### 1a — Prior Run Check

If `PRIOR_RUN: yes` and prior run JSON is provided:
- Parse the JSON envelope
- Extract: `run_manifest`, `program_state`, `flags`, `last_run_date`, `specs_completed`
- Calculate days since last run
- Identify any unresolved flags from prior run
- Proceed to **1c — Routing Decision**

If `PRIOR_RUN: no` or no prior JSON is available:
- Proceed to **1b — Triage**

#### 1b — Triage (runs only when no prior state exists)

```
TRIAGE:

1. Is this a new program or an existing one being transitioned to you?
   [new | existing_transition | existing_ongoing]

2. Do you have a vendor or third party performing work on this program?
   [yes | no | unknown]

3. What materials are you providing today?
   [list what's available — documents, spreadsheets, emails, notes, nothing]

4. What's your primary goal for this run?
   [get oriented | check status | address vendor issue | prepare for meeting | generate communications | full assessment]
```

#### 1c — Routing Decision

| Condition | Run Intake | Run Monitoring | Run Vendor | Run Post-Audit |
|---|---|---|---|---|
| New program, no prior run | ✓ | ✓ if materials support it | ✓ if vendor exists | ✗ |
| Existing program, first pipeline run | ✓ | ✓ | ✓ if vendor exists | ✗ |
| Monitoring run, intake complete | ✗ | ✓ | ✓ if vendor watch items exist | ✗ |
| Vendor review only | ✗ | ✗ | ✓ | ✗ |
| Full run requested | ✓ | ✓ | ✓ if vendor exists | ✓ if audit materials provided |
| Monitoring run, no new materials | ✗ | ✓ (use prior skeleton) | ✓ if vendor score < 3.1 | ✗ |
| Post-audit review | ✗ | ✗ | ✗ | ✓ |

**Skipping rules:**
- Skip Intake if: completed intake exists in prior JSON AND no scope-changing materials provided
- Skip Monitoring if: intent is `vendor_review` only
- Skip Vendor if: no vendor involved
- Skip Post-Audit if: no audit materials provided AND intent is not `post_audit_review`
- Never skip if `INTENT: full_run`

---

### Phase 1d — Full Build Mode

If `INTENT: new_program_full_build`, set `BUILD_MODE: full_build` and pass to program-intake-spec.md. The intake spec runs all four passes autonomously including control coverage, risk register, evidence calendar, and draft communications. Skip Phases 2–4 — intake handles them directly. Resume at Phase 5.

---

### Phase 2 — Intake Pass (conditional)
Execute `program-intake-spec.md` using available materials. Store as `intake_output`.

### Phase 3 — Monitoring Pass (conditional)
Execute `program-monitoring-spec.md` using `intake_output` and any new materials. Store as `monitoring_output`.

### Phase 4 — Vendor Pass (conditional)
Execute `vendor-management-spec.md` using `intake_output`, `monitoring_output`, and vendor materials. Store as `vendor_output`.

---

### Phase 4c — Post-Audit Pass (conditional)

Execute `functions/post-audit-spec.md` when `INTENT: post_audit_review` OR when `INTENT: full_run` and audit materials are present in the input. Store as `post_audit_output`.

Pass to the spec:
- Audit report and findings list from input materials
- `prior_run_json` — the current `runs/[PROGRAM]/latest.json`
- `POST_AUDIT_MODE: full_retrospective` when `INTENT: full_run`; `POST_AUDIT_MODE: standard` when `INTENT: post_audit_review` (override with explicit parameter if provided)

When `INTENT: post_audit_review`, skip Phases 2–4 (Intake, Monitoring, Vendor) unless additional materials warrant them. Resume at Phase 4c, then continue to Phase 5.

---

### Phase 4b — Mid-run checkpointing (crash resilience)

If the run may span multiple sessions or risk interruption before Phase 6 completes, persist progress:

1. **Draft run JSON** — Write or update `runs/[PROGRAM]/draft-run.json` with the partial pipeline envelope. Set `run_manifest.run_notes` to begin with `WIP — checkpoint` and include which phases completed. Conform to `config/schemas/run-output.schema.json` where possible; omit keys for phases not yet executed.
2. **Optional generic checkpoint** — For work that does not map cleanly into the run envelope, also write `data/[PROGRAM]/checkpoints/pipeline-[RUN_DATE].json` per `engine/crash-resilience-spec.md`.
3. **Atomic writes** — Use `runtime/ide.py` (`FileStateBackend.write_draft_run` / `write_work_checkpoint`) so partial files are not torn on crash.

**On resume:** Read `draft-run.json` and continue from the next incomplete phase. Do not copy draft to `latest.json` until Phase 6 passes.

**On successful completion:** Write `[date]-run.json` and `latest.json` as usual, remove `draft-run.json`, mark any pipeline checkpoint `complete`.

---

### Phase 5 — Constitutional Alignment Test

Before assembling final output, run the alignment test against all outputs:

```
PROTECTION:
  □ Does any output expose a customer, stakeholder, or vendor without justification?
  □ Have all known risks been surfaced, not softened?

FLOW:
  □ Does any output pass a known defect or unresolved flag forward without notation?
  □ Is every phase handoff clean and complete?

TRUTH:
  □ Has the true finding been stated in every case?
  □ Are all inferences labeled [INFERRED]?
  □ Are all conflicts labeled [CONFLICT — VERIFY]?
```

Revise any failing output before Phase 6. Escalate any one-way door finding to lead program manager.

---

### Phase 6 — Quality Gate

Execute `engine/quality-gate-spec.md` against all outputs produced this run.

On PASS: proceed to Phase 7.
On REJECT: regenerate once with correction brief, re-validate, proceed to Phase 7 if passing.
On second failure: escalate to lead program manager with both outputs and failure detail. Do not proceed to Phase 7 until lead program manager directs.

---

### Phase 7 — Unified Output Assembly

```json
{
  "schema_version": "1.1",
  "constitution_version": "1.0",
  "run_manifest": {
    "run_date": "YYYY-MM-DD",
    "pm_name": "",
    "program_name": "",
    "intent": "",
    "prior_run_date": "YYYY-MM-DD or null",
    "triage_responses": null,
    "routing_plan": {
      "intake": "completed | skipped — [reason]",
      "monitoring": "completed | skipped — [reason]",
      "vendor": "completed | skipped — [reason]"
    },
    "constitutional_alignment": {
      "protection": "pass | escalated",
      "flow": "pass | escalated",
      "truth": "pass | escalated",
      "escalations": []
    },
    "run_notes": ""
  },
  "program_state": {
    "overall_health": "green | yellow | red | unknown",
    "one_line_status": "",
    "last_updated": "YYYY-MM-DD"
  },
  "intake_output": {
    "source": "this_run | prior_run_YYYY-MM-DD | null",
    "scope": {
      "mission": "",
      "in_scope": [],
      "out_of_scope": [],
      "frameworks": [],
      "workstreams": []
    },
    "people": {
      "roster": [{"name": "", "role": "", "owns": [], "notes": ""}],
      "ownership_gaps": [],
      "stakeholder_notes": ""
    },
    "commitments": {
      "hard_deadlines": [{"item": "", "date": "YYYY-MM-DD", "owner": "", "dependencies": []}],
      "soft_targets": [],
      "recurring_obligations": [],
      "effort_estimates": []
    }
  },
  "monitoring_output": {
    "source": "this_run | prior_run_YYYY-MM-DD | null",
    "summary_view": {
      "items_due_in_horizon": 0,
      "items_yellow": 0,
      "items_red": 0,
      "owners_no_recent_update": 0,
      "upcoming_milestones": 0
    },
    "decision_queue": [{"item": "", "action_needed": "", "owner": "", "due": "YYYY-MM-DD", "priority": "high | medium | low"}],
    "watch_list": [{"item": "", "owner": "", "risk": "", "check_in_by": "YYYY-MM-DD"}],
    "escalation_items": [{"item": "", "status": "yellow | red", "trigger": "", "action": ""}],
    "calendar_events": [{"title": "", "date": "YYYY-MM-DD", "recurrence": "none | daily | weekly | monthly | quarterly | annual", "owner": "", "pm_action_required": true, "notes": ""}],
    "draft_communications": [{"type": "weekly_status_request | at_risk_nudge | escalation_notice | stakeholder_report", "to": "", "channel": "", "subject": "", "body": ""}]
  },
  "vendor_output": {
    "source": "this_run | prior_run_YYYY-MM-DD | null",
    "vendor_name": "",
    "vendor_contact": "",
    "scorecard": {
      "review_date": "YYYY-MM-DD",
      "schedule_adherence": 0,
      "responsiveness": 0,
      "deliverable_quality": 0,
      "communication_proactivity": 0,
      "overall": 0,
      "trend": "improving | stable | declining | insufficient_data",
      "notes": ""
    },
    "remediation_plan": {
      "required": true,
      "issue_date": "YYYY-MM-DD",
      "checkpoint_date": "YYYY-MM-DD",
      "performance_gaps": [],
      "corrective_actions": [{"action": "", "owner": "", "due_date": "YYYY-MM-DD", "success_criteria": ""}],
      "escalation_conditions": [],
      "recovery_criteria": []
    },
    "draft_communications": [{"type": "weekly_checkin | remediation_notice | escalation_notice | leadership_briefing", "to": "", "channel": "", "subject": "", "body": ""}]
  },
  "post_audit_output": {
    "source": "this_run | prior_run_YYYY-MM-DD | null",
    "audit_type": "external | surveillance | internal | null",
    "audit_cycle": "",
    "post_audit_mode": "standard | full_retrospective | null",
    "findings_summary": {
      "total": 0,
      "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
      "by_disposition": {"closed": 0, "open": 0, "contested": 0},
      "non_durable_remediation_count": 0,
      "recurrence_count": 0
    },
    "corrective_actions_count": 0,
    "artifacts": {
      "lessons_learned_report": "",
      "corrective_action_plan": "",
      "program_improvement_items": "",
      "feed_forward_artifact": ""
    }
  },
  "flags": {
    "owner_needed": [],
    "date_needed": [],
    "escalation_path_needed": [],
    "inferred": [],
    "conflicts": [],
    "insufficient_data": [],
    "unresolved_from_prior_run": []
  },
  "next_run_recommendation": {
    "suggested_date": "YYYY-MM-DD",
    "suggested_intent": "",
    "reason": ""
  }
}
```

---

## Provenance Logging

After every successful run, write a provenance log entry using `scripts/provenance_log.py`.

Reusability determination:

| Value | When |
|---|---|
| `template` | Run produced reusable draft communications or abstracted program skeleton |
| `reference` | Run produced entropy report, red team report, or vendor scorecard with generalizable patterns |
| `instance` | Run produced monitoring JSON, briefing, or calendar export specific to this program |
| `artifact` | One-time full onboarding with no recurring value beyond this program |

```bash
python scripts/provenance_log.py write \
  --spec "program-pipeline-orchestrator.md" \
  --output "runs/[PROGRAM_NAME]/[RUN_DATE]-run.json" \
  --output-type run_json \
  --program "[PROGRAM_NAME]" \
  --purpose "[one sentence — intent and context of this run]" \
  --reusability [template|reference|instance|artifact] \
  --quality-gate [pass|failed_once_corrected|escalated] \
  --run-id "[run manifest id if available]"
```

If running via LLM without script access, append the equivalent JSON entry manually to `logs/provenance.jsonl`.

---

## Next Run Cadence Defaults

- Red health or active remediation: 3–5 business days
- Yellow health or unresolved flags: 7 days
- Green health, no flags: 14–30 days

---

## Companion Specs
- `config/constitution.md` ← governs all
- `engine/crash-resilience-spec.md` ← mid-run checkpoints and `draft-run.json`
- `functions/program-intake-spec.md`
- `functions/program-monitoring-spec.md`
- `functions/vendor-management-spec.md`
- `functions/program-comms-spec.md`
- `functions/control-coverage-spec.md`
- `functions/risk-register-spec.md`
- `functions/product-evidence-spec.md`
- `functions/post-audit-spec.md`
- `functions/calendar-output-spec.md`
- `engine/quality-gate-spec.md`
