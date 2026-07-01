# Probabilistic-Deterministic Architecture
**Document type:** Technical Architecture Reference
**Intended audience:** Development team, technical leads
**Companion documents:** `docs/agent-governance-overview.md`, `docs/quality-controls-reference.md`
**Version:** 1.0

---

## Why This Balance Is a Design Choice

The system uses two fundamentally different types of mechanisms: LLM-executed specs that produce probabilistic outputs, and Python scripts and rules that produce deterministic outputs. Both are necessary. Neither alone is sufficient.

LLM mechanisms handle work that requires language understanding, contextual judgment, and synthesis across unstructured inputs: extracting program scope from raw documents, classifying external signals by framework relevance, drafting stakeholder communications calibrated to audience. These tasks resist deterministic scripting because the inputs are not structured and the correctness criteria cannot be expressed as a boolean condition.

Deterministic mechanisms handle work where correctness is binary: a heading is present or absent, a field is populated or null, a routing rule matches or does not, a schema field exists or is missing. These tasks require no judgment. Running them through an LLM would introduce unnecessary variance and make failures harder to detect.

The design principle is to place LLM mechanisms inside deterministic boundaries. The LLM generates; deterministic checks validate, log, and gate what reaches the lead program manager. This arrangement uses LLM capability where it adds genuine value while producing auditable, repeatable outputs.

---

## Mechanism Taxonomy

### Deterministic Mechanisms

These mechanisms produce the same output for the same input, every time. Failures are detectable and reproducible.

| Mechanism | File | What it enforces |
|---|---|---|
| Heading manifest | `scripts/integrity_check.py` | Required headings present in protected files |
| Frontmatter validation | `scripts/validate_frontmatter.py` | Required YAML fields on every spec file |
| Routing coverage | `scripts/spec_coverage.py` | Every routing rule references an existing spec file |
| Schema drift detection | `scripts/validate_schema_drift.py` | Run JSON matches documented schema |
| Provenance logging | `scripts/provenance_log.py` | Every deliverable recorded with metadata |
| Run JSON schema | `config/schemas/run-output.schema.json` | Uniform output envelope structure |
| CI pipeline | `.gitlab-ci.yml` | Validate, test, and build gates on every merge |
| Routing rules table | `runtime/router.py` (`ROUTING_RULES`) | Regex pattern-to-spec-file mapping |
| Trust level gating | `runtime/trust.py` | Autonomy thresholds by agent type and intent |
| One-way door prohibition | `config/constitution.md` Article V.5 | Constitutional bar on autonomous irreversible action |
| Quality gate format checks | `engine/quality-gate-spec.md` Gates 3, 5 | Prohibited patterns and type-specific checklists |
| Flag vocabulary | `config/constitution.md` Article IV | Defined inline markers for uncertainty and missing data |

### Probabilistic Mechanisms

These mechanisms use LLM execution. Output quality depends on the model and the precision of the governing spec. Failures are probabilistic and may not be reproducible with the same inputs.

| Mechanism | File | What it does |
|---|---|---|
| Spec execution | All `engine/` and `functions/` specs | LLM reads spec and produces compliance artifact |
| Session routing classification | `engine/session-init-spec.md` | LLM classifies input and selects routing path |
| Routing confidence | `runtime/router.py` (`RoutingDecision.confidence`) | Float 0.0–1.0 estimating routing match quality |
| Constitutional alignment evaluation | `engine/quality-gate-spec.md` Gate 1 | LLM evaluates whether output passes Protection/Flow/Truth |
| Tone evaluation | `engine/quality-gate-spec.md` Gate 4 | LLM evaluates directness, authority, economy |
| Language scan | `engine/doc-style-guide.md` | LLM identifies Tier 1 and Tier 2 style violations |
| Relevance scoring | `functions/external-intel-spec.md` | LLM scores external findings against program framework and stack |
| Health trajectory analysis | `scripts/predictive_health.py` | Heuristic analysis of run history (see note) |

Note on `predictive_health.py`: the health trajectory, gap velocity, and certification timeline calculations in this script are deterministic arithmetic over structured run history — not learned models. The term "predictive" describes the forward-looking output, not the mechanism. It appears in this table because its output is presented to the lead program manager as an estimate with a stated confidence level, which requires the same consumer discipline as probabilistic output: treat it as directional, not authoritative.

### Semantic Convention Layer

This layer defines shared meaning between the lead program manager and the LLM. It is neither probabilistic nor deterministic in execution — it is a contract expressed in the spec system that enables the deterministic layer to validate probabilistic outputs without understanding their content.

| Convention | Where defined | What it encodes |
|---|---|---|
| Flag vocabulary | `config/constitution.md` | Shared meaning for inline uncertainty markers |
| Heading manifests | `scripts/integrity_check.py` | Structural contract for protected files |
| Spec frontmatter fields | YAML headers on every spec | Machine-readable routing and triggering metadata |
| Status indicators | `engine/quality-gate-spec.md` Gate 3 | Defined meaning for emoji in briefings and dashboards |
| Reusability classification | Provenance schema | Defined meaning for `template`, `reference`, `instance`, `artifact` |
| Constitutional alignment fields | Run JSON schema | Defined meaning for `pass` and `escalated` values |

The semantic layer is what makes it possible for `integrity_check.py` to verify that a heading exists without reading the content under it, and for Gate 2 to verify that a required section is present without evaluating its accuracy. The LLM and the deterministic scripts share a vocabulary; without it, structural validation would require content interpretation.

---

## Current Architecture Map

The table below maps each major pipeline phase and system function to its position on the deterministic-probabilistic spectrum.

| Phase / Function | Mechanism type | Notes |
|---|---|---|
| Phase 0 — Constitutional preload | Deterministic | Checklist: constitution loaded, no one-way doors embedded, outputs internal until review |
| Phase 1a — Prior run state parsing | Deterministic | JSON parsing of structured run envelope |
| Phase 1b — Triage | Probabilistic | LLM interprets responses to four structured questions |
| Phase 1c — Routing decision | Hybrid | Condition table (deterministic) applied to triage output (probabilistic) |
| Phase 2 — Intake | Probabilistic | LLM extraction and synthesis from unstructured program materials |
| Phase 3 — Monitoring | Probabilistic | LLM classification of program items into status categories |
| Phase 4 — Vendor | Probabilistic | LLM scoring and analysis of vendor performance data |
| Phase 4b — Crash checkpoint | Deterministic | Atomic write of partial state via `runtime/ide.py` |
| Phase 5 — Alignment test | LLM against deterministic criteria | Probabilistic mechanism evaluating probabilistic output against a defined three-part rubric |
| Phase 6, Gates 3 and 5 — Quality gate | Deterministic | Pattern matching and structural comparison against defined checklists |
| Phase 6, Gates 1, 4, and 6 — Quality gate | Probabilistic | LLM evaluation of constitutional alignment, tone, and language patterns |
| Phase 6, Gate 2 — Quality gate | Structural comparison | Deterministic check of section presence; content within sections is not evaluated |
| Phase 7 — Output assembly | Deterministic | JSON schema enforces structure of final envelope |
| Routing | Hybrid | Regex pattern matching (deterministic) plus confidence float and agent load signals (probabilistic) |
| Predictive health | Deterministic arithmetic | Gap velocity and health score calculations on structured JSON; not ML |
| Provenance logging | Deterministic | Append-only structured log; no LLM involvement |
| CI validation | Deterministic | Script execution with pass/fail exit codes |
| Human evaluation harness | Human judgment against defined rubric | Neither deterministic nor probabilistic — the deliberate final backstop |

The pipeline's structure is: probabilistic generation, wrapped by deterministic validation, delivered through a human review checkpoint. This ordering is not arbitrary. Probabilistic generation handles the work that deterministic scripting cannot. Deterministic validation catches the failure modes probabilistic generation cannot self-correct reliably. Human review handles the residual judgment that neither layer covers.

---

## Maintenance Principles

These principles apply when adding, modifying, or removing system features. They are what preserves the architecture's structure as the system grows.

**New output types require a quality gate entry before shipping**

Gate 2 (structural completeness) defines required sections by output type. A new LLM-generated output type without a Gate 2 entry has no structural completeness check. Before shipping any new output type, add its required section list to `engine/quality-gate-spec.md` Gate 2. This is a precondition, not a follow-up item.

**Routing logic lives in `runtime/router.py` only**

No spec, tool, or agent may implement routing logic inline. Adding a routing path means: one entry in `ROUTING_RULES` with a regex pattern, target spec, target agent, and intent label; one corresponding spec file at the referenced path; and a passing spec coverage check that verifies the file exists. Routing logic that exists outside this file is invisible to `spec_coverage.py` and cannot be validated by CI.

**Probabilistic outputs must produce deterministic artifacts**

Every LLM-generated output that reaches the lead program manager must also produce at minimum a run JSON entry or provenance log entry, and a flags array entry for each uncertainty in the output. Prose-only outputs with no structured artifact are not auditable. If an output cannot be linked to a provenance log entry, it did not pass through the system's traceability layer.

**Confidence is always explicit**

New probabilistic mechanisms must surface a confidence indicator before the output reaches the lead program manager. `RoutingDecision.confidence` is the existing pattern. A mechanism that presents probabilistic output without a stated confidence level treats uncertain output as certain. The correct handling for low-confidence output is either `[INFERRED]` flags on specific fields or a confidence label on the output as a whole — not a clean-looking output with hidden uncertainty.

**New autonomy requires trust level justification**

Expanding what the system can do without lead program manager confirmation is a change to the authority boundary in the constitution. It does not happen through spec edits alone. It goes through `runtime/trust.py` trust level thresholds and requires a constitutional amendment (Article VIII) with the rationale recorded. The current thresholds are defined there; do not replicate or override them inline.

**Every new probabilistic capability needs a deterministic failure check**

Before adding an LLM capability, identify its most likely failure mode and build the deterministic check for that failure mode first. For a new output type: the structural completeness gate entry. For a new routing path: the spec coverage entry. For a new confidence mechanism: the explicit confidence surfacing requirement. The check is the design work that makes the capability safe to ship — not something added after the fact.

**Protected file changes go through the integrity check**

Adding or renaming a heading in `config/constitution.md`, `engine/program-pipeline-orchestrator.md`, or `engine/quality-gate-spec.md` requires a corresponding update to the heading manifest in `scripts/integrity_check.py`. The file's version number must be incremented. If the manifest is not updated, the integrity check will fail on the next CI run — which is the correct behavior, and not an oversight to work around.

---

## Long-Term Considerations

**Model drift**

The reliable capability boundary of what the LLM can do shifts as the underlying model changes. Constitution Article VIII defines the amendment process for revising authority boundaries. This is a recurring governance obligation, not a one-time setup. After any model change: re-run the human evaluation harness (Layer 8 in `docs/quality-controls-reference.md`), compare results against the prior baseline, and assess whether any authority boundary in the constitution requires update. Model capability improvements do not automatically justify expanded autonomy — they require deliberate assessment and a recorded decision.

**Spec portability**

Every spec in this system is plain markdown. No spec requires a specific LLM vendor, API version, or model capability beyond general instruction-following. This is a deliberate constraint. It preserves the option to compare model performance across vendors on the same spec corpus, to run specs on locally-hosted models, and to avoid vendor lock-in at the governance layer. Any feature addition that requires a specific model API call violates this constraint. Such additions require explicit lead program manager approval and a recorded rationale.

**Complexity ceiling**

Both sides of the architecture carry maintenance costs. Deterministic checks require updating when the system changes — the heading manifest, routing table, and schema must stay synchronized with the live system. Probabilistic capabilities increase the surface area for subtle failure — each new spec introduces new LLM failure modes. The appropriate response to either cost is not to add more of the other type. The correct balance is the minimum of each type needed to produce reliable, auditable output for the current scope. Adding complexity on either side beyond that minimum increases maintenance burden without improving reliability.

**Spec drift**

Specs edited by LLMs are subject to the same structural regression risk as any other document. The integrity check currently protects three files. As the system adds specs that become load-bearing for pipeline correctness, evaluate whether they warrant integrity check protection. The criteria: would a silently degraded heading in this file change the LLM's behavior in ways that other controls would not catch? If yes, add it to the manifest in `scripts/integrity_check.py`.

**Trust level architecture**

The current trust model uses three levels: level 1 requires confirmation for all routing decisions, level 2 allows auto-routing for low-stakes intents, level 3 allows auto-routing for all intents within spec scope. This is a coarse instrument. As the system handles more diverse work patterns, the trust model will need per-capability or per-intent granularity. The risk of extending trust too broadly is invisible autonomous action. The risk of keeping trust too narrow is a system that produces no leverage. Both failure modes are observable: the first through the provenance log (unexpected outputs with no lead program manager decision recorded), the second through lead program manager workload (the system requests confirmation for work that does not warrant it).

**Predictive mechanisms and learned models**

`predictive_health.py` uses arithmetic heuristics — gap velocity, moving averages of health scores, deadline clustering — not learned models. Its failure modes are inspectable directly from the source code. If this analysis is replaced or augmented with a trained model, all maintenance principles in the preceding section apply with greater urgency. A trained model's failure modes are not inspectable from its source code. The training data and feature engineering become part of the system's audit surface. Confidence calibration requires empirical validation rather than formula inspection. That transition requires explicit design work before implementation — not a drop-in replacement of the existing script.

---

*This document reflects the architecture as of the version date above. Material changes to the mechanism taxonomy, pipeline phase classification, or maintenance principles require a corresponding update to this document and a review of any affected control in `docs/quality-controls-reference.md`.*
