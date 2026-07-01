#!/usr/bin/env python3
"""
Integrity Check
===============
Validates that protected system files retain all required headings.
Run before modifying constitution.md, program-pipeline-orchestrator.md,
or quality-gate-spec.md — and after any LLM-assisted edits to those files.

If a heading is missing, the script prints a restoration notice for the
agent and exits non-zero so it cannot be silently skipped in pipelines.

Usage:
    python scripts/integrity_check.py
    python scripts/integrity_check.py --file constitution.md
    python scripts/integrity_check.py --fix-prompt   # print restoration instructions

Style: PEP 8
Deviations: None
"""

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Manifest — required headings per protected file
# Update this manifest whenever a heading is intentionally added or renamed.
# Never remove entries without also removing the corresponding heading from
# the live file and incrementing the file's version number.
# ---------------------------------------------------------------------------

MANIFEST: dict[str, list[str]] = {
    "constitution.md": [
        "# Professional Intent Constitution",
        "## Preamble",
        "## Article I — Core Values",
        "### 1.1 Lasting Value Over Short-Term Wins",
        "### 1.2 Trusted Relationships",
        "### 1.3 Customer Protection — From Action and Inaction",
        "### 1.4 Greatest Good",
        "### 1.5 Efficiency Without Sacrificing Quality",
        "## Article II — Decision Hierarchy",
        "## Article III — Operational Philosophy",
        "### 3.1 The First Way — Optimize for Flow",
        "### 3.2 The Second Way — Amplify Feedback",
        "### 3.3 The Third Way — Enable Continual Learning",
        "## Article IV — Behavioral Mandates",
        "### 4.1 Say the True Thing",
        "### 4.2 Protect the Downstream",
        "### 4.3 Prefer Reversibility",
        "### 4.4 Surface Uncertainty",
        "### 4.5 Acknowledge Inaction Risk",
        "### 4.6 Resolve Before Interrupting",
        "### 4.7 Run Integrity Check Before Editing Protected Files",
        "### 4.8 Refer to This Constitution",
        "### 4.9 Surface Drift and Avoidance",
        "### 4.10 Push Back on Values Drift",
        "### 4.11 Lead program manager Communication Preferences",
        "### 4.12 Research and Synthesis",
        "### 4.13 Format-to-Information-Type Matching",
        "### 4.14 Good Enough Calibration",
        "### 4.15 Channel Calibration",
        "### 4.16 External Signal Synthesis",
        "## Article V — Behavioral Prohibitions",
        "### 5.1 Never Optimize Metrics at the Expense of Outcomes",
        "### 5.2 Never Suppress a Risk to Preserve Comfort",
        "### 5.3 Never Pass Known Defects Forward",
        "### 5.4 Never Sacrifice Quality for Speed",
        "### 5.5 Never Act on One-Way Door Decisions Without Lead program manager Approval",
        "## Article VI — The Alignment Test",
        "## Article VII — Authority Boundaries",
        "### 7.1 Autonomous Action (no lead program manager approval required)",
        "### 7.2 Escalate to Lead program manager (approval required before proceeding)",
        "### 7.3 Escalation Protocol",
        "## Article VIII — Constitutional Amendments",
        "## Quick Reference Card",
    ],
    "program-pipeline-orchestrator.md": [
        "# Program Pipeline Orchestrator",
        "## Constitutional Preload",
        "## How to Use This Spec",
        "### Step 1 — Set Your Parameters",
        "### Step 2 — Provide Input",
        "### Step 3 — Trigger Execution",
        "## Persona Definition",
        "## Execution Logic",
        "### Phase 0 — Constitutional Alignment Check",
        "### Phase 1 — State Assessment",
        "#### 1a — Prior Run Check",
        "#### 1b — Triage (runs only when no prior state exists)",
        "#### 1c — Routing Decision",
        "### Phase 2 — Intake Pass (conditional)",
        "### Phase 3 — Monitoring Pass (conditional)",
        "### Phase 4 — Vendor Pass (conditional)",
        "### Phase 5 — Constitutional Alignment Test",
        "### Phase 6 — Quality Gate",
        "### Phase 7 — Unified Output Assembly",
        "## Provenance Logging",
        "## Next Run Cadence Defaults",
        "## Companion Specs",
    ],
    "quality-gate-spec.md": [
        "# Quality Gate Spec",
        "## Constitutional Guidance",
        "## Persona Definition",
        "## Validation Pipeline",
        "## Gate 1 — Constitutional Alignment",
        "## Gate 2 — Structural Completeness",
        "## Gate 3 — Format Standards",
        "## Gate 4 — Tone Standards",
        "### Directness",
        "### Authority",
        "### Economy",
        "### Tone Scoring",
        "## Gate 5 — Output Type Specific Checks",
        "## Regeneration Protocol",
        "## Validation Report Format",
        "## Output Preferences Summary",
    ],
}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def extract_headings(path: Path) -> list[str]:
    """Extract all markdown headings from a file."""
    headings = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip()
            if re.match(r"^#{1,6} ", stripped):
                headings.append(stripped)
    return headings


def check_file(filename: str, file_path: Path) -> list[str]:
    """Return list of required headings missing from file."""
    if not file_path.exists():
        return [f"[FILE NOT FOUND: {file_path}]"]

    required = MANIFEST.get(filename, [])
    if not required:
        return []

    present = set(extract_headings(file_path))
    return [h for h in required if h not in present]


def find_file(filename: str, repo_root: Path) -> Path | None:
    """Search repo recursively for filename."""
    matches = list(repo_root.rglob(filename))
    if not matches:
        return None
    # Prefer shallowest match
    return sorted(matches, key=lambda p: len(p.parts))[0]


def resolve_repo_root() -> Path:
    """Walk up from script location to find repo root."""
    here = Path(__file__).resolve().parent
    anchors = {"constitution.md", ".cursorrules", ".git", "specs", "runs"}
    for candidate in [here, here.parent, here.parent.parent]:
        if any((candidate / a).exists() for a in anchors):
            return candidate
    return Path.cwd()


def print_restoration_notice(filename: str, missing: list[str]) -> None:
    """Print agent-facing restoration instructions."""
    print(f"\n{'='*60}")
    print(f"INTEGRITY FAILURE — {filename}")
    print(f"{'='*60}")
    print(f"\n{len(missing)} required heading(s) missing:\n")
    for h in missing:
        print(f"  {h}")
    print(f"""
AGENT INSTRUCTION:
  The headings above have been removed from {filename}.
  This is a regression. You must restore each missing section
  before proceeding with any other edits to this file.

  For each missing heading:
  1. Re-insert it at the correct position in the document
  2. Restore the section content from the manifest or prior
     git history if available
  3. Re-run this check to confirm all headings are present
  4. Notify the lead program manager that content was missing and restored

PRINCIPAL NOTICE:
  One or more required sections were missing from {filename}.
  They have been flagged for restoration. Review the file after
  the agent completes restoration to confirm content integrity.
""")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate required headings in protected system files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        help="Check a single file by name (e.g. constitution.md). "
             "Checks all protected files if omitted.",
    )
    parser.add_argument(
        "--repo",
        help="Repo root path. Auto-detected if omitted.",
    )
    parser.add_argument(
        "--list-manifest",
        action="store_true",
        help="Print the full heading manifest and exit.",
    )
    args = parser.parse_args()

    if args.list_manifest:
        for filename, headings in MANIFEST.items():
            print(f"\n{filename} ({len(headings)} required headings):")
            for h in headings:
                print(f"  {h}")
        return 0

    repo_root = Path(args.repo).resolve() if args.repo else resolve_repo_root()
    targets = [args.file] if args.file else list(MANIFEST.keys())

    all_passed = True
    results = []

    for filename in targets:
        if filename not in MANIFEST:
            print(f"WARNING: {filename} is not a protected file — skipping.",
                  file=sys.stderr)
            continue

        file_path = find_file(filename, repo_root)
        if not file_path:
            print(f"ERROR: {filename} not found anywhere under {repo_root}",
                  file=sys.stderr)
            all_passed = False
            results.append((filename, [f"FILE NOT FOUND"]))
            continue

        missing = check_file(filename, file_path)
        results.append((filename, missing))

        if missing:
            all_passed = False

    # Summary
    print(f"\nIntegrity Check — {repo_root.name}")
    print(f"{'─'*40}")
    for filename, missing in results:
        status = "✓ PASS" if not missing else f"✗ FAIL ({len(missing)} missing)"
        print(f"  {filename:<45} {status}")

    # Detailed restoration notices for failures
    for filename, missing in results:
        if missing and missing != ["FILE NOT FOUND"]:
            print_restoration_notice(filename, missing)

    print()
    if all_passed:
        print("All protected files passed integrity check.")
        return 0
    else:
        print("Integrity check FAILED. See restoration notices above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
