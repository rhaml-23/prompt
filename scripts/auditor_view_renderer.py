#!/usr/bin/env python3
"""
auditor_view_renderer.py

Purpose: Generate a read-only, per-program auditor compliance posture dashboard
         as a static HTML file. Suitable for third-party auditor review.
         Demonstrates continuous monitoring, control coverage, risk posture,
         and evidence collection cadence.

Usage:
  python scripts/auditor_view_renderer.py --program fedramp-high
  python scripts/auditor_view_renderer.py --program fedramp-high --lookback 180
  python scripts/auditor_view_renderer.py --program fedramp-high --output ui/custom.html
  python scripts/auditor_view_renderer.py --program fedramp-high --open

Dependencies: None beyond Python standard library
Repo path: /scripts/auditor_view_renderer.py
Standards: PEP 8, type hints, argparse, standard library only
"""

import argparse
import json
import sys
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# ── Constants ────────────────────────────────────────────────────────────────

BLUE       = "#1F4E79"
LIGHT_BLUE = "#2E75B6"
BLACK      = "#1a1a1a"
GRAY       = "#555555"
LIGHT_GRAY = "#f5f5f5"
WHITE      = "#ffffff"
RED        = "#c0392b"
YELLOW     = "#d68910"
GREEN      = "#1e8449"
BORDER     = "#dddddd"

QG_COLOR   = {"pass": GREEN, "fail": RED, "not applicable": GRAY}
SEV_COLOR  = {"critical": RED, "high": "#e67e22", "medium": YELLOW, "low": GRAY}
CAL_COLOR  = {
    "complete":    GREEN,
    "scheduled":   LIGHT_BLUE,
    "in progress": YELLOW,
    "overdue":     RED,
    "skipped":     GRAY,
}

HIGH_INTENSITY_PROGRAMS = []  # add slugs that warrant 7-day gap threshold


# ── Helpers ──────────────────────────────────────────────────────────────────

def e(text: Any) -> str:
    """HTML-escape a value."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def pct(n: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{round(n / total * 100)}%"


def badge(text: str, color: str) -> str:
    return (f'<span style="display:inline-block;padding:2px 10px;border-radius:3px;'
            f'font-size:0.78em;font-weight:600;color:#fff;background:{color}">'
            f'{e(text)}</span>')


def section(title: str, content: str, note: str = "") -> str:
    note_html = f'<div style="font-size:0.78em;color:{GRAY};margin-bottom:12px">{e(note)}</div>' if note else ""
    return f"""
<div style="margin-bottom:36px">
  <div style="font-size:0.72em;font-weight:700;letter-spacing:0.1em;
       color:{GRAY};text-transform:uppercase;border-bottom:2px solid {LIGHT_BLUE};
       padding-bottom:6px;margin-bottom:16px">{e(title)}</div>
  {note_html}
  {content}
</div>"""


def unavailable(field: str, path: str) -> str:
    return (f'<div style="padding:16px;background:{LIGHT_GRAY};border-radius:4px;'
            f'font-size:0.85em;color:{GRAY}">'
            f'Data not available for this reporting period.<br>'
            f'<span style="font-family:monospace;font-size:0.9em">Source: {e(path)}</span><br>'
            f'Next pipeline run will populate this section.</div>')


def table(headers: list[str], rows: list[list[str]], col_widths: list[str] = None) -> str:
    border = f"1px solid {BORDER}"
    cell_style = f"padding:8px 12px;font-size:0.83em;border:{border}"
    header_style = (f"padding:8px 12px;font-size:0.78em;font-weight:700;"
                    f"background:{BLUE};color:{WHITE};border:{border};"
                    f"text-transform:uppercase;letter-spacing:0.04em")

    width_attrs = ""
    if col_widths:
        width_attrs = "".join(f'<col style="width:{w}">' for w in col_widths)

    header_row = "".join(f"<th style='{header_style}'>{e(h)}</th>" for h in headers)
    body_rows = ""
    for i, row in enumerate(rows):
        bg = WHITE if i % 2 == 0 else "#f9fbfd"
        cells = "".join(f"<td style='{cell_style};background:{bg}'>{c}</td>" for c in row)
        body_rows += f"<tr>{cells}</tr>"

    return (f'<table style="width:100%;border-collapse:collapse;margin-bottom:8px">'
            f'{"<colgroup>" + width_attrs + "</colgroup>" if width_attrs else ""}'
            f'<thead><tr>{header_row}</tr></thead>'
            f'<tbody>{body_rows}</tbody></table>')


def stat_row(stats: list[tuple[str, str, str]]) -> str:
    """Render a row of stat boxes: [(label, value, color), ...]"""
    boxes = ""
    for label, value, color in stats:
        boxes += (f'<div style="text-align:center;padding:12px 16px;flex:1">'
                  f'<div style="font-size:1.6em;font-weight:700;color:{color}">{e(value)}</div>'
                  f'<div style="font-size:0.72em;color:{GRAY};text-transform:uppercase;'
                  f'letter-spacing:0.05em;margin-top:2px">{e(label)}</div></div>')
    return (f'<div style="display:flex;flex-wrap:wrap;background:{LIGHT_GRAY};'
            f'border-radius:4px;margin-bottom:16px">{boxes}</div>')


# ── Data Loading ─────────────────────────────────────────────────────────────

def load_run(program: str) -> dict[str, Any]:
    path = Path(f"runs/{program}/latest.json")
    if not path.exists():
        print(f"[ERROR] Run file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def load_provenance(program: str, lookback_days: int, report_date: date) -> list[dict]:
    path = Path("logs/provenance.jsonl")
    if not path.exists():
        return []
    cutoff = report_date - timedelta(days=lookback_days)
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("program") != program:
                continue
            ts = entry.get("timestamp", "")[:10]
            try:
                entry_date = date.fromisoformat(ts)
            except ValueError:
                continue
            if cutoff <= entry_date <= report_date:
                entries.append(entry)
    return sorted(entries, key=lambda x: x.get("timestamp", ""), reverse=True)


# ── Section Renderers ─────────────────────────────────────────────────────────

def render_activity_log(entries: list[dict], program: str,
                        lookback_days: int) -> str:
    if not entries:
        return section(
            "Continuous Monitoring Activity",
            unavailable("provenance entries", "logs/provenance.jsonl"),
            f"Lookback window: {lookback_days} days"
        )

    # Compute cadence stats
    dates = []
    for e_ in entries:
        ts = e_.get("timestamp", "")[:10]
        try:
            dates.append(date.fromisoformat(ts))
        except ValueError:
            pass

    total_runs = len(entries)
    last_run = max(dates).isoformat() if dates else "—"
    gap_threshold = 7 if program in HIGH_INTENSITY_PROGRAMS else 14

    gaps = []
    if len(dates) >= 2:
        sorted_dates = sorted(dates)
        gaps = [(sorted_dates[i+1] - sorted_dates[i]).days
                for i in range(len(sorted_dates)-1)]
    avg_cadence = f"every {round(sum(gaps)/len(gaps))} days" if gaps else "—"
    max_gap = max(gaps) if gaps else 0
    gap_flag = (f' <span style="color:{RED};font-size:0.85em">'
                f'⚠ Gap exceeds {gap_threshold}-day threshold</span>'
                if max_gap > gap_threshold else "")

    summary = (f'<div style="font-size:0.85em;color:{GRAY};margin-bottom:16px">'
               f'<strong>{total_runs}</strong> monitoring activities recorded '
               f'over {lookback_days} days &nbsp;·&nbsp; '
               f'Average cadence: {avg_cadence} &nbsp;·&nbsp; '
               f'Last run: {last_run} &nbsp;·&nbsp; '
               f'Longest gap: {max_gap} days{gap_flag}</div>')

    rows = []
    for entry in entries:
        ts = entry.get("timestamp", "")[:19].replace("T", " ")
        spec = Path(entry.get("spec", "—")).name
        artifact = entry.get("output_type", "—").replace("_", " ")
        output = Path(entry.get("output", "—")).name
        qg = entry.get("quality_gate", "not applicable").lower()
        qg_color = QG_COLOR.get(qg, GRAY)
        rows.append([
            e(ts),
            e(spec),
            e(artifact),
            e(output),
            badge(qg.title(), qg_color)
        ])

    log_table = table(
        ["Timestamp", "Spec Invoked", "Artifact Type", "Output", "Quality Gate"],
        rows,
        ["18%", "25%", "18%", "25%", "14%"]
    )

    return section("Continuous Monitoring Activity", summary + log_table,
                   f"Lookback window: {lookback_days} days")


def _normalize_coverage(run: dict) -> dict:
    """Return a normalised control_coverage dict regardless of source schema.

    Schema 2.0 programs store ``control_coverage.families`` with a ``family``
    key.  Schema 1.1 programs (62443) store ``control_coverage_matrix`` with a
    flat ``controls`` list and a ``coverage_summary`` object.  Both are
    normalised into the shape expected by ``render_coverage``.
    """
    cov = run.get("control_coverage", {})
    if cov:
        return cov

    # 62443-style: control_coverage_matrix --------------------------------
    ccm = run.get("control_coverage_matrix", {})
    if not ccm:
        return {}

    cs = ccm.get("coverage_summary", {})
    controls = ccm.get("controls", [])

    # Group individual controls by their ID prefix to create family rows.
    from collections import defaultdict
    groups: dict[str, dict] = defaultdict(lambda: {
        "evidenced": 0, "implemented_no_evidence": 0, "gap": 0, "not_applicable": 0,
    })
    status_map = {"✓": "evidenced", "~": "implemented_no_evidence", "✗": "gap"}
    for ctrl in controls:
        prefix = ctrl.get("control_id", "").split("-")[0] or "Other"
        key = status_map.get(ctrl.get("status", ""), "gap")
        groups[prefix][key] += 1

    families = []
    for prefix, counts in sorted(groups.items()):
        total = sum(counts.values())
        families.append({
            "name": prefix,
            "total": total,
            "evidenced": counts["evidenced"],
            "implemented_no_evidence": counts["implemented_no_evidence"],
            "gap": counts["gap"],
            "not_applicable": counts["not_applicable"],
        })

    return {
        "framework": ccm.get("framework", "IEC 62443-4-2"),
        "assessment_date": ccm.get("assessment_date", ""),
        "families": families,
        "totals": {
            "total": cs.get("total_controls", 0),
            "evidenced": cs.get("evidenced", 0),
            "implemented_no_evidence": cs.get("implemented_no_evidence", 0),
            "gap": cs.get("gap", 0),
            "not_applicable": cs.get("not_applicable", 0),
        },
    }


def render_coverage(run: dict) -> str:
    coverage_data = _normalize_coverage(run)
    if not coverage_data:
        return section(
            "Control Coverage Status",
            unavailable("control_coverage", "runs/[PROGRAM]/latest.json → control_coverage")
        )

    families = coverage_data.get("families", [])
    totals = coverage_data.get("totals", {})

    total = totals.get("total", 0)
    evidenced = totals.get("evidenced", 0)
    impl_no_evidence = totals.get("implemented_no_evidence", 0)
    gap = totals.get("gap", 0)
    na = totals.get("not_applicable", 0)
    denominator = total - na if total > na else total
    overall_pct = pct(evidenced + impl_no_evidence, denominator)

    stats = stat_row([
        ("Total Controls", str(total), BLACK),
        ("Evidenced", pct(evidenced, denominator), GREEN),
        ("Impl / No Evidence", pct(impl_no_evidence, denominator), YELLOW),
        ("Gap", pct(gap, denominator), RED),
        ("Overall Coverage", overall_pct, LIGHT_BLUE),
    ])

    rows = []
    for fam in families:
        fam_total = fam.get("total", 0)
        fam_ev = fam.get("evidenced", 0)
        fam_impl = fam.get("implemented_no_evidence", 0)
        fam_gap = fam.get("gap", 0)
        fam_na = fam.get("not_applicable", 0)
        fam_denom = fam_total - fam_na if fam_total > fam_na else fam_total
        fam_pct_val = round((fam_ev + fam_impl) / fam_denom * 100) if fam_denom else 0
        pct_color = RED if fam_pct_val < 50 else (YELLOW if fam_pct_val < 80 else GREEN)
        rows.append([
            e(fam.get("name", "—")),
            str(fam_total),
            str(fam_ev),
            str(fam_impl),
            str(fam_gap),
            f'<span style="color:{pct_color};font-weight:600">{fam_pct_val}%</span>'
        ])

    cov_table = table(
        ["Control Family", "Total", "Evidenced", "Impl/No Evidence", "Gap", "Coverage"],
        rows
    )

    note = (f"Framework: {e(coverage_data.get('framework', '—'))} &nbsp;·&nbsp; "
            f"Assessment date: {e(coverage_data.get('assessment_date', '—'))}")

    return section("Control Coverage Status", stats + cov_table, note)


def render_risk(run: dict) -> str:
    risk_data = run.get("risk_register", {})
    if not risk_data:
        return section(
            "Risk Register Summary",
            unavailable("risk_register", "runs/[PROGRAM]/latest.json → risk_register")
        )

    severities = ["critical", "high", "medium", "low"]
    open_counts = {s: risk_data.get("open", {}).get(s, 0) for s in severities}
    closed_counts = {s: risk_data.get("closed_period", {}).get(s, 0) for s in severities}
    overdue_poam = {s: risk_data.get("overdue_poam", {}).get(s, 0) for s in severities}

    total_open = sum(open_counts.values())
    total_closed = sum(closed_counts.values())
    total_active = risk_data.get("total_active_period", total_open + total_closed)
    closure_rate = pct(total_closed, total_active) if total_active else "—"
    total_overdue = sum(overdue_poam.values())

    stats = stat_row([
        ("Open Items", str(total_open), RED if total_open > 0 else GREEN),
        ("Closed (Period)", str(total_closed), GREEN),
        ("Closure Rate", closure_rate, LIGHT_BLUE),
        ("Overdue POA&M", str(total_overdue), RED if total_overdue > 0 else GREEN),
    ])

    rows = []
    for s in severities:
        sev_color = SEV_COLOR.get(s, GRAY)
        rows.append([
            badge(s.title(), sev_color),
            str(open_counts[s]),
            str(closed_counts[s]),
            str(overdue_poam[s])
        ])

    risk_table = table(
        ["Severity", "Open", "Closed (Period)", "Overdue POA&M"],
        rows,
        ["20%", "20%", "30%", "30%"]
    )

    closure_note = (f'<div style="font-size:0.82em;color:{GRAY};margin-top:8px">'
                    f'Closure rate ({risk_data.get("lookback_days", "—")} days): '
                    f'<strong>{closure_rate}</strong> — '
                    f'{total_closed} items closed of {total_active} items active in period</div>')

    return section("Risk Register Summary", stats + risk_table + closure_note)


def render_calendar(run: dict, report_date: date) -> str:
    cal_data = run.get("evidence_calendar", {})
    if not cal_data:
        return section(
            "Evidence Collection Calendar",
            unavailable("evidence_calendar", "runs/[PROGRAM]/latest.json → evidence_calendar")
        )

    upcoming = [w for w in cal_data.get("windows", [])
                if w.get("due_date", "") >= report_date.isoformat()]
    completed = [w for w in cal_data.get("windows", [])
                 if w.get("status", "").lower() in ("complete", "skipped", "overdue")
                 and w.get("due_date", "") < report_date.isoformat()]

    upcoming_rows = []
    for w in sorted(upcoming, key=lambda x: x.get("due_date", ""))[:15]:
        status = w.get("status", "scheduled").lower()
        color = CAL_COLOR.get(status, GRAY)
        upcoming_rows.append([
            e(w.get("name", "—")),
            e(w.get("controls", "—")),
            e(w.get("due_date", "—")),
            badge(status.title(), color)
        ])

    completed_rows = []
    for w in sorted(completed, key=lambda x: x.get("due_date", ""), reverse=True)[:15]:
        status = w.get("status", "complete").lower()
        color = CAL_COLOR.get(status, GRAY)
        completed_rows.append([
            e(w.get("name", "—")),
            e(w.get("controls", "—")),
            e(w.get("due_date", "—")),
            badge(status.title(), color)
        ])

    total_windows = len(cal_data.get("windows", []))
    complete_count = sum(1 for w in cal_data.get("windows", [])
                         if w.get("status", "").lower() == "complete")
    overdue_count = sum(1 for w in cal_data.get("windows", [])
                        if w.get("status", "").lower() == "overdue")
    completion_rate = pct(complete_count, total_windows) if total_windows else "—"

    stats = stat_row([
        ("Total Windows", str(total_windows), BLACK),
        ("Complete", str(complete_count), GREEN),
        ("Upcoming", str(len(upcoming_rows)), LIGHT_BLUE),
        ("Overdue", str(overdue_count), RED if overdue_count > 0 else GREEN),
        ("Completion Rate", completion_rate, LIGHT_BLUE),
    ])

    upcoming_section = ""
    if upcoming_rows:
        upcoming_section = (
            f'<div style="font-size:0.8em;font-weight:600;color:{GRAY};'
            f'margin-bottom:8px;margin-top:4px">UPCOMING (NEXT 90 DAYS)</div>'
            + table(["Window", "Controls / Items", "Due Date", "Status"], upcoming_rows)
        )

    completed_section = ""
    if completed_rows:
        completed_section = (
            f'<div style="font-size:0.8em;font-weight:600;color:{GRAY};'
            f'margin-bottom:8px;margin-top:16px">COMPLETED (REPORTING PERIOD)</div>'
            + table(["Window", "Controls / Items", "Completed Date", "Status"], completed_rows)
        )

    return section("Evidence Collection Calendar",
                   stats + upcoming_section + completed_section)


# ── Full Page ─────────────────────────────────────────────────────────────────

def render_html(program: str, run: dict, provenance: list[dict],
                report_date: date, lookback_days: int) -> str:

    display_name = run.get("program_name", program)
    framework = run.get("framework", run.get("scope", {}).get("framework", "—"))
    phase = run.get("phase", "—")
    last_run_date = run.get("run_date", "—")
    next_run_rec = run.get("next_run_recommendation", "—")

    # Staleness warning
    staleness_html = ""
    try:
        next_run = date.fromisoformat(next_run_rec)
        if report_date > next_run:
            staleness_html = (
                f'<div style="background:#fdf2f2;border-left:4px solid {RED};'
                f'padding:12px 16px;margin-bottom:24px;font-size:0.85em;color:{RED}">'
                f'⚠ This view was generated from program data last updated {e(last_run_date)}. '
                f'A pipeline run was due {e(next_run_rec)}. '
                f'Data may not reflect current program state.</div>'
            )
    except (ValueError, TypeError):
        pass

    activity_html  = render_activity_log(provenance, program, lookback_days)
    coverage_html  = render_coverage(run)
    risk_html      = render_risk(run)
    calendar_html  = render_calendar(run, report_date)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(display_name)} — Compliance Monitoring Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, Helvetica, sans-serif; background: #f5f5f5;
         color: {BLACK}; line-height: 1.5; font-size: 14px; }}
  .page {{ max-width: 960px; margin: 0 auto; padding: 32px 24px; }}
  @media print {{
    body {{ background: white; }}
    .page {{ padding: 0; max-width: 100%; }}
    .no-print {{ display: none; }}
  }}
</style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <div style="border-bottom:3px solid {BLUE};padding-bottom:16px;margin-bottom:28px">
    <div style="font-size:1.5em;font-weight:700;color:{BLUE}">{e(display_name)}</div>
    <div style="font-size:0.85em;color:{GRAY};margin-top:4px">
      Compliance Monitoring Report &nbsp;·&nbsp;
      Framework: {e(framework)} &nbsp;·&nbsp;
      Phase: {e(phase)} &nbsp;·&nbsp;
      Report date: {report_date.isoformat()} &nbsp;·&nbsp;
      Data as of: {e(last_run_date)}
    </div>
  </div>

  <!-- Staleness warning if applicable -->
  {staleness_html}

  <!-- Four sections -->
  {activity_html}
  {coverage_html}
  {risk_html}
  {calendar_html}

  <!-- Footer -->
  <div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:8px;
       font-size:0.75em;color:{GRAY};display:flex;justify-content:space-between">
    <span>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} &nbsp;·&nbsp;
          Lookback: {lookback_days} days &nbsp;·&nbsp;
          Program: {e(program)}</span>
    <span>Read-only view — for audit and compliance review purposes</span>
  </div>

</div>
</body>
</html>"""


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate read-only auditor compliance posture dashboard"
    )
    parser.add_argument("--program", required=True,
                        help="Program slug (must match runs/ directory name)")
    parser.add_argument("--lookback", type=int, default=90,
                        help="Days of provenance history to include (default: 90)")
    parser.add_argument("--report-date", default=None,
                        help="Report date YYYY-MM-DD (default: today)")
    parser.add_argument("--output", default=None,
                        help="Output HTML path (default: ui/[program]-auditor-[date].html)")
    parser.add_argument("--open", action="store_true",
                        help="Open dashboard in browser after generating")
    args = parser.parse_args()

    report_date = date.today()
    if args.report_date:
        try:
            report_date = date.fromisoformat(args.report_date)
        except ValueError:
            print(f"[ERROR] Invalid date format: {args.report_date}", file=sys.stderr)
            sys.exit(1)

    output_path = Path(args.output) if args.output else \
        Path(f"ui/{args.program}-auditor-{report_date.isoformat()}.html")

    run = load_run(args.program)
    provenance = load_provenance(args.program, args.lookback, report_date)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_html(args.program, run, provenance, report_date, args.lookback)
    output_path.write_text(html, encoding="utf-8")

    print(f"Auditor dashboard written to: {output_path}")
    print(f"  Program: {args.program}")
    print(f"  Report date: {report_date.isoformat()}")
    print(f"  Provenance entries included: {len(provenance)}")
    print(f"  Lookback window: {args.lookback} days")
    print(f"  Print to PDF from browser for submission.")

    if args.open:
        try:
            webbrowser.open(output_path.resolve().as_uri())
        except Exception as err:
            print(f"Could not open browser: {err}", file=sys.stderr)


if __name__ == "__main__":
    main()
