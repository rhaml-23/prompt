#!/usr/bin/env python3
"""
Calendar Exporter
=================
Transforms the calendar_events array from a pipeline run JSON into:
  - A portable .ics file (RFC 5545 iCalendar)
  - A human-readable markdown event list

Companion to functions/calendar-output-spec.md. Implements the Python
execution mode for calendar generation (the LLM spec handles the other mode).

Usage:
    python scripts/calendar_exporter.py --run runs/[PROGRAM]/latest.json
    python scripts/calendar_exporter.py --run runs/[PROGRAM]/latest.json --output events.ics
    python scripts/calendar_exporter.py --run runs/[PROGRAM]/latest.json --markdown
    python scripts/calendar_exporter.py --run runs/[PROGRAM]/latest.json --preview

Style: PEP 8
Deviations: None
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

WORK_START_HOUR = 9
WORK_END_HOUR = 17
GAP_MINUTES = 15
DEFAULT_TIMEZONE = "America/New_York"

US_FEDERAL_HOLIDAYS_2026 = {
    "2026-01-01",
    "2026-01-19",
    "2026-02-16",
    "2026-05-25",
    "2026-07-03",
    "2026-07-04",
    "2026-09-07",
    "2026-10-12",
    "2026-11-11",
    "2026-11-26",
    "2026-12-25",
}

EVENT_DURATION_DEFAULTS = {
    "evidence_collection": 60,
    "audit_checkpoint": 90,
    "vendor_review": 60,
    "status_report": 30,
    "stakeholder_meeting": 60,
    "remediation_deadline": 0,
    "default": 30,
}


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    anchors = {"config", "engine", "functions", "scripts"}
    for candidate in [here.parent, here, here.parent.parent]:
        if sum(1 for a in anchors if (candidate / a).exists()) >= 3:
            return candidate
    return Path.cwd()


def is_working_day(date_str: str) -> bool:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    if dt.weekday() >= 5:
        return False
    if date_str in US_FEDERAL_HOLIDAYS_2026:
        return False
    return True


def next_working_day(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt += timedelta(days=1)
    while dt.weekday() >= 5 or dt.strftime("%Y-%m-%d") in US_FEDERAL_HOLIDAYS_2026:
        dt += timedelta(days=1)
    return dt.strftime("%Y-%m-%d")


def load_calendar_events(run_path: Path) -> list[dict[str, Any]]:
    with open(run_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = data.get("monitoring_output", {}).get("calendar_events", [])
    if not events:
        events = data.get("calendar_events", [])
    return events


def classify_event(event: dict[str, Any]) -> str:
    title = event.get("title", "").lower()
    if "evidence" in title:
        return "evidence_collection"
    if "audit" in title:
        return "audit_checkpoint"
    if "vendor" in title:
        return "vendor_review"
    if "status" in title:
        return "status_report"
    if "meeting" in title or "stakeholder" in title:
        return "stakeholder_meeting"
    if "deadline" in title or "remediation" in title:
        return "remediation_deadline"
    return "default"


def adjust_to_working_day(date_str: str) -> tuple[str, bool]:
    if is_working_day(date_str):
        return date_str, False
    original = date_str
    while not is_working_day(date_str):
        date_str = next_working_day(date_str)
    return date_str, True


def to_ics(events: list[dict[str, Any]], timezone: str = DEFAULT_TIMEZONE) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//CompliancePipeline//CalendarExporter//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-TIMEZONE:{timezone}",
    ]

    for event in events:
        date_str = event.get("date", "")
        if not date_str:
            continue

        adjusted_date, was_adjusted = adjust_to_working_day(date_str)
        event_type = classify_event(event)
        duration_min = EVENT_DURATION_DEFAULTS.get(
            event_type, EVENT_DURATION_DEFAULTS["default"]
        )

        title = event.get("title", "Untitled Event")
        if was_adjusted:
            title = f"[ADJUSTED] {title}"

        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{title}-{adjusted_date}"))
        dt_start = datetime.strptime(adjusted_date, "%Y-%m-%d").replace(
            hour=WORK_START_HOUR
        )

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{datetime.now(tz=None).strftime('%Y%m%dT%H%M%SZ')}")

        if duration_min == 0:
            lines.append(f"DTSTART;VALUE=DATE:{dt_start.strftime('%Y%m%d')}")
        else:
            lines.append(f"DTSTART:{dt_start.strftime('%Y%m%dT%H%M%S')}")
            dt_end = dt_start + timedelta(minutes=duration_min)
            lines.append(f"DTEND:{dt_end.strftime('%Y%m%dT%H%M%S')}")

        lines.append(f"SUMMARY:{title}")

        desc_parts = []
        if event.get("owner"):
            desc_parts.append(f"Owner: {event['owner']}")
        if event.get("notes"):
            desc_parts.append(f"Notes: {event['notes']}")
        if was_adjusted:
            desc_parts.append(f"Original date: {date_str} (non-working day)")
        if event.get("recurrence", "none") != "none":
            desc_parts.append(f"Recurrence: {event['recurrence']}")
        if desc_parts:
            lines.append(f"DESCRIPTION:{'\\n'.join(desc_parts)}")

        recurrence = event.get("recurrence", "none")
        rrule_map = {
            "daily": "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR",
            "weekly": "FREQ=WEEKLY",
            "monthly": "FREQ=MONTHLY",
            "quarterly": "FREQ=MONTHLY;INTERVAL=3",
            "annual": "FREQ=YEARLY",
        }
        if recurrence in rrule_map:
            lines.append(f"RRULE:{rrule_map[recurrence]}")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def to_markdown(events: list[dict[str, Any]]) -> str:
    lines = ["# Calendar Events", ""]
    if not events:
        lines.append("No calendar events found in run JSON.")
        return "\n".join(lines)

    sorted_events = sorted(events, key=lambda e: e.get("date", ""))
    for event in sorted_events:
        date_str = event.get("date", "unknown")
        adjusted_date, was_adjusted = adjust_to_working_day(date_str)
        title = event.get("title", "Untitled")
        owner = event.get("owner", "unassigned")
        recurrence = event.get("recurrence", "none")
        notes = event.get("notes", "")

        marker = " [ADJUSTED]" if was_adjusted else ""
        lines.append(f"## {adjusted_date} — {title}{marker}")
        lines.append(f"- **Owner:** {owner}")
        lines.append(f"- **Recurrence:** {recurrence}")
        if notes:
            lines.append(f"- **Notes:** {notes}")
        if was_adjusted:
            lines.append(f"- **Original date:** {date_str} (non-working day)")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export calendar events from run JSON to .ics or markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--run",
        required=True,
        help="Path to run JSON file (e.g. runs/PROGRAM/latest.json).",
    )
    parser.add_argument(
        "--output",
        help="Output file path. Defaults to stdout.",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output as markdown instead of .ics.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print event summary to stdout without writing files.",
    )
    parser.add_argument(
        "--timezone",
        default=DEFAULT_TIMEZONE,
        help=f"IANA timezone (default: {DEFAULT_TIMEZONE}).",
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root()
    run_path = Path(args.run)
    if not run_path.is_absolute():
        run_path = repo_root / run_path

    if not run_path.exists():
        print(f"ERROR: Run file not found: {run_path}", file=sys.stderr)
        return 1

    events = load_calendar_events(run_path)
    if not events:
        print("No calendar events found in run JSON.", file=sys.stderr)
        return 0

    if args.preview:
        print(f"\nCalendar Events — {len(events)} found\n{'─' * 40}")
        for e in sorted(events, key=lambda x: x.get("date", "")):
            date_str = e.get("date", "?")
            adjusted, moved = adjust_to_working_day(date_str)
            marker = f" → {adjusted}" if moved else ""
            print(
                f"  {date_str}{marker}  {e.get('title', '?')}"
                f"  [{e.get('owner', '?')}]"
            )
        print()
        return 0

    if args.markdown:
        content = to_markdown(events)
    else:
        content = to_ics(events, args.timezone)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"Written: {output_path} ({len(events)} events)")
    else:
        print(content)

    return 0


if __name__ == "__main__":
    sys.exit(main())
