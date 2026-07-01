# Quality Controls Reference
**Document type:** Technical Quality Control Reference
**Intended audience:** Auditors, compliance reviewers, program oversight stakeholders
**Prepared by:** Alex Langston, Lead program manager Compliance Program Manager
**Companion document:** `docs/agent-governance-overview.md` — governance philosophy and boundary design
**Version:** 1.0

---

## Purpose and Scope

This document inventories every quality control mechanism in the compliance program management system. For each mechanism it states: what the control does, where it lives, when it runs, what it detects or prevents, and how it routes failures.

This document does not repeat the governance philosophy, boundary sensing model, seam design, or failure model narrative in `docs/agent-governance-overview.md`. Read that document first for the conceptual context. This document covers the specific mechanisms that implement those concepts.

Controls are organized in eight layers from the most abstract to the most concrete. Each layer catches failures the layer before it may not detect.

---

## Layer 1 — Constitutional Guardrails

**File:** `config/constitution.md`
**When it applies:** Every session, every output, every agent action — loaded before any execution begins.

The constitution is the governing document for all agents, specs, and automations. Its controls operate continuously, not as a discrete check.

**Authority hierarchy**
Five core values in ranked order. When values conflict, customer protection takes precedence, followed by greatest good, lasting value, trusted relationships, and efficiency. No spec or instruction can override this ordering.

**Alignment test**
Three checks that must pass before any output is delivered:

- Protection — does this output expose a party who could not protect themselves, without justification?
- Flow — does this output pass a known defect forward without notation?
- Truth — does this output state the true finding, with inferences labeled and conflicts flagged?

Any output that fails one check must be revised or escalated. The pipeline runs this test explicitly at Phase 5, before final output assembly.

**One-way door prohibition**
Actions that cannot be undone — communications sent externally, decisions with legal or contractual consequence, actions that materially affect another person's standing — require explicit lead program manager approval before execution. The agent is constitutionally prohibited from executing them autonomously. No exceptions are built into the system.

**Flag vocabulary**
A defined set of inline markers that surface uncertainty and missing data without suppressing output:

| Flag | Meaning |
|---|---|
| `[DATA NEEDED: source]` | Missing data — do not fabricate |
| `[OWNER NEEDED]` | No owner assigned |
| `[INFERRED]` | Not explicitly stated in source material |
| `[CONFLICT — VERIFY]` | Contradictory information found in sources |
| `[CITATION NOT FOUND]` | Source section not locatable |

These markers appear inline in all outputs. Their presence is not a failure — it is the correct handling for uncertainty. Suppressing them to produce a cleaner-looking output violates constitutional mandate IV.4.

**Escalation protocol**
When a one-way door is reached, a values conflict is unresolved, or the alignment test fails: the agent states the decision point, identifies which article triggered the escalation, presents available options with tradeoffs, states a recommendation where one can be made, and waits for explicit lead program manager approval. It does not proceed.

---

## Layer 2 — Output Quality Gate

**File:** `engine/quality-gate-spec.md`
**When it runs:** After every spec-generated output, before delivery to the lead program manager. Invoked by the pipeline orchestrator at Phase 6.

Six gates run in sequence on every output. All six run regardless of whether earlier gates passed. A single REJECT on any gate triggers the regeneration protocol.

**Gate 1 — Constitutional Alignment**
Verifies the output passed the Article VI alignment test (Protection, Flow, Truth). A one-way door action not escalated during generation triggers an ESCALATE classification that bypasses regeneration and routes directly to the lead program manager.

**Gate 2 — Structural Completeness**
Verifies the output contains all sections required by the generating spec, cross-referenced against the spec's defined output structure. Required sections by output type:

| Output type | Required sections |
|---|---|
| Program Skeleton | Mission, In Scope, Frameworks, Workstreams, People Roster, Hard Deadlines, Flags Summary |
| Monitoring Output | Cadence Map, Escalation Framework, Draft Communications (minimum one), Daily Briefing Template, Flags Summary |
| Vendor Output | Obligation Inventory, Performance Scorecard, Remediation or Monitoring Plan, Draft Communications (minimum one), Flags Summary |
| JSON Pipeline Output | schema_version, constitution_version, run_manifest, program_state, constitutional_alignment block, flags, next_run_recommendation |
| Draft Communication | To, Channel, Subject, Body, Send Checklist |

A section that exists but contains only placeholder text fails as INCOMPLETE.

**Gate 3 — Format Standards**
Detects prohibited formatting patterns. Each is an automatic REJECT:

- Numbered headers — any heading beginning with a digit followed by a period or parenthesis (`## 1. Title`, `### 2.1 Findings`)
- Parenthetical subtitles in headers — any heading containing `( )` characters (`## Risk Assessment (Current State)`)
- Emojis in professional outputs — prohibited in all reports, communications, and JSON; permitted only in daily briefing and dashboard outputs where they serve as status indicators with defined meaning
- AI generation artifacts — "Certainly!", "Absolutely!", "As an AI...", "I hope this helps", excessive hedging chains

**Gate 4 — Tone Standards**
Evaluates three principles. Any principle rated NEEDS_REVISION produces a REJECT:

- Directness: conclusions stated without hedging the substance; appropriate qualification of uncertainty is permitted, hedging the conclusion to soften impact is not
- Authority: written from expertise, not deference; does not over-explain basics; treats the lead program manager as a peer
- Economy: every sentence earns its place; no section introductions that restate the title, no summaries that repeat what was already stated, no closing filler

**Gate 5 — Output Type Specific Checks**
Additional checks applied by output type. Draft communications: recipient and channel specified, subject line specific (not "Update" or "FYI"), single primary ask, no one-way door action without lead program manager approval notation, send checklist present. Reports and analysis: executive summary stands alone, every finding has a recommendation, every recommendation is specific and actionable (names the control or clause or person or date), final line reads exactly "All findings require validation by a qualified compliance SME before action is taken." JSON output: syntactically valid, no null values in required fields.

**Gate 6 — Document Language Standards**
Loads `engine/doc-style-guide.md` and runs the style scan protocol against the full output text. Two severity tiers:

- Tier 1 (Critical) — automatic REJECT on any single finding. Categories: AI vocabulary cluster (three or more flagged words in any 200-word passage, including "delve", "pivotal", "crucial", "underscore" as verb, "showcase", "foster", "garner", "tapestry", "testament", "intricate", and others enumerated in the style guide); vague attribution ("experts argue", "industry reports indicate", "studies show" without citation); promotional language ("groundbreaking", "renowned", "boasts", "vibrant" as modifier); collaborative preamble ("Certainly!", "Here is a comprehensive overview", "As an AI"); knowledge-gap speculation (passages that speculate about undocumented information rather than placing `[DATA NEEDED]`).
- Tier 2 (Caution) — noted in validation report; triggers REJECT only when Gate 4 also failed. Categories: significance inflation, superficial participial appends, challenges boilerplate, negative parallelisms, rule-of-three padding, copulative avoidance, elegant variation of defined compliance terms, overuse of boldface, em dash clusters.

**Regeneration protocol**
When any gate produces a REJECT: compile a terse correction brief listing each failed check and what must change; regenerate the output; re-validate all six gates on the regenerated output. If the regenerated output still fails any gate: escalate to the lead program manager with both outputs and all failure detail. Do not attempt a third regeneration without lead program manager direction.

---

## Layer 3 — Structural Integrity Check

**File:** `scripts/integrity_check.py`
**When it runs:** Mandatory before any edit to a protected file. Also runs in CI on every merge request and default branch push.

The script maintains a heading manifest: an explicit list of every required heading in each protected file. Current protected files and their heading counts:

| File | Required headings |
|---|---|
| `config/constitution.md` | 43 |
| `engine/program-pipeline-orchestrator.md` | 21 |
| `engine/quality-gate-spec.md` | 14 |

On execution, the script extracts all markdown headings from each protected file and compares them against the manifest. Any heading present in the manifest but absent from the file is a failure. The script exits non-zero, which causes CI to fail and blocks the test and build stages.

On failure, the script prints a restoration notice to the lead program manager: the list of missing headings, instructions to restore each one at its correct position in the document, and a directive to re-run the check before proceeding. The lead program manager notice reads separately from the agent instruction so the human reviewer can confirm that restoration was completed correctly.

The manifest is updated only when a heading is intentionally added or renamed. Removing a manifest entry without removing the corresponding heading from the file is invisible to the check but produces a maintenance gap. Removing a heading without removing the manifest entry is visible immediately on the next run. Both cases require deliberate manifest maintenance — the script does not self-update.

The constitutional mandate (Article IV.7) instructs the agent to run this check before editing any protected file, not as a recommendation but as a precondition to editing. The agent is also instructed to notify the lead program manager if any heading is found missing and restored.

---

## Layer 4 — Spec and Schema Validation

**Files:** `scripts/validate_frontmatter.py`, `scripts/spec_coverage.py`, `scripts/validate_schema_drift.py`
**When they run:** CI validate stage, on every merge request and default branch push.

**Frontmatter validation**
Every spec file carries a YAML frontmatter block. Required fields include `resource_type`, `version`, `domain`, `governed_by`, and `triggers`. The script parses each spec file's frontmatter in strict mode and fails if any required field is absent or malformed. This prevents a spec from being deployed with incomplete metadata that would break routing or orchestration.

**Spec coverage**
Cross-references all routing rules in `runtime/router.py` against the actual spec files they reference. If a routing rule points to a spec that does not exist at the expected path, the check fails. This detects stale routing entries and prevents the system from routing work to a file that has been moved or deleted without updating the routing table.

**Schema drift detection**
Compares run JSON output against the canonical schema definition. Runs in warn-only mode: it does not fail CI on drift, but logs warnings when a run JSON produced by the pipeline diverges from the documented schema. This makes schema evolution visible before it becomes a silent incompatibility between pipeline output and downstream consumers.

---

## Layer 5 — Provenance and Traceability

**Files:** `scripts/provenance_log.py`, `logs/provenance.jsonl`, `runs/[program]/[date]-run.json`
**When it runs:** After every successful pipeline run. The orchestrator spec mandates a provenance log write as the final step.

**Provenance log**
An append-only log of every deliverable the system has produced. Each entry records: generating spec, output file path, output type, program name, purpose, reusability classification, quality gate result, and run ID. The log is never overwritten — only appended. It is queryable by program, spec, output type, date range, and reusability via `python scripts/provenance_log.py query`.

Before generating new work, the system checks provenance for existing reusable artifacts:

```
python scripts/provenance_log.py query --program [program] --reusability template
```

If a reusable artifact exists, the system uses it rather than regenerating. This check is a behavioral mandate, not a suggestion.

**Reusability classification**

| Value | When applied |
|---|---|
| `template` | Output contains reusable draft communications or abstracted program skeleton |
| `reference` | Output contains entropy report, red team report, or vendor scorecard with generalizable patterns |
| `instance` | Output is monitoring JSON, briefing, or calendar export specific to this program |
| `artifact` | One-time full onboarding output with no recurring value beyond this program |

**Run JSON structure**
Every pipeline run produces a dated run JSON and overwrites `runs/[program]/latest.json`. The JSON envelope carries fields that function as traceability records:

- `schema_version` and `constitution_version` — document which version of each governing spec produced this output
- `run_manifest.constitutional_alignment` — records whether Protection, Flow, and Truth passed or were escalated, with an escalations array listing any items that triggered escalation
- `flags` — seven typed arrays: `owner_needed`, `date_needed`, `escalation_path_needed`, `inferred`, `conflicts`, `insufficient_data`, `unresolved_from_prior_run`
- `next_run_recommendation` — records the system's recommended follow-up date, intent, and rationale

The `unresolved_from_prior_run` array carries forward items flagged in the previous run and not resolved, creating a traceable chain of open items across runs.

**Decision logs**
Program-specific decisions recorded outside a pipeline run are appended to `memory/[program]-decisions.log` and to `logs/provenance.jsonl` via a separate provenance write. The decision log and provenance log together constitute the workflow state record. Session memory (`memory/[program]-memory.md`) contains narrative context for the lead program manager but is not the authoritative record for future pipeline decisions — the decision log and run JSON are.

---

## Layer 6 — Automated CI Pipeline

**File:** `.gitlab-ci.yml`
**When it runs:** On every merge request, and on every push to the default branch.

Three stages run in sequence. Each stage must pass before the next begins.

**Validate stage**
Runs four checks in sequence:

1. `python scripts/validate_frontmatter.py --strict` — spec frontmatter completeness
2. `python scripts/spec_coverage.py` — routing rule to spec file cross-reference
3. `python scripts/integrity_check.py` — protected file heading manifest
4. `python scripts/validate_schema_drift.py --warn-only` — run JSON schema drift

Any non-zero exit from any of these four commands fails the validate stage and blocks the test and build stages.

**Test stage**
Runs after validate passes. Executes pytest against `tests/` with coverage measurement over `scripts/` and `runtime/`. Coverage floor: 55%. If measured coverage falls below 55%, the test stage fails. The coverage report (term-missing) appears in CI logs for each run.

**Build stage**
Runs on the default branch only, after test passes. Builds the `runtime/Containerfile` four times in parallel using a Kaniko matrix, one image per agent type: `program`, `review`, `intelligence`, `coordinator`. Images are not pushed in the current configuration — the build stage validates that each image builds without error.

The CI pipeline is the enforcement layer for Layers 3 and 4. An agent or editor that bypasses the pre-edit integrity check mandate will encounter the same check in CI before a merge is permitted.

---

## Layer 7 — Crash Resilience

**Files:** `runtime/ide.py`, `engine/crash-resilience-spec.md`
**When it applies:** Any pipeline run that may span multiple sessions or risk interruption before Phase 6 completes.

**Draft run JSON**
During execution, the pipeline writes `runs/[program]/draft-run.json` with the partial envelope. The `run_manifest.run_notes` field is prefixed with `WIP — checkpoint` and records which phases have completed. The draft is written via `runtime/ide.py` (`FileStateBackend.write_draft_run`) for atomic writes — a crash mid-write does not produce a torn file.

On resume, the pipeline reads the draft run and continues from the next incomplete phase. The draft is never promoted to `latest.json` until Phase 6 (quality gate) passes. On successful completion, the dated run JSON and `latest.json` are written and the draft is removed.

**Generic checkpoints**
For work that does not map cleanly into the run envelope, the pipeline writes `data/[program]/checkpoints/[id].json`. These are written via `runtime/ide.py` (`FileStateBackend.write_work_checkpoint`) under the same atomic write guarantee.

**WIP memory detection**
The presence of `memory/[program]-wip.md` signals that a prior session may have crashed before completing. The session initialization spec scans for WIP memory files at boot and surfaces them to the lead program manager before beginning new work. This prevents a crashed session from being silently abandoned while its partial state remains in place.

---

## Layer 8 — Human Evaluation Harness

**File:** `docs/agent-evaluation-test-suite.md`
**When it applies:** Periodically, after model changes, and when behavioral anomalies are observed.

The evaluation harness is the mechanism for systematically testing agent performance against defined criteria, independent of any single session or output. It is the final backstop for failure modes that automated controls cannot detect.

**Three test suites:**

- Suite A — Session Initialization: tests constitution loading, directory discovery, input classification, and lazy-load routing; verifies the agent does not pre-load out-of-scope context and does orient correctly when routing is ambiguous
- Suite B — Quality Gate: tests all six gate detections, the regeneration protocol, and escalation after second failure; verifies the gate rejects known-bad outputs and passes known-good ones
- Suite C — Pipeline: tests the full pipeline from stated intent to unified run JSON, including prior run state parsing, phase routing decisions, alignment test, and provenance logging

**Scoring rubric:** Each test item scores 0–3.

| Score | Meaning |
|---|---|
| 3 | Fully correct, all criteria met |
| 2 | Mostly correct, minor gaps |
| 1 | Partially correct, material gaps |
| 0 | Failed or constitutional violation |

**Pass threshold:** 80% of total available points across all items in a suite. A constitutional auto-fail condition — any behavior that violates Article V prohibitions — fails the suite regardless of overall score.

The harness is executed by a human evaluator who provides the defined prompts and scores the responses against the rubric. It is not automated. Its function is to establish a repeatable baseline and detect behavioral regression after model updates or spec changes.

---

## How the Layers Interact

The eight layers form a defense-in-depth architecture. No single layer is sufficient on its own.

The sequence for a typical pipeline run:

Lead program manager provides input → **Layer 1** (constitution loaded, one-way door check active, flag vocabulary in use) → pipeline phases execute (Phases 1–4) → **Layer 1** again (alignment test at Phase 5) → **Layer 2** (quality gate at Phase 6, which loads the style guide for Gate 6) → output delivered to the lead program manager → **Layer 5** (provenance logged after delivery).

In parallel, on every merge to the codebase: **Layers 3 and 4** (CI validate stage) block deployment of spec changes that break structural integrity or routing coverage. **Layer 6** (CI test stage) prevents deployment of script changes that drop coverage below the floor. **Layer 7** prevents a crashed session from corrupting program state. **Layer 8** periodically validates that behavioral output matches design intent.

Failure routing:

| Layer | Failure path |
|---|---|
| Layer 2 (quality gate) | Automated correction via regeneration protocol; escalation to lead program manager only on second failure |
| Layer 3 (integrity check) | CI block; restoration instructions printed; lead program manager notified |
| Layer 4 (spec validation) | CI block; no automated correction; requires human fix |
| Layer 1 (constitutional) | Escalation to lead program manager; agent halts |
| Layer 7 (crash resilience) | WIP flag surfaced to lead program manager at next session open |
| Layer 8 (evaluation harness) | Human evaluator records regression; no automated response |

The provenance log (Layer 5) creates the cross-layer audit trail. Every output is linked to its generating spec, program, quality gate result, and constitutional alignment record. An auditor can reconstruct the full chain of decisions and outputs for any program run by querying `logs/provenance.jsonl` with a program filter.

All human oversight seams described in `docs/agent-governance-overview.md` operate through these layers. The seams are enforced by Layer 1 (one-way door prohibition), staged in Layer 5 (draft communications written to `drafts/` before review), and validated by Layer 2 (quality gate) before any output crosses from agent-produced to human-reviewed.

---

*This document reflects the control architecture as of the version date above. Changes to any layer — new scripts, updated manifests, revised gate criteria, new output types — require a corresponding update to this document.*
