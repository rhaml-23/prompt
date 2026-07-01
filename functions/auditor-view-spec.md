---
resource_type: spec
version: "1.0"
domain: compliance
triggers:
  - auditor_view
  - generate_auditor_dashboard
  - audit_prep
inputs:
  - program_run_json
  - provenance_log
  - control_coverage_matrix
  - risk_register
  - evidence_calendar
outputs:
  - auditor_dashboard_html
governed_by: config/constitution.md
standalone: true
entry_point: true
depends_on:
  - runs/[PROGRAM]/latest.json
  - logs/provenance.jsonl
---

# Auditor View Spec
**Version:** 1.0
**Purpose:** Generate a read-only, per-program compliance posture dashboard suitable for auditor review. Demonstrates continuous monitoring activity, control coverage status, risk register posture, and evidence collection cadence. Does not expose internal program management detail, decision queues, or session-level operational data.
**Governed by:** `/config/constitution.md`
**Output:** Static HTML file — generated on demand via this spec OR automatically on every CI push to main via `scripts/build_pages.py` (Step 1, sub-step 4).
**Audience:** Third-party auditors, compliance reviewers, oversight stakeholders.
**Maintainer:** `[your name/handle]`

---

## Constitutional Guidance

- **Say the true thing** (Article IV.1) — the auditor view must reflect actual program state. Coverage percentages, POA&M counts, and monitoring cadence are reported as-is from source data. Nothing is inflated or softened for presentation.
- **Surface uncertainty** (Article IV.4) — if source data is incomplete or stale, the dashboard notes it rather than presenting a confident-looking output from weak signal.
- **Good enough calibration** (Article IV.14) — this is an operational artifact, not a polished report. Accurate and clear is the goal. Formatting serves legibility, not aesthetics.

---

## What This View Shows

Four sections, nothing more:

1. **Monitoring Activity Log** — provenance entries for this program, full detail: timestamp, spec invoked, artifact type produced, quality gate result. Proves continuous monitoring is occurring on cadence.

2. **Control Coverage Status** — percentage of controls evidenced, implemented without evidence, and gap by control family. Derived from the most recent coverage matrix in the run JSON or coverage spec output.

3. **Risk Register Summary** — open item count by severity, closure rate, POA&M item status. Does not expose individual risk descriptions beyond severity classification unless explicitly included in the run JSON's auditor-visible fields.

4. **Evidence Collection Calendar** — upcoming and completed collection windows with status. Shows that evidence collection is planned and tracked.

## What This View Does Not Show

- Internal decision queues or deferred items
- Session-level operational notes or memory content
- Draft communications or staged outputs
- Watch list items or internal health classifications
- Any field tagged `internal_only: true` in the run JSON
- Lead program manager name or organizational chart detail beyond program ownership fields

---

## Parameters

```
PROGRAM:          [program slug]
REPORT_DATE:      [YYYY-MM-DD — defaults to today]
LOOKBACK_DAYS:    [90 | 180 | 365 — provenance window, default 90]
OUTPUT_PATH:      [ui/[program]-auditor-[date].html — default]
```

---

## Processing Instructions

### Pass 1 — Data Load

Load the following sources for the named program:

- `runs/[PROGRAM]/latest.json` — current program state
- `logs/provenance.jsonl` — filter to entries where `program == PROGRAM` and `timestamp >= REPORT_DATE - LOOKBACK_DAYS`
- Control coverage matrix — from `latest.json` field `control_coverage` or `data/[PROGRAM]/` if stored separately
- Risk register — from `latest.json` field `risk_register`
- Evidence calendar — from `latest.json` field `evidence_calendar`

If any source is missing, note it in the dashboard as `[DATA UNAVAILABLE — source: path]` rather than omitting the section or rendering blank.

If `latest.json` is stale (past `next_run_recommendation`), add a staleness notice at the top of the dashboard:

```
⚠ Note: This view was generated from program data last updated [date].
A pipeline run is overdue as of [next_run_recommendation date].
Data may not reflect current program state.
```

Narrate:
```
[AUDITOR VIEW] Loading program: [PROGRAM]
[AUDITOR VIEW] Provenance entries in window: [n]
[AUDITOR VIEW] Coverage matrix: [loaded | unavailable]
[AUDITOR VIEW] Risk register: [loaded | unavailable]
[AUDITOR VIEW] Evidence calendar: [loaded | unavailable]
[AUDITOR VIEW] Generating dashboard...
```

---

### Pass 2 — Monitoring Activity Log Assembly

From the filtered provenance entries, produce a chronological activity log.

Each entry includes:
- **Timestamp** — ISO 8601, date and time
- **Spec invoked** — the spec or script that produced the output (from `spec` field)
- **Artifact type** — from `output_type` field
- **Output reference** — filename only, not full path (strip directory prefix)
- **Quality gate** — Pass / Fail / Not applicable

Sort descending — most recent first.

Compute:
- Total runs in window
- Average days between runs
- Most recent run date
- Longest gap between runs (flag if > 14 days for standard programs, > 7 days for high-intensity programs)

Summary line:
```
[n] monitoring activities recorded over [n] days
Average cadence: every [n] days | Last run: [date] | Longest gap: [n] days
```

---

### Pass 3 — Control Coverage Assembly

From the coverage matrix, compute:

- Total controls in scope
- Evidenced (status: ✓) — count and percentage
- Implemented, no evidence (status: ~) — count and percentage
- Gap (status: ✗) — count and percentage
- Not applicable (status: N/A) — count

Overall coverage percentage = (Evidenced + Implemented no evidence) / (Total - N/A)

By control family or trust service category — one row per family:

| Family | Total | Evidenced | Impl/No Evidence | Gap | Coverage % |
|---|---|---|---|---|---|

Flag any family where coverage is below 50% — these are the families most likely to draw auditor attention.

If coverage matrix is unavailable, render the section as:
```
Control coverage data not available for this reporting period.
Source: runs/[PROGRAM]/latest.json → control_coverage
Next pipeline run will populate this section.
```

---

### Pass 4 — Risk Register Summary Assembly

From the risk register, compute:

- Total open items
- By severity: Critical / High / Medium / Low counts
- Closure rate: items closed in the lookback window / (items open at start of window + new items)
- POA&M items: total / with target date / overdue (target date past with status still Open)

Do not list individual risk descriptions unless the run JSON marks them `auditor_visible: true`. Surface counts and classifications only.

Summary table:

| Severity | Open | Closed (period) | Overdue POA&M |
|---|---|---|---|
| Critical | n | n | n |
| High | n | n | n |
| Medium | n | n | n |
| Low | n | n | n |

Closure rate line:
```
Closure rate (last [n] days): [x]% — [n] items closed of [n] items active in period
```

If risk register is unavailable, render the section analogously to coverage above.

---

### Pass 5 — Evidence Calendar Assembly

From the evidence calendar, produce two lists:

**Upcoming collection windows (next 90 days):**

| Window | Controls / Items | Due Date | Status |
|---|---|---|---|
| Q2 Access Review | AC-2, AC-3, AC-6 | 2026-04-15 | Scheduled |

**Completed collection windows (lookback period):**

| Window | Controls / Items | Completed Date | Status |
|---|---|---|---|
| Q1 Access Review | AC-2, AC-3, AC-6 | 2026-01-20 | Complete |

Status values: Scheduled / In Progress / Complete / Overdue / Skipped

Compute:
- Completion rate for the lookback period: Complete / (Complete + Overdue + Skipped)
- Count of upcoming windows in the next 30 days

---

### Pass 6 — HTML Assembly

Invoke `scripts/auditor_view_renderer.py` with the assembled data to produce the static HTML file.

Output path: `ui/[PROGRAM]-auditor-[REPORT_DATE].html`

The renderer produces a clean, print-friendly HTML document. No JavaScript. No external dependencies. Renders correctly when printed to PDF from any browser.

Log provenance on completion:
```bash
python scripts/provenance_log.py write \
  --spec "functions/auditor-view-spec.md" \
  --output "ui/[PROGRAM]-auditor-[DATE].html" \
  --output-type auditor_dashboard \
  --program "[PROGRAM]" \
  --purpose "Auditor view generated for [context]" \
  --reusability artifact \
  --quality-gate pass
```

---

## Trigger

```
PROGRAM: [slug]
REPORT_DATE: [YYYY-MM-DD]
LOOKBACK_DAYS: [90]

BEGIN AUDITOR VIEW
```

---

## Suggested Repo Path
`/functions/auditor-view-spec.md`

## Companion Specs
- Governed by: `/config/constitution.md`
- Reads: `/runs/[PROGRAM]/latest.json`, `/logs/provenance.jsonl`
- Writes: `/ui/[PROGRAM]-auditor-[DATE].html`
- Rendered by: `scripts/auditor_view_renderer.py`
- Auto-invoked by: `scripts/build_pages.py` on every push to main (Step 1, sub-step 4)
