#!/usr/bin/env python3
"""
Kanban Board Renderer
=====================
Reads data/[program]/kanban.yaml and generates a static HTML kanban board.

Usage:
    python scripts/kanban_renderer.py --program fedramp-high
    python scripts/kanban_renderer.py --program fedramp-high --output ui/fedramp-kanban.html
    python scripts/kanban_renderer.py --program fedramp-high --open
    python scripts/kanban_renderer.py --all                 # renders all programs
    python scripts/kanban_renderer.py --all --open          # renders and opens all

Dependencies:
    PyYAML (yaml) — install with: pip install pyyaml

Repo path: /scripts/kanban_renderer.py
"""

import argparse
import sys
import webbrowser
from datetime import date, datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLUMN_ORDER = ["backlog", "to_do", "in_progress", "in_review", "blocked", "done", "canceled"]

COLUMN_LABELS = {
    "backlog":     "Backlog",
    "to_do":       "To Do",
    "in_progress": "In Progress",
    "in_review":   "In Review",
    "blocked":     "Blocked",
    "done":        "Done",
    "canceled":    "Canceled",
}

TYPE_BADGE = {
    "epic":    ("E", "#7c3aed", "#ede9fe"),
    "story":   ("S", "#1d4ed8", "#dbeafe"),
    "task":    ("T", "#0369a1", "#e0f2fe"),
    "bug":     ("B", "#dc2626", "#fee2e2"),
    "subtask": ("↳", "#374151", "#f3f4f6"),
}

PRIORITY_COLOR = {
    "critical": "#dc2626",
    "high":     "#ea580c",
    "medium":   "#ca8a04",
    "low":      "#16a34a",
}

PRIORITY_DOT = {
    "critical": "🔴",
    "high":     "🟠",
    "medium":   "🟡",
    "low":      "🟢",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_board(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_boards(data_dir: Path) -> list[Path]:
    """Find all kanban.yaml files under data/*/kanban.yaml."""
    return sorted(data_dir.glob("*/kanban.yaml"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe(text) -> str:
    if text is None:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def days_diff(date_str: str) -> int | None:
    try:
        d = datetime.strptime(str(date_str), "%Y-%m-%d").date()
        return (d - date.today()).days
    except (ValueError, TypeError):
        return None


def overdue_label(due_str) -> str:
    if not due_str:
        return ""
    delta = days_diff(str(due_str))
    if delta is None:
        return safe(due_str)
    if delta < 0:
        return f'<span class="due overdue">{safe(due_str)} ({abs(delta)}d overdue)</span>'
    if delta == 0:
        return f'<span class="due today">Due today</span>'
    if delta <= 3:
        return f'<span class="due soon">{safe(due_str)} (in {delta}d)</span>'
    return f'<span class="due">{safe(due_str)}</span>'


def type_badge(card_type: str) -> str:
    label, fg, bg = TYPE_BADGE.get(card_type, ("?", "#374151", "#f3f4f6"))
    return (f'<span class="type-badge" style="color:{fg};background:{bg}" '
            f'title="{safe(card_type)}">{label}</span>')


def priority_dot(priority: str) -> str:
    return PRIORITY_DOT.get(priority.lower(), "⚪") if priority else "⚪"


def is_overdue(card: dict) -> bool:
    if card.get("column") in ("done", "canceled"):
        return False
    delta = days_diff(str(card.get("due", "")))
    return delta is not None and delta < 0


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    min-height: 100vh;
    padding: 1.5rem;
}

.header { margin-bottom: 1.5rem; }
.header h1 { font-size: 1.3rem; font-weight: 700; color: #f8fafc; }
.header .meta { font-size: 0.78rem; color: #64748b; margin-top: 0.2rem; }
.jira-link { font-size: 0.75rem; color: #38bdf8; margin-left: 0.5rem; }

.stats { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.stat { background: #1e293b; border: 1px solid #334155; border-radius: 0.5rem;
        padding: 0.6rem 1rem; font-size: 0.8rem; color: #94a3b8; }
.stat strong { color: #f1f5f9; font-size: 1rem; display: block; }
.stat.warn strong { color: #f59e0b; }
.stat.danger strong { color: #ef4444; }

.board { display: flex; gap: 0.75rem; overflow-x: auto; padding-bottom: 1rem; align-items: flex-start; }

.column {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 0.75rem;
    min-width: 240px;
    max-width: 280px;
    flex-shrink: 0;
}
.column.col-blocked { border-color: #f59e0b; }
.column.col-done { opacity: 0.7; }
.column.col-canceled { opacity: 0.55; }

.col-header {
    padding: 0.75rem 1rem 0.5rem;
    border-bottom: 1px solid #334155;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.col-title { font-size: 0.78rem; font-weight: 700; text-transform: uppercase;
             letter-spacing: 0.06em; color: #94a3b8; }
.col-title.blocked { color: #f59e0b; }
.col-count { font-size: 0.72rem; background: #334155; color: #94a3b8;
             padding: 0.1rem 0.4rem; border-radius: 999px; font-weight: 600; }
.wip-warn { font-size: 0.65rem; color: #f59e0b; margin-left: 0.3rem; }

.cards { padding: 0.6rem; display: flex; flex-direction: column; gap: 0.5rem; }

.card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.5rem;
    padding: 0.65rem 0.75rem;
    font-size: 0.82rem;
    cursor: default;
    transition: border-color 0.15s;
}
.card:hover { border-color: #64748b; }
.card.blocked { border-left: 3px solid #f59e0b; }
.card.overdue { border-left: 3px solid #ef4444; }

.card-top { display: flex; align-items: flex-start; gap: 0.4rem; margin-bottom: 0.35rem; }
.card-id { font-size: 0.68rem; color: #475569; font-family: monospace; white-space: nowrap; }
.jira-key { font-size: 0.68rem; color: #38bdf8; font-family: monospace; }
.card-title { color: #f1f5f9; line-height: 1.35; flex: 1; }

.card-meta { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-top: 0.4rem; }
.badge {
    font-size: 0.65rem; font-weight: 600;
    padding: 0.1rem 0.35rem; border-radius: 0.2rem;
}
.badge-label { background: #1e293b; color: #94a3b8; border: 1px solid #334155; }
.badge-control { background: #0c1a2e; color: #38bdf8; border: 1px solid #1e40af; font-family: monospace; }
.badge-poam { background: #1a0a0a; color: #fca5a5; border: 1px solid #7f1d1d; font-family: monospace; }

.type-badge {
    font-size: 0.65rem; font-weight: 700;
    padding: 0.1rem 0.35rem; border-radius: 0.2rem;
    flex-shrink: 0;
}

.assignee { font-size: 0.7rem; color: #64748b; margin-top: 0.3rem; }
.due { font-size: 0.7rem; color: #64748b; }
.due.overdue { color: #ef4444; font-weight: 600; }
.due.today { color: #f59e0b; font-weight: 600; }
.due.soon { color: #f59e0b; }

.blocked-reason {
    font-size: 0.72rem; color: #f59e0b;
    background: #1a1200;
    border-radius: 0.25rem;
    padding: 0.25rem 0.4rem;
    margin-top: 0.4rem;
    border: 1px solid #78350f;
}

.points { font-size: 0.65rem; color: #475569; }

.sprint-section { padding: 1rem 0 0; }
.sprint-title {
    font-size: 0.7rem; font-weight: 700; color: #475569;
    text-transform: uppercase; letter-spacing: 0.06em;
    padding: 0 0.75rem 0.4rem;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 0.5rem;
}

.empty-col { font-size: 0.78rem; color: #334155; font-style: italic; text-align: center; padding: 1rem 0; }

footer { margin-top: 2rem; font-size: 0.72rem; color: #334155; text-align: center; }
"""


def render_card(card: dict) -> str:
    cid = safe(card.get("id", ""))
    jira_key = card.get("jira_key")
    title = safe(card.get("title", "Untitled"))
    ctype = card.get("type", "task")
    priority = card.get("priority", "medium")
    assignee = card.get("assignee")
    due = card.get("due")
    blocked_by = card.get("blocked_by")
    labels = card.get("labels", [])
    controls = card.get("linked_controls", [])
    poam_id = card.get("poam_id")
    points = card.get("story_points")
    column = card.get("column", "")

    card_classes = "card"
    if column == "blocked":
        card_classes += " blocked"
    elif is_overdue(card):
        card_classes += " overdue"

    html = f'<div class="{card_classes}">'

    # Top row: priority dot + type badge + title
    prio_html = f'<span title="{safe(priority)}">{priority_dot(priority)}</span>'
    jira_html = f' <span class="jira-key">{safe(jira_key)}</span>' if jira_key else ""
    html += (f'<div class="card-top">'
             f'{prio_html} {type_badge(ctype)}'
             f'<div style="flex:1">'
             f'<div class="card-id">{cid}{jira_html}</div>'
             f'<div class="card-title">{title}</div>'
             f'</div>'
             f'</div>')

    # Meta badges
    meta_parts = []
    for lbl in labels[:4]:
        meta_parts.append(f'<span class="badge badge-label">{safe(lbl)}</span>')
    for ctrl in controls[:3]:
        meta_parts.append(f'<span class="badge badge-control">{safe(ctrl)}</span>')
    if poam_id:
        meta_parts.append(f'<span class="badge badge-poam">{safe(poam_id)}</span>')
    if meta_parts:
        html += f'<div class="card-meta">{"".join(meta_parts)}</div>'

    # Due date
    if due:
        html += f'<div style="margin-top:0.3rem">{overdue_label(due)}</div>'

    # Assignee + points row
    footer_parts = []
    if assignee:
        footer_parts.append(f'<span class="assignee">👤 {safe(assignee)}</span>')
    if points is not None:
        footer_parts.append(f'<span class="points">⚡ {points}pt</span>')
    if footer_parts:
        html += f'<div style="display:flex;gap:0.5rem;margin-top:0.3rem">{"".join(footer_parts)}</div>'

    # Blocked reason
    if blocked_by:
        html += f'<div class="blocked-reason">⛔ {safe(blocked_by)}</div>'

    html += "</div>"
    return html


def render_column(col: dict, cards: list[dict]) -> str:
    col_id = col.get("id", "")
    col_name = col.get("name", COLUMN_LABELS.get(col_id, col_id))
    wip_limit = col.get("wip_limit")

    col_cards = [c for c in cards if c.get("column") == col_id]
    count = len(col_cards)

    wip_warn = ""
    if wip_limit and count > wip_limit:
        wip_warn = f'<span class="wip-warn">⚠ WIP limit {wip_limit}</span>'

    title_class = f"col-title{' blocked' if col_id == 'blocked' else ''}"
    col_class = f"column col-{col_id}"

    cards_html = "".join(render_card(c) for c in col_cards)
    if not col_cards:
        cards_html = '<div class="empty-col">—</div>'

    return f"""
<div class="{col_class}">
  <div class="col-header">
    <span class="{title_class}">{safe(col_name)}</span>
    <span>{wip_warn}<span class="col-count">{count}</span></span>
  </div>
  <div class="cards">{cards_html}</div>
</div>"""


def compute_stats(cards: list[dict], sprints: list[dict]) -> dict:
    today = date.today().isoformat()
    active_sprint = None
    for s in sprints:
        if s.get("state") == "active" or (s.get("start", "") <= today <= s.get("end", "")):
            active_sprint = s.get("id")
            break

    in_progress = sum(1 for c in cards if c.get("column") == "in_progress")
    blocked = sum(1 for c in cards if c.get("column") == "blocked")
    overdue = sum(1 for c in cards if is_overdue(c))
    done_sprint = sum(1 for c in cards
                      if c.get("column") == "done" and c.get("sprint") == active_sprint)
    unscheduled = sum(1 for c in cards
                      if c.get("column") not in ("done", "canceled") and not c.get("sprint"))

    return {
        "in_progress": in_progress,
        "blocked": blocked,
        "overdue": overdue,
        "done_sprint": done_sprint,
        "unscheduled": unscheduled,
        "active_sprint": active_sprint,
    }


def render_stats(stats: dict, active_sprint_name: str) -> str:
    sprint_label = f"Done ({safe(active_sprint_name)})" if active_sprint_name else "Done (sprint)"
    parts = [
        ("In Progress", stats["in_progress"], ""),
        ("Blocked", stats["blocked"], "danger" if stats["blocked"] else ""),
        ("Overdue", stats["overdue"], "danger" if stats["overdue"] else ""),
        (sprint_label, stats["done_sprint"], ""),
        ("Unscheduled", stats["unscheduled"], "warn" if stats["unscheduled"] > 5 else ""),
    ]
    html = '<div class="stats">'
    for label, value, cls in parts:
        html += f'<div class="stat{" " + cls if cls else ""}"><strong>{value}</strong>{label}</div>'
    html += "</div>"
    return html


def render_board(board: dict) -> str:
    program = safe(board.get("program", "unknown"))
    board_name = safe(board.get("board_name", f"{program} — Project Board"))
    updated_at = safe(board.get("updated_at", ""))
    jira_project_key = board.get("jira_project_key")
    sprints = board.get("sprints", [])
    columns = board.get("columns", [])
    cards = board.get("cards", [])
    today = date.today().isoformat()

    # Use declared columns if present; fall back to order constant
    if not columns:
        columns = [{"id": cid, "name": COLUMN_LABELS[cid]} for cid in COLUMN_ORDER]

    stats = compute_stats(cards, sprints)
    active_sprint_name = ""
    for s in sprints:
        if s.get("id") == stats.get("active_sprint"):
            active_sprint_name = s.get("name", "")
            break

    jira_badge = ""
    if jira_project_key:
        jira_badge = f'<span class="jira-link">Jira: {safe(jira_project_key)}</span>'

    columns_html = "".join(render_column(col, cards) for col in columns)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{board_name} — {today}</title>
<style>{CSS}</style>
</head>
<body>

<div class="header">
  <h1>{board_name}{jira_badge}</h1>
  <div class="meta">Program: {program} &nbsp;·&nbsp; Updated: {updated_at} &nbsp;·&nbsp; {len(cards)} cards</div>
</div>

{render_stats(stats, active_sprint_name)}

<div class="board">
{columns_html}
</div>

<footer>Generated by kanban-renderer · {today} · {len(cards)} cards across {len(columns)} columns</footer>

</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def resolve_paths(args) -> tuple[Path, Path]:
    """Return (repo_root, data_dir)."""
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    data_dir = repo_root / "data"
    return repo_root, data_dir


def render_one(board_path: Path, output_path: Path, do_open: bool) -> None:
    board = load_board(board_path)
    program = board.get("program", board_path.parent.name)
    html = render_board(board)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    cards = board.get("cards", [])
    blocked = sum(1 for c in cards if c.get("column") == "blocked")
    overdue = sum(1 for c in cards if is_overdue(c))
    print(f"  {program} — {len(cards)} cards | {blocked} blocked | {overdue} overdue → {output_path}")

    if do_open:
        webbrowser.open(output_path.resolve().as_uri())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a static HTML kanban board from data/[program]/kanban.yaml"
    )
    parser.add_argument("--program", help="Program slug (renders one board)")
    parser.add_argument("--all", action="store_true", help="Render boards for all programs")
    parser.add_argument("--data", default="data", help="Path to data directory (default: ./data)")
    parser.add_argument("--output", help="Output HTML path (default: ui/[program]-kanban-[date].html)")
    parser.add_argument("--open", action="store_true", help="Open rendered board(s) in browser")
    args = parser.parse_args()

    if not args.program and not args.all:
        parser.error("Specify --program [slug] or --all")

    repo_root, data_dir = resolve_paths(args)
    data_dir = Path(args.data)
    ui_dir = repo_root / "ui"
    today = date.today().isoformat()

    print("Kanban Renderer")
    print("─" * 40)

    if args.all:
        boards = find_boards(data_dir)
        if not boards:
            print(f"No kanban.yaml files found under {data_dir}/*/kanban.yaml", file=sys.stderr)
            sys.exit(1)
        print(f"Found {len(boards)} board(s):\n")
        for board_path in boards:
            program = board_path.parent.name
            out = ui_dir / f"{program}-kanban-{today}.html"
            try:
                render_one(board_path, out, getattr(args, "open"))
            except Exception as e:
                print(f"  ERROR rendering {program}: {e}", file=sys.stderr)
    else:
        program = args.program
        board_path = data_dir / program / "kanban.yaml"
        if not board_path.exists():
            print(f"ERROR: No kanban board found at {board_path}", file=sys.stderr)
            print(f"Run: /kanban init {program}", file=sys.stderr)
            sys.exit(1)
        out = Path(args.output) if args.output else ui_dir / f"{program}-kanban-{today}.html"
        print(f"Rendering {program}:\n")
        render_one(board_path, out, getattr(args, "open"))

    print("\nDone.")


if __name__ == "__main__":
    main()
