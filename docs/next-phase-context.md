# Context Handoff — Multi-Program Coordinator Architecture
**Date:** 2026-03-03
**Prepared by:** Alex Langston
**Purpose:** Pick up planning for the next phase — a coordinator/team lead layer above the existing per-program IC agents.
**Prior session summary:** See transcript 2026-03-03-15-34-32-system-expansion-skills-tools-integrity.txt for full system history.

---

## What Was Built (Current State)

An agentic compliance operating system structured as an application with the following directories:

```
config/       ← constitution.md (v1.5), tool-requirements.md
engine/       ← orchestrator, session-init, weekly-session, quality-gate, spec-creation
functions/    ← intake, monitoring, comms, vendor, control-coverage, risk-register,
                calendar, entropy, redteam, external-intel (new this session)
skills/       ← empty — behavioral skills live in constitution Article IV (IV.11–IV.16)
scripts/      ← briefing_renderer, draft_formatter, calendar_exporter, dashboard,
                provenance_log, integrity_check
memory/       ← session-memory-template + one file per active program
runs/         ← versioned JSON state per program
data/         ← program materials drop zone + agent-generated reference data
ui/           ← dashboard.html (generated)
logs/         ← provenance.jsonl
drafts/       ← staged communications
docs/         ← obsidian-vault-guide, agent-evaluation-test-suite,
                agent-governance-overview (new this session)
```

**Key capabilities validated in production:**
- Full build mode: `new_program_full_build` — drops all materials, agent builds skeleton → coverage matrix → risk register → evidence calendar → draft comms autonomously with narration
- Validated across 2–3 active programs at Red Hat
- Thursday surprise drop of 5 certs / 2 programs → full ISMS + dashboard + calendar + project plan by Friday afternoon (~5 hours total including 3 hrs spec building)
- External intel monitoring spec built this session — scans CISA KEV, NVD, MITRE ATT&CK, AI Incident DB, MIT/Stanford HAI, regulatory updates, threat intel feeds, arXiv

**Constitution highlights:**
- v1.5 — 16 behavioral mandates (Article IV.1–IV.16)
- IV.16 added this session: External Signal Synthesis skill
- Protected files: constitution.md, orchestrator, quality-gate — validated by integrity_check.py
- One-way door rule: no external action without lead program manager sign-off, no exceptions

---

## What Was Discussed (Not Built) — The Next Phase

### The Problem Being Solved

Alex is now running the IC-level agent across 2–3 programs simultaneously. The bottleneck is cross-program coordination — triaging which program needs attention, understanding dependencies between programs, maintaining visibility across all of them without running each one manually.

The analogy used: IC agent = individual contributor who knows one program deeply. What's needed = team lead capability that knows all programs shallowly, understands relationships between them, and surfaces what needs the lead program manager's attention without requiring the lead program manager to drive every lookup.

### Scaling Analogy Established

**Vertical scaling** = deepening what a single agent knows and can do. Alex has been doing this for months. Near the useful ceiling — spreading one agent across 6 programs in one session degrades output specificity.

**Horizontal scaling** = multiple agents with bounded context, coordinated by something above them. That's the next phase.

### Three Paths Discussed

**Path 1 — Portfolio aggregator, no autonomy**
- Coordinator reads all program states, produces cross-program briefing and priority ordering
- Reporting layer only — no initiation authority
- Lowest risk, immediately useful, builds on existing infrastructure
- Weekly session becomes a portfolio session

**Path 2 — Coordinator with routing authority**
- Coordinator decides which IC agent to activate, routes inputs, aggregates outputs
- Can initiate monitoring runs without explicit trigger from lead program manager
- Lead program manager reviews outputs, not initiation decisions
- Requires clear authority boundaries on what coordinator can start vs. must ask about

**Path 3 — Full team lead model**
- Coordinator manages IC agents, maintains portfolio backlog, surfaces only decisions and exceptions
- Requires solving the memory architecture problem first
- Most complex seam design — coordinator to IC seam + coordinator to lead program manager seam

### Recommendation Given (Not Yet Accepted/Rejected)

Start with Path 1. Validate that the cross-program view is useful before investing in routing authority. The risk of jumping to Path 2 or 3 is building coordination infrastructure for a signal problem not yet fully understood.

**Key infrastructure piece identified:** A portfolio state file — lightweight JSON or markdown that each program's pipeline writes to on every run. Aggregates signals up from each program without carrying full program detail. This is the data structure that makes Path 1 possible and that Path 2/3 build on top of.

### Open Questions Not Yet Answered

Alex was asked two questions that were not answered before the session ended:

1. **Where is the bottleneck?** Is the pain point manually triaging across programs, or is it lack of visibility into what's happening across all of them simultaneously? (This shapes whether Path 1 or Path 2 is the right starting point.)

2. **What does coordination look like in practice?** What does a week look like when you're managing 3+ programs — what decisions are you making that feel like they should be automated or aggregated?

These should be the first questions answered in the next session before any building begins.

---

## Architecture Constraints to Carry Forward

- **LLM-agnostic.** Any coordinator spec must run on Claude, GPT, Gemini, or local models. No vendor lock-in.
- **Constitution governs everything.** The coordinator is subject to the same constitutional authority boundaries as IC agents. One-way doors still require lead program manager sign-off.
- **Seam design is the hard problem.** Two seam types in the coordinator model: coordinator → IC agents, coordinator → lead program manager. Failure modes multiply. Explicit authority boundaries required before building.
- **Portfolio state file must be additive.** It should be written by existing pipeline runs without requiring changes to IC-level specs. The IC layer should not need to know a coordinator exists.
- **Memory architecture changes at scale.** Each IC agent needs bounded context (its own program). The coordinator needs a shallow cross-program view. These cannot be the same files at different granularities — they need to be designed as separate data structures from the start.

---

## Files Produced This Session (Not Previously Existing)

| File | Location | Purpose |
|---|---|---|
| `external-intel-spec.md` | `functions/` | External source monitoring and risk delta generation |
| `agent-governance-overview.md` | `docs/` | Auditor-facing governance statement — 5 frontier ops concepts |
| `control-coverage-spec.md` | `functions/` | Control mapping and gap analysis |
| `risk-register-spec.md` | `functions/` | Risk register and POA&M starter |
| `constitution.md` v1.5 | `config/` | Added IV.12–IV.16 (5 new skills), full build wiring |
| `README.md` | `/` | Rewritten for application-style directory structure |
| `program-intake-spec.md` v1.2 | `functions/` | Added BUILD_MODE and Pass 4 autonomous build sequence |

---

## Suggested Starting Point for Next Session

Open with the two unanswered questions. Once Alex answers them, the path selection (1, 2, or 3) becomes obvious and design can begin. The likely first artifact is the portfolio state schema — what fields each program pipeline writes to the portfolio file on every run. That's the foundation everything else builds on.
