---
resource_type: spec
version: "3.1"
domain: agent-initialization
triggers:
  - session_start
  - cursor_open
inputs:
  - any_unstructured_input
  - email
  - slack_thread
  - meeting_notes
  - stakeholder_request
  - scheduled_run
  - no_input
outputs:
  - routed_task
  - classified_work
  - spec_invocation
  - orientation_briefing
governed_by: config/constitution.md
entry_point: true
standalone: true
invokes:
  - engine/crash-resilience-spec.md
  - engine/program-pipeline-orchestrator.md
  - engine/portfolio-orchestrator.md
  - engine/weekly-session-spec.md
  - engine/quality-gate-spec.md
  - functions/program-intake-spec.md
  - functions/program-monitoring-spec.md
  - functions/vendor-management-spec.md
  - functions/compliance-entropy-spec.md
  - functions/compliance-redteam-spec.md
  - functions/program-comms-spec.md
  - functions/external-intel-spec.md
  - functions/control-coverage-spec.md
  - functions/risk-register-spec.md
  - functions/calendar-output-spec.md
  - functions/program-dashboard-spec.md
  - functions/product-evidence-spec.md
  - functions/post-audit-spec.md
---

# Session Initialization Spec
**Version:** 3.1
**Purpose:** Entry point for every session. Load minimally, classify input, route to the correct spec. Load only what the request requires — not the full engine.
**Governed by:** `config/constitution.md`
**Load order:** Constitution first. Directory discovery second. Everything else on demand after routing.

---

## Step 1 — Always Load

```
1. config/constitution.md          — governs everything, load fully
2. ls engine/ functions/ agents/ scripts/ config/   — live directory inventory
3. ls runs/ memory/ data/          — programs, memory, program-scoped data (including checkpoints)
```

Do not load any spec, memory file, or run JSON yet. That happens after classification.

---

## Step 1b — Recovery Scan (before classification)

After directory discovery, scan for interrupted work. Load `engine/crash-resilience-spec.md` only if this step finds candidates — otherwise skip.

**Discover (glob or search from repo root):**

- **Control assessment state** — files under `data/[program]/assessments/` named `*-state.json`. Resumable when JSON field `status` is `in_progress`.
- **Generic checkpoints** — files under `data/[program]/checkpoints/` with extension `.json`. Resumable when JSON field `status` is `in_progress`.
- **Pipeline draft run** — file `runs/[program]/draft-run.json` if present (WIP pipeline envelope per `engine/crash-resilience-spec.md`).
- **Session WIP notes** — files matching `memory/*-wip.md` if present (in-progress session narrative written before session close; indicates a prior session may have crashed before writing the final memory entry).

**If none found:** continue to Step 2 — Classify Input.

**If any found:** emit a Recovery block before classification or orientation:

```
RECOVERY — interrupted work detected

[For each artifact, one line:]
- [program] | [type: assessment_state | checkpoint | draft_run | session_wip] | last updated [updated_at or file mtime] | [checkpoint_id or RUN_ID or draft-run or wip]

Resume? Options:
  (a) Resume — load artifact(s), continue from recorded step (see engine/crash-resilience-spec.md or functions/control-assessment-spec.md)
  (b) Review — open files for lead program manager inspection before continuing
  (c) Discard — lead program manager confirms abandonment; agent sets checkpoint `status: abandoned` or deletes `draft-run.json` as appropriate

Do not silently continue destructive or one-way-door work. Wait for lead program manager direction unless they already stated resume intent in this message.
```

If the lead program manager chooses resume, load the relevant checkpoint or draft run and the governing spec (`invoked_spec` or pipeline orchestrator) before other routing.

---

## Step 2 — Classify Input

**If input is provided — classify immediately and route. No orientation.**

```
CLASSIFICATION
Input type:    [email | slack_thread | meeting_notes | stakeholder_request |
                scheduled_run | task | artifact | question | unknown]
Program:       [program slug from input | "portfolio" | "cross-program" | "unknown"]
Urgency:       [immediate | today | this_week | no_deadline]
Work pattern:  [from routing table]
Recommended action: [one sentence]
```

If the recommended action is a one-way door — external communication, irreversible change, action affecting another person's standing — state it and request confirmation before proceeding.

**If no input is provided — produce orientation then ask:**

```
SESSION ORIENTATION — [today's date]

Portfolio Health:
  [read data/portfolio/latest.json if present — one line per program with health icon]
  [if stale or missing — suggest: BEGIN PORTFOLIO RUN]

Due Today / This Week:
  [scan runs/*/latest.json next_run_recommendation and decision_queue — top items only]

Flags Requiring Resolution:
  [count of open flags across programs]

Recent Activity:
  [tail logs/provenance.jsonl — last 3 entries]

Ready. What are you working on today?
```

Keep orientation under 20 lines. Surface memory patterns if present — deferred items aging, persistent flags — as a single note at the end.

---

## Step 3 — Load on Demand

After classification, load only what the work requires:

**Program-scoped request:**
- `memory/[program]-memory.md` — hot layer, full load
- `tail -20 memory/[program]-decisions.log` — recent decisions only
- `runs/[program]/latest.json` — that program only
- The spec the routing table points to
- That spec's declared `depends_on` and `invokes` — no further

**Portfolio or cross-program request:**
- `data/portfolio/latest.json`
- `memory/*-memory.md` and `runs/*/latest.json` — all programs
- `tail -20 memory/*-decisions.log` per program — recent decisions
- `engine/portfolio-orchestrator.md`

**No program identified yet:**
- Ask one clarifying question before loading anything

If a spec referenced in the routing table is not found in the live directory inventory, search recursively before flagging it missing.

---

## Routing Table

| Work Pattern | Route To | Notes |
|---|---|---|
| New program — full build | `functions/program-intake-spec.md` | BUILD_MODE: full_build |
| New program — standard | `engine/program-pipeline-orchestrator.md` | INTENT: new_program |
| Program status check | `engine/program-pipeline-orchestrator.md` | INTENT: monitoring_run |
| Vendor issue or check-in | `engine/program-pipeline-orchestrator.md` | INTENT: vendor_review |
| Full program reassessment | `engine/program-pipeline-orchestrator.md` | INTENT: full_run |
| Cross-program portfolio briefing | `engine/portfolio-orchestrator.md` | SESSION_MODE: briefing |
| Portfolio weekly session | `engine/portfolio-orchestrator.md` | SESSION_MODE: weekly_session |
| Weekly focused session (single program) | `engine/weekly-session-spec.md` | Standard session flow |
| Intel scan / threat scan | `functions/external-intel-spec.md` | BEGIN INTEL SCAN |
| Control coverage assessment | `functions/control-coverage-spec.md` | Standalone or via full build |
| Risk register / POA&M build | `functions/risk-register-spec.md` | Standalone or via full build |
| Compliance artifact review | `functions/compliance-redteam-spec.md` | Standalone |
| Longitudinal program health | `functions/compliance-entropy-spec.md` | Requires multi-cycle data |
| Stakeholder communication | `functions/program-comms-spec.md` | Translation or original drafting |
| Status report | `functions/program-comms-spec.md` | COMMUNICATION_TYPE: status_report |
| Meeting recap | `functions/program-comms-spec.md` | COMMUNICATION_TYPE: meeting_recap |
| Resource or decision request | `functions/program-comms-spec.md` | COMMUNICATION_TYPE: resource_request |
| Program dashboard generation | `functions/program-dashboard-spec.md` | BEGIN PROGRAM DASHBOARD or /program-status |
| Auditor view | `functions/auditor-view-spec.md` | BEGIN AUDITOR VIEW |
| Management system assembly | `functions/management-system-assembler-spec.md` | BEGIN MANAGEMENT SYSTEM ASSEMBLY |
| Control assessment / fill template | `functions/control-assessment-spec.md` | BEGIN CONTROL ASSESSMENT |
| Product evidence extraction (repo scan) | `functions/product-evidence-spec.md` | BEGIN PRODUCT EVIDENCE EXTRACTION |
| Compliance document generation | `functions/compliance-doc-generator-spec.md` | BEGIN COMPLIANCE DOC GENERATION |
| Post-audit debrief / lessons learned | `functions/post-audit-spec.md` | BEGIN POST-AUDIT REVIEW |
| Post-run review | `agents/run-reviewer.md` | Auto or on demand |
| Calendar generation | `functions/calendar-output-spec.md` | Or scripts/calendar_exporter.py |
| Morning briefing | `scripts/briefing_renderer.py` | Against latest.json |
| Portfolio dashboard | `scripts/portfolio_renderer.py --open` | Reads data/portfolio/latest.json |
| Program dashboard | `scripts/dashboard.py --open` | All programs |
| Evidence lifecycle check | `agents/evidence-agent.md` | Staleness, gaps, validation |
| ISO 42001 / AIMS query | `agents/framework-iso42001.md` | AI management system framework specialist |
| Cross-framework crosswalk | `agents/framework-nist-fedramp.md` | Or appropriate framework specialist |
| Common control catalog | `agents/coordinator.md` | Portfolio-level cross-framework view |
| Predictive health analysis | `scripts/predictive_health.py` | Against runs/ and portfolio |
| Fleet dashboard | `scripts/fleet_dashboard.py --open` | Reads fleet metrics |
| Trust level report | `agents/coordinator.md` | Fleet trust state and history |
| Unknown | Ask one clarifying question | Do not guess |
| Memory housekeeping | `memory/memory-housekeeping-spec.md` | BEGIN MEMORY HOUSEKEEPING |
| Memory migration (single→three-file) | `memory/memory-migration-spec.md` | BEGIN MEMORY MIGRATION |
| Task / kanban view or update | `functions/kanban-spec.md` | Via `agents/project-manager.md` |
| Jira ticket generation or export | `agents/project-manager.md` | Jira MCP if available; CSV/JSON otherwise |

---

## Input Processing by Type

### Email or Slack Thread
Extract: sender and role, primary ask, program relevance, implied deadline, response required.
Route to `functions/program-comms-spec.md` if a draft response is needed. Flag one-way door responses for approval before generating.

### Meeting Notes
Extract: date and attendees, decisions made, actions for lead program manager, actions for others, program state changes.
Actions for lead program manager → decision queue or watch list. Actions for others → draft follow-up if needed. Program state changes → flag for next pipeline run. Do not trigger a full pipeline run from meeting notes alone unless scope-changing information is present.

### Stakeholder Request
Extract: who is asking and authority level, what is being asked, which program, time constraint, delegation potential.
Check provenance before generating new work:
```bash
python scripts/provenance_log.py query --program [program] --reusability template
```
If a reusable artifact exists, surface it. Reuse over regeneration where quality is equivalent.

### Scheduled or Automated Run
Check `next_run_recommendation` in `runs/[program]/latest.json`. Confirm intent matches. Route to `engine/program-pipeline-orchestrator.md`. Log provenance after run.

---

## Output Behavior

All outputs pass through `engine/quality-gate-spec.md` before being presented.

- Lead with the most actionable item
- State what was produced and where it was saved
- State what the lead program manager needs to do next, if anything
- Do not summarize what the lead program manager can read themselves

---

## Session Closing

When the lead program manager signals done or a work unit completes:

```
Produced this session:
  [outputs with file paths]

Provenance logged: [yes / no — log now if no]

Next session:
  [pending items or next_run_recommendation dates]
```

---

## Behavioral Constraints

- Never load a spec or memory file before classification
- Never load program memory or run JSON for programs not relevant to the request
- Never act on a one-way door without explicit lead program manager confirmation
- Never generate new work when provenance shows a reusable artifact that meets the need
- Never present outputs that have not passed the quality gate
- Never summarize what the lead program manager can read directly
- Always classify before routing
- Always use live directory discovery — never assume a file exists
- When routing target is not found via discovery, search recursively before flagging
- When uncertain about routing, ask one clarifying question
