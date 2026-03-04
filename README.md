# Program Management Pipeline

A portable, LLM-powered professional operating system for compliance and security program managers. Encodes expertise into reusable specs, automates routine oversight work, enforces output quality and constitutional alignment, and produces structured outputs you can act on or route to downstream tooling.

**Designed for:** Security and compliance program managers who want to operate at a principal level — reviewing and deciding, not executing.

**Runs on:** Any capable LLM (Claude, Gemini, GPT, local Ollama models) + Python 3.9+

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Repo Structure](#repo-structure)
3. [Directory Guide](#directory-guide)
4. [Load Order](#load-order)
5. [First-Time Setup](#first-time-setup)
6. [Using This Repo in Cursor](#using-this-repo-in-cursor)
7. [Full Build — New Program](#full-build--new-program)
8. [Running the Pipeline](#running-the-pipeline)
9. [Weekly Session Workflow](#weekly-session-workflow)
10. [Daily Workflow](#daily-workflow)
11. [Updating State with New Materials](#updating-state-with-new-materials)
12. [Function Reference](#function-reference)
13. [Script Reference](#script-reference)
14. [Provenance Log](#provenance-log)
15. [Episodic Memory](#episodic-memory)
16. [Obsidian Integration](#obsidian-integration)
17. [Troubleshooting](#troubleshooting)
18. [Design Principles](#design-principles)

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
Principal
    │
    ▼
.cursorrules → engine/session-init-spec.md     ← Cursor entry point
    │           engine/weekly-session-spec.md  ← Weekly focused sessions
    │
    ▼
config/constitution.md                          ← Governing authority (load first)
    │
    ▼
memory/[program]-memory.md                      ← Episodic context (read at open, write at close)
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
    ├── scripts/calendar_exporter.py            ← → .ics + event list
    └── scripts/dashboard.py                    ← → ui/dashboard.html

Standalone functions (invoked directly):
    functions/compliance-entropy-spec.md        ← Longitudinal compliance analysis
    functions/compliance-redteam-spec.md        ← Adversarial artifact review
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
│   └── tool-requirements.md                    ← build standards for all scripts and tools
│
├── engine/
│   ├── program-pipeline-orchestrator.md        ← pipeline entry point and routing
│   ├── session-init-spec.md                    ← Cursor agent initialization
│   ├── weekly-session-spec.md                  ← weekly focused work session
│   ├── quality-gate-spec.md                    ← output validation — runs before every delivery
│   └── spec-creation-spec.md                   ← how to extend the system with new specs
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
│   └── compliance-redteam-spec.md              ← adversarial artifact review
│
├── skills/
│   └── (empty — populated when skills become task-specific enough for selective loading)
│
├── scripts/
│   ├── briefing_renderer.py                    ← run JSON → morning briefing
│   ├── draft_formatter.py                      ← run JSON → draft communications
│   ├── calendar_exporter.py                    ← run JSON → .ics + markdown events
│   ├── dashboard.py                            ← all programs → HTML dashboard
│   ├── provenance_log.py                       ← deliverable provenance log
│   └── integrity_check.py                      ← protected file heading validation
│
├── memory/
│   ├── session-memory-template.md              ← copy this to create a program memory file
│   └── [program_slug]-memory.md                ← one per active program
│
├── runs/
│   └── [PROGRAM_NAME]/
│       ├── YYYY-MM-DD-run.json                 ← versioned run output
│       └── latest.json                         ← most recent run (never edit directly)
│
├── data/
│   └── [PROGRAM_NAME]/                         ← program materials and agent-generated data
│       └── materials/                          ← SOWs, emails, meeting notes, audit docs
│
├── ui/
│   └── dashboard.html                          ← generated by scripts/dashboard.py
│
├── logs/
│   └── provenance.jsonl                        ← append-only deliverable history
│
├── drafts/
│   └── [PROGRAM_NAME]_YYYY-MM-DD/
│       ├── 00_index.md
│       └── 01_[type]_[recipient].md
│
└── docs/
    ├── obsidian-vault-guide.md                 ← Obsidian vault setup and workflow
    └── agent-evaluation-test-suite.md          ← standardized agent performance tests
```

**Rule:** Never edit `latest.json` directly — always overwritten by the pipeline.
**Rule:** Never edit `provenance.jsonl` directly — always append-only via `provenance_log.py`.
**Rule:** Never edit memory files except by appending a new session entry or updating standing context. Never delete entries.

---

## Directory Guide

Understanding what lives where makes maintenance obvious.

**`config/`** — Rules the system runs under. Constitution governs agent behavior. Tool requirements govern how scripts are built. Neither is executable — both are loaded as context. When you amend the system's values or build standards, this is where you do it.

**`engine/`** — The runtime layer. These files run on every session regardless of what you're doing. The orchestrator routes work. Session init and weekly session manage your interaction with the agent. The quality gate validates output. The spec creation spec is how you extend the engine itself. Changes here affect every session.

**`functions/`** — Discrete work specs. Each encodes one domain: intake, monitoring, comms, vendor, coverage, risk, calendar, entropy, red team. The engine calls them when work matches their domain. Adding a new work pattern means adding a file here and wiring it into the orchestrator. Changes here affect only the relevant work pattern.

**`skills/`** — Currently empty. Agent behavioral skills live in `config/constitution.md` Article IV while they are session-wide and few. When skills become numerous or task-specific enough to warrant selective loading, they graduate to files here. The constitution will reference a skills index when that threshold is reached.

**`scripts/`** — Python tools that consume run JSON and produce artifacts. Stateless — they read from `runs/` and write to `ui/` or `drafts/`. Adding a new output format means adding a file here. Changes here never affect specs or agent behavior.

**`memory/`** — Episodic logs. One file per active program. Written at session close, read at session open. The agent's long-term context. Never overwritten — always appended.

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
2. memory/[program]-memory.md              ← episodic context
3. engine/session-init-spec.md             ← agent behavior and routing (Cursor / ad-hoc)
   OR
   engine/weekly-session-spec.md           ← for focused weekly sessions
   OR
   engine/program-pipeline-orchestrator.md ← for direct pipeline execution
4. Relevant function spec                  ← the spec for the work at hand
5. engine/quality-gate-spec.md             ← applied automatically before any output delivery
```

`.cursorrules` handles steps 1–3 automatically in Cursor.

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
pip install rich icalendar
```

### 4. Point Archivist at this repo

Archivist indexes all specs via YAML frontmatter `resource_type: spec` across both `engine/` and `functions/`.

### 5. Create your first program directory and memory file

```bash
mkdir -p runs/[PROGRAM_SLUG] data/[PROGRAM_SLUG]/materials
cp memory/session-memory-template.md memory/[PROGRAM_SLUG]-memory.md
```

Edit the memory file Standing Context section with basic program information.

---

## Using This Repo in Cursor

### Setup

1. Open this repo in Cursor
2. `.cursorrules` is at repo root — Cursor loads it automatically
3. Drop your input into the composer, or say "weekly session" to trigger the full session workflow

### What happens at session start

1. Loads `config/constitution.md`
2. Reads all `memory/*.md` files for episodic context
3. Scans `runs/*/latest.json` for current program state
4. Tails `logs/provenance.jsonl` for recent activity
5. Waits for input or produces a brief orientation

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

### Engine (`/engine/`)

| File | Role |
|---|---|
| `program-pipeline-orchestrator.md` | Pipeline entry point and routing |
| `session-init-spec.md` | Cursor agent initialization and classification |
| `weekly-session-spec.md` | Weekly focused work session |
| `quality-gate-spec.md` | Output validation before every delivery |
| `spec-creation-spec.md` | How to build new specs and skills |

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

### `calendar_exporter.py`
```bash
python scripts/calendar_exporter.py --run runs/[program]/latest.json
python scripts/calendar_exporter.py --run runs/[program]/latest.json --output events.ics
```
Import `.ics`: Google Calendar → Other calendars → Import. Outlook → File → Import/Export.

### `provenance_log.py`
```bash
python scripts/provenance_log.py write --spec "[spec]" --output "[path]" \
  --output-type [type] --program [slug] --purpose "[why]" \
  --reusability [template|reference|instance|artifact]

python scripts/provenance_log.py query --program fedramp_high
python scripts/provenance_log.py summary
python scripts/provenance_log.py tail --n 10
```

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

Memory files give the agent context across sessions. Without them every session starts cold. With them the agent notices patterns, tracks decisions, and surfaces avoidance without being asked.

Each memory file: Standing Context, Decision Log, Deferred Items, Session Entries (append-only).

```bash
cp memory/session-memory-template.md memory/[PROGRAM_SLUG]-memory.md
```

Pattern detection scans for: deferred items pushed 3+ times, flags in 3+ consecutive runs, decision queue items stagnant 14+ days. Surfaces at session open as agenda items — observations, not accusations.

After 20+ sessions: summarize older entries into a historical context paragraph, keep the most recent 10 in full. Never delete Decision Log or Deferred Items tables.

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

**`calendar_exporter.py` fallback warning**
`pip install icalendar`

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
- **Quality gates before delivery.** No output reaches the principal without passing constitutional alignment, structural completeness, format, and tone checks.
- **Reuse over regeneration.** Check the provenance log before producing new work.
- **Search before interrupting.** Missing files get found, not escalated.
- **Patterns get named.** Drift, avoidance, and accumulating risk surface at session open.
- **One-way doors require the principal.** No exceptions.
- **Portability over optimization.** Everything works in the most constrained environment: a free LLM and a terminal with Python.
