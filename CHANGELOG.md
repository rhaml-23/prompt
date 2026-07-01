# Changelog

All notable changes to the compliance agent system are documented here.
Versioned by spec and schema changes, not individual sessions.

---

## 2026-03-26 — ISO 42001 Framework Specialist

### Framework Specialist Addition
- Created `agents/framework-iso42001.md` — ISO/IEC 42001:2023 AI Management System (AIMS) specialist with Annex A control interpretation, AI-specific SoA assembly, crosswalks to NIST AI RMF and EU AI Act, and SC 42 publication monitoring
- Added ISO 42001 routing rule to `runtime/router.py` — matches `iso 42001`, `aims`, and `ai management system` patterns
- Added ISO 42001 / AIMS entry to `engine/session-init-spec.md` routing table
- Updated `README.md` agents directory description to enumerate all framework specialists

---

## 2026-03-26 — Phase 3 Fleet-Native Patterns

### Phase 3 Prerequisite — Deployed Runtime
- Created `runtime/deployed.py` — PostgreSQL/NATS-backed implementations of all four runtime interfaces (`DbStateBackend`, `NatsMessageBus`, `DbMemoryStore`, `DbAuditLog`)
- Auto-creates database tables and indexes on initialization
- Hash chain integrity preserved in deployed-mode audit log (identical algorithm to IDE mode)
- Updated `runtime/factory.py` to wire deployed mode (no longer raises `NotImplementedError`)
- Updated `runtime/entrypoint.py` with full deployed-mode startup sequence including trust and metrics initialization

### Intelligent Routing and Load Distribution (3a)
- Created `runtime/router.py` — dynamic work router with `DynamicRouter` and `PriorityQueue` classes
- 23 routing rules with regex pattern matching (replaces static routing table as the decision engine)
- Priority elevation for red-program work items
- Trust-level-aware confirmation requirements (level 3 agents get auto-routed work)
- Load-aware agent selection (routes away from overloaded agents)
- Batch routing with priority ordering (critical before high before normal before low)
- Updated `agents/coordinator.md` with dynamic routing function (Function 2) replacing static routing

### Continuous Evidence Lifecycle (3b)
- Created `agents/evidence-agent.md` — evidence lifecycle agent with staleness monitoring, gap detection, evidence validation (5 levels: strong/adequate/weak/missing/invalid), and source integration
- Created `config/schemas/evidence-record.schema.json` v1.0 — evidence records with staleness tracking, validation levels, source types, and collection windows
- Evidence cadence rules defined: vulnerability scans (30d), access reviews (90d), pen tests (365d), etc.
- Communication interface: accepts `EVIDENCE_CHECK`, `CONTROL_MAPPING`, `FRAMEWORK_UPDATE`; emits `EVIDENCE_ALERT`, `EVIDENCE_REPORT`, `ESCALATION`

### Cross-Framework Intelligence (3c)
- Created `runtime/crosswalk.py` — Common Control Catalog (CCC) engine with `CommonControl`, `ControlMapping`, and `CommonControlCatalog` classes
- Created `config/schemas/common-control-catalog.schema.json` v1.0 — schema for cross-framework control mappings with evidence reuse tracking, 5 mapping confidence levels, and efficiency statistics
- Impact analysis: when a control finding changes, propagates impact across all frameworks sharing that control
- Efficiency reporting: identifies where one evidence artifact satisfies controls across multiple frameworks
- Serialize/deserialize roundtrip support for catalog persistence

### Predictive Program Health (3d)
- Created `scripts/predictive_health.py` — predictive health analysis with 4 prediction functions
- Health trajectory analysis (improving/stable/declining based on historical run scores)
- Certification timeline prediction (gap closure velocity → estimated ready date)
- Audit readiness scoring (0-100 scale with 4 readiness levels)
- Resource contention forecasting (shared vendors, deadline clustering)
- CLI interface: `--program`, `--portfolio`, `--output`, `--detail` flags

### Graduated Autonomy (3e)
- Created `runtime/trust.py` — trust level management with `TrustManager` and `TrustRecord` classes
- Three-tier trust model: Level 1 (human reviews all), Level 2 (exceptions only), Level 3 (autonomous)
- Promotion criteria: 20+ actions at 95%+ quality gate pass rate for L1→L2; 50+ actions at 99%+ for L2→L3
- Demotion triggers: quality gate failure (-1 level), constitutional violation (-2 levels), critical review finding (-2 levels)
- Per-agent per-action-type trust levels (e.g. program agent may be L2 for monitoring but L1 for full runs)
- Serialize/deserialize support for trust state persistence
- Trust level changes logged as audit trail events

### Fleet Observability (3f)
- Created `runtime/metrics.py` — fleet metrics collector with `FleetMetricsCollector`, `AgentMetrics`, `ProgramMetrics`, and `CostRecord` classes
- Agent health tracking: status, error rates, action counts, token usage, trust level
- Program performance tracking: finding velocity, evidence coverage, run cadence
- Cost tracking: token usage grouped by agent, program, or action
- Decision audit trail: routing decisions, escalations, authority boundary checks
- Created `scripts/fleet_dashboard.py` — HTML fleet dashboard with dark theme showing agent health, program performance, cost breakdown, predictions, and decision trail
- CLI interface: `--metrics`, `--portfolio`, `--predictions`, `--output`, `--open`, `--summary` flags

### Schema and Message Updates
- Updated `config/schemas/agent-message.schema.json` — added 11 new message types: `ROUTING_DECISION`, `EVIDENCE_CHECK`, `EVIDENCE_ALERT`, `EVIDENCE_REPORT`, `CCC_UPDATE`, `IMPACT_ANALYSIS`, `TRUST_PROMOTION`, `TRUST_DEMOTION`, `METRICS_REPORT`, `PREDICTION_REPORT`, `CIRCUIT_BREAKER`
- Created `config/schemas/trust-state.schema.json` v1.0 — trust level state with change history and action statistics
- Created `config/schemas/fleet-metrics.schema.json` v1.0 — fleet operational metrics with agent, program, cost, and decision schemas
- Total schemas: 8 (4 from Phase 2 + 4 new in Phase 3)

### Routing and Agent Updates
- Updated `engine/session-init-spec.md` routing table — added 6 new entries for evidence lifecycle, cross-framework crosswalk, common control catalog, predictive health, fleet dashboard, and trust level report
- Updated `agents/coordinator.md` — added Functions 4 (fleet health monitoring), 5 (predictive intelligence), expanded Function 2 (dynamic routing), expanded escalation protocol (4 new triggers), expanded communication interface (7 new message types accepted, 3 new emitted)

### Testing
- Created `tests/test_phase3.py` — 56 new tests covering dynamic router (10), priority queue (4), common control catalog (6), trust manager (13), fleet metrics (6), schemas (5), predictive health (7), evidence agent validation (2), routing table completeness (1), plus 2 existing tests updated
- All 179 tests passing (123 Phase 1-2 + 56 Phase 3)

---

## 2026-03-26 — Phase 2 Fleet Architecture

### Agent Decomposition (2a)
- Created `agents/program-agent.md` — per-program lifecycle management agent with owned specs, state access, authority boundary, communication interface, and dual-mode instantiation
- Created `agents/review-agent.md` — quality assurance agent wrapping run-reviewer, quality-gate, redteam, and entropy specs
- Created `agents/intelligence-agent.md` — continuous external signal monitoring agent with source catalog and scan cadences

### Coordination Layer (2b)
- Created `agents/coordinator.md` — portfolio coordinator implementing Path 1 (aggregator) with Path 2 (routing authority) preparation
- Created `config/schemas/portfolio-state.schema.json` — versioned JSON Schema for cross-program portfolio state
- Defined escalation protocol with trigger-action table for coordinator decision-making

### Framework Specialists (2c)
- Created `agents/framework-nist-fedramp.md` — NIST 800-53, FedRAMP, CSF, SP 800-171, CMMC, AI RMF specialist
- Created `agents/framework-iso27001.md` — ISO 27001/27002, 27017, 27018, 27701 specialist with SoA assembly
- Created `agents/framework-soc2.md` — SOC 2 / AICPA TSC specialist with Type I/II readiness assessment

### Abstraction Layer (2d)
- Created `runtime/interfaces.py` — abstract base classes for StateBackend, MessageBus, MemoryStore, AuditLog
- Created `runtime/ide.py` — file-based IDE-mode implementations for all four interfaces
- Created `runtime/factory.py` — runtime factory selecting implementations by deployment mode
- AuditLog implementation includes cryptographic hash chaining for tamper detection

### Schema Registry (2e)
- Created `config/schemas/portfolio-state.schema.json` v1.0 — portfolio state with program summaries, cross-program signals, health aggregation
- Created `config/schemas/run-output.schema.json` v1.1 — pipeline run output envelope (formalized from inline orchestrator definition)
- Created `config/schemas/agent-message.schema.json` v1.0 — inter-agent message envelope with 26 message types
- Created `config/schemas/audit-entry.schema.json` v1.0 — append-only audit log entry with hash chain fields

### Testing Framework (2f)
- Created `tests/test_spec_validation.py` — 103 tests: frontmatter presence, schema compliance, governed_by, bare path detection, cross-references, routing targets, schema validation
- Created `tests/test_runtime.py` — 20 tests: state backend CRUD, memory store operations, audit log hash chain, message bus send/receive/escalate, runtime factory
- All 123 tests passing

### Deployment Manifests (2g)
- Created `runtime/Containerfile` — parameterized multi-agent container using UBI9 Python 3.12
- Created `runtime/entrypoint.py` — container entrypoint with agent type selection and validation
- Created OpenShift deployment manifests for program-agent, review-agent, intelligence-agent, coordinator
- Created ConfigMap and Secret templates for fleet configuration
- Created `.github/workflows/ci.yaml` — CI pipeline: frontmatter validation → spec coverage → integrity check → test suite → container build

---

## 2026-03-26 — Phase 1 Stabilization (Complete)

### Documentation (1a)
- Updated `README.md` to reflect actual repo structure: added `agents/`, `commands/` directories, updated `functions/` with 4 missing specs (external-intel, control-assessment, management-system-assembler, compliance-doc-generator), updated `skills/` to show actual contents (research.md, gemara.md), updated `memory/` to three-file model
- Rewrote all directory READMEs (`config/`, `docs/`, `engine/`, `functions/`, `memory/`, `scripts/`, `skills/`) to replace stale Archivist auto-generated indexes with accurate, descriptive content
- Fixed `functions/README.md` — removed incorrect `quality-gate-spec.md` listing (lives in `engine/`)
- Fixed `engine/README.md` — added missing `quality-gate-spec.md`
- Fixed `config/README.md` — added missing `spec-frontmatter-schema.yaml`
- Fixed `skills/README.md` — added missing `gemara.md`
- Fixed `docs/README.md` — removed reference to non-existent `ROADMAP.md`
- Fixed `scripts/README.md` — added missing `auditor_view_renderer.py`, `spec_coverage.py`, `validate_frontmatter.py`
- Fixed all stale `/specs/` paths in `program-pipeline-orchestrator.md`, `program-monitoring-spec.md`, `vendor-management-spec.md`, `program-comms-spec.md`, and `docs/agent-evaluation-test-suite.md`
- Normalized all body text `Governed by:` references to `config/constitution.md` (was `/constitution.md` in program-comms, compliance-redteam, compliance-entropy, program-monitoring, vendor-management)

### Frontmatter (1b)
- Defined canonical YAML frontmatter schema at `config/spec-frontmatter-schema.yaml` with fleet-ready fields (`agent_role`, `state_reads`, `state_writes`, `deployment_modes`)
- Normalized `governed_by` to `config/constitution.md` across all specs
- Fixed bare filename references in frontmatter `invokes`/`invoked_by`/`depends_on` fields across `program-pipeline-orchestrator.md`, `program-comms-spec.md`, `program-monitoring-spec.md`, `vendor-management-spec.md` to use relative paths from repo root
- Enhanced `validate_frontmatter.py` with bare filename detection, `agent_role` validation, and `deployment_modes` validation
- All 21 spec and agent files pass frontmatter validation

### Memory Model (1c)
- Verified memory housekeeping and migration specs are complete at `memory/` paths
- Confirmed three-file model is consistently documented across `README.md`, `memory/README.md`, and session-init routing table
- Memory specs remain in `memory/` (consistent with existing convention)

### Quality Infrastructure (1d)
- Added `scripts/calendar_exporter.py` — run JSON → .ics and markdown event list (was referenced in `calendar-output-spec.md` but missing)
- Added `scripts/validate_frontmatter.py` — validates YAML frontmatter against canonical schema
- Added `scripts/spec_coverage.py` — validates routing table and orchestrator cross-reference integrity
- Added `compliance-doc-generator-spec.md` to session-init routing table (was missing)
- Fixed routing table entry for run-reviewer agent (was `agents/compliance-run-reviewer.md`, actual file is `agents/run-reviewer.md`)
- All specs pass frontmatter validation and spec coverage checks

---

## 2026-03-03 — External Intel and System Expansion

### Specs Added
- `functions/external-intel-spec.md` v1.0 — external source monitoring and risk deltas
- `functions/control-coverage-spec.md` v2.0 — control mapping and gap analysis
- `functions/risk-register-spec.md` v2.0 — risk register and POA&M starter

### Constitution
- v1.5 — added IV.12 (Research and Synthesis), IV.13 (Format-to-Information-Type Matching), IV.14 (Good Enough Calibration), IV.15 (Channel Calibration), IV.16 (External Signal Synthesis)
- `functions/program-intake-spec.md` v2.0 — added BUILD_MODE and Pass 4 autonomous build

### Documentation
- Added `docs/agent-governance-overview.md` — auditor-facing governance narrative
- Rewrote `README.md` for application-style directory structure

---

## Prior History

System development history prior to formal changelog. See `docs/next-phase-context.md` for the 2026-03-03 session handoff document covering full build history.

### Key Milestones
- Constitution v1.0–v1.4 — progressive behavioral mandate development
- Engine specs: orchestrator, session-init, weekly-session, quality-gate, spec-creation, portfolio-orchestrator
- Function specs: program-intake, program-monitoring, program-comms, vendor-management, calendar-output, compliance-entropy, compliance-redteam, auditor-view
- Scripts: dashboard, briefing_renderer, draft_formatter, portfolio_renderer, auditor_view_renderer, provenance_log, integrity_check
- Memory model evolution: single-file to three-file (state/decisions.log/archive)
- Agents: run-reviewer with D1-D6 review dimensions and spec improvement workflow
- Commands: 13 slash commands for daily operations
