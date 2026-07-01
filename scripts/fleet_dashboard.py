"""
Fleet observability dashboard (Phase 3f).

Produces an HTML dashboard showing fleet-wide operational status:
- Agent health (active/idle/error, load, trust level)
- Program performance (health trajectory, finding velocity, evidence coverage)
- Cost tracking (token usage by agent, program, framework)
- Decision audit trail (routing decisions, escalations, authority boundary checks)

Usage:
    python scripts/fleet_dashboard.py --output ui/fleet-dashboard.html --open
    python scripts/fleet_dashboard.py --metrics data/fleet-metrics.json
    python scripts/fleet_dashboard.py --summary
"""

import argparse
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any


def load_metrics(metrics_path: Path | None = None) -> dict[str, Any]:
    """Load fleet metrics from JSON file or return empty structure."""
    if metrics_path and metrics_path.exists():
        return json.loads(metrics_path.read_text(encoding="utf-8"))
    return {
        "agent_metrics": {},
        "program_metrics": {},
        "cost_records": [],
        "decision_trail": [],
    }


def render_dashboard(
    metrics: dict[str, Any],
    portfolio: dict[str, Any] | None = None,
    predictions: dict[str, Any] | None = None,
) -> str:
    """Render fleet dashboard as HTML."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    agents = metrics.get("agent_metrics", {})
    programs = metrics.get("program_metrics", {})
    decisions = metrics.get("decision_trail", [])
    cost = metrics.get("cost_records", [])

    agent_rows = ""
    for agent_id, m in agents.items():
        status_class = "healthy" if m.get("error_rate_24h", 0) < 0.05 else "warning" if m.get("error_rate_24h", 0) < 0.1 else "critical"
        agent_rows += f"""
            <tr class="{status_class}">
                <td>{agent_id}</td>
                <td>{m.get('agent_type', '')}</td>
                <td>{m.get('status', 'unknown')}</td>
                <td>L{m.get('trust_level', 1)}</td>
                <td>{m.get('actions_24h', 0)}</td>
                <td>{m.get('error_rate_24h', 0):.1%}</td>
                <td>{m.get('tokens_used_24h', 0):,}</td>
                <td>{m.get('last_active', 'never')[:19]}</td>
            </tr>"""

    program_rows = ""
    for prog, m in programs.items():
        health = m.get("health", "unknown")
        health_icon = {"green": "&#x1F7E2;", "yellow": "&#x1F7E1;", "red": "&#x1F534;", "unknown": "&#x26AA;"}.get(health, "&#x26AA;")
        velocity = m.get("finding_velocity", 0)
        vel_class = "improving" if velocity < 0 else "stable" if velocity == 0 else "declining"
        program_rows += f"""
            <tr>
                <td>{health_icon} {prog}</td>
                <td>{health}</td>
                <td>{m.get('runs_30d', 0)}</td>
                <td>{m.get('open_findings', 0)}</td>
                <td class="{vel_class}">{velocity:+.2f}/run</td>
                <td>{m.get('evidence_coverage_pct', 0):.0f}%</td>
                <td>{m.get('tokens_used_30d', 0):,}</td>
                <td>{m.get('last_run_date', '')}</td>
            </tr>"""

    decision_rows = ""
    for d in (decisions or [])[-20:]:
        decision_rows += f"""
            <tr>
                <td>{d.get('timestamp', '')[:19]}</td>
                <td>{d.get('decision_type', '')}</td>
                <td>{d.get('agent_id', '')}</td>
                <td>{json.dumps(d.get('details', {}), default=str)[:100]}</td>
            </tr>"""

    token_by_agent: dict[str, int] = {}
    for r in cost:
        aid = r.get("agent_id", "unknown")
        token_by_agent[aid] = token_by_agent.get(aid, 0) + r.get("tokens_input", 0) + r.get("tokens_output", 0)
    cost_rows = ""
    for aid, tokens in sorted(token_by_agent.items(), key=lambda x: -x[1]):
        cost_rows += f"<tr><td>{aid}</td><td>{tokens:,}</td></tr>"

    prediction_section = ""
    if predictions:
        pred_programs = predictions.get("programs", {})
        pred_rows = ""
        for prog, p in pred_programs.items():
            traj = p.get("health_trajectory", {}).get("trajectory", "unknown")
            readiness = p.get("audit_readiness", {}).get("readiness", "unknown")
            score = p.get("audit_readiness", {}).get("score", 0)
            timeline = p.get("certification_timeline", {}).get("estimated_ready_date", "unknown")
            pred_rows += f"""
                <tr>
                    <td>{prog}</td>
                    <td>{traj}</td>
                    <td>{score}/100</td>
                    <td>{readiness}</td>
                    <td>{timeline}</td>
                </tr>"""
        prediction_section = f"""
        <div class="section">
            <h2>Predictive Health</h2>
            <table>
                <tr><th>Program</th><th>Trajectory</th><th>Readiness Score</th><th>Status</th><th>Est. Ready</th></tr>
                {pred_rows}
            </table>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Compliance Fleet Dashboard — {now}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
           background: #0f1419; color: #e1e8ed; padding: 20px; }}
    h1 {{ color: #1da1f2; margin-bottom: 8px; font-size: 24px; }}
    h2 {{ color: #8899a6; margin: 20px 0 10px; font-size: 18px; border-bottom: 1px solid #38444d; padding-bottom: 6px; }}
    .subtitle {{ color: #8899a6; font-size: 14px; margin-bottom: 20px; }}
    .section {{ background: #1c2732; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }}
    .card {{ background: #253341; border-radius: 8px; padding: 16px; text-align: center; }}
    .card .number {{ font-size: 32px; font-weight: bold; color: #1da1f2; }}
    .card .label {{ font-size: 12px; color: #8899a6; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th {{ background: #253341; color: #8899a6; text-align: left; padding: 8px 12px; font-weight: 600; }}
    td {{ padding: 8px 12px; border-bottom: 1px solid #38444d; }}
    tr:hover {{ background: #253341; }}
    .healthy {{ }}
    .warning td {{ color: #ffad1f; }}
    .critical td {{ color: #e0245e; }}
    .improving {{ color: #17bf63; }}
    .stable {{ color: #8899a6; }}
    .declining {{ color: #e0245e; }}
</style>
</head>
<body>
<h1>Compliance Fleet Dashboard</h1>
<p class="subtitle">Generated {now}</p>

<div class="summary">
    <div class="card"><div class="number">{len(agents)}</div><div class="label">Agents</div></div>
    <div class="card"><div class="number">{len(programs)}</div><div class="label">Programs</div></div>
    <div class="card"><div class="number">{sum(m.get('actions_24h', 0) for m in agents.values())}</div><div class="label">Actions (24h)</div></div>
    <div class="card"><div class="number">{sum(token_by_agent.values()):,}</div><div class="label">Tokens Used</div></div>
    <div class="card"><div class="number">{len(decisions)}</div><div class="label">Decisions Logged</div></div>
</div>

<div class="section">
    <h2>Agent Health</h2>
    <table>
        <tr><th>Agent</th><th>Type</th><th>Status</th><th>Trust</th><th>Actions (24h)</th><th>Error Rate</th><th>Tokens (24h)</th><th>Last Active</th></tr>
        {agent_rows if agent_rows else '<tr><td colspan="8" style="text-align:center; color:#8899a6;">No agent metrics collected yet</td></tr>'}
    </table>
</div>

<div class="section">
    <h2>Program Performance</h2>
    <table>
        <tr><th>Program</th><th>Health</th><th>Runs (30d)</th><th>Open Findings</th><th>Finding Velocity</th><th>Evidence Coverage</th><th>Tokens (30d)</th><th>Last Run</th></tr>
        {program_rows if program_rows else '<tr><td colspan="8" style="text-align:center; color:#8899a6;">No program metrics available</td></tr>'}
    </table>
</div>

{prediction_section}

<div class="section">
    <h2>Cost by Agent</h2>
    <table>
        <tr><th>Agent</th><th>Total Tokens</th></tr>
        {cost_rows if cost_rows else '<tr><td colspan="2" style="text-align:center; color:#8899a6;">No cost data</td></tr>'}
    </table>
</div>

<div class="section">
    <h2>Decision Audit Trail (Last 20)</h2>
    <table>
        <tr><th>Timestamp</th><th>Type</th><th>Agent</th><th>Details</th></tr>
        {decision_rows if decision_rows else '<tr><td colspan="4" style="text-align:center; color:#8899a6;">No decisions logged</td></tr>'}
    </table>
</div>

</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Fleet observability dashboard")
    parser.add_argument("--metrics", help="Path to fleet metrics JSON")
    parser.add_argument("--portfolio", help="Path to portfolio state JSON")
    parser.add_argument("--predictions", help="Path to predictions JSON")
    parser.add_argument("--output", default="ui/fleet-dashboard.html", help="Output HTML path")
    parser.add_argument("--open", action="store_true", help="Open in browser after rendering")
    parser.add_argument("--summary", action="store_true", help="Print text summary instead of HTML")
    args = parser.parse_args()

    metrics = load_metrics(Path(args.metrics) if args.metrics else None)

    portfolio = None
    if args.portfolio and Path(args.portfolio).exists():
        portfolio = json.loads(Path(args.portfolio).read_text(encoding="utf-8"))

    predictions = None
    if args.predictions and Path(args.predictions).exists():
        predictions = json.loads(Path(args.predictions).read_text(encoding="utf-8"))

    if args.summary:
        agents = metrics.get("agent_metrics", {})
        programs = metrics.get("program_metrics", {})
        print(f"Fleet Summary — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"  Agents:    {len(agents)}")
        print(f"  Programs:  {len(programs)}")
        print(f"  Decisions: {len(metrics.get('decision_trail', []))}")
        return 0

    html = render_dashboard(metrics, portfolio, predictions)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {output_path}")

    if args.open:
        webbrowser.open(str(output_path.resolve()))

    return 0


if __name__ == "__main__":
    sys.exit(main())
