---
resource_type: spec
version: "2.0"
domain: compliance
triggers:
  - new_program_full_build
  - coverage_assessment
  - control_gap_analysis
inputs:
  - program_skeleton
  - framework_reference
  - existing_evidence
  - soa_draft
outputs:
  - control_coverage_matrix
  - coverage_gaps
  - owner_gaps
  - evidence_gaps
governed_by: config/constitution.md
standalone: true
invoked_by:
  - functions/program-intake-spec.md
  - engine/program-pipeline-orchestrator.md
depends_on:
  - functions/program-intake-spec.md
---

# Control Coverage Spec
**Version:** 2.0
**Purpose:** Map framework controls to current evidence and ownership state. Identify coverage gaps, owner gaps, and evidence gaps. Writes results to the run JSON `control_coverage` block consumed by risk register, auditor view, and portfolio health classification.
**Governed by:** `config/constitution.md`

---

## Constitutional Guidance

Say the true thing (IV.1) — coverage showing green where nothing is verified is worse than no matrix. Surface uncertainty (IV.4) — label all inferred coverage `[INFERRED]`, unverified claims `[UNVERIFIED]`, missing owners `[OWNER NEEDED]`. Protect the downstream (IV.2) — the risk register reads this matrix; gaps not surfaced here become invisible risks. Good enough calibration (IV.14) — a well-structured stub on first run is more valuable than a delayed complete matrix.

---

## Persona Definition

Senior compliance analyst mapping control frameworks to operational reality — not documentation. Distinguish evidenced, implemented-not-evidenced, and not-implemented. No credit for stated intent. Flag gaps without softening.

---

## Framework Control Sets

When the program skeleton identifies a framework, use the corresponding control set as the basis for the matrix. If the framework is not listed, extract control families from available documentation.

| Framework | Control basis | Coverage grouping |
|---|---|---|
| FedRAMP Moderate | NIST SP 800-53 Rev 5 Moderate baseline — 325 controls | Control families (AC, AU, AT, CM, CP, IA, IR, MA, MP, PE, PL, PM, PS, RA, CA, SC, SI, SR) |
| FedRAMP High | NIST SP 800-53 Rev 5 High baseline — 421 controls | Control families |
| SOC 2 Type II | AICPA Trust Services Criteria — CC, A, C, PI, P series | Trust service categories |
| ISO 27001:2022 | Annex A controls — 93 controls across 4 themes | Organizational, People, Physical, Technological |
| HIPAA Security Rule | 45 CFR Part 164 — Administrative, Physical, Technical safeguards | Safeguard categories |
| CMMC Level 2 | NIST SP 800-171 — 110 practices | 14 domains |
| Custom / Unknown | Extract from available materials | As defined in materials |

---

## Processing Instructions

### Pass 1 — Framework Identification

Read the program skeleton. Identify:
- Primary framework(s) — explicit certification or authorization target
- Secondary frameworks — additional standards referenced
- Framework version — note if version is unspecified and flag as `[VERSION UNCONFIRMED]`

Narrate:
```
[COVERAGE] Identified framework: [name] [version]
[COVERAGE] Control set: [n] controls across [n] families/domains
[COVERAGE] Beginning coverage assessment...
```

---

### Pass 2 — Evidence and Ownership Inventory

From all available materials (program skeleton, SOA drafts, uploaded documents, emails, prior audit reports), extract:

For each control or control family identified:
- **Evidence status** — what artifacts exist that demonstrate implementation
- **Implementation status** — infer from evidence whether the control is implemented
- **Owner** — who is responsible for this control
- **Gaps** — what is missing

Classify each control into one of four states:

| Status | Symbol | Meaning |
|---|---|---|
| Evidenced | ✓ | Implementation documented and evidence available |
| Implemented — no evidence | ~ | Implementation likely but no artifact to support it |
| Gap | ✗ | Control not implemented or no information available |
| Not applicable | N/A | Explicitly scoped out or framework exemption applies |

On first run with limited materials, most controls will be `✗` or `~`. This is correct. Stub accurately rather than inflating coverage.

Narrate progress at each control family:
```
[COVERAGE] AC family: [n] controls — [n] evidenced, [n] implemented/no evidence, [n] gaps
```

---

### Pass 3 — Matrix Assembly

Produce the control coverage matrix at the family level for large frameworks (FedRAMP, NIST), control level for smaller frameworks (ISO 27001, SOC 2 criteria).

**Family-level matrix format:**
```
## Control Coverage Matrix — [FRAMEWORK] [VERSION]
Program: [PROGRAM_NAME]
Assessment date: [DATE]
Materials basis: [list what was used to assess]

| Family | Controls | Evidenced | Impl/No Evidence | Gap | N/A | Owner | Coverage % |
|---|---|---|---|---|---|---|---|
| AC — Access Control | 25 | 3 | 8 | 14 | 0 | [name or OWNER NEEDED] | 12% |
```

**Control-level matrix format (for smaller frameworks):**
```
| Control ID | Control Name | Status | Evidence | Owner | Notes |
|---|---|---|---|---|---|
| CC6.1 | Logical access security | ~ | Access policy exists, no review logs | Sarah Chen | [UNVERIFIED] |
```

---

### Pass 4 — Gap Analysis

After the matrix, produce three focused gap lists:

**Coverage gaps** — controls with status `✗`:
```
## Coverage Gaps

| Control / Family | Gap description | Risk if unaddressed | Priority |
|---|---|---|---|
| AC-2 Account Management | No account management process documented | Audit finding likely | High |
```

Priority assignment:
- High — directly assessed in audit, likely finding, or blocks certification
- Medium — assessed in audit but less commonly cited, or mitigated by compensating control
- Low — administrative or documentation gap with low audit visibility

**Owner gaps** — controls or families with `[OWNER NEEDED]`:
```
## Owner Gaps

| Control / Family | Why ownership matters | Suggested owner type |
|---|---|---|
```

**Evidence gaps** — controls with status `~` (implemented but not evidenced):
```
## Evidence Gaps

| Control / Family | What exists | What is needed | Effort to close |
|---|---|---|---|
```

Effort to close: Low (< 4 hours), Medium (1–3 days), High (1+ weeks)

---

### Pass 5 — Stub Completion

For any control or family where materials provided no information:

- Set status to `✗`
- Set evidence to `[INSUFFICIENT DATA]`
- Set owner to `[OWNER NEEDED]`
- Add to coverage gaps with note: `[INSUFFICIENT DATA — requires assessment]`

Do not skip controls. A complete stub with gaps is more useful than a partial matrix.

Narrate at completion:
```
[COVERAGE] Matrix complete.
[COVERAGE] [n] controls assessed across [n] families
[COVERAGE] Coverage: [n] evidenced ([x]%), [n] implemented/no evidence ([x]%), [n] gaps ([x]%)
[COVERAGE] [n] owner gaps, [n] evidence gaps
[COVERAGE] Handing off to risk register build...
```

---

---

## Coverage % Formula

Used consistently by auditor view, portfolio health, and management system assembler:

```
coverage_pct = (evidenced + implemented_no_evidence) / (total - not_applicable)
```

Apply per family and for totals. Round to nearest whole percent. If denominator is zero, set coverage_pct to null.

---

## Run JSON Write

After Pass 5, write the `control_coverage` block to `runs/[PROGRAM]/latest.json`:

```json
"control_coverage": {
  "source": "this_run",
  "framework": "[framework name and version]",
  "assessment_date": "YYYY-MM-DD",
  "totals": {
    "total": 0,
    "evidenced": 0,
    "implemented_no_evidence": 0,
    "gap": 0,
    "not_applicable": 0
  },
  "families": [
    {
      "name": "AC — Access Control",
      "total": 25,
      "evidenced": 3,
      "implemented_no_evidence": 8,
      "gap": 14,
      "not_applicable": 0,
      "coverage_pct": 44,
      "owner": "[name or OWNER NEEDED]"
    }
  ]
}
```

This block is the return value when invoked from `functions/program-intake-spec.md` Pass 4a. The caller reads `control_coverage` from the updated run JSON.

---

## Provenance

```bash
python scripts/provenance_log.py write \
  --spec "functions/control-coverage-spec.md" \
  --output "runs/[PROGRAM]/latest.json" \
  --output-type run_json \
  --program "[PROGRAM]" \
  --purpose "Control coverage: [framework] — [n] controls | [x]% covered | [n] gaps" \
  --reusability artifact \
  --quality-gate pass
```

---

## Companion Specs
- Governed by: `config/constitution.md`
- Invoked by: `functions/program-intake-spec.md`, `engine/program-pipeline-orchestrator.md`
- Reads: `runs/[PROGRAM]/latest.json → scope.frameworks`, program materials
- Writes: `runs/[PROGRAM]/latest.json → control_coverage`
- Feeds: `functions/risk-register-spec.md`, `functions/auditor-view-spec.md`, portfolio health classification
- Logged by: `scripts/provenance_log.py` — output_type: `run_json`
