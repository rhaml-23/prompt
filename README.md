# Program Management Pipeline

A portable, LLM-powered professional operating system for compliance and security program managers. Encodes expertise into reusable specs, automates routine oversight work, enforces output quality and constitutional alignment, and produces structured outputs you can act on or route to downstream tooling.

**Designed for:** Security and compliance program managers who want to operate at a strategic oversight level — reviewing and deciding, not executing.

**Runs on:** Any capable LLM (Claude, Gemini, GPT, local Ollama models) + Python 3.9+

**Optional — Archivist:** If you use Archivist or similar tooling, all engine and function specs carry YAML frontmatter (`resource_type: spec`) for discovery and tagging. Not required to run this repo in Cursor.

---

## Supported Environments

The core specs (`config/`, `engine/`, `commands/`, `agents/`, `functions/`) are tool-agnostic — they work in any LLM interface. Two thin adapter layers wire them into specific tools without changing the source of truth:

| Layer | Cursor | Claude Code |
|---|---|---|
| Always-loaded context | `.cursor/rules/*.mdc` | `CLAUDE.md` (repo root) |
| Slash commands | `.cursor/skills/*/SKILL.md` | `.claude/commands/*.md` |
| Canonical specs | `commands/*.md` ← single source of truth for both | |

**Cursor:** Open the repo in Cursor. The `.cursor/rules/` files load automatically. Use `/[command]` in the Agent composer to invoke any skill.

**Claude Code:** Run `claude` from the repo root. `CLAUDE.md` loads automatically at session start. Use `/[command]` in the Claude Code prompt to invoke any slash command.

Both adapters point to the same `commands/*.md` specs. Adding a new command requires one entry in `commands/`, one SKILL.md in `.cursor/skills/`, and one wrapper in `.claude/commands/`.

---

## Table of Contents

1. [Supported Environments](#supported-environments)
2. [System Architecture](#system-architecture)
3. [Repo Structure](#repo-structure)
4. [Directory Guide](#directory-guide)
5. [Load Order](#load-order)
6. [First-Time Setup](#first-time-setup)
7. [Using This Repo in Cursor](#using-this-repo-in-cursor)
8. [Using This Repo in Claude Code](#using-this-repo-in-claude-code)
9. [Full Build — New Program](#full-build--new-program)
10. [Running the Pipeline](#running-the-pipeline)
11. [Weekly Session Workflow](#weekly-session-workflow)
12. [Daily Workflow](#daily-workflow)
13. [Updating State with New Materials](#updating-state-with-new-materials)
14. [Function Reference](#function-reference)
15. [Script Reference](#script-reference)
16. [Provenance Log](#provenance-log)
17. [Episodic Memory](#episodic-memory)
18. [Obsidian Integration](#obsidian-integration)
19. [Troubleshooting](#troubleshooting)
20. [Design Principles](#design-principles)

---

## System Architecture

The system is organized as an application with six layers:

**Config** — The constitution and build standards govern how everything else behaves. Loaded before any other file. Never overridden by any spec or agent instruction.

**Engine** — The runtime. Handles session management, pipeline routing, output validation, and the meta-spec for extending the system. Runs on every session.

**Functions** — Discrete callable work specs. Each encodes one work pattern. Invoked by the engine when the work matches their domain.

**Skills** — Behavioral instructions living in the constitution. Applied automatically every session. Promoted to files in `/skills/` when they become task-specific enough to warrant selective loading.

**Scripts** — Python utilities that consume pipeline JSON and produce human-ready artifacts. Stateless, standard-library-first, runs anywhere.

**Data/State** — Program materials drop zone, versioned run JSON, episodic memory, provenance log, and generated outputs. Git tracks everything.

```
Lead program manager
    │
    ▼
.cursor/rules/ → engine/session-init-spec.md   ← Cursor entry point
CLAUDE.md     → engine/session-init-spec.md   ← Claude Code entry point
    │           engine/weekly-session-spec.md  ← Weekly focused sessions
    │
    ▼
config/constitution.md                          ← Governing authority (load first)
    │
    ▼
memory/[program]-memory.md                      ← Hot layer (read at open, update at close)
    │
    ▼
engine/program-pipeline-orchestrator.md         ← Pipeline routing
    │
    ├── functions/program-intake-spec.md        ← Scope, people, commitments
    │       └── [full_build triggers] ──────────────────────────────────────┐
    ├── functions/program-monitoring-spec.md    ← Cadence, escalations      │
    ├── functions/vendor-management-spec.md     ← Vendor scoring            │
    ├── functions/program-comms-spec.md         ← Status reports, recaps    │
    ├── functions/control-coverage-spec.md      ← Control mapping & gaps ◄──┘
    ├── functions/risk-register-spec.md         ← Risk register & POA&M
    ├── engine/quality-gate-spec.md             ← Output validation (runs last)
    │
    ▼
runs/[PROGRAM]/latest.json                      ← Persistent program state
    │
    ├── scripts/briefing_renderer.py            ← → morning briefing markdown
    ├── scripts/draft_formatter.py              ← → draft communications
    └── scripts/dashboard.py                    ← → ui/dashboard.html

Portfolio layer (sits above programs):
    engine/portfolio-orchestrator.md       ← cross-program triage and briefing
        └── scripts/portfolio_renderer.py  ← → ui/portfolio.html

Post-run review:
    agents/run-reviewer.md                      ← Compliance run review and spec improvement

Standalone functions (invoked directly):
    functions/compliance-entropy-spec.md        ← Longitudinal compliance analysis
    functions/compliance-redteam-spec.md        ← Adversarial artifact review
    functions/external-intel-spec.md            ← External source monitoring and risk deltas
    functions/control-assessment-spec.md        ← Auditor template filling
    functions/management-system-assembler-spec.md ← ISMS/AIMS document assembly
    functions/compliance-doc-generator-spec.md  ← Orchestrated compliance output generation
    functions/product-evidence-spec.md          ← Product repo scan → control matrix, evidence gaps
    functions/post-audit-spec.md                ← Post-audit lessons learned, corrective actions, feed-forward
    functions/calendar-output-spec.md           ← LLM fallback calendar generation
```

---

## Repo Structure

```
/
├── .cursorrules                                ← Cursor persistent config — must stay at root
├── README.md                                   ← this file
├── CHANGELOG.md                                ← version history for specs and schema
│
├── config/
│   ├── constitution.md                         ← LOAD FIRST — behavioral and ethical governance
│   ├── tool-requirements.md                    ← build standards for all scripts and tools
│   ├── spec-frontmatter-schema.yaml            ← canonical YAML frontmatter schema
│   └── schemas/                                ← versioned JSON Schemas for fleet data types
│       ├── portfolio-state.schema.json         ← cross-program portfolio state
│       ├── run-output.schema.json              ← pipeline run output envelope
│       ├── agent-message.schema.json           ← inter-agent message envelope (37 types)
│       ├── audit-entry.schema.json             ← append-only audit log entry
│       ├── common-control-catalog.schema.json  ← cross-framework control mappings
│       ├── evidence-record.schema.json         ← evidence lifecycle tracking
│       ├── trust-state.schema.json             ← agent trust levels and history
│       └── fleet-metrics.schema.json           ← fleet operational metrics
│
├── engine/
│   ├── program-pipeline-orchestrator.md        ← pipeline entry point and routing
│   ├── session-init-spec.md                    ← Cursor agent initialization
│   ├── crash-resilience-spec.md                ← checkpoints, draft-run.json, resume after interrupt
│   ├── weekly-session-spec.md                  ← weekly focused work session
│   ├── quality-gate-spec.md                    ← output validation — runs before every delivery
│   ├── spec-creation-spec.md                   ← how to extend the system with new specs
│   └── portfolio-orchestrator.md               ← cross-program portfolio briefing and triage
│
├── functions/
│   ├── program-intake-spec.md                  ← program onboarding and full build
│   ├── program-monitoring-spec.md              ← ongoing oversight and escalations
│   ├── program-comms-spec.md                   ← status reports, recaps, requests
│   ├── vendor-management-spec.md               ← vendor scoring and remediation
│   ├── control-coverage-spec.md                ← control mapping and gap analysis
│   ├── risk-register-spec.md                   ← risk register and POA&M starter
│   ├── calendar-output-spec.md                 ← calendar generation (LLM mode)
│   ├── compliance-entropy-spec.md              ← longitudinal compliance analysis
│   ├── compliance-redteam-spec.md              ← adversarial artifact review
│   ├── auditor-view-spec.md                    ← read-only auditor compliance posture dashboard
│   ├── external-intel-spec.md                  ← external source monitoring and risk deltas
│   ├── control-assessment-spec.md              ← auditor template filling from framework + product docs
│   ├── management-system-assembler-spec.md     ← ISMS/AIMS document assembly from artifacts
│   ├── compliance-doc-generator-spec.md        ← orchestrated CSV/MD compliance output generation
│   ├── product-evidence-spec.md               ← product repo scan → ISO 42001 control matrix and evidence gaps
│   └── post-audit-spec.md                     ← post-audit lessons learned, corrective actions, feed-forward
│
├── agents/
│   ├── program-agent.md                        ← per-program lifecycle management agent
│   ├── review-agent.md                         ← quality assurance and adversarial review agent
│   ├── intelligence-agent.md                   ← external signal monitoring agent
│   ├── evidence-agent.md                       ← continuous evidence monitoring and validation
│   ├── coordinator.md                          ← portfolio coordination and dynamic routing
│   └── run-reviewer.md                         ← post-run compliance review and spec improvement
│
├── commands/
│   ├── COMMANDS.md                             ← slash command reference
│   ├── daily-brief.md                          ← /daily-brief
│   ├── program-status.md                       ← /program-status
│   ├── due-this-week.md                        ← /due-this-week
│   ├── meeting-prep.md                         ← /meeting-prep
│   ├── draft-status-update.md                  ← /draft-status-update
│   ├── evidence-due.md                         ← /evidence-due
│   ├── log-decision.md                         ← /log-decision
│   ├── update-item.md                          ← /update-item
│   ├── intel-scan.md                           ← /intel-scan
│   ├── auditor-view.md                         ← /auditor-view
│   ├── provenance-query.md                     ← /provenance-query
│   ├── meeting-debrief.md                      ← /meeting-debrief
│   └── control-assessment.md                   ← /control-assessment
│
├── skills/
│   ├── research.md                             ← research and synthesis skill
│   └── gemara.md                               ← Gemara YAML generation and QC
│
├── scripts/
│   ├── auditor_view_renderer.py                ← per-program auditor dashboard → ui/[program]-auditor-[date].html
│   ├── briefing_renderer.py                    ← run JSON → morning briefing
│   ├── calendar_exporter.py                    ← run JSON → .ics calendar and markdown event list
│   ├── dashboard.py                            ← all programs → HTML dashboard
│   ├── draft_formatter.py                      ← run JSON → draft communications
│   ├── integrity_check.py                      ← protected file heading validation
│   ├── portfolio_renderer.py                   ← portfolio JSON → ui/portfolio.html
│   ├── provenance_log.py                       ← deliverable provenance log
│   ├── spec_coverage.py                        ← routing table and orchestrator cross-reference validation
│   ├── validate_frontmatter.py                 ← YAML frontmatter validation against schema
│   ├── predictive_health.py                    ← predictive program health and certification timeline
│   └── fleet_dashboard.py                      ← fleet observability HTML dashboard
│
├── memory/
│   ├── session-memory-template.md              ← copy and rename to [program]-memory.md
│   ├── memory-housekeeping-spec.md             ← quarterly maintenance — compress, validate, refresh
│   ├── memory-migration-spec.md                ← migration helper (if needed)
│   └── [program_slug]-memory.md                ← one per active program
│
├── runs/
│   └── [PROGRAM_NAME]/
│       ├── YYYY-MM-DD-run.json                 ← versioned run output
│       └── latest.json                         ← most recent run (never edit directly)
│
├── data/
│   ├── [PROGRAM_NAME]/                         ← program materials and agent-generated data
│   │   └── materials/                          ← SOWs, emails, meeting notes, audit docs
│   └── portfolio/
│       └── latest.json                         ← cross-program portfolio state (written by portfolio-orchestrator)
│
├── ui/
│   ├── dashboard.html                          ← generated by scripts/dashboard.py
│   ├── portfolio.html                          ← generated by scripts/portfolio_renderer.py
│   └── [program]-auditor-[date].html          ← generated by scripts/auditor_view_renderer.py
│
├── logs/
│   └── provenance.jsonl                        ← append-only deliverable history
│
├── drafts/
│   └── [PROGRAM_NAME]_YYYY-MM-DD/
│       ├── 00_index.md
│       └── 01_[type]_[recipient].md
│
├── runtime/
│   ├── __init__.py                             ← runtime abstraction layer package
│   ├── interfaces.py                           ← abstract interfaces (StateBackend, MessageBus, MemoryStore, AuditLog)
│   ├── ide.py                                  ← file-based IDE-mode implementations
│   ├── deployed.py                             ← PostgreSQL/NATS deployed-mode implementations
│   ├── factory.py                              ← runtime factory — selects implementations by mode
│   ├── router.py                               ← dynamic work router with priority queue
│   ├── crosswalk.py                            ← cross-framework Common Control Catalog engine
│   ├── trust.py                                ← graduated autonomy trust level management
│   ├── metrics.py                              ← fleet observability metrics collection
│   ├── entrypoint.py                           ← container entrypoint for IDE and deployed modes
│   ├── Containerfile                           ← parameterized multi-agent container
│   ├── requirements.txt                        ← runtime dependencies
│   └── deploy/                                 ← OpenShift/Kubernetes deployment manifests
│
├── tests/
│   ├── test_spec_validation.py                 ← frontmatter, cross-reference, and schema tests
│   ├── test_runtime.py                         ← runtime abstraction implementation tests
│   └── test_phase3.py                          ← Phase 3: router, crosswalk, trust, metrics, predictions
│
└── docs/
    ├── obsidian-vault-guide.md                 ← Obsidian vault setup and workflow
    ├── agent-evaluation-test-suite.md          ← standardized agent performance tests
    ├── agent-governance-overview.md            ← auditor-facing governance narrative
    ├── next-phase-context.md                   ← coordinator/fleet architecture planning
    └── compliance-agent-guide.docx             ← human-facing compliance agent guide
```

**Rule:** Never edit `latest.json` directly — always overwritten by the pipeline.
**Rule:** Never edit `provenance.jsonl` directly — always append-only via `provenance_log.py`.
**Rule:** Never edit memory files except by appending a new session entry or updating standing context. Never delete entries.

---

## Directory Guide

Understanding what lives where makes maintenance obvious.

**`config/`** — Rules the system runs under. Constitution governs agent behavior. Tool requirements govern how scripts are built. Neither is executable — both are loaded as context. When you amend the system's values or build standards, this is where you do it.

**`engine/`** — The runtime layer. These files run on every session regardless of what you're doing. The orchestrator routes work. Session init and weekly session manage your interaction with the agent. The quality gate validates output. The spec creation spec is how you extend the engine itself. Changes here affect every session.

**`functions/`** — Discrete work specs. Each encodes one domain: intake, monitoring, comms, vendor, coverage, risk, calendar, entropy, red team, external intel, auditor view, control assessment, management system assembly, compliance doc generation, product evidence extraction. The engine calls them when work matches their domain. Adding a new work pattern means adding a file here and wiring it into the orchestrator and session-init routing table. Changes here affect only the relevant work pattern.

**`agents/`** — Agent definitions for the compliance fleet. Each agent wraps one or more specs and defines its authority boundary, communication interface, state access, and deployment modes. Contains `program-agent.md` (per-program lifecycle management), `review-agent.md` (quality assurance and adversarial review), `intelligence-agent.md` (external signal monitoring), `evidence-agent.md` (continuous evidence monitoring and validation), `coordinator.md` (portfolio coordination and dynamic routing), `run-reviewer.md` (post-run compliance review with spec improvement staging), and framework specialists: `framework-nist-fedramp.md`, `framework-iso27001.md`, `framework-soc2.md`, `framework-iso42001.md` (AI management system).

**`commands/`** — Slash command specs — the tool-agnostic source of truth. Each file defines one `/command-name`. `COMMANDS.md` is the reference index. Commands route to specs or scripts — they do not contain compliance logic themselves. Cursor loads them via `.cursor/skills/*/SKILL.md`; Claude Code loads them via `.claude/commands/*.md`.

**`skills/`** — Task-specific behavioral instructions loaded selectively. Currently contains `research.md` (research and synthesis skill) and `gemara.md` (Gemara YAML generation and QC). Session-wide behavioral skills remain in `config/constitution.md` Article IV. Skills graduate to files here when they become task-specific enough to warrant selective loading.

**`scripts/`** — Python tools that consume run JSON and produce artifacts. Stateless — they read from `runs/` and write to `ui/` or `drafts/`. Adding a new output format means adding a file here. Changes here never affect specs or agent behavior.

**`memory/`** — Long-term context using one active memory file per program. `[program]-memory.md` is the hot layer loaded every session and appended at session close.

**`runs/`** — Pipeline state. One directory per program. `latest.json` is the current state. Dated files are the version history. Scripts read from here. Nothing else writes here except the pipeline.

**`data/`** — Program materials and agent-generated reference data. Drop raw inputs here before a pipeline run. The agent may also write structured data here that doesn't fit in runs — reference lookups, framework mappings, cross-run context.

**`ui/`** — Generated output for human consumption. Currently the HTML dashboard. Any future interface component lives here.

**`logs/`** — Append-only system logs. Currently the provenance log. Never edited directly.

**`drafts/`** — Staged communications. Written by `draft_formatter.py`. Reviewed and sent by you. Organized by program and date.

**`docs/`** — Human-facing reference material that isn't executable. Obsidian guide, evaluation test suite. Not loaded by the agent during normal operation.

---

## Load Order

When initializing any session or pipeline run, load in this order:

```
1. config/constitution.md                  ← values, decision hierarchy, authority boundaries
2. memory/[program]-memory.md              ← hot layer — current phase, health, blockers, recent sessions
3. engine/session-init-spec.md             ← agent behavior and routing (Cursor / ad-hoc)
   OR
   engine/weekly-session-spec.md           ← for focused weekly sessions
   OR
   engine/program-pipeline-orchestrator.md ← for direct pipeline execution
4. Relevant function spec                  ← the spec for the work at hand
5. engine/quality-gate-spec.md             ← applied automatically before any output delivery
```

`.cursor/rules/` handles steps 1–3 automatically in Cursor. `CLAUDE.md` handles steps 1–3 automatically in Claude Code.

---

## First-Time Setup

### 1. Clone or initialize your repo

```bash
git clone [your-repo-url]
cd [repo-name]
```

Or initialize fresh:

```bash
mkdir program-pipeline && cd program-pipeline
git init
mkdir -p config engine functions skills scripts memory runs data ui logs drafts docs
```

### 2. Place files in repo

```
config/constitution.md               → /config/
config/tool-requirements.md          → /config/
engine/*.md                          → /engine/
functions/*.md                       → /functions/
scripts/*.py                         → /scripts/
memory/session-memory-template.md    → /memory/
docs/*.md                            → /docs/
.cursorrules                         → / (repo root)
```

### 3. Install script dependencies

```bash
pip install rich
```

### 4. (Optional) Index specs with Archivist or similar

If you use external spec indexing, point it at this repo. Specs use YAML frontmatter with `resource_type: spec` across `engine/` and `functions/`.

### 5. Create your first program directory and memory files

```bash
mkdir -p runs/[PROGRAM_SLUG] data/[PROGRAM_SLUG]/materials
cp memory/session-memory-template.md memory/[PROGRAM_SLUG]-memory.md
```

Edit the state file Standing Context section with basic program information.

---

## Using This Repo in Cursor

### Setup

1. Open this repo in Cursor
2. `.cursorrules` is at repo root — Cursor loads it automatically
3. Drop your input into the composer, or say "weekly session" to trigger the full session workflow

### What happens at session start

1. Loads `config/constitution.md`
2. Discovers available programs via `ls runs/ memory/`
3. Classifies input and loads only what the request requires
4. For program-scoped work: loads `memory/[program]-memory.md`, reads `runs/[program]/latest.json`
5. If no input: produces a brief orientation from portfolio state, run recommendations, and recent provenance

### File resolution

Agent searches the entire repo recursively before asking about a missing file. Notes what it found and where. Interrupts only if genuinely not found anywhere.

### Dropping work in

- Email or Slack thread → classifies, routes, drafts response
- Meeting notes → extracts decisions and actions, routes to comms function
- Stakeholder request → checks provenance, routes appropriately
- "Weekly session" → full session workflow with agenda proposal
- "Run monitoring for [program]" → triggers orchestrator
- "Full build" + materials → autonomous build sequence

The agent states its classification before acting. You confirm before any one-way door action.

---

## Using This Repo in Claude Code

### Setup

1. Install Claude Code: `npm install -g @anthropic-ai/claude-code`
2. Open a terminal at the repo root
3. Run `claude` — `CLAUDE.md` loads automatically

### What happens at session start

Same as Cursor: constitution load → directory discovery → classify input → load on demand. `CLAUDE.md` carries the same boot sequence as `.cursor/rules/lazy-load.mdc`.

### Invoking commands

Type `/[command-name]` in the Claude Code prompt. The `.claude/commands/[name].md` wrapper loads and executes the canonical spec from `commands/[name].md`.

```
/init                    ← session initialization
/daily-brief             ← morning portfolio briefing
/program-status          ← single-program snapshot
/due-this-week           ← deadline digest
/kanban                  ← task board view
```

### Dropping work in

Same patterns as Cursor — paste an email, meeting notes, or a stakeholder request directly. The agent classifies, routes, and produces output through the same quality gate.

---

## Full Build — New Program

Use `new_program_full_build` to have the agent autonomously build every artifact it can from whatever materials you provide. Gaps are stubbed — a complete starting point, not a partial one.

### What gets built

1. **Program skeleton** — scope, people, commitments
2. **Control coverage matrix** — framework controls mapped to evidence and ownership state
3. **Risk register and POA&M starter** — coverage gaps rated and tracked
4. **Evidence collection calendar** — deadlines, collection windows, reminder scaffolds
5. **Draft communications** — kickoff email and stakeholder intro (flagged for review)

### Trigger

Drop materials into `data/[PROGRAM_SLUG]/materials/`, then:

```
BUILD_MODE: full_build
PROGRAM_NAME: [slug]
INTENT: new_program_full_build

[paste or reference materials]

BEGIN FULL BUILD
```

### What to expect

```
[BUILD] Program skeleton complete. Beginning autonomous build sequence.
[COVERAGE] Identified framework: FedRAMP Moderate — 325 controls
[RISK] Risk register complete: 94 items (12 critical, 31 high)
[BUILD] Evidence calendar: 47 events, 8 with reminder scaffolds
BUILD COMPLETE — [program]
```

### After the build

```bash
python scripts/dashboard.py --open
cp memory/session-memory-template.md memory/[PROGRAM_SLUG]-memory.md
git add runs/ memory/ logs/
git commit -m "feat([PROGRAM]): initial full build"
```

---

## Portfolio Briefing — Multiple Programs

When managing 2+ active programs, use the portfolio orchestrator to get a single cross-program view before deciding where to spend your time.

### What it produces

- Health classification for each program (Red / Yellow / Green) with primary reason
- Red programs auto-expand — full decision queue, blockers, and escalations visible inline
- Yellow and green programs show one-line summary
- Cross-program signals: shared vendor risk, near-term deadlines across all programs, resource contention, intel overlap
- Three suggested first actions ranked by urgency and age

### Trigger

In Cursor or any LLM interface:

```
PROGRAMS: all
SESSION_MODE: briefing
BEGIN PORTFOLIO RUN
```

For a portfolio weekly session (portfolio briefing + agenda):

```
SESSION_SCOPE: portfolio
Weekly session
```

### Render the dashboard

```bash
python scripts/portfolio_renderer.py --open
python scripts/portfolio_renderer.py --output ui/portfolio.html
```

### Health classification rules

| Health | Triggers |
|---|---|
| 🔴 Red | Any escalation, or decision queue item 14+ days old, or 2+ blockers, or run JSON 7+ days stale |
| 🟡 Yellow | Decision queue item 7–13 days old, or 1 blocker, or run JSON 1–6 days stale, or 3+ owner gaps |
| 🟢 Green | No escalations, no aged decisions, no blockers, run current |

---

## Running the Pipeline

### Parameters

```
RUN_DATE: [YYYY-MM-DD]
PROGRAM_NAME: [slug]
INTENT: [new_program | new_program_full_build | monitoring_run | vendor_review | full_run]
PRIOR_RUN: [yes | no]
OUTPUT_FORMAT: [json | markdown | both]
```

### Trigger

```
BEGIN PIPELINE
```

### Save and log

```bash
cp output.json runs/[PROGRAM]/$(date +%Y-%m-%d)-run.json
cp output.json runs/[PROGRAM]/latest.json
git add runs/[PROGRAM]/
git commit -m "feat([PROGRAM]): [intent] run"

python scripts/provenance_log.py write \
  --spec "engine/program-pipeline-orchestrator.md" \
  --output "runs/[PROGRAM]/[DATE]-run.json" \
  --output-type run_json --program "[PROGRAM]" \
  --purpose "[context]" --reusability instance --quality-gate pass
```

---

## Weekly Session Workflow

Once a week, open a focused 1–3 hour session. The system operates as a collaborator, not a task executor.

Start in Cursor: `Weekly session`
Or load `engine/weekly-session-spec.md` in any LLM interface.

The agent opens by reading memory, scanning for patterns, and proposing an agenda. It waits for your approval before starting work. At close it stages deliverables, updates memory, and logs provenance.

Memory accumulates: session 1 is sparse, session 3 activates pattern detection, session 6 is a meaningful program history.

---

## Daily Workflow

```bash
# Portfolio view first (2+ programs)
python scripts/portfolio_renderer.py --open

# Per-program if needed
python scripts/dashboard.py --open
python scripts/briefing_renderer.py --run runs/[PROGRAM]/latest.json --preview
```

Read order: Decision Queue → Summary View → Watch List → Escalations → Communications to Send → Flags → Next Run Recommendation.

---

## Updating State with New Materials

| Trigger | Intent / Spec |
|---|---|
| New SOW, contract, or scope document | `full_run` |
| Vendor check-in completed | `vendor_review` |
| Scheduled monitoring cadence reached | `monitoring_run` |
| New owner or roster change | `monitoring_run` |
| Stakeholder communication needed | `functions/program-comms-spec.md` |
| Meeting recap needed | `functions/program-comms-spec.md` |
| Weekly focused work | `engine/weekly-session-spec.md` |
| New program with all materials | `new_program_full_build` |
| Auditor review or audit prep | `functions/auditor-view-spec.md` |
| External threat or regulatory change | `functions/external-intel-spec.md` |
| Control assessment or template fill | `functions/control-assessment-spec.md` |
| ISMS or management system build | `functions/management-system-assembler-spec.md` |
| Audit closed / lessons learned | `functions/post-audit-spec.md` |
| Meeting debrief | `/meeting-debrief` command |

---

## Function Reference

### Functions (`/functions/`)

| File | Domain | Standalone | When to Use |
|---|---|---|---|
| `program-intake-spec.md` | Onboarding | — | New program or full build |
| `program-monitoring-spec.md` | Oversight | — | Ongoing oversight runs |
| `program-comms-spec.md` | Communications | ✓ | Status reports, recaps, requests |
| `vendor-management-spec.md` | Vendor | — | Vendor scoring and remediation |
| `control-coverage-spec.md` | Compliance | ✓ | Control mapping and gap analysis |
| `risk-register-spec.md` | Compliance | ✓ | Risk register and POA&M starter |
| `calendar-output-spec.md` | Calendar | ✓ | LLM fallback — prefer the script |
| `compliance-entropy-spec.md` | Compliance | ✓ | Longitudinal analysis — needs 2+ cycles |
| `compliance-redteam-spec.md` | Compliance | ✓ | Adversarial artifact review |
| `auditor-view-spec.md` | Compliance | ✓ | Read-only auditor compliance posture dashboard |
| `external-intel-spec.md` | Intelligence | ✓ | External source monitoring and risk deltas |
| `control-assessment-spec.md` | Compliance | ✓ | Fill auditor templates from framework + product docs |
| `management-system-assembler-spec.md` | Compliance | ✓ | ISMS/AIMS document assembly from artifacts |
| `compliance-doc-generator-spec.md` | Compliance | ✓ | Orchestrated CSV/MD compliance output generation |
| `product-evidence-spec.md` | Compliance | ✓ | Product repo scan → ISO 42001 control matrix and evidence gaps |
| `post-audit-spec.md` | Program Management | ✓ | Post-audit debrief — lessons learned, corrective actions, feed-forward |

### Agents (`/agents/`)

| File | Role | Fleet Role |
|---|---|---|
| `program-agent.md` | Per-program lifecycle management — pipeline, memory, functions | Program |
| `review-agent.md` | Quality assurance — run review, red team, entropy, quality gate | Review |
| `intelligence-agent.md` | External signal monitoring — vulnerabilities, regulations, frameworks | Intelligence |
| `evidence-agent.md` | Continuous evidence monitoring — staleness, gaps, validation | Evidence |
| `coordinator.md` | Portfolio coordination — aggregation, dynamic routing, fleet health | Coordination |
| `run-reviewer.md` | Post-run compliance review (D1-D6) and spec improvement staging | Review |

### Engine (`/engine/`)

| File | Role |
|---|---|
| `program-pipeline-orchestrator.md` | Pipeline entry point and routing |
| `session-init-spec.md` | Cursor agent initialization and classification |
| `weekly-session-spec.md` | Weekly focused work session |
| `quality-gate-spec.md` | Output validation before every delivery |
| `spec-creation-spec.md` | How to build new specs and skills |
| `portfolio-orchestrator.md` | Cross-program portfolio briefing and triage |

### Using functions standalone

```
Load /config/constitution.md
Load /functions/[spec-name].md
[provide inputs]
BEGIN [TRIGGER]
```

---

## Script Reference

### `dashboard.py`
```bash
python scripts/dashboard.py --open
python scripts/dashboard.py --output ui/dashboard.html
```

### `briefing_renderer.py`
```bash
python scripts/briefing_renderer.py --run runs/[program]/latest.json --preview
python scripts/briefing_renderer.py --run runs/[program]/latest.json --stdout
```

### `draft_formatter.py`
```bash
python scripts/draft_formatter.py --run runs/[program]/latest.json --list
python scripts/draft_formatter.py --run runs/[program]/latest.json
```

### `provenance_log.py`
```bash
python scripts/provenance_log.py write --spec "[spec]" --output "[path]" \
  --output-type [type] --program [slug] --purpose "[why]" \
  --reusability [template|reference|instance|artifact]

python scripts/provenance_log.py query --program fedramp_high
python scripts/provenance_log.py summary
python scripts/provenance_log.py tail --n 10
```

### `portfolio_renderer.py`
```bash
python scripts/portfolio_renderer.py --open
python scripts/portfolio_renderer.py --output ui/portfolio.html
python scripts/portfolio_renderer.py --portfolio data/portfolio/latest.json
```

### `auditor_view_renderer.py`
```bash
python scripts/auditor_view_renderer.py --program [slug] --open
python scripts/auditor_view_renderer.py --program [slug] --lookback 180
python scripts/auditor_view_renderer.py --program [slug] --output ui/custom.html
```
Print to PDF for submission: browser → Print → Save as PDF. No additional tooling required.

### `integrity_check.py`
```bash
python scripts/integrity_check.py                      # check all protected files
python scripts/integrity_check.py --file constitution.md
python scripts/integrity_check.py --list-manifest
```

Protected files: `config/constitution.md`, `engine/program-pipeline-orchestrator.md`, `engine/quality-gate-spec.md`

---

## Provenance Log

Every pipeline run and significant deliverable should be logged. Answers: what did I produce for this program, do I have a reusable artifact, what has the system produced this quarter.

Location: `logs/provenance.jsonl` — append-only, git-tracked, queryable forever.

---

## Episodic Memory

Memory gives the agent context across sessions. Without it every session starts cold. With it the agent notices patterns, tracks decisions, and surfaces avoidance without being asked.

Each program uses three files optimized for different access patterns:

- **`[program]-memory.md`** — Hot layer. Loaded every session. Current phase, health, active blockers, pending decisions, relationship notes, deferred items, recurring patterns, and session entries.

```bash
cp memory/session-memory-template.md memory/[PROGRAM_SLUG]-memory.md
```

Pattern detection scans for: deferred items pushed 3+ times, flags in 3+ consecutive runs, decision queue items stagnant 14+ days. Surfaces at session open as agenda items — observations, not accusations.

Run `BEGIN MEMORY HOUSEKEEPING` quarterly to compress sessions older than 90 days into the archive, validate the decisions log integrity, and refresh the state file from current run JSON. See `memory/README.md` for details.

---

## Obsidian Integration

Two parallel vaults. See `docs/obsidian-vault-guide.md` for setup.

**Work vault** — execution context, disposable when you leave a job.
**Personal vault** — long-term professional asset, survives every transition.

End-of-day: pipeline wrap-up → file meeting notes → transfer lessons to personal vault → commit run JSONs and memory.

---

## Troubleshooting

**LLM stopped mid-run**
`Do not ask clarifying questions. Make a reasonable inference, flag it as [INFERRED], and continue.`

**File not found after restructure**
The agent searches recursively — it will find files in new locations. If Cursor still fails, verify `.cursorrules` references paths that exist.

**Integrity check failing after restructure**
Update the file paths in the integrity check manifest to reflect `config/` and `engine/` prefixes.

**JSON output malformed or truncated**
Split materials into batches, run in passes, combine manually.

**Quality gate keeps rejecting**
Numbered headers, parenthetical subtitles, emojis, missing required sections. Two failures escalates with a correction brief.

**Memory file too large**
Keep most recent 10 entries in full. Summarize older entries. Never delete Decision Log or Deferred Items.

**Agent not detecting patterns**
Requires 3+ session entries. Expected on new files.

**Cursor not loading config**
Verify `.cursorrules` is at repo root. Paste its contents into the composer if not triggering.

---

## Design Principles

- **Constitution first.** Governs all agent behavior. Supersedes every other instruction in conflict.
- **Application structure.** Config, engine, functions, skills, scripts, data, ui — each directory has one job. Maintenance is obvious when the structure is obvious.
- **Engine vs functions.** Engine runs every session. Functions are called only when the work matches their domain. The distinction keeps the runtime lean.
- **Skills in config until they earn a file.** Behavioral instructions live in the constitution until they are numerous or task-specific enough to warrant selective loading.
- **Build completely or stub explicitly.** A complete stub is more valuable than a partial build. Gaps are marked, never silently omitted.
- **Memory over cold starts.** Every session builds on the last. Episodic memory is a first-class artifact.
- **Scripts are stateless renderers.** They read from `runs/`, write to `ui/` or `drafts/`, and know nothing about agent behavior.
- **Quality gates before delivery.** No output reaches the lead program manager without passing constitutional alignment, structural completeness, format, and tone checks.
- **Reuse over regeneration.** Check the provenance log before producing new work.
- **Search before interrupting.** Missing files get found, not escalated.
- **Patterns get named.** Drift, avoidance, and accumulating risk surface at session open.
- **One-way doors require the lead program manager.** No exceptions.
- **Portability over optimization.** Everything works in the most constrained environment: a free LLM and a terminal with Python.
