# Scripts — Tools Registry

**Path:** `scripts/`

This file is the authoritative registry of all reusable scripts in the pipeline. Agents must scan this file before writing new code — if a script already covers the needed function, invoke it rather than reimplementing it. Each entry includes purpose, inputs, outputs, and the exact CLI signature.

---

## Renderers

Produce human-readable HTML or markdown from run/data JSON. Standard library only — no install required unless noted.

---

### `auditor_view_renderer.py`

Generates a read-only, per-program auditor compliance posture dashboard as static HTML. Shows control coverage, risk posture, evidence collection cadence, and continuous monitoring signals. Suitable for sharing with third-party auditors.

| | |
|---|---|
| **Input** | `runs/[PROGRAM]/latest.json` (auto-resolved from repo root) |
| **Output** | `ui/[program]-auditor-[date].html` |
| **Dependencies** | Standard library only |

```
python scripts/auditor_view_renderer.py --program fedramp-high
python scripts/auditor_view_renderer.py --program fedramp-high --lookback 180
python scripts/auditor_view_renderer.py --program fedramp-high --output ui/custom.html
python scripts/auditor_view_renderer.py --program fedramp-high --open
```

---

### `briefing_renderer.py`

Reads a program pipeline run JSON and produces a clean markdown daily briefing digest. Terminal preview available if `rich` is installed.

| | |
|---|---|
| **Input** | `runs/[PROGRAM]/latest.json` |
| **Output** | Markdown file or stdout |
| **Dependencies** | Standard library; `rich` optional for terminal preview |

```
python scripts/briefing_renderer.py --run runs/[PROGRAM]/latest.json
python scripts/briefing_renderer.py --run runs/[PROGRAM]/latest.json --output briefing.md
python scripts/briefing_renderer.py --run runs/[PROGRAM]/latest.json --stdout
```

---

### `dashboard.py`

Reads all `runs/*/latest.json` files and generates a single static HTML dashboard showing multi-program health, decision queues, and flags.

| | |
|---|---|
| **Input** | `runs/*/latest.json` (auto-glob) |
| **Output** | `ui/dashboard.html` |
| **Dependencies** | Standard library only |

```
python scripts/dashboard.py
python scripts/dashboard.py --runs path/to/runs/ --output dashboard.html
python scripts/dashboard.py --open
```

---

### `draft_formatter.py`

Reads a program pipeline run JSON and writes one markdown file per draft communication into an output directory. Files are organized for review, light editing, and sending.

| | |
|---|---|
| **Input** | `runs/[PROGRAM]/latest.json` |
| **Output** | `drafts/[PROGRAM]_[DATE]/` (one `.md` per draft) |
| **Dependencies** | Standard library only |

```
python scripts/draft_formatter.py --run runs/[PROGRAM]/latest.json
python scripts/draft_formatter.py --run runs/[PROGRAM]/latest.json --output drafts/custom/
python scripts/draft_formatter.py --run runs/[PROGRAM]/latest.json --list
```

---

### `fleet_dashboard.py`

Produces a fleet-wide HTML observability dashboard. Covers agent health (status, trust level, error rate, token usage), program performance (health trajectory, finding velocity, evidence coverage), cost tracking, and decision audit trail.

| | |
|---|---|
| **Input** | `data/fleet-metrics.json` (optional; renders empty state if absent) |
| **Output** | `ui/fleet-dashboard.html` |
| **Dependencies** | Standard library only |

```
python scripts/fleet_dashboard.py --output ui/fleet-dashboard.html
python scripts/fleet_dashboard.py --metrics data/fleet-metrics.json --open
python scripts/fleet_dashboard.py --summary
```

---

### `portfolio_renderer.py`

Reads the portfolio state JSON and renders a cross-program HTML dashboard showing health, decisions, blockers, escalations, and cross-program signals.

| | |
|---|---|
| **Input** | `data/portfolio/latest.json` |
| **Output** | `ui/portfolio.html` |
| **Dependencies** | Standard library only |

```
python scripts/portfolio_renderer.py
python scripts/portfolio_renderer.py --portfolio data/portfolio/latest.json
python scripts/portfolio_renderer.py --output ui/portfolio.html --open
```

---

## Validators

CI and integrity checks. All exit non-zero on failure. Run as part of the CI `validate` stage and before modifying protected files.

---

### `integrity_check.py`

Validates that protected system files (`constitution.md`, `program-pipeline-orchestrator.md`, `quality-gate-spec.md`) retain all required headings. Run before and after any LLM-assisted edits to those files. Prints a restoration notice if a heading is missing.

| | |
|---|---|
| **Input** | `config/constitution.md`, `engine/program-pipeline-orchestrator.md`, `engine/quality-gate-spec.md` |
| **Output** | stdout (pass/fail + restoration instructions) |
| **Exit** | `0` = pass, `1` = missing headings |

```
python scripts/integrity_check.py
python scripts/integrity_check.py --file constitution.md
python scripts/integrity_check.py --fix-prompt
```

---

### `spec_coverage.py`

Validates cross-reference integrity across the spec system: every spec in `engine/` and `functions/` has a routing table entry in `session-init-spec.md`, every routing target exists on disk, every orchestrator invocation target exists, and every agent is referenced by at least one routing entry.

| | |
|---|---|
| **Input** | `engine/session-init-spec.md`, `engine/program-pipeline-orchestrator.md`, `agents/`, `functions/` |
| **Output** | stdout (pass/fail) |
| **Exit** | `0` = pass, `1` = broken references |

```
python scripts/spec_coverage.py
python scripts/spec_coverage.py --repo /path/to/compliance
```

---

### `validate_frontmatter.py`

Validates YAML frontmatter in all spec files against the canonical schema. Checks all `.md` files in `engine/`, `functions/`, and `agents/`.

| | |
|---|---|
| **Input** | `config/spec-frontmatter-schema.yaml`, `engine/*.md`, `functions/*.md`, `agents/*.md` |
| **Output** | stdout (pass/fail with field-level errors) |
| **Exit** | `0` = pass, `1` = validation errors |

```
python scripts/validate_frontmatter.py
python scripts/validate_frontmatter.py --strict
```

---

### `validate_schema_drift.py`

Detects misalignment between what renderer scripts read from JSON and what the canonical schemas declare. ERRORs (renderer reads undeclared key) cause a non-zero exit; WARNINGs (schema declares a key no renderer reads) are informational only.

Checks covered:
- `scripts/dashboard.py` → `config/schemas/run-output.schema.json`
- `scripts/auditor_view_renderer.py` → `config/schemas/run-output.schema.json`
- `scripts/portfolio_renderer.py` → `config/schemas/portfolio-state.schema.json`

| | |
|---|---|
| **Input** | `config/schemas/*.schema.json`, renderer scripts |
| **Output** | stdout (ERROR / WARNING lines) |
| **Exit** | `0` = no errors, `1` = schema drift detected |

```
python scripts/validate_schema_drift.py
python scripts/validate_schema_drift.py --repo /path/to/compliance
python scripts/validate_schema_drift.py --renderers scripts/dashboard.py
```

---

## Analysis

Derive structured insights or calendar data from historical run output. Outputs are JSON or `.ics` files consumed by other scripts or agents.

---

### `calendar_exporter.py`

Transforms the `calendar_events` array from a pipeline run JSON into a portable RFC 5545 `.ics` file and/or a human-readable markdown event list. Companion to `functions/calendar-output-spec.md`.

| | |
|---|---|
| **Input** | `runs/[PROGRAM]/latest.json` |
| **Output** | `.ics` file (default) or markdown event list |
| **Dependencies** | Standard library only |

```
python scripts/calendar_exporter.py --run runs/[PROGRAM]/latest.json
python scripts/calendar_exporter.py --run runs/[PROGRAM]/latest.json --output events.ics
python scripts/calendar_exporter.py --run runs/[PROGRAM]/latest.json --markdown
python scripts/calendar_exporter.py --run runs/[PROGRAM]/latest.json --preview
```

---

### `predictive_health.py`

Analyzes historical run data across programs to produce: certification timeline prediction based on current velocity and open gap count, resource contention forecasting, audit readiness scoring with trajectory, and finding velocity trends.

| | |
|---|---|
| **Input** | `runs/` directory (historical `*-run.json` files) or `data/portfolio/latest.json` |
| **Output** | `data/predictions.json` |
| **Dependencies** | Standard library only |

```
python scripts/predictive_health.py --runs-dir runs/ --output data/predictions.json
python scripts/predictive_health.py --program fedramp-high --detail
python scripts/predictive_health.py --portfolio data/portfolio/latest.json
```

---

## Logging

Append-only audit infrastructure. Agents must write to the provenance log via this script — never write to `logs/provenance.jsonl` directly.

---

### `provenance_log.py`

Append-only JSONL log of all deliverables produced by the pipeline. Tracks what was created, when, why, for which program, and whether the artifact is reusable. Supports querying by program, spec, reusability class, date, or output type.

| | |
|---|---|
| **Input** | CLI arguments |
| **Output** | `logs/provenance.jsonl` (append) or stdout (query/summary/tail) |
| **Dependencies** | Standard library only |
| **Constraint** | Never write to `logs/provenance.jsonl` directly — always use this script |

```
# Append an entry
python scripts/provenance_log.py write \
    --spec "program-intake-spec.md" \
    --output "runs/fedramp/2025-03-01-run.json" \
    --program "fedramp_high" \
    --purpose "Initial onboarding" \
    --reusability template

# Query
python scripts/provenance_log.py query --program fedramp_high
python scripts/provenance_log.py query --reusability template
python scripts/provenance_log.py query --since 2025-01-01
python scripts/provenance_log.py query --output-type report

# Summary and tail
python scripts/provenance_log.py summary
python scripts/provenance_log.py tail --n 10
```
