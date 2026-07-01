---
resource_type: spec
version: "1.1"
domain: compliance
triggers:
  - product_onboarding
  - product_evidence_extraction
  - repo_audit_intake
inputs:
  - product_name
  - repo_urls
  - framework_control_subset
  - existing_program_materials
outputs:
  - product_profile
  - product_control_matrix
  - evidence_gaps
  - product_data_stub
governed_by: config/constitution.md
standalone: true
entry_point: false
invoked_by:
  - engine/program-pipeline-orchestrator.md
  - functions/program-intake-spec.md
invokes: []
depends_on:
  - runs/[PROGRAM]/latest.json
  - functions/control-coverage-spec.md

---

# Product Evidence Spec

**Version:** 1.1
**Purpose:** Extract ISO 42001-relevant signals from a product's source repository and available materials. Produce a product profile, an annotated Annex A control matrix, and an evidence gap list that feeds the AIMS pipeline — enabling evidence-building before product team contact. Designed for the 5-empty-product-folder problem: generate a meaningful stub from what exists publicly or internally before pinging engineering.
**Governed by:** `config/constitution.md`

---

## Constitutional Guidance

Say the true thing (IV.1) — repo signals are not formal evidence. Never classify a control as Evidenced based on a README alone. Classify as Implemented-no-evidence (`~`) at best. Surface uncertainty (IV.4) — label all repo-sourced findings `[REPO SIGNAL]`, all inferences `[INFERRED]`. Protect the downstream (IV.2) — the control matrix this spec produces feeds the AIMS run JSON and auditor view; gaps not surfaced here become invisible risks. Good enough calibration (IV.14) — a directionally correct stub with explicit gaps is more valuable than a delayed complete matrix.

---

## Persona Definition

Senior compliance analyst extracting ISO 42001 evidence signals from engineering artifacts. Distinguish between what the repo *demonstrates* (implementation exists), what it *claims* (documented intent), and what it *cannot tell us* (requires product team). No credit for intent stated only in documentation without implementation signals. Flag gaps without softening.

---

## Confidence Vocabulary

Use these tags throughout all outputs from this spec:

| Tag | Meaning |
|---|---|
| `[REPO SIGNAL]` | Observed in public repo (README, code, CI config, architecture docs) — not a formal compliance artifact |
| `[INFERRED]` | Logical conclusion from observed signals — not explicitly stated |
| `[DATA NEEDED]` | Cannot be determined from repo materials — requires product team input |
| `[OWNER NEEDED]` | Responsible party not identified in available materials |
| `[CONFLICT — VERIFY]` | Contradictory information found across sources |
| `[FORMAL ARTIFACT]` | Formal compliance document (audit report, published system card, signed policy) |

---

## Coverage Status States

Inherit from `functions/control-coverage-spec.md`:

| Status | Symbol | Meaning |
|---|---|---|
| Evidenced | ✓ | Formal artifact exists and demonstrates implementation |
| Implemented — no evidence | ~ | Implementation observable in repo signals; no formal audit artifact |
| Gap | ✗ | Not implemented or no information available |
| Not applicable | N/A | Explicitly scoped out or not relevant to this product's AI profile |

**Important:** Repo README signals alone never produce `✓`. Maximum confidence from repo scan is `~`. Only formal artifacts (published system cards, audit reports, signed policies, independent test results) produce `✓`.

---

## Parameters

```
PRODUCT_NAME:     [product name as it appears in the AIMS charter]
PROGRAM_SLUG:     [e.g., iso42001]
REPO_URLS:        [list of repo URLs scanned]
FRAMEWORK:        ISO/IEC 42001:2023
ANNEX_A_SUBSET:   [list of control IDs applicable to this product — default: all Annex A]
SCAN_DATE:        [YYYY-MM-DD]
ANALYST:          [agent | name]
```

---

## Processing Instructions

### Pass 1 — Product Classification

Identify the product's AI system type from repo materials. Use the ISO 42001:2023 Annex B / Annex C taxonomy as the reference. Record:

1. **Primary function** — what the system does for users
2. **AI system type** — generative assistant, RAG-augmented system, inference infrastructure, evaluation tooling, safety layer, or combination
3. **Deployment context** — SaaS, on-prem, embedded library, API service, container workload
4. **Foundational role** — does this product serve as infrastructure for other products in the AIMS scope? If yes, note which products depend on it.
5. **Third-party model dependency** — which foundation models or LLM providers does the product use? Are they upstream third parties per A.10.3?

Narrate:

```
[PRODUCT-EVIDENCE] Product: [name]
[PRODUCT-EVIDENCE] AI system type: [type]
[PRODUCT-EVIDENCE] Deployment context: [context]
[PRODUCT-EVIDENCE] Foundational dependency role: [yes/no — which products depend on this]
[PRODUCT-EVIDENCE] Third-party models: [list]
[PRODUCT-EVIDENCE] Pass 1 complete. Beginning repo signal extraction...
```

---

### Pass 2 — Repo Signal Extraction

Scan all provided repo URLs. For each repo, extract signals relevant to ISO 42001 Annex A control families. Process in order:

**A.4 — Resources for AI systems**
Look for: LLM provider configurations, model registries, embedding model specifications, compute resource documentation, dependency management files.

**A.5 — Assessing impacts of AI systems**
Look for: Impact assessment documents, risk documentation, bias testing references, fairness evaluation pipelines, model card references.

**A.6 — AI system life cycle**
Look for: Architecture documentation, CI/CD pipelines, container build configs, versioning schemes, test suites (unit, integration, e2e), deployment configs, API specifications, change management processes.

**A.7 — Data for AI systems**
Look for: Data collection configurations, data export integrations, data provenance tracking, vector database generation, dataset management, privacy controls on data collection.

**A.8 — Information for interested parties**
Look for: Published API specifications, system cards, model cards, transparency documentation, evaluation results, performance metrics, health endpoints.

**A.9 — Use of AI systems**
Look for: Safety shields, content filtering, input validation, output filtering, PII redaction, topic restriction, system prompt controls, human-in-the-loop mechanisms, authorization controls.

**A.10 — Third-party and customer relationships**
Look for: Third-party API integration patterns, authentication mechanisms for external services, supplier dependency management, customer-facing transparency artifacts.

For each signal found, record:
- Control ID it maps to
- Repository source and specific location (README section, config file, doc page)
- What it demonstrates (not what it claims)
- Confidence tag

Narrate progress:

```
[PRODUCT-EVIDENCE] Scanning [repo-name]...
[PRODUCT-EVIDENCE] A.6 signals found: [n] — [brief description]
[PRODUCT-EVIDENCE] A.7 signals found: [n] — [brief description]
...
```

---

### Pass 3 — Control Matrix Assembly

Produce the Annex A control matrix at the control level (not family level) for the applicable subset. Use the control-level matrix format from `functions/control-coverage-spec.md`:

```
## Product Control Matrix — ISO/IEC 42001:2023 Annex A
Product: [PRODUCT_NAME]
Scan date: [DATE]
Repos scanned: [list]
Materials basis: Repo READMEs, architecture docs, CI/CD configs, published API specs

| Control ID | Control Name | Status | Evidence / Signal | Source | Notes |
|---|---|---|---|---|---|
| A.4.2 | Data for AI systems | ~ | Embedding model spec in rag-content README | github.com/lightspeed-core/rag-content | [REPO SIGNAL] |
```

Status rationale column is required for any control classified `✗` (explain why there is no signal) and any `N/A` (explain scope exclusion).

After the matrix, summarize:

```
[PRODUCT-EVIDENCE] Matrix complete.
[PRODUCT-EVIDENCE] [n] controls assessed
[PRODUCT-EVIDENCE] [n] implemented/no-evidence ([x]%), [n] gaps ([x]%), [n] N/A
[PRODUCT-EVIDENCE] All repo-sourced signals classified [REPO SIGNAL] — formal artifacts needed to reach Evidenced status
```

---

### Pass 4 — Evidence Gap Analysis

Produce three focused outputs:

**1. Formal artifact gaps** — controls at `~` that need a formal artifact to reach `✓`:

```
## Formal Artifact Gaps
Controls currently Implemented-no-evidence. Formal artifacts needed for audit readiness.

| Control ID | What repo shows | Formal artifact needed | Effort estimate | Priority |
|---|---|---|---|---|
```

Priority: High = auditor will sample this; Medium = may be sampled; Low = administrative, low audit visibility.

**2. Data needed from product team** — controls at `✗` where the signal simply isn't in the repo:

```
## Data Needed from Product Team
Controls with no repo signal. Questions for the product team engineering or PM contact.

| Control ID | Control Name | Question for product team | Why it matters |
|---|---|---|---|
```

**3. Owner gaps**:

```
## Owner Gaps
Controls or functions with no identified owner from repo materials.

| Area | Why ownership matters | Suggested owner type |
|---|---|---|
```

---

### Pass 5 — Product Profile Assembly

Produce `data/ISO42001/[product]/product-profile.md` with these sections:

1. **Product Summary** — one-paragraph plain-language description for an auditor unfamiliar with the product
2. **AI System Classification** — type, deployment context, foundational role
3. **Architecture Overview** — key components, external dependencies, LLM providers, data flows (narrative, not diagram)
4. **ISO 42001 Applicability Notes** — which Annex A controls are most relevant, which are inherited from enterprise AIMS policies vs. product-specific implementations
5. **Known Evidence Artifacts** — list of any formal artifacts found or referenced in repo materials
6. **Open Questions** — explicit list of items requiring product team input before audit prep
7. **Repo Sources** — list of repos scanned with last-updated dates

---

### Pass 6 — Run JSON Write

After Pass 5, if a program run JSON exists, write the product data stub. Append to the program's `runs/[PROGRAM]/latest.json` under a `products` array (create the key if absent):

```json
"products": [
  {
    "name": "[PRODUCT_NAME]",
    "slug": "[product-slug]",
    "status": "repo-scan-complete",
    "scan_date": "YYYY-MM-DD",
    "repos_scanned": ["url1", "url2"],
    "system_owner": "[name or OWNER NEEDED]",
    "ai_system_type": "[type]",
    "deployment_context": "[context]",
    "foundational_for": ["product1", "product2"],
    "control_matrix_path": "data/ISO42001/[product]/control-matrix.md",
    "product_profile_path": "data/ISO42001/[product]/product-profile.md",
    "evidence_gaps_path": "data/ISO42001/[product]/evidence-gaps.md",
    "annex_a_summary": {
      "total_controls_assessed": 0,
      "implemented_no_evidence": 0,
      "gap": 0,
      "not_applicable": 0,
      "evidenced": 0
    },
    "flags": ["[OWNER NEEDED]", "[REPO SIGNAL — formal artifacts needed]"]
  }
]
```

Narrate at completion:

```
[PRODUCT-EVIDENCE] Product stub written to runs/[PROGRAM]/latest.json
[PRODUCT-EVIDENCE] Handing off to provenance log...
```

---

## Provenance

Run once per output file — the script accepts one `--output` per call:

```bash
python3 scripts/provenance_log.py write \
  --spec "functions/product-evidence-spec.md" \
  --output "data/ISO42001/[PRODUCT]/product-profile.md" \
  --output-type product_evidence \
  --program "[PROGRAM]" \
  --purpose "Product evidence extraction: [PRODUCT] — [n] controls | repo scan | [n] gaps" \
  --reusability artifact \
  --quality-gate pass

python3 scripts/provenance_log.py write \
  --spec "functions/product-evidence-spec.md" \
  --output "data/ISO42001/[PRODUCT]/control-matrix.md" \
  --output-type product_evidence \
  --program "[PROGRAM]" \
  --purpose "Product control matrix: [PRODUCT] — [n] controls | [x]% coverage | [n] gaps" \
  --reusability artifact \
  --quality-gate pass

python3 scripts/provenance_log.py write \
  --spec "functions/product-evidence-spec.md" \
  --output "data/ISO42001/[PRODUCT]/evidence-gaps.md" \
  --output-type product_evidence \
  --program "[PROGRAM]" \
  --purpose "Evidence gap analysis: [PRODUCT] — [n] formal artifact gaps | [n] product team items" \
  --reusability artifact \
  --quality-gate pass
```

---

## Quality Gate

Invoke `engine/quality-gate-spec.md`. Spec-specific REJECT triggers:

- Any control classified `✓` (Evidenced) from repo README alone — maximum from repo scan is `~`
- Any repo-sourced signal missing `[REPO SIGNAL]` tag
- Any inference missing `[INFERRED]` tag
- Any `✗` control without a corresponding entry in Pass 4 Section 2 (data needed from product team)
- Product profile missing a plain-language summary suitable for an auditor with no product context
- Run JSON stub not written when program run JSON exists

---

## Companion Specs

- Governed by: `config/constitution.md`
- Feeds: `functions/control-coverage-spec.md` (program-level rollup), `functions/risk-register-spec.md`
- Reads: Repo materials (public), `runs/[PROGRAM]/latest.json`
- Writes: `data/ISO42001/[PRODUCT]/`, `runs/[PROGRAM]/latest.json → products[]`
- Logged by: `scripts/provenance_log.py` — output_type: `artifact`
