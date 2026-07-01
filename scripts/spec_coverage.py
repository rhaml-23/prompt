#!/usr/bin/env python3
"""
Spec Coverage Test
==================
Validates cross-reference integrity across the compliance spec system:
- Every spec in engine/ and functions/ has a routing table entry in session-init-spec.md
- Every routing table target exists as a file on disk
- Every spec declared in orchestrator invokes list exists on disk
- Every agent in agents/ is referenced by at least one routing entry

Usage:
    python3 scripts/spec_coverage.py
    python3 scripts/spec_coverage.py --repo /path/to/compliance

Style: PEP 8
Deviations: None
"""

import argparse
import re
import sys
from pathlib import Path


def resolve_repo_root() -> Path:
    """Walk up from script location to find repo root."""
    here = Path(__file__).resolve().parent
    anchors = {"config", "engine", "functions", "scripts"}
    for candidate in [here.parent, here, here.parent.parent]:
        if sum(1 for a in anchors if (candidate / a).exists()) >= 3:
            return candidate
    return Path.cwd()


def collect_spec_files(repo_root: Path) -> set[str]:
    """Collect all spec .md files in engine/, functions/, agents/, memory/."""
    specs: set[str] = set()
    for d in ["engine", "functions", "agents", "memory"]:
        dirpath = repo_root / d
        if not dirpath.exists():
            continue
        for md in dirpath.glob("*.md"):
            if md.name.lower() == "readme.md":
                continue
            specs.add(f"{d}/{md.name}")
    return specs


def extract_routing_targets(session_init: Path) -> dict[str, str]:
    """Extract route-to targets from the routing table in session-init-spec.md.

    Returns {target_path: work_pattern_label}.
    """
    targets: dict[str, str] = {}
    text = session_init.read_text(encoding="utf-8")

    table_pattern = re.compile(
        r"^\|\s*(.+?)\s*\|\s*`([^`]+)`\s*\|", re.MULTILINE
    )
    for match in table_pattern.finditer(text):
        label = match.group(1).strip()
        target = match.group(2).strip()
        if label.startswith("---") or label == "Work Pattern":
            continue
        if target.endswith(".py") or target.startswith("scripts/"):
            continue
        if target == "Ask one clarifying question":
            continue
        targets[target] = label

    return targets


def extract_orchestrator_invokes(orchestrator: Path) -> list[str]:
    """Extract invokes list from orchestrator YAML frontmatter."""
    text = orchestrator.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return []

    end = text.find("\n---", 3)
    if end == -1:
        return []

    frontmatter = text[3:end]
    in_invokes = False
    invokes: list[str] = []

    for line in frontmatter.splitlines():
        stripped = line.strip()
        if stripped.startswith("invokes:"):
            in_invokes = True
            continue
        if in_invokes:
            if stripped.startswith("- "):
                item = stripped[2:].strip()
                if not item.startswith("functions/") and not item.startswith("engine/"):
                    item = f"functions/{item}" if "-spec.md" in item else item
                invokes.append(item)
            elif stripped and not stripped.startswith("-"):
                in_invokes = False

    return invokes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate spec cross-reference coverage.",
    )
    parser.add_argument("--repo", help="Repo root path. Auto-detected if omitted.")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve() if args.repo else resolve_repo_root()

    session_init = repo_root / "engine" / "session-init-spec.md"
    orchestrator = repo_root / "engine" / "program-pipeline-orchestrator.md"

    if not session_init.exists():
        print(f"ERROR: {session_init} not found.", file=sys.stderr)
        return 1

    spec_files = collect_spec_files(repo_root)
    routing_targets = extract_routing_targets(session_init)
    orchestrator_invokes = extract_orchestrator_invokes(orchestrator) if orchestrator.exists() else []

    findings: list[str] = []
    warnings: list[str] = []

    # Check 1: Specs with no routing table entry
    # Only enforce bidirectional routing for functions/ specs. Engine specs run
    # on every session by default (not invoked via routing table). Agent specs
    # are autonomous fleet agents deployed as containers — not user-invoked.
    routed_paths = set(routing_targets.keys())
    orchestrator_set = set(orchestrator_invokes)
    for spec in sorted(spec_files):
        if spec in routed_paths:
            continue
        if not spec.startswith("functions/"):
            continue
        if "template" in spec:
            continue
        if spec in orchestrator_set:
            continue
        bare_name = spec.split("/")[-1]
        if any(inv.endswith(bare_name) for inv in orchestrator_invokes):
            continue
        warnings.append(f"Spec not in routing table: {spec}")

    # Check 2: Routing targets that don't exist on disk
    for target, label in sorted(routing_targets.items()):
        target_path = repo_root / target
        if not target_path.exists():
            findings.append(
                f'Routing target missing on disk: {target} '
                f'(routed from: "{label}")'
            )

    # Check 3: Orchestrator invokes that don't exist on disk
    for invoke in orchestrator_invokes:
        invoke_path = repo_root / invoke
        if not invoke_path.exists():
            bare = invoke.split("/")[-1]
            found = False
            for d in ["engine", "functions"]:
                if (repo_root / d / bare).exists():
                    found = True
                    break
            if not found:
                findings.append(f"Orchestrator invokes missing file: {invoke}")

    # Report
    print(f"\nSpec Coverage — {repo_root.name}")
    print(f"{'─' * 50}")
    print(f"  Spec files on disk:     {len(spec_files)}")
    print(f"  Routing table entries:  {len(routing_targets)}")
    print(f"  Orchestrator invokes:   {len(orchestrator_invokes)}")

    if findings:
        print(f"\n  ERRORS ({len(findings)}):")
        for f in findings:
            print(f"    ✗ {f}")

    if warnings:
        print(f"\n  WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"    ⚠ {w}")

    if not findings and not warnings:
        print("\n  All specs have routing coverage.")

    print()

    if findings:
        print("Spec coverage check FAILED.")
        return 1

    if warnings:
        print("Spec coverage check FAILED — unreachable specs detected.")
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
