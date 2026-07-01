#!/usr/bin/env python3
# build_pages.py
# Purpose: Assemble the public/ directory for GitLab Pages: regenerate program
#          and fleet dashboards, copy committed HTML artifacts, and emit a
#          unified navigation hub at public/index.html.
# Style: PEP 8, type hints throughout
# Deviations: None
#
# Usage:
#   python scripts/build_pages.py
#   python scripts/build_pages.py --runs runs/ --ui ui/ --output public/
#   python scripts/build_pages.py --skip-regen   # copy committed HTML only
#
# Inputs:
#   runs/*/latest.json                 — program state (health, decisions, flags)
#   runs/*/dashboard.html              — per-program detailed dashboards (if committed)
#   ui/portfolio.html                  — portfolio briefing page
#   ui/fleet-dashboard.html            — fleet observability page
#   ui/*-auditor-*.html                — auditor view snapshots (if generated)
#   scripts/dashboard.py               — combined program dashboard generator
#   scripts/fleet_dashboard.py         — fleet observability dashboard generator
#
# Outputs:
#   public/index.html                  — navigation hub
#   public/programs.html               — regenerated combined program dashboard
#   public/fleet.html                  — regenerated fleet dashboard
#   public/portfolio.html              — copied portfolio briefing
#   public/[program]/index.html        — per-program detailed dashboards
#   public/auditor/[file].html         — auditor view snapshots
#
# Dependencies: Standard library only.
# Security: No credentials. Reads repo-local files only.
# Repo path: scripts/build_pages.py

"""GitLab Pages build script for the compliance portfolio dashboard hub."""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROGRAM_DISPLAY_NAMES: dict[str, str] = {
    "62443": "ISA/IEC 62443",
    "customer-portal-ugc-sso": "Customer Portal, UGC, SSO",
    "hds": "HDS",
    "hcc-lightspeed": "HCC Lightspeed",
    "iso42001": "ISO/IEC 42001",
}

HEALTH_COLORS: dict[str, str] = {
    "green": "#22c55e",
    "yellow": "#f59e0b",
    "red": "#ef4444",
    "unknown": "#94a3b8",
}

HEALTH_LABELS: dict[str, str] = {
    "green": "Green",
    "yellow": "Yellow",
    "red": "Red",
    "unknown": "Unknown",
}

NAV_HUB_CSS = """
:root {
  --bg: #f1f5f9;
  --surface: #ffffff;
  --surface-2: #f8fafc;
  --border: #e2e8f0;
  --text: #0f172a;
  --text-muted: #64748b;
  --text-light: #94a3b8;
  --primary: #0891b2;
  --primary-light: #cffafe;
  --radius: 10px;
  --radius-sm: 6px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow: 0 4px 6px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.04);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}
.site-header {
  margin-bottom: 2.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
}
.site-header h1 {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.25rem;
}
.site-header .meta {
  font-size: 0.8rem;
  color: var(--text-muted);
}
.section { margin-bottom: 2.5rem; }
.section-title {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-bottom: 1rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--border);
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
  box-shadow: var(--shadow-sm);
  text-decoration: none;
  color: inherit;
  display: block;
  transition: box-shadow 0.15s ease, transform 0.15s ease;
  position: relative;
  overflow: hidden;
}
.card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-1px);
}
.card-health-bar {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
}
.card-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.25rem;
  margin-top: 0.2rem;
}
.card-status {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 0.6rem;
  line-height: 1.4;
}
.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  font-size: 0.73rem;
  color: var(--text-light);
}
.health-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  background: #f1f5f9;
  color: var(--text-muted);
}
.health-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}
.utility-card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
  box-shadow: var(--shadow-sm);
  text-decoration: none;
  color: inherit;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}
.utility-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-1px);
}
.utility-icon {
  font-size: 1.3rem;
  flex-shrink: 0;
}
.utility-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text);
}
.utility-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.1rem;
}
.utility-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.75rem;
}
.empty { color: var(--text-muted); font-size: 0.85rem; font-style: italic; }
footer {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
  text-align: center;
  font-size: 0.73rem;
  color: var(--text-light);
}
"""


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def safe_get(d: dict, *keys: str, default: str = "") -> str:
    """Traverse nested dict keys, returning default on any miss."""
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default)  # type: ignore[assignment]
    return d if d is not None else default


def load_program_states(runs_dir: Path) -> list[dict]:
    """Load all latest.json files under runs_dir, attaching slug metadata."""
    programs: list[dict] = []
    for latest in sorted(runs_dir.glob("*/latest.json")):
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
            data["_program_slug"] = latest.parent.name
            data["_source"] = str(latest)
            programs.append(data)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"WARNING: Could not load {latest}: {exc}", file=sys.stderr)
    return programs


def get_health(program: dict) -> str:
    return safe_get(program, "program_state", "overall_health", default="unknown").lower()


def count_decisions(program: dict) -> int:
    queue = program.get("monitoring_output", {}).get("decision_queue", [])
    return len(queue) if isinstance(queue, list) else 0


def count_flags(program: dict) -> int:
    flags = program.get("flags", {})
    return sum(
        len(v) for k, v in flags.items()
        if isinstance(v, list) and k != "inferred"
    )


# ---------------------------------------------------------------------------
# Regeneration
# ---------------------------------------------------------------------------

def run_script(script_path: Path, extra_args: list[str], label: str) -> bool:
    """Run a Python script as a subprocess. Returns True on success."""
    cmd = [sys.executable, str(script_path)] + extra_args
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        for line in result.stdout.strip().splitlines():
            print(f"    {line}")
    if result.returncode != 0:
        print(f"  ERROR: {label} exited {result.returncode}", file=sys.stderr)
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                print(f"    {line}", file=sys.stderr)
        return False
    return True


def discover_program_slugs(runs_dir: Path) -> list[str]:
    """Return sorted list of program slugs that have a latest.json."""
    return sorted(p.parent.name for p in runs_dir.glob("*/latest.json"))


def regenerate_dashboards(
    scripts_dir: Path,
    runs_dir: Path,
    public_dir: Path,
    ui_dir: Path,
    skip_regen: bool,
) -> None:
    """Regenerate all dashboards and auditor views into public/ and ui/."""
    programs_html = public_dir / "programs.html"
    fleet_html = public_dir / "fleet.html"

    dashboard_script = scripts_dir / "dashboard.py"
    fleet_script = scripts_dir / "fleet_dashboard.py"
    auditor_script = scripts_dir / "auditor_view_renderer.py"

    if skip_regen:
        print("  --skip-regen set: skipping dashboard regeneration.")
        return

    slugs = discover_program_slugs(runs_dir)

    # 1 — Combined multi-program view
    if dashboard_script.exists():
        print("\n[1/5] Regenerating combined program dashboard...")
        run_script(
            dashboard_script,
            ["--runs", str(runs_dir), "--output", str(programs_html)],
            "dashboard.py",
        )
    else:
        print(f"  WARNING: {dashboard_script} not found — skipping.", file=sys.stderr)

    # 2 — Fleet observability view
    if fleet_script.exists():
        print("\n[2/5] Regenerating fleet dashboard...")
        run_script(
            fleet_script,
            ["--output", str(fleet_html)],
            "fleet_dashboard.py",
        )
    else:
        print(f"  WARNING: {fleet_script} not found — skipping.", file=sys.stderr)

    # 3 — Per-program dashboards (62443-style light-theme, gold standard)
    program_renderer_script = scripts_dir / "program_dashboard_renderer.py"
    if program_renderer_script.exists() and slugs:
        print(f"\n[3/5] Regenerating per-program dashboards ({len(slugs)} programs)...")
        for slug in slugs:
            dst = public_dir / slug / "index.html"
            dst.parent.mkdir(parents=True, exist_ok=True)
            ok = run_script(
                program_renderer_script,
                ["--runs", str(runs_dir), "--program", slug, "--output", str(dst)],
                f"program_dashboard_renderer.py --program {slug}",
            )
            if ok:
                print(f"  → {dst}")
    elif slugs:
        print(f"\n[3/5] program_dashboard_renderer.py not found — "
              f"per-program dashboards will use committed fallback.", file=sys.stderr)

    # 4 — Auditor views per program
    if auditor_script.exists() and slugs:
        today = date.today().isoformat()
        print(f"\n[4/5] Regenerating auditor views ({len(slugs)} programs)...")
        for slug in slugs:
            dst = ui_dir / f"{slug}-auditor-{today}.html"
            ok = run_script(
                auditor_script,
                ["--program", slug, "--output", str(dst)],
                f"auditor_view_renderer.py --program {slug}",
            )
            if ok:
                print(f"  → {dst}")
    else:
        print(f"\n[4/5] Skipping auditor views "
              f"({'script not found' if not auditor_script.exists() else 'no programs'}).",
              file=sys.stderr)

    # 5 — Portfolio briefing page
    portfolio_renderer_script = scripts_dir / "portfolio_renderer.py"
    if portfolio_renderer_script.exists():
        print("\n[5/5] Regenerating portfolio briefing...")
        portfolio_out = ui_dir / "portfolio.html"
        run_script(
            portfolio_renderer_script,
            ["--output", str(portfolio_out)],
            "portfolio_renderer.py",
        )
    else:
        print(f"\n[5/5] portfolio_renderer.py not found — "
              f"portfolio.html will use committed fallback.", file=sys.stderr)


# ---------------------------------------------------------------------------
# File assembly
# ---------------------------------------------------------------------------

def copy_ui_files(ui_dir: Path, public_dir: Path) -> None:
    """Copy ui/portfolio.html and ui/fleet-dashboard.html into public/."""
    mappings = {
        "portfolio.html": "portfolio.html",
        "fleet-dashboard.html": "fleet.html",
    }
    for src_name, dst_name in mappings.items():
        src = ui_dir / src_name
        dst = public_dir / dst_name
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
            print(f"  Copied {src} → {dst}")
        elif src.exists():
            print(f"  Kept regenerated {dst} (already written)")
        else:
            print(f"  WARNING: {src} not found — skipping.", file=sys.stderr)


def copy_program_dashboards(runs_dir: Path, public_dir: Path) -> list[str]:
    """
    Copy runs/[program]/dashboard.html into public/[program]/index.html as a
    fallback — only when Step 1 regeneration did NOT already write the file.
    Returns a list of slugs that have a per-program dashboard available.
    """
    slugs_with_dashboard: list[str] = []
    for src in sorted(runs_dir.glob("*/dashboard.html")):
        slug = src.parent.name
        dst_dir = public_dir / slug
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / "index.html"
        if dst.exists():
            print(f"  Skipping fallback for {slug} — freshly generated copy already present")
            slugs_with_dashboard.append(slug)
            continue
        shutil.copy2(src, dst)
        slugs_with_dashboard.append(slug)
        print(f"  Copied (fallback) {src} → {dst}")
    # Also include slugs where Step 1 wrote directly (no committed dashboard.html)
    for generated in sorted(public_dir.glob("*/index.html")):
        slug = generated.parent.name
        if slug not in slugs_with_dashboard and slug != "auditor":
            slugs_with_dashboard.append(slug)
    return sorted(set(slugs_with_dashboard))


def copy_auditor_files(ui_dir: Path, public_dir: Path) -> list[Path]:
    """
    Copy ui/*-auditor-*.html into public/auditor/.
    Returns a list of destination paths copied.
    """
    auditor_files = sorted(ui_dir.glob("*-auditor-*.html"))
    if not auditor_files:
        return []
    auditor_dir = public_dir / "auditor"
    auditor_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for src in auditor_files:
        dst = auditor_dir / src.name
        shutil.copy2(src, dst)
        copied.append(dst)
        print(f"  Copied {src} → {dst}")
    return copied


# ---------------------------------------------------------------------------
# Nav hub HTML generation
# ---------------------------------------------------------------------------

def render_program_card(program: dict, has_detail_page: bool) -> str:
    """Render a single program card for the nav hub."""
    slug = program.get("_program_slug", "")
    name = (
        safe_get(program, "run_manifest", "program_name", default="")
        or PROGRAM_DISPLAY_NAMES.get(slug, slug)
    )
    health = get_health(program)
    health_color = HEALTH_COLORS.get(health, HEALTH_COLORS["unknown"])
    health_label = HEALTH_LABELS.get(health, "Unknown")
    status = safe_get(program, "program_state", "one_line_status", default="No status available.")
    run_date = safe_get(program, "run_manifest", "run_date", default="Unknown")
    decisions = count_decisions(program)
    flags = count_flags(program)

    href = f"{slug}/" if has_detail_page else "programs.html"
    link_hint = "" if has_detail_page else " (combined view)"

    return f"""
    <a href="{href}" class="card" title="{name}{link_hint}">
      <div class="card-health-bar" style="background:{health_color}"></div>
      <div class="card-name">{name}</div>
      <div class="card-status">{status[:120]}{'…' if len(status) > 120 else ''}</div>
      <div class="card-meta">
        <span class="health-pill">
          <span class="health-dot" style="background:{health_color}"></span>
          {health_label}
        </span>
        <span>{decisions} decision{'s' if decisions != 1 else ''}</span>
        <span>{flags} flag{'s' if flags != 1 else ''}</span>
        <span>Run: {run_date}</span>
      </div>
    </a>"""


def render_utility_card(href: str, icon: str, label: str, desc: str) -> str:
    return f"""
    <a href="{href}" class="utility-card">
      <span class="utility-icon">{icon}</span>
      <div>
        <div class="utility-label">{label}</div>
        <div class="utility-desc">{desc}</div>
      </div>
    </a>"""


def render_auditor_cards(auditor_files: list[Path]) -> str:
    if not auditor_files:
        return '<p class="empty">No auditor view snapshots found.</p>'
    cards = []
    for f in auditor_files:
        href = f"auditor/{f.name}"
        label = f.stem.replace("-", " ").title()
        cards.append(render_utility_card(href, "📋", label, "Read-only auditor posture snapshot"))
    return "\n".join(cards)


def generate_nav_hub(
    programs: list[dict],
    slugs_with_dashboard: list[str],
    auditor_files: list[Path],
    public_dir: Path,
    has_programs_html: bool,
    has_fleet_html: bool,
    has_portfolio_html: bool,
) -> None:
    """Write public/index.html — the unified navigation hub."""
    now = datetime.now().strftime("%A, %B %d %Y — %I:%M %p")
    today = date.today().isoformat()

    if programs:
        program_cards_html = "\n".join(
            render_program_card(p, p.get("_program_slug", "") in slugs_with_dashboard)
            for p in programs
        )
    else:
        program_cards_html = '<p class="empty">No program run data found.</p>'

    utility_links: list[str] = []
    if has_programs_html:
        utility_links.append(render_utility_card(
            "programs.html", "📊",
            "All Programs Dashboard",
            "Combined health, decisions, and flags across every program",
        ))
    if has_portfolio_html:
        utility_links.append(render_utility_card(
            "portfolio.html", "📁",
            "Portfolio Briefing",
            "Portfolio-level summary with health counters and suggested actions",
        ))
    if has_fleet_html:
        utility_links.append(render_utility_card(
            "fleet.html", "🔭",
            "Fleet Dashboard",
            "Agent health, program performance, cost tracking, decision audit",
        ))
    utility_section = (
        "\n".join(utility_links)
        if utility_links
        else '<p class="empty">No portfolio-level views available.</p>'
    )

    auditor_section = render_auditor_cards(auditor_files)

    red = sum(1 for p in programs if get_health(p) == "red")
    yellow = sum(1 for p in programs if get_health(p) == "yellow")
    green = sum(1 for p in programs if get_health(p) == "green")
    health_parts = [f"{len(programs)} program{'s' if len(programs) != 1 else ''}"]
    if red:
        health_parts.append(f'<span style="color:#ef4444;font-weight:600">{red} red</span>')
    if yellow:
        health_parts.append(f'<span style="color:#f59e0b;font-weight:600">{yellow} yellow</span>')
    if green:
        health_parts.append(f'<span style="color:#22c55e;font-weight:600">{green} green</span>')
    health_summary = " &nbsp;·&nbsp; ".join(health_parts)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Compliance Portfolio</title>
  <style>{NAV_HUB_CSS}</style>
</head>
<body>

<header class="site-header">
  <h1>Compliance Portfolio</h1>
  <div class="meta">{now} &nbsp;·&nbsp; {health_summary}</div>
</header>

<section class="section">
  <div class="section-title">Programs</div>
  <div class="card-grid">
    {program_cards_html}
  </div>
</section>

<section class="section">
  <div class="section-title">Portfolio Views</div>
  <div class="utility-grid">
    {utility_section}
  </div>
</section>

<section class="section">
  <div class="section-title">Auditor Views</div>
  <div class="utility-grid">
    {auditor_section}
  </div>
</section>

<footer>
  Generated by build_pages.py &nbsp;·&nbsp; {today} &nbsp;·&nbsp; {len(programs)} program(s)
</footer>

</body>
</html>"""

    out = public_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Nav hub written: {out}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assemble the GitLab Pages public/ directory for the compliance portfolio.",
    )
    parser.add_argument(
        "--runs", default="runs",
        help="Path to the runs/ directory (default: runs/)",
    )
    parser.add_argument(
        "--ui", default="ui",
        help="Path to the ui/ directory (default: ui/)",
    )
    parser.add_argument(
        "--scripts", default="scripts",
        help="Path to the scripts/ directory (default: scripts/)",
    )
    parser.add_argument(
        "--output", default="public",
        help="Destination directory for GitLab Pages artifacts (default: public/)",
    )
    parser.add_argument(
        "--skip-regen", action="store_true",
        help="Skip running dashboard.py and fleet_dashboard.py; copy committed HTML only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    runs_dir = Path(args.runs)
    ui_dir = Path(args.ui)
    scripts_dir = Path(args.scripts)
    public_dir = Path(args.output)

    if not scripts_dir.exists():
        print(f"ERROR: scripts/ directory not found: {scripts_dir}", file=sys.stderr)
        return 1
    for path, label in [(runs_dir, "runs/"), (ui_dir, "ui/")]:
        if not path.exists():
            print(f"WARNING: {label} directory not found: {path} — treating as empty",
                  file=sys.stderr)
            path.mkdir(parents=True, exist_ok=True)

    public_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {public_dir.resolve()}\n")

    print("=== Step 1: Dashboard regeneration ===")
    regenerate_dashboards(scripts_dir, runs_dir, public_dir, ui_dir, args.skip_regen)

    print("\n=== Step 2: Portfolio HTML ===")
    copy_ui_files(ui_dir, public_dir)

    print("\n=== Step 3: Per-program dashboards ===")
    slugs_with_dashboard = copy_program_dashboards(runs_dir, public_dir)
    if not slugs_with_dashboard:
        print("  No per-program dashboard.html files found.")

    print("\n=== Step 4: Auditor views ===")
    auditor_files = copy_auditor_files(ui_dir, public_dir)
    if not auditor_files:
        print("  No auditor view snapshots found in ui/.")

    print("\n=== Step 5: Generating nav hub ===")
    programs = load_program_states(runs_dir)
    if not programs:
        print("  WARNING: No latest.json files found — nav hub will have no program cards.",
              file=sys.stderr)

    has_programs_html = (public_dir / "programs.html").exists()
    has_fleet_html = (public_dir / "fleet.html").exists()
    has_portfolio_html = (public_dir / "portfolio.html").exists()

    generate_nav_hub(
        programs=programs,
        slugs_with_dashboard=slugs_with_dashboard,
        auditor_files=auditor_files,
        public_dir=public_dir,
        has_programs_html=has_programs_html,
        has_fleet_html=has_fleet_html,
        has_portfolio_html=has_portfolio_html,
    )

    print("\n=== Build complete ===")
    all_html = list(public_dir.rglob("*.html"))
    print(f"  {len(all_html)} HTML file(s) in {public_dir}/")
    for f in sorted(all_html):
        print(f"    {f.relative_to(public_dir)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
