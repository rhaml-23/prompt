#!/usr/bin/env python3
"""
Provenance Log
==============
Append-only JSONL log of all deliverables produced by the program pipeline.
Tracks what was created, when, why, for which program, and whether it is reusable.

The Archivist tracks what files exist.
This log tracks why they were created and what they are worth.

Usage:
    # Write a log entry manually
    python provenance_log.py write \\
        --spec "program-intake-spec.md" \\
        --output "runs/fedramp/2025-03-01-run.json" \\
        --program "fedramp_high" \\
        --purpose "Initial program onboarding — inherited from prior PM" \\
        --reusability template

    # Query log entries
    python provenance_log.py query --program fedramp_high
    python provenance_log.py query --spec vendor-management-spec.md
    python provenance_log.py query --reusability template
    python provenance_log.py query --since 2025-01-01
    python provenance_log.py query --output-type report

    # Show summary statistics
    python provenance_log.py summary

    # Tail recent entries
    python provenance_log.py tail --n 10

Log location: /logs/provenance.jsonl (relative to repo root)
Repo path: /scripts/provenance_log.py

Dependencies:
    Standard library only

Schema:
    See ENTRY_SCHEMA below.
"""

import json
import argparse
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

ENTRY_SCHEMA = {
    "id":             "UUID — unique entry identifier",
    "timestamp":      "ISO 8601 UTC — when the deliverable was created",
    "spec":           "Generating spec filename — e.g. program-intake-spec.md",
    "output":         "Relative path to the deliverable file",
    "output_type":    "Deliverable type — see OUTPUT_TYPES",
    "program":        "Program slug this deliverable belongs to — e.g. fedramp_high",
    "purpose":        "Free text — why this was created, in one or two sentences",
    "reusability":    "Classification — see REUSABILITY_CLASSES",
    "reuse_notes":    "Optional — what would need to change to reuse this elsewhere",
    "quality_gate":   "pass | failed_once_corrected | escalated | skipped",
    "run_id":         "Optional — links to a pipeline run JSON if applicable",
}

OUTPUT_TYPES = [
    "program_skeleton",     # intake spec output
    "run_json",             # full pipeline run JSON
    "briefing",             # rendered morning briefing
    "draft_communication",  # draft email or message
    "calendar_export",      # .ics or markdown event list
    "vendor_scorecard",     # vendor performance scorecard
    "remediation_plan",     # vendor remediation plan
    "entropy_report",       # compliance entropy analysis
    "red_team_report",      # compliance red team report
    "qbr_report",           # portfolio quarterly business review
    "dashboard",            # HTML program dashboard
    "script",               # generated or adapted script
    "spec",                 # a spec document itself
    "product_evidence",     # product profile, control matrix, evidence gap from repo scan
    "lessons_learned_report",   # post-audit lessons learned by control family
    "corrective_action_plan",   # finding-to-action mapping with owners and target dates
    "feed_forward_artifact",    # structured JSON consumed by next intake cycle and entropy spec
    "program_improvement_items", # broader program improvements list (full_retrospective mode)
    "other",                # anything not covered above
]

REUSABILITY_CLASSES = {
    "template": (
        "Reusable as-is or with minor parameter changes. "
        "Program-specific content has been abstracted or is clearly parameterized. "
        "Example: a vendor scorecard template, a comms draft structure."
    ),
    "reference": (
        "Not directly reusable but worth consulting for future similar work. "
        "Contains patterns, approaches, or decisions worth repeating. "
        "Example: an entropy report for a mature program, a red team finding list."
    ),
    "instance": (
        "Program-specific. No reuse value beyond this program's context. "
        "Example: a run JSON for a specific program, a dated briefing output."
    ),
    "artifact": (
        "One-time deliverable. Created for a specific purpose that will not recur. "
        "Example: a pre-audit preparation package, a one-off stakeholder briefing."
    ),
}


# ---------------------------------------------------------------------------
# Log path
# ---------------------------------------------------------------------------

DEFAULT_LOG_PATH = Path("logs/provenance.jsonl")


def resolve_log_path(log_path: str | None) -> Path:
    if log_path:
        return Path(log_path)
    # Walk up from script location to find repo root (contains /specs or /runs)
    here = Path(__file__).resolve().parent
    for candidate in [here.parent, here.parent.parent]:
        if (candidate / "specs").exists() or (candidate / "runs").exists():
            return candidate / "logs" / "provenance.jsonl"
    return Path.cwd() / "logs" / "provenance.jsonl"


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def write_entry(
    spec: str,
    output: str,
    output_type: str,
    program: str,
    purpose: str,
    reusability: str,
    reuse_notes: str = "",
    quality_gate: str = "pass",
    run_id: str = "",
    log_path: Path = DEFAULT_LOG_PATH,
) -> dict:
    """Append a single provenance entry to the log."""

    if output_type not in OUTPUT_TYPES:
        print(f"WARNING: output_type '{output_type}' not in schema. Using 'other'.", file=sys.stderr)
        output_type = "other"

    if reusability not in REUSABILITY_CLASSES:
        valid = ", ".join(REUSABILITY_CLASSES.keys())
        print(f"ERROR: reusability must be one of: {valid}", file=sys.stderr)
        sys.exit(1)

    entry = {
        "id":           str(uuid.uuid4()),
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "spec":         spec,
        "output":       output,
        "output_type":  output_type,
        "program":      program,
        "purpose":      purpose,
        "reusability":  reusability,
        "reuse_notes":  reuse_notes,
        "quality_gate": quality_gate,
        "run_id":       run_id,
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def load_entries(log_path: Path) -> list[dict]:
    """Load all entries from the log."""
    if not log_path.exists():
        return []
    entries = []
    with open(log_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"WARNING: Skipping malformed entry on line {i}: {e}", file=sys.stderr)
    return entries


def filter_entries(
    entries: list[dict],
    program: str | None = None,
    spec: str | None = None,
    reusability: str | None = None,
    output_type: str | None = None,
    since: str | None = None,
) -> list[dict]:
    """Filter entries by any combination of criteria."""
    result = entries

    if program:
        result = [e for e in result if program.lower() in e.get("program", "").lower()]
    if spec:
        result = [e for e in result if spec.lower() in e.get("spec", "").lower()]
    if reusability:
        result = [e for e in result if e.get("reusability") == reusability]
    if output_type:
        result = [e for e in result if e.get("output_type") == output_type]
    if since:
        result = [e for e in result if e.get("timestamp", "") >= since]

    return result


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def fmt_entry(entry: dict, verbose: bool = False) -> str:
    ts = entry.get("timestamp", "")[:19].replace("T", " ")
    spec = entry.get("spec", "—")
    output = entry.get("output", "—")
    program = entry.get("program", "—")
    purpose = entry.get("purpose", "—")
    reusability = entry.get("reusability", "—")
    quality = entry.get("quality_gate", "—")
    run_id = entry.get("run_id", "")
    reuse_notes = entry.get("reuse_notes", "")

    reuse_icon = {
        "template":  "♻️ ",
        "reference": "📖 ",
        "instance":  "📄 ",
        "artifact":  "📎 ",
    }.get(reusability, "   ")

    gate_icon = {
        "pass":                  "✓",
        "failed_once_corrected": "~",
        "escalated":             "!",
        "skipped":               "-",
    }.get(quality, "?")

    lines = [
        f"[{ts}] {gate_icon} {reuse_icon}{reusability.upper()}",
        f"  Spec:    {spec}",
        f"  Output:  {output}",
        f"  Program: {program}",
        f"  Purpose: {purpose}",
    ]

    if verbose:
        if reuse_notes:
            lines.append(f"  Reuse:   {reuse_notes}")
        if run_id:
            lines.append(f"  Run ID:  {run_id}")
        lines.append(f"  ID:      {entry.get('id', '—')}")

    return "\n".join(lines)


def print_summary(entries: list[dict]) -> None:
    if not entries:
        print("No entries found.")
        return

    total = len(entries)
    by_reuse = {}
    by_type = {}
    by_program = {}
    by_spec = {}

    for e in entries:
        r = e.get("reusability", "unknown")
        t = e.get("output_type", "unknown")
        p = e.get("program", "unknown")
        s = e.get("spec", "unknown")
        by_reuse[r] = by_reuse.get(r, 0) + 1
        by_type[t] = by_type.get(t, 0) + 1
        by_program[p] = by_program.get(p, 0) + 1
        by_spec[s] = by_spec.get(s, 0) + 1

    first = entries[0].get("timestamp", "")[:10]
    last = entries[-1].get("timestamp", "")[:10]

    print(f"\nProvenance Log Summary")
    print(f"{'─' * 40}")
    print(f"Total entries:  {total}")
    print(f"Date range:     {first} → {last}")

    print(f"\nBy reusability:")
    for k, v in sorted(by_reuse.items(), key=lambda x: -x[1]):
        print(f"  {k:<20} {v}")

    print(f"\nBy output type:")
    for k, v in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {k:<25} {v}")

    print(f"\nBy program (top 10):")
    for k, v in sorted(by_program.items(), key=lambda x: -x[1])[:10]:
        print(f"  {k:<30} {v}")

    print(f"\nBy spec:")
    for k, v in sorted(by_spec.items(), key=lambda x: -x[1]):
        print(f"  {k:<40} {v}")

    templates = [e for e in entries if e.get("reusability") == "template"]
    if templates:
        print(f"\nReusable templates ({len(templates)}):")
        for e in templates:
            print(f"  {e.get('output', '—')}  [{e.get('spec', '—')}]")
            if e.get("reuse_notes"):
                print(f"    → {e['reuse_notes']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_write(args, log_path: Path) -> None:
    entry = write_entry(
        spec=args.spec,
        output=args.output,
        output_type=args.output_type,
        program=args.program,
        purpose=args.purpose,
        reusability=args.reusability,
        reuse_notes=args.reuse_notes or "",
        quality_gate=args.quality_gate,
        run_id=args.run_id or "",
        log_path=log_path,
    )
    print(f"Entry written: {entry['id']}")
    print(fmt_entry(entry))


def cmd_query(args, log_path: Path) -> None:
    entries = load_entries(log_path)
    if not entries:
        print("Log is empty or does not exist.")
        return

    filtered = filter_entries(
        entries,
        program=args.program,
        spec=args.spec,
        reusability=args.reusability,
        output_type=args.output_type,
        since=args.since,
    )

    if not filtered:
        print("No matching entries.")
        return

    print(f"{len(filtered)} entry/entries found:\n")
    for e in filtered:
        print(fmt_entry(e, verbose=args.verbose))
        print()


def cmd_summary(args, log_path: Path) -> None:
    entries = load_entries(log_path)
    print_summary(entries)


def cmd_tail(args, log_path: Path) -> None:
    entries = load_entries(log_path)
    if not entries:
        print("Log is empty or does not exist.")
        return
    recent = entries[-(args.n):]
    for e in recent:
        print(fmt_entry(e, verbose=args.verbose))
        print()


def cmd_schema(args, log_path: Path) -> None:
    print("\nProvenance Log Entry Schema")
    print("─" * 40)
    for field, description in ENTRY_SCHEMA.items():
        print(f"  {field:<20} {description}")

    print("\nOutput Types:")
    for t in OUTPUT_TYPES:
        print(f"  {t}")

    print("\nReusability Classes:")
    for cls, description in REUSABILITY_CLASSES.items():
        print(f"\n  {cls.upper()}")
        print(f"    {description}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Provenance log for program pipeline deliverables.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--log",
        help="Path to provenance.jsonl (default: auto-detected from repo structure)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # write
    wp = subparsers.add_parser("write", help="Write a provenance entry")
    wp.add_argument("--spec",         required=True, help="Generating spec filename")
    wp.add_argument("--output",       required=True, help="Relative path to deliverable")
    wp.add_argument("--output-type",  required=True, dest="output_type",
                    choices=OUTPUT_TYPES, help="Deliverable type")
    wp.add_argument("--program",      required=True, help="Program slug")
    wp.add_argument("--purpose",      required=True, help="Why this was created")
    wp.add_argument("--reusability",  required=True,
                    choices=list(REUSABILITY_CLASSES.keys()),
                    help="Reusability classification")
    wp.add_argument("--reuse-notes",  dest="reuse_notes", default="",
                    help="Optional: what would need to change to reuse this")
    wp.add_argument("--quality-gate", dest="quality_gate", default="pass",
                    choices=["pass", "failed_once_corrected", "escalated", "skipped"],
                    help="Quality gate result")
    wp.add_argument("--run-id",       dest="run_id", default="",
                    help="Optional: pipeline run ID this belongs to")

    # query
    qp = subparsers.add_parser("query", help="Query log entries")
    qp.add_argument("--program",      help="Filter by program slug")
    qp.add_argument("--spec",         help="Filter by spec name")
    qp.add_argument("--reusability",  choices=list(REUSABILITY_CLASSES.keys()),
                    help="Filter by reusability class")
    qp.add_argument("--output-type",  dest="output_type", choices=OUTPUT_TYPES,
                    help="Filter by output type")
    qp.add_argument("--since",        help="Filter entries after date (YYYY-MM-DD)")
    qp.add_argument("--verbose", "-v", action="store_true", help="Show all fields")

    # summary
    subparsers.add_parser("summary", help="Show log statistics")

    # tail
    tp = subparsers.add_parser("tail", help="Show most recent entries")
    tp.add_argument("--n", type=int, default=10, help="Number of entries to show")
    tp.add_argument("--verbose", "-v", action="store_true", help="Show all fields")

    # schema
    subparsers.add_parser("schema", help="Show entry schema and valid values")

    args = parser.parse_args()
    log_path = resolve_log_path(args.log)

    {
        "write":   cmd_write,
        "query":   cmd_query,
        "summary": cmd_summary,
        "tail":    cmd_tail,
        "schema":  cmd_schema,
    }[args.command](args, log_path)


if __name__ == "__main__":
    main()
