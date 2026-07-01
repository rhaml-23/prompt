---
resource_type: spec
version: "1.0"
domain: agent-infrastructure
triggers:
  - session_start
  - checkpoint_write
  - pipeline_interrupt
  - resume_request
inputs:
  - prior_checkpoint_json
  - draft_run_json
  - assessment_state_json
outputs:
  - updated_checkpoint
  - resume_directives
  - abandoned_checkpoint_notice
governed_by: config/constitution.md
standalone: true
invoked_by:
  - engine/session-init-spec.md
  - engine/program-pipeline-orchestrator.md
invokes:
  - engine/quality-gate-spec.md
---

# Crash Resilience Spec
**Version:** 1.0  
**Purpose:** Define durable checkpoints so agents can resume interrupted work without re-deriving context from chat history. Checkpoints are internal continuity artifacts — they do not replace `engine/quality-gate-spec.md` before external delivery.  
**Governed by:** `config/constitution.md`

---

## Relationship to Existing Patterns

| Pattern | Location | Role |
|---------|----------|------|
| Control assessment batches | `data/[program]/assessments/[RUN_ID]-state.json` | Specialized schema; see `functions/control-assessment-spec.md` and `RESUME: yes` |
| Generic work checkpoints | `data/[program]/checkpoints/[checkpoint_id].json` | Any long-running work not covered by assessment state |
| Pipeline draft envelope | `runs/[program]/draft-run.json` | Partial pipeline output before final quality gate |
| Finished pipeline runs | `runs/[program]/latest.json`, `[date]-run.json` | Complete runs only — never treat `draft-run.json` as authoritative for dashboards |

---

## Generic Work Checkpoint

**Path:** `data/[program]/checkpoints/[checkpoint_id].json`

`checkpoint_id` is URL-safe: lowercase letters, digits, hyphens (e.g. `intel-scan-2026-04-02`, `pipeline-wip`).

**Schema:** `config/schemas/work-checkpoint.schema.json`

### Required lifecycle

1. **Create** — When starting critical multi-step work, write an initial checkpoint with `status: in_progress`.
2. **Update** — After each bounded sub-step that is validated (same spirit as control-assessment batches), overwrite the file with `updated_at` and revised `current_step`, `context`, and `next_actions`.
3. **Complete** — Set `status: complete`, set `updated_at`, optionally log provenance for final outputs.
4. **Abandon** — Set `status: abandoned` if the lead program manager cancels; do not delete immediately (audit trail). Lead program manager may delete later.

### Quality gate

Checkpoint content may include draft text or partial JSON intended for the lead program manager. Before any **external** delivery or irreversible action, outputs still pass `engine/quality-gate-spec.md`. A checkpoint is not a waiver of the gate.

### Atomic writes

Prefer `runtime/ide.py` (`atomic_write_json`, `FileStateBackend.write_work_checkpoint`) so a crash mid-write does not leave a torn JSON file.

---

## Pipeline Draft Run

**Path:** `runs/[program]/draft-run.json`

Use during `engine/program-pipeline-orchestrator.md` execution when a full run cannot finish in one session.

- Content follows `config/schemas/run-output.schema.json` where possible; partial sections may omit keys not yet produced.
- **Required:** `run_manifest.run_notes` must begin with `WIP — checkpoint` (lead program manager-visible signal that the run is incomplete).
- **Do not** copy `draft-run.json` to `latest.json` until Phase 6 (Quality Gate) passes and the orchestrator declares the run complete.
- Renderers and dashboards (`scripts/dashboard.py`, `scripts/briefing_renderer.py`, etc.) read `latest.json` — they must not treat `draft-run.json` as the current program state unless the lead program manager explicitly opens it.

On successful completion: write final JSON via normal run write paths (`[date]-run.json` + `latest.json`), then **remove** `draft-run.json` if present.

---

## Session Resume (for agents)

When resuming:

1. Load the checkpoint or `draft-run.json` and the spec named in `invoked_spec` / pipeline manifest.
2. Confirm `spec_version` still matches the repo file (if drift, escalate to lead program manager before continuing).
3. Continue from `next_actions` / next pipeline phase — do not redo completed steps recorded in `context`.

---

## Provenance

Log significant checkpoint events when practical:

```bash
python scripts/provenance_log.py write \
  --spec "engine/crash-resilience-spec.md" \
  --output "data/[program]/checkpoints/[checkpoint_id].json" \
  --program "[program]" \
  --purpose "Checkpoint updated — resume after interrupt" \
  --reusability instance
```

---

## Companion Specs

- `functions/control-assessment-spec.md` — assessment-specific state files
- `engine/session-init-spec.md` — recovery scan at session open (including `memory/*-wip.md` detection)
- `engine/program-pipeline-orchestrator.md` — when to write `draft-run.json`
- `engine/quality-gate-spec.md` — validation before delivery
- `runtime/metrics.py` (`FleetMetricsCollector.check_cascade`) — enforces the cascade-depth circuit breaker declared in `agents/coordinator.md`; depth > 3 is halted and logged to the decision audit trail
