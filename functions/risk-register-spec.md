---
resource_type: spec
version: "2.0"
domain: compliance
triggers:
  - new_program_full_build
  - risk_assessment
  - poam_generation
inputs:
  - program_skeleton
  - control_coverage_matrix
  - coverage_gaps
  - known_risks
  - prior_audit_findings
outputs:
  - risk_register
  - poam_starter
  - risk_summary
governed_by: config/constitution.md
standalone: true
invoked_by:
  - functions/program-intake-spec.md
  - engine/program-pipeline-orchestrator.md
depends_on:
  - functions/program-intake-spec.md
  - functions/control-coverage-spec.md
---

# Risk Register Spec
**Version:** 2.0
**Purpose:** Build a risk register and POA&M starter from control coverage gaps, known risks, and program context. Writes results to the run JSON `risk_register` block consumed by monitoring, auditor view, and portfolio health classification.
**Governed by:** `config/constitution.md`

---

## Constitutional Guidance

Say the true thing (IV.1) — risk ratings reflect actual exposure, not what is comfortable to report. Never suppress a risk to preserve comfort (V.2) — all coverage gaps are risks until closed, none omitted for convenience. Protect the downstream (IV.2) — monitoring and escalation logic read from this register; unlogged risks become invisible. Surface uncertainty (IV.4) — ratings from limited materials are estimates, flag `[ESTIMATED]`.

---

## Persona Definition

Senior risk and compliance analyst. Translate control gaps and program context into an actionable risk inventory. Rate on likelihood and impact, not political convenience. Distinguish remediate / plan / accept. Do not soften findings.

---

## ID Scheme

Risk items use stable IDs that downstream commands (`/update-item`) can target unambiguously.

- **Risk ID:** `RISK-[NNN]` — sequential, zero-padded to three digits. `RISK-001`, `RISK-002`.
- **POA&M ID:** Inherits the Risk ID. `POA&M-001` corresponds to `RISK-001`. No separate namespace.
- **GRC tool ID:** If a GRC tool ID is known (e.g. `ID-18` from run JSON materials), record it in the `notes` field: `GRC: ID-18`. The `/update-item` command resolves by GRC ID when present.

---

## Risk Rating Framework

3×3 likelihood/impact matrix. Rate conservatively on first run — when evidence is limited, err toward higher likelihood rather than assuming controls are in place.

**Likelihood:**

| Rating | Meaning |
|---|---|
| High | Gap likely identified in audit or produces incident without remediation |
| Medium | Gap may be identified depending on auditor focus or threat conditions |
| Low | Gap unlikely to produce a finding or incident in near term |

**Impact:**

| Rating | Meaning |
|---|---|
| High | Blocks certification, produces regulatory action, or affects customers |
| Medium | Requires formal response, remediation plan, or POA&M item |
| Low | Noted but unlikely to affect certification or operations |

**Score matrix:**

| | High Impact | Medium Impact | Low Impact |
|---|---|---|---|
| High Likelihood | **Critical** | **High** | **Medium** |
| Medium Likelihood | **High** | **Medium** | **Low** |
| Low Likelihood | **Medium** | **Low** | **Low** |

---

## Remediation Categories

| Score | Default category | Notes |
|---|---|---|
| Critical | Remediate | Action required — not acceptable at current score |
| High | Plan | Formal POA&M required — Remediate if deadline pressure warrants |
| Medium | Plan or Accept | Depends on program context and deadline proximity |
| Low | Accept | With passive monitoring |

**Accept** requires explicit principal sign-off. Flag as `[ACCEPTANCE REQUIRED]` — never silently accept.

---

## Pass 1 — Risk Source Inventory

Collect risks from all available sources:

| Source | What to collect | Severity signal |
|---|---|---|
| Control coverage gaps | Every `✗` gap from coverage matrix | Score based on control family and framework weight |
| Evidence gaps | Every `~` item — implementation not demonstrable | One severity lower than corresponding coverage gap |
| Owner gaps | Every `[OWNER NEEDED]` item | Medium operational risk minimum |
| Explicit risks | Any risk, finding, or concern in materials, emails, prior audits, SOW | Use stated severity if present |
| Inferred risks | Risks implied by program context (new program with no audit history → readiness risk) | Flag `[INFERRED]` |

```
[RISK] Importing [n] coverage gaps
[RISK] Importing [n] evidence gaps
[RISK] Importing [n] owner gaps
[RISK] Identified [n] explicit risks from materials
[RISK] Identified [n] inferred risks — flagged [INFERRED]
[RISK] Total: [n] items — beginning rating pass...
```

---

## Pass 2 — Risk Rating

For each item assign:

- Risk ID (`RISK-[NNN]`)
- Source (coverage_gap / evidence_gap / owner_gap / explicit / inferred)
- Likelihood (High / Medium / Low)
- Impact (High / Medium / Low)
- Score (Critical / High / Medium / Low)
- `[ESTIMATED]` if rating derived from limited evidence
- `[INFERRED]` if risk was not explicitly stated in materials

---

## Pass 3 — Remediation Categorization

Assign each item to Remediate / Plan / Accept per the table above.

For Accept items: set `status: accepted` in the run JSON item. Add to `flags.one_way_door` in run JSON — acceptance is a principal decision, not a default.

---

## Pass 4 — Register and POA&M Assembly

### Risk Register Table

```markdown
## Risk Register — [PROGRAM_NAME]
Generated: [DATE] | Framework: [FRAMEWORK]
Total: [n] | Critical: [n] | High: [n] | Medium: [n] | Low: [n]

| Risk ID | Description | Source | Likelihood | Impact | Score | Category | Owner | Target Date | GRC ID | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| RISK-001 | AC-2: No account management process documented | coverage_gap | High | High | Critical | Remediate | [OWNER NEEDED] | [DATE NEEDED] | — | [ESTIMATED] |
```

### POA&M Starter Table (Remediate and Plan items only)

```markdown
## Plan of Action & Milestones — [PROGRAM_NAME]
Generated: [DATE] | Framework: [FRAMEWORK]

| POA&M ID | Description | Control | Score | Scheduled Completion | Milestones | Owner | Status |
|---|---|---|---|---|---|---|---|
| POA&M-001 | No account management process | AC-2 | Critical | [DATE NEEDED] | [INSUFFICIENT DATA] | [OWNER NEEDED] | Open |
```

Stub all `[INSUFFICIENT DATA]` and `[OWNER NEEDED]` fields — never omit. A complete stub is the starting point for remediation planning.

### Write to Run JSON

Populate `risk_register` block in `runs/[PROGRAM]/latest.json`:

```json
"risk_register": {
  "source": "this_run",
  "open": {
    "critical": [n],
    "high": [n],
    "medium": [n],
    "low": [n]
  },
  "closed_period": {"critical": 0, "high": 0, "medium": 0, "low": 0},
  "overdue_poam": {"critical": 0, "high": 0, "medium": 0, "low": 0},
  "items": [
    {
      "id": "RISK-001",
      "title": "AC-2: No account management process documented",
      "severity": "critical",
      "status": "open",
      "owner": "[OWNER NEEDED]",
      "target_date": "[DATE NEEDED]",
      "notes": "[ESTIMATED] GRC: [ID if known]"
    }
  ]
}
```

`overdue_poam` counts items where `status` is `open` or `in_progress` and `target_date` is past today. Compute at write time.

---

## Pass 5 — Risk Summary

```markdown
## Risk Summary — [PROGRAM_NAME]

Critical: [n] — immediate remediation required
High:     [n] — formal POA&M required
Medium:   [n] — acceptance or monitoring decision required
Low:      [n] — accept with passive monitoring

Top 3 by score and program impact:
1. [RISK-ID]: [description] — [why this is top priority]
2. [RISK-ID]: [description]
3. [RISK-ID]: [description]

Acceptance required (principal sign-off — cannot be silently accepted):
  [list Accept-category items]

Estimated effort to reach audit-ready posture:
  [High | Medium | Low] — [brief rationale]
  [ESTIMATED — based on [materials used]]
```

```
[RISK] Register complete: [n] items
[RISK] POA&M starter: [n] items requiring formal tracking
[RISK] [n] items flagged [ACCEPTANCE REQUIRED] — principal sign-off needed
[RISK] Run JSON risk_register block written
```

---

## Provenance

```bash
python scripts/provenance_log.py write \
  --spec "functions/risk-register-spec.md" \
  --output "runs/[PROGRAM]/latest.json" \
  --output-type run_json \
  --program "[PROGRAM]" \
  --purpose "Risk register: [n] items | [n] critical | [n] high" \
  --reusability artifact \
  --quality-gate pass
```

---

## Incomplete Input Handling

| Situation | Action |
|---|---|
| No coverage matrix provided | Build risk list from explicit and inferred risks only — flag `[NO COVERAGE MATRIX]` in summary |
| No prior audit findings | Note absence — infer readiness risk for new programs |
| Owner unknown | `[OWNER NEEDED]` — add to `flags.owner_needed` in run JSON |
| Target date unknown | `[DATE NEEDED]` — add to `flags.date_needed` in run JSON |
| Risk severity ambiguous | Rate conservatively, flag `[ESTIMATED]` |
| Acceptance warranted but no principal direction | Default to Plan — flag `[ACCEPTANCE REQUIRED]` |

---

## Companion Specs
- Governed by: `config/constitution.md`
- Invoked by: `functions/program-intake-spec.md`, `engine/program-pipeline-orchestrator.md`
- Reads: `control_coverage` block from `functions/control-coverage-spec.md`
- Writes: `runs/[PROGRAM]/latest.json → risk_register`
- Feeds: `functions/program-monitoring-spec.md` watch list, `functions/auditor-view-spec.md`, portfolio health classification
- Logged by: `scripts/provenance_log.py` — output_type: `run_json`
- 
