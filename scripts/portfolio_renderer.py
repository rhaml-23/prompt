#!/usr/bin/env python3
# portfolio_renderer.py
# Purpose: Generate ui/portfolio.html from data/portfolio/latest.json using the
#          62443 gold-standard light-theme design system.
#
# Args:  --data [path]    (default: data/portfolio/latest.json)
#        --output [path]  (default: ui/portfolio.html)
#        --public [path]  (default: public/)  — used to build live links
#
# Governed by: config/constitution.md + functions/program-dashboard-spec.md
# Quality gate: IV.1 no fabrication, IV.2 protect downstream, IV.4 surface uncertainty
#
# Dependencies: Standard library only.
# Repo path: scripts/portfolio_renderer.py

"""Portfolio briefing page renderer — 62443 light-theme design system."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path


# ---------------------------------------------------------------------------
# HTML escaping
# ---------------------------------------------------------------------------

def e(s: object) -> str:
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# Core CSS (same design system as program_dashboard_renderer)
# ---------------------------------------------------------------------------

CSS = """\
    :root {
      --bg: #f1f5f9; --surface: #ffffff; --surface-2: #f8fafc;
      --border: #e2e8f0; --text: #0f172a; --text-muted: #64748b;
      --text-light: #94a3b8; --primary: #0891b2; --primary-light: #cffafe;
      --critical: #dc2626; --critical-light: #fee2e2;
      --high: #ea580c; --high-light: #ffedd5;
      --medium: #ca8a04; --medium-light: #fef9c3;
      --low: #16a34a; --low-light: #dcfce7;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
      --radius: 10px; --radius-sm: 6px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter',
           system-ui, sans-serif; background: var(--bg); color: var(--text);
           font-size: 14px; line-height: 1.5; min-height: 100vh; }
    a { color: inherit; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .header { background: #0c1a2e; color: #fff; padding: 0 32px;
              display: flex; align-items: center; justify-content: space-between;
              height: 64px; position: sticky; top: 0; z-index: 100;
              box-shadow: 0 2px 8px rgba(0,0,0,0.4); }
    .header-left { display: flex; align-items: center; gap: 16px; }
    .header-logo { width: 38px; height: 38px;
                   background: linear-gradient(135deg, #0891b2, #0e7490);
                   border-radius: 8px; display: flex; align-items: center;
                   justify-content: center; font-size: 13px; font-weight: 800;
                   color: #fff; flex-shrink: 0; }
    .header-title { font-size: 15px; font-weight: 700; color: #f1f5f9; }
    .header-subtitle { font-size: 11px; color: #64748b; margin-top: 1px; }
    .header-right { display: flex; align-items: center; gap: 20px; }
    .run-meta { text-align: right; }
    .run-meta .label { font-size: 10px; color: #475569; text-transform: uppercase; }
    .run-meta .value { font-size: 12px; color: #cbd5e1; font-weight: 500; }
    .main { padding: 28px 32px; max-width: 1440px; margin: 0 auto; }
    .stats-row { display: grid; grid-template-columns: repeat(6,1fr); gap: 14px;
                 margin-bottom: 24px; }
    @media (max-width:1200px) { .stats-row { grid-template-columns: repeat(3,1fr); } }
    @media (max-width:700px)  { .stats-row { grid-template-columns: repeat(2,1fr); } }
    .stat-card { background: var(--surface); border: 1px solid var(--border);
                 border-radius: var(--radius); padding: 18px 20px;
                 box-shadow: var(--shadow-sm); }
    .stat-label { font-size: 10px; font-weight: 700; text-transform: uppercase;
                  letter-spacing: 0.6px; color: var(--text-muted); margin-bottom: 8px; }
    .stat-value { font-size: 34px; font-weight: 800; line-height: 1; margin-bottom: 4px; }
    .stat-sub { font-size: 11px; color: var(--text-muted); }
    .stat-card.critical .stat-value { color: var(--critical); }
    .stat-card.warning  .stat-value { color: var(--high); }
    .stat-card.info     .stat-value { color: var(--primary); }
    .stat-card.neutral  .stat-value { color: var(--text); }
    .stat-card.ok       .stat-value { color: var(--low); }
    .stat-bar { height: 3px; border-radius: 2px; margin-top: 10px;
                background: var(--border); overflow: hidden; }
    .stat-bar-fill { height: 100%; border-radius: 2px; }
    .section-label { font-size: 11px; font-weight: 700; text-transform: uppercase;
                     letter-spacing: 0.8px; color: var(--text-muted);
                     margin: 24px 0 12px; display: flex; align-items: center; gap: 10px; }
    .section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }
    .program-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px,1fr));
                    gap: 16px; margin-bottom: 24px; }
    .program-card { background: var(--surface); border: 1px solid var(--border);
                    border-radius: var(--radius); box-shadow: var(--shadow-sm);
                    overflow: hidden; display: flex; flex-direction: column; }
    .program-card-header { padding: 14px 18px; background: #0c1a2e; color: #fff;
                           display: flex; align-items: center; gap: 10px; }
    .prog-logo { width: 32px; height: 32px; border-radius: 6px;
                 background: linear-gradient(135deg, #0891b2, #0e7490);
                 display: flex; align-items: center; justify-content: center;
                 font-size: 11px; font-weight: 800; color: #fff; flex-shrink: 0; }
    .prog-name { font-size: 13px; font-weight: 700; color: #f1f5f9; }
    .prog-slug { font-size: 10px; color: #64748b; margin-top: 1px; font-family: monospace; }
    .health-pill { margin-left: auto; font-size: 10px; font-weight: 700; padding: 3px 9px;
                   border-radius: 12px; text-transform: uppercase; letter-spacing: 0.4px; }
    .health-pill.yellow { background: #78350f; color: #fde68a; }
    .health-pill.red    { background: #7f1d1d; color: #fecaca; }
    .health-pill.green  { background: #14532d; color: #bbf7d0; }
    .health-pill.unknown{ background: #1e293b; color: #94a3b8; }
    .program-card-body { padding: 14px 18px; flex: 1; }
    .prog-status { font-size: 12px; color: var(--text); line-height: 1.5; margin-bottom: 12px; }
    .prog-kpi-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
    .prog-kpi { font-size: 11px; padding: 3px 8px; border-radius: 8px;
                font-weight: 600; }
    .prog-kpi.critical { background: var(--critical-light); color: var(--critical); }
    .prog-kpi.warn     { background: var(--high-light); color: var(--high); }
    .prog-kpi.info     { background: var(--primary-light); color: var(--primary); }
    .prog-kpi.neutral  { background: var(--surface-2); color: var(--text-muted);
                          border: 1px solid var(--border); }
    .prog-frameworks { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 12px; }
    .fw-tag { font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 8px;
              text-transform: uppercase; letter-spacing: 0.3px;
              background: var(--primary-light); color: #0e7490; }
    .prog-links { display: flex; gap: 8px; flex-wrap: wrap; padding-top: 10px;
                  border-top: 1px solid var(--border); }
    .prog-link { font-size: 11px; font-weight: 600; padding: 4px 10px;
                 border-radius: 8px; background: #0c1a2e; color: #93c5fd;
                 display: inline-flex; align-items: center; gap: 4px; }
    .prog-link:hover { background: #1e3a5f; }
    .prog-link.auditor { background: #1e293b; color: #a5f3fc; }
    .prog-link.auditor:hover { background: #0f2a3f; }
    .prog-link.unavailable { background: var(--surface-2); color: var(--text-light);
                              border: 1px solid var(--border); cursor: default; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
               margin-bottom: 20px; }
    @media (max-width:900px) { .grid-2 { grid-template-columns: 1fr; } }
    .card { background: var(--surface); border: 1px solid var(--border);
            border-radius: var(--radius); box-shadow: var(--shadow-sm); overflow: hidden; }
    .card-header { padding: 13px 20px; border-bottom: 1px solid var(--border);
                   display: flex; align-items: center; justify-content: space-between;
                   background: var(--surface-2); }
    .card-title { font-size: 12px; font-weight: 700; color: var(--text);
                  text-transform: uppercase; letter-spacing: 0.4px; }
    .card-badge { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 10px;
                  background: var(--primary-light); color: var(--primary); }
    .card-badge.warn { background: var(--critical-light); color: var(--critical); }
    .card-body { padding: 20px; }
    .signal-item { padding: 10px 14px; border-radius: var(--radius-sm);
                   border: 1px solid var(--border); background: var(--surface-2);
                   margin-bottom: 8px; }
    .signal-item:last-child { margin-bottom: 0; }
    .signal-label { font-size: 11px; font-weight: 700; color: var(--text);
                    margin-bottom: 3px; display: flex; align-items: center; gap: 6px; }
    .signal-label .badge { font-size: 9px; font-weight: 700; padding: 1px 5px;
                           border-radius: 6px; }
    .signal-label .badge.warn { background: var(--high-light); color: var(--high); }
    .signal-label .badge.info { background: var(--primary-light); color: var(--primary); }
    .signal-note { font-size: 11px; color: var(--text-muted); line-height: 1.5; }
    .action-item { padding: 12px 16px; border-radius: var(--radius-sm);
                   border: 1px solid; margin-bottom: 8px; }
    .action-item.high { background: var(--critical-light); border-color: #fca5a5; }
    .action-item.medium { background: var(--medium-light); border-color: #fde047; }
    .action-item.low { background: var(--low-light); border-color: #86efac; }
    .action-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
    .action-prog { font-size: 10px; font-weight: 700; font-family: monospace;
                   color: var(--text-muted); background: var(--surface);
                   padding: 1px 6px; border-radius: 4px; border: 1px solid var(--border); }
    .action-urgency { font-size: 10px; font-weight: 700; text-transform: uppercase;
                      letter-spacing: 0.3px; }
    .action-urgency.high   { color: var(--critical); }
    .action-urgency.medium { color: var(--medium); }
    .action-urgency.low    { color: var(--low); }
    .action-text { font-size: 12px; line-height: 1.5; }
    .action-rationale { font-size: 11px; color: var(--text-muted); margin-top: 4px;
                        line-height: 1.4; }
    .stale-notice { background: #fef9c3; border: 1px solid #fde047; border-left: 4px solid #ca8a04;
                    border-radius: var(--radius); padding: 12px 20px; margin-bottom: 20px;
                    font-size: 12px; color: #78350f; }
    footer { text-align: center; font-size: 11px; color: var(--text-light);
             padding: 20px 32px 32px; }
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _health_pill(health: str) -> str:
    labels = {"yellow": "Yellow", "red": "Red", "green": "Green", "unknown": "Unknown"}
    cls = health.lower() if health.lower() in labels else "unknown"
    lbl = labels.get(cls, health.title())
    return f'<span class="health-pill {cls}">{lbl}</span>'


def _fw_tags(frameworks: list) -> str:
    tags = ""
    for fw in frameworks[:3]:
        if isinstance(fw, dict):
            fw = fw.get("name", str(fw))
        short = str(fw)[:30]
        tags += f'<span class="fw-tag">{e(short)}</span>'
    return f'<div class="prog-frameworks">{tags}</div>' if tags else ""


def _prog_logo(slug: str) -> str:
    words = slug.replace("-", " ").split()
    initials = "".join(w[0] for w in words)[:3].upper()
    return f'<div class="prog-logo">{e(initials)}</div>'


def _lookup_program_name(slug: str, runs_dir: Path) -> str:
    """Try to get program_name from runs/[slug]/latest.json."""
    path = runs_dir / slug / "latest.json"
    if path.exists():
        try:
            with path.open(encoding="utf-8") as f:
                run = json.load(f)
            return (run.get("program_name")
                    or (run.get("run_manifest") or {}).get("program_name")
                    or slug)
        except Exception:
            pass
    return slug


def _dashboard_url(slug: str, public_dir: Path) -> str | None:
    # Return path relative to public/ (the GitLab Pages root)
    p = public_dir / slug / "index.html"
    if p.exists():
        return f"{slug}/index.html"
    p2 = Path("runs") / slug / "dashboard.html"
    if p2.exists():
        return f"runs/{slug}/dashboard.html"
    return None


def _auditor_url(slug: str, public_dir: Path, today: str) -> str | None:
    # Auditor views now live directly in public/auditor/ — return path relative to public/
    auditor_dir = public_dir / "auditor"
    for f in sorted(auditor_dir.glob(f"{slug}-auditor-*.html"), reverse=True):
        return f"auditor/{f.name}"
    return None


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def render_header(portfolio: dict, today: str) -> str:
    ph = portfolio.get("portfolio_health") or {}
    gen_at = portfolio.get("generated_at") or today
    total = ph.get("total_programs") or len(portfolio.get("programs") or [])
    green = ph.get("green") or 0
    yellow = ph.get("yellow") or 0
    red = ph.get("red") or 0
    health = ("red" if red > 0 else "yellow" if yellow > 0 else "green")
    health_labels = {"red": "Red", "yellow": "Yellow", "green": "Green"}
    health_label = health_labels[health]
    health_colors = {
        "red": ("background: #7f1d1d; color: #fecaca;"),
        "yellow": ("background: #78350f; color: #fde68a;"),
        "green": ("background: #14532d; color: #bbf7d0;"),
    }
    style = health_colors[health]
    return f"""<header class="header">
  <div class="header-left">
    <div class="header-logo">P</div>
    <div>
      <div class="header-title">Compliance Program Portfolio</div>
      <div class="header-subtitle">{total} active programs &nbsp;·&nbsp; {green} green &nbsp;·&nbsp; {yellow} yellow &nbsp;·&nbsp; {red} red</div>
    </div>
  </div>
  <div class="header-right">
    <div style="display:flex;align-items:center;gap:6px;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;{style}">
      <div style="width:7px;height:7px;border-radius:50%;background:currentColor;animation:pulse 2s infinite;"></div>
      {health_label}
    </div>
    <div class="run-meta">
      <div class="label">Portfolio updated</div>
      <div class="value">{e(gen_at)}</div>
    </div>
  </div>
</header>
<style>@keyframes pulse {{ 0%, 100% {{ opacity:1; }} 50% {{ opacity:0.35; }} }}</style>"""


def render_kpi_strip(portfolio: dict) -> str:
    ph = portfolio.get("portfolio_health") or {}
    total = int(ph.get("total_programs") or 0)
    red = int(ph.get("red") or 0)
    yellow = int(ph.get("yellow") or 0)
    green = int(ph.get("green") or 0)
    decisions = int(ph.get("total_open_decisions") or 0)
    blockers = int(ph.get("total_blockers") or 0)
    escalations = int(ph.get("total_escalations") or 0)

    return f"""<div class="stats-row">
  <div class="stat-card ok">
    <div class="stat-label">Green Programs</div>
    <div class="stat-value">{green}</div>
    <div class="stat-sub">of {total} total</div>
    <div class="stat-bar"><div class="stat-bar-fill" style="width:{int(green/max(total,1)*100)}%;background:var(--low)"></div></div>
  </div>
  <div class="stat-card{'  warning' if yellow > 0 else ''}">
    <div class="stat-label">Yellow Programs</div>
    <div class="stat-value">{yellow}</div>
    <div class="stat-sub">Active / in-flight</div>
    <div class="stat-bar"><div class="stat-bar-fill" style="width:{int(yellow/max(total,1)*100)}%;background:var(--high)"></div></div>
  </div>
  <div class="stat-card{'  critical' if red > 0 else ''}">
    <div class="stat-label">Red Programs</div>
    <div class="stat-value">{red}</div>
    <div class="stat-sub">Require escalation</div>
    <div class="stat-bar"><div class="stat-bar-fill" style="width:{int(red/max(total,1)*100)}%;background:var(--critical)"></div></div>
  </div>
  <div class="stat-card info">
    <div class="stat-label">Open Decisions</div>
    <div class="stat-value">{decisions}</div>
    <div class="stat-sub">Across all programs</div>
    <div class="stat-bar"><div class="stat-bar-fill" style="width:60%;background:var(--primary)"></div></div>
  </div>
  <div class="stat-card{'  warning' if blockers > 0 else ' neutral'}">
    <div class="stat-label">Blockers</div>
    <div class="stat-value">{blockers}</div>
    <div class="stat-sub">Active certification blockers</div>
    <div class="stat-bar"><div class="stat-bar-fill" style="width:{min(100, blockers*15)}%;background:var(--high)"></div></div>
  </div>
  <div class="stat-card{'  critical' if escalations > 0 else ' neutral'}">
    <div class="stat-label">Escalations</div>
    <div class="stat-value">{escalations}</div>
    <div class="stat-sub">Need immediate action</div>
    <div class="stat-bar"><div class="stat-bar-fill" style="width:{min(100, escalations*30)}%;background:var(--critical)"></div></div>
  </div>
</div>"""


def render_program_cards(portfolio: dict, public_dir: Path) -> str:
    programs = portfolio.get("programs") or []
    today = date.today().isoformat()
    cards = ""
    for prog in programs:
        slug = prog.get("program_slug") or prog.get("slug") or ""
        name = (prog.get("program_name")
                or prog.get("display_name")
                or _lookup_program_name(slug, Path("runs"))
                or slug)
        health = (prog.get("health") or "unknown").lower()
        status = e(prog.get("one_line_status") or "")
        phase = e(prog.get("phase") or "")
        frameworks = prog.get("frameworks") or []
        if not frameworks and prog.get("framework"):
            frameworks = [prog.get("framework")]
        fws = _fw_tags(frameworks)
        decisions = int(prog.get("open_decision_count")
                        or len(prog.get("decision_queue") or [])
                        or 0)
        blockers = int(prog.get("blocker_count")
                       or len(prog.get("blockers") or [])
                       or 0)
        escalations = int(prog.get("escalation_count")
                          or len(prog.get("escalations") or [])
                          or 0)
        owner_gaps = int(prog.get("owner_gap_count") or 0)
        vendors = prog.get("vendors") or []
        last_run = e(prog.get("last_run_date") or prog.get("last_run") or "")

        logo = _prog_logo(slug)
        pill = _health_pill(health)

        # KPI chips
        kpis = ""
        if escalations > 0:
            kpis += f'<span class="prog-kpi critical">{escalations} escalation{"s" if escalations != 1 else ""}</span>'
        if blockers > 0:
            kpis += f'<span class="prog-kpi warn">{blockers} blocker{"s" if blockers != 1 else ""}</span>'
        if decisions > 0:
            kpis += f'<span class="prog-kpi info">{decisions} decision{"s" if decisions != 1 else ""}</span>'
        if owner_gaps > 0:
            kpis += f'<span class="prog-kpi neutral">{owner_gaps} owner gap{"s" if owner_gaps != 1 else ""}</span>'
        if phase:
            kpis += f'<span class="prog-kpi neutral">{phase}</span>'
        kpi_row = f'<div class="prog-kpi-row">{kpis}</div>' if kpis else ""

        # Vendor
        vendor_html = ""
        for v in vendors[:1]:
            if isinstance(v, dict):
                vname = e(v.get("name") or "")
                vscore = v.get("score")
                vtrend = e(v.get("trend") or "")
                if vname or vscore:
                    score_txt = f" {vscore}/5 · {vtrend}" if vscore else ""
                    vendor_html = f'<div style="font-size:11px;color:var(--text-muted);margin-bottom:10px;">Vendor: <strong style="color:var(--text)">{vname}</strong>{score_txt}</div>'

        # Links
        dash_url = _dashboard_url(slug, public_dir)
        aud_url = _auditor_url(slug, public_dir, today)

        if dash_url:
            dash_link = f'<a class="prog-link" href="{e(dash_url)}">📊 Program Dashboard</a>'
        else:
            dash_link = '<span class="prog-link unavailable">Dashboard not generated</span>'

        if aud_url:
            aud_link = f'<a class="prog-link auditor" href="{e(aud_url)}">🔍 Auditor View</a>'
        else:
            aud_link = '<span class="prog-link unavailable auditor" style="color:var(--text-light)">Auditor view not generated</span>'

        cards += f"""<div class="program-card">
  <div class="program-card-header">
    {logo}
    <div>
      <div class="prog-name">{e(name)}</div>
      <div class="prog-slug">{e(slug)}</div>
    </div>
    {pill}
  </div>
  <div class="program-card-body">
    {"<div class='prog-status'>" + status + "</div>" if status else ""}
    {kpi_row}
    {fws}
    {vendor_html}
    {"<div style='font-size:11px;color:var(--text-muted);margin-bottom:10px;'>Last run: " + last_run + "</div>" if last_run else ""}
    <div class="prog-links">{dash_link}{aud_link}</div>
  </div>
</div>"""

    return f"""<div class="section-label">Active Programs</div>
<div class="program-grid">{cards}</div>"""


def render_signals(portfolio: dict) -> str:
    cs = portfolio.get("cross_program_signals") or {}
    sections = []

    # Deadline clustering
    clustering = cs.get("deadline_clustering") or []
    if clustering:
        rows = ""
        for cluster in clustering:
            date_range = e(cluster.get("date_range") or "")
            progs = cluster.get("programs") or []
            note = e(cluster.get("note") or "")
            prog_badges = " ".join(
                f'<code style="font-size:10px;padding:1px 5px;background:var(--surface);border:1px solid var(--border);border-radius:4px;">{e(p)}</code>'
                for p in progs
            )
            rows += f"""<div class="signal-item">
  <div class="signal-label">
    <strong>{date_range}</strong> &nbsp; {prog_badges}
    <span class="badge warn">{len(progs)} program{"s" if len(progs)!=1 else ""}</span>
  </div>
  <div class="signal-note">{note}</div>
</div>"""
        sections.append(("Deadline Clustering", rows, f"{len(clustering)} clusters"))

    # Resource contention
    contention = cs.get("resource_contention") or []
    if contention:
        rows = ""
        for c in contention:
            resource = e(c.get("resource") or "")
            progs = c.get("programs") or []
            note = e(c.get("note") or "")
            prog_badges = " ".join(
                f'<code style="font-size:10px;padding:1px 5px;background:var(--surface);border:1px solid var(--border);border-radius:4px;">{e(p)}</code>'
                for p in progs
            )
            rows += f"""<div class="signal-item">
  <div class="signal-label">
    <strong>{resource}</strong> &nbsp; {prog_badges}
    <span class="badge info">{len(progs)} programs</span>
  </div>
  <div class="signal-note">{note}</div>
</div>"""
        sections.append(("Resource Contention", rows, f"{len(contention)} resources"))

    # Intel overlap
    intel = cs.get("intel_overlap") or []
    if intel:
        rows = ""
        for it in intel[:5]:
            title = e(it.get("title") or it.get("signal") or str(it)[:60])
            progs = it.get("programs") or []
            prog_badges = " ".join(
                f'<code style="font-size:10px;padding:1px 5px;background:var(--surface);border:1px solid var(--border);border-radius:4px;">{e(p)}</code>'
                for p in progs
            )
            rows += f"""<div class="signal-item">
  <div class="signal-label">{title} &nbsp; {prog_badges}</div>
</div>"""
        sections.append(("Intel Overlap", rows, f"{len(intel)} signals"))

    if not sections:
        return ""

    html = '<div class="section-label">Cross-Program Signals</div><div class="grid-2">'
    for title, content, badge in sections[:2]:
        html += f"""<div class="card">
  <div class="card-header">
    <div class="card-title">{title}</div>
    <div class="card-badge">{badge}</div>
  </div>
  <div class="card-body">{content}</div>
</div>"""
    html += "</div>"

    if len(sections) > 2:
        html += '<div class="grid-2" style="margin-top:-12px;">'
        for title, content, badge in sections[2:4]:
            html += f"""<div class="card">
  <div class="card-header">
    <div class="card-title">{title}</div>
    <div class="card-badge">{badge}</div>
  </div>
  <div class="card-body">{content}</div>
</div>"""
        html += "</div>"

    return html


def render_suggested_actions(portfolio: dict) -> str:
    actions = portfolio.get("suggested_actions") or []
    if not actions:
        return ""
    rows = ""
    for act in actions:
        if not isinstance(act, dict):
            continue
        prog = e(act.get("program") or "")
        urgency = str(act.get("urgency") or "medium").lower()
        text = e(act.get("action") or "")
        rationale = e(act.get("rationale") or "")
        rows += f"""<div class="action-item {urgency}">
  <div class="action-header">
    {"<span class='action-prog'>" + prog + "</span>" if prog else ""}
    <span class="action-urgency {urgency}">{urgency.upper()}</span>
  </div>
  <div class="action-text">{text}</div>
  {"<div class='action-rationale'>" + rationale + "</div>" if rationale else ""}
</div>"""

    return f"""<div class="section-label">Suggested Actions</div>
<div class="card" style="margin-bottom:24px;">
  <div class="card-header">
    <div class="card-title">Recommended Next Steps</div>
    <div class="card-badge{"" if all(str((a.get("urgency") or "")).lower() != "high" for a in actions) else " warn"}">{len(actions)} actions</div>
  </div>
  <div class="card-body">{rows}</div>
</div>"""


def render_staleness_notice(portfolio: dict) -> str:
    gen_at = portfolio.get("generated_at") or ""
    if not gen_at:
        return ""
    try:
        from datetime import date as ddate
        gen = ddate.fromisoformat(gen_at.split("T")[0])
        days = (ddate.today() - gen).days
        if days > 14:
            return (f'<div class="stale-notice"><strong>Note:</strong> This portfolio briefing '
                    f'was generated from data last updated {e(gen_at)} ({days} days ago). '
                    f'Some program data may not reflect current state.</div>')
    except (ValueError, TypeError):
        pass
    return ""


# ---------------------------------------------------------------------------
# Top-level assembly
# ---------------------------------------------------------------------------

def generate_html(portfolio: dict, public_dir: Path) -> str:
    today = date.today().isoformat()
    gen_at = portfolio.get("generated_at") or today

    header = render_header(portfolio, today)
    stale = render_staleness_notice(portfolio)
    kpi = render_kpi_strip(portfolio)
    program_cards = render_program_cards(portfolio, public_dir)
    signals = render_signals(portfolio)
    actions = render_suggested_actions(portfolio)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Compliance Program Portfolio — {today}</title>
<style>{CSS}</style>
</head>
<body>

{header}

<div class="main">

{stale}
{kpi}
{program_cards}
{signals}
{actions}

</div>
<footer>Generated by program-pipeline · {today} · Governed by config/constitution.md</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate portfolio briefing HTML from data/portfolio/latest.json."
    )
    parser.add_argument("--data", "--portfolio", dest="data",
                        default="data/portfolio/latest.json",
                        help="Path to portfolio latest.json")
    parser.add_argument("--output", default="ui/portfolio.html",
                        help="Output HTML path (default: ui/portfolio.html)")
    parser.add_argument("--public", default="public",
                        help="Path to the public/ directory for link resolution")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"ERROR: Portfolio data not found at {data_path}", file=sys.stderr)
        sys.exit(1)

    with data_path.open(encoding="utf-8") as f:
        portfolio = json.load(f)

    public_dir = Path(args.public)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    html = generate_html(portfolio, public_dir)
    out_path.write_text(html, encoding="utf-8")

    ph = portfolio.get("portfolio_health") or {}
    print(f"Portfolio briefing written to: {out_path}")
    print(f"  Programs: {ph.get('total_programs', '?')}  "
          f"Green: {ph.get('green', 0)}  "
          f"Yellow: {ph.get('yellow', 0)}  "
          f"Red: {ph.get('red', 0)}")


if __name__ == "__main__":
    main()
