---
resource_type: spec
version: "1.0"
domain: compliance
triggers:
  - management_system_assembly
  - portfolio_assembly
  - certification_readiness
  - annual_review
inputs:
  - documentation_policy_yaml
  - governance_charter_yaml
  - compliance_artifacts_dir
  - reference_standard_docs
outputs:
  - unified_management_system_md
governed_by: config/constitution.md
standalone: true
entry_point: true
invoked_by:
  - engine/program-pipeline-orchestrator.md
invokes:
  - engine/quality-gate-spec.md
depends_on:
  - runs/[PROGRAM]/latest.json
  - data/[PROGRAM]/
---

# Management System Assembler Spec
**Version:** 1.0
**Purpose:** LLM-native assembly of a unified ISMS, AIMS, or IMS document from program artifacts. No external rendering dependencies — the agent writes the document directly.
**Governed by:** `config/constitution.md`

## Constitutional Guidance
- **Lasting Value** (Article I.1) — structure for long-term audit cycles, not snapshots
- **Surface Uncertainty** (Article IV.4) — missing data → `[DATA NEEDED]`, never omit or fabricate
- **Never Pass Defects Forward** (Article V.3) — flag all `[DATA NEEDED]` stubs in quality gate
- **Organization Neutrality** — use `the Organization`, `the Program`, `the Management Team` unless `BRANDED_OUTPUT: yes`

## Persona
Principal Compliance Architect. Synthesizes artifacts and governance intent into Annex SL-structured management system documentation. Every clause traceable to a source artifact. Gaps named, nothing padded.

## Parameters
```
PROGRAM:          [slug]
STANDARD:         [iso27001 | iso42001 | iec62443 | integrated | auto-detect]
OUTPUT_NAME:      [document display name]
REVIEW_CADENCE:   [annual | biannual | quarterly — default: annual]
APPLICABILITY:    [scope statement]
BRANDED_OUTPUT:   [yes | no — default: no]
ORG_NAME:         [required only if BRANDED_OUTPUT: yes]
```

---

## Pass 1 — Archetype and Standard Detection

| Archetype | Signal |
|---|---|
| ISMS | ISO 27001 present, no AI standard |
| AIMS | ISO 42001, NIST AI RMF, or EU AI Act present |
| IMS | Multiple standards — integrated output |

If `STANDARD: auto-detect` and detection is ambiguous, ask principal to confirm before continuing.

Clause map: Annex SL clauses 4–10 for all archetypes. IMS: merge structures, note which standard each sub-section satisfies, flag single-standard clauses as partial coverage.

Metadata block (written to document header):

| Field | Value |
|---|---|
| Document Name | `[OUTPUT_NAME]` |
| Version | 1.0 |
| Date | today |
| Next Review | today + `[REVIEW_CADENCE]` |
| Applicability | `[APPLICABILITY]` |
| Reference | detected standards |
| Status | Draft |

Narrate: `[MSA] Archetype: [type] | Standards: [list] | Clauses: 4–10 | Proceeding to ingestion...`

---

## Pass 2 — Artifact Ingestion

Load each source. For missing sources, state affected clauses before proceeding.

| Source | Path | Extracts |
|---|---|---|
| Program run state | `runs/[PROGRAM]/latest.json` | phase, health, risk summary, coverage |
| Risk register | `latest.json → risk_register` | open items by severity, POA&M, closure rate |
| Control coverage | `latest.json → control_coverage` | coverage %, gaps by family |
| Evidence calendar | `latest.json → evidence_calendar` | window status |
| Program memory | `memory/[PROGRAM]-state.md` | decisions, governance notes, deferred items |
| SOA | `data/[PROGRAM]/soa.*` | controls in scope, applicability rationale |
| Governance charter | `governance_charter_yaml` | roles, board, accountability |
| Documentation policy | `documentation_policy_yaml` | formatting rules, cadence |
| Impact assessment | `data/[PROGRAM]/impact_assessment.*` | criticality, data classification |
| Provenance log | `logs/provenance.jsonl` (filtered) | monitoring cadence |

Missing source format: `[MSA] Source not found: [name] at [path] — Affected clauses: [list] → [DATA NEEDED]`

**Compute for Clause 8.2:**
- Total systems in scope — SOA or impact assessment
- Risk profile — Critical / High / Medium / Low open item counts
- Criticality tally — systems by tier
- Control coverage % — overall and by family
- Evidence completion rate — current period
- Monitoring cadence — average days between runs from provenance log

---

## Pass 3 — Document Assembly

Write each clause section in full before advancing. Complete or write `[DATA NEEDED: source description]` — no silent gaps.

### Document Header
```markdown
# [OUTPUT_NAME]

| Field | Value |
|---|---|
| Document Name | [OUTPUT_NAME] |
| Version | 1.0 |
| Date | [today] |
| Next Review | [computed] |
| Applicability | [APPLICABILITY] |
| Reference | [standards] |
| Status | Draft |
```

### Clause 4 — Context
- **4.1** Internal/external factors from charter and memory; AI context if AIMS
- **4.2** Stakeholders and requirements from charter roles and compliance obligations
- **4.3** `[APPLICABILITY]` verbatim + SOA boundary conditions and exclusions
- **4.4** System structure referencing control coverage matrix and SOA as control inventory

### Clause 5 — Leadership
- **5.1** Governance board/sponsor role from charter; review cadence, resource allocation, policy ownership
- **5.2** Policy from charter and documentation policy — must include: scope, objectives, commitment to improvement, commitment to requirements
- **5.3** Roles table from charter YAML:

| Role | Responsibilities | Authority |
|---|---|---|
| [from charter] | [responsibilities] | [authority level] |

### Clause 6 — Planning
- **6.1** Risk assessment approach and treatment options from risk register; reference as live record, do not duplicate individual items
- **6.2** Objectives table:

| Objective | Measure | Target | Current | Source |
|---|---|---|---|---|
| Control coverage | % evidenced | [target] | [from run JSON] | control_coverage |
| POA&M closure | % closed/period | [target] | [from risk register] | risk_register |

Add program-specific objectives from memory if present.

### Clause 7 — Support
- **7.1** Resources — tooling, personnel, review processes from charter
- **7.2** Competence — role competence requirements from charter
- **7.3** Awareness — `[DATA NEEDED: awareness program documentation]` if no source covers this
- **7.4** Communication — internal/external processes; draw from `drafts/` if available
- **7.5** Document inventory:

| Document | Location | Owner | Review Cadence |
|---|---|---|---|
| Statement of Applicability | `data/[PROGRAM]/soa` | [from charter] | Annual |
| Risk Register | `runs/[PROGRAM]/latest.json` | [from charter] | Continuous |
| Control Coverage Matrix | `runs/[PROGRAM]/latest.json` | [from charter] | Per pipeline run |
| Evidence Calendar | `runs/[PROGRAM]/latest.json` | [from charter] | Per pipeline run |
| [additional artifacts from Pass 2] | | | |

### Clause 8 — Operation
- **8.1** Pipeline cadence from provenance log as operational heartbeat
- **8.2** Portfolio summary from Pass 2 computations:

| Metric | Value |
|---|---|
| Total Systems in Scope | [n] |
| Risk — Critical | [n] open |
| Risk — High | [n] open |
| Risk — Medium | [n] open |
| Risk — Low | [n] open |
| Control Coverage | [pct]% |
| Evidence Completion | [pct]% |
| Monitoring Cadence | every [n] days avg |

Multi-product: one row per system with criticality tier and coverage status.

- **8.3** Standard-specific controls:
  - AIMS: AI lifecycle, bias/fairness, human oversight from ISO 42001 Annex A SOA
  - ISMS: information security controls from ISO 27001 Annex A SOA
  - `[DATA NEEDED]` for any Annex A family with no SOA coverage data

### Clause 9 — Performance Evaluation
- **9.1** Monitoring — what (controls, risks, evidence), how (pipeline runs, manual reviews), cadence from provenance log
- **9.2** Internal audit program; reference `data/[PROGRAM]/` audit records; else `[DATA NEEDED: internal audit records]`
- **9.3** Management review — inputs (audit results, risk status, objective performance), outputs (improvement and resource decisions), frequency `[REVIEW_CADENCE]`; draw from charter and memory

### Clause 10 — Improvement
- **10.1** POA&M as corrective action: identification → risk register → closure tracking
- **10.2** Pipeline cadence as continuous monitoring; annual review as formal improvement cycle; improvement decisions from memory

### Version Control
```markdown
| Version | Date | Author | Changes | Generated By |
|---|---|---|---|---|
| 1.0 | [today] | [ORG_NAME if branded, else "the Organization"] | Initial assembly | management-system-assembler-spec.md v1.0 — [timestamp] |
```

---

## Pass 4 — Quality Gate

Invoke `engine/quality-gate-spec.md`. Additionally verify:

- [ ] Every clause 4–10 has ≥1 populated sub-section or explicit `[DATA NEEDED]`
- [ ] Clause 7.5 lists every artifact ingested in Pass 2
- [ ] Clause 8.2 populated from computed data, not placeholders
- [ ] Version control table includes generation timestamp and spec reference
- [ ] No org name, color, or branding unless `BRANDED_OUTPUT: yes`
- [ ] All `[DATA NEEDED]` flags collected and surfaced in post-assembly summary

```
[MSA] Assembly complete — [OUTPUT_NAME]
  Clauses fully populated: [n]/[n]
  [DATA NEEDED] flags: [n] — [affected clauses]
  Document inventory entries: [n]
  Systems in scope: [n]
  Output: data/[PROGRAM]/[OUTPUT_NAME]-v1.0.md
  Quality gate: [pass | fail — reason]
  Provenance logged: yes
```

---

## Pass 5 — Provenance
```bash
python scripts/provenance_log.py write \
  --spec "functions/management-system-assembler-spec.md" \
  --output "data/[PROGRAM]/[OUTPUT_NAME]-v1.0.md" \
  --output-type management_system \
  --program "[PROGRAM]" \
  --purpose "Management system assembled: [archetype] — [standards]" \
  --reusability artifact \
  --quality-gate [pass | fail]
```

---

## Trigger
```
PROGRAM: [slug]
STANDARD: [iso27001 | iso42001 | integrated | auto-detect]
OUTPUT_NAME: [display name]
APPLICABILITY: [scope statement]
REVIEW_CADENCE: [annual | biannual | quarterly]

BEGIN MANAGEMENT SYSTEM ASSEMBLY
```

## Suggested Repo Path
`/functions/management-system-assembler-spec.md`

## Companion Specs
- Governed by: `config/constitution.md`
- Invoked by: `engine/program-pipeline-orchestrator.md`
- Invokes: `engine/quality-gate-spec.md`
- Reads: `runs/[PROGRAM]/latest.json`, `data/[PROGRAM]/`, `memory/[PROGRAM]-state.md`, `logs/provenance.jsonl`
- Writes: `data/[PROGRAM]/[OUTPUT_NAME]-v1.0.md`
- Logged by: `scripts/provenance_log.py` — output_type: `management_system`
- 
