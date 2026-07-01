#!/usr/bin/env python3
"""
Frontmatter Validator
=====================
Validates YAML frontmatter in spec and agent definition files against the
canonical schema defined in config/spec-frontmatter-schema.yaml.

Checks:
- Frontmatter presence and YAML parse-ability
- Required fields present
- governed_by uses correct relative path (no leading slashes, no bare filenames)
- Path references use relative paths from repo root
- Domain values are from the allowed set
- Version format is valid

Usage:
    python scripts/validate_frontmatter.py
    python scripts/validate_frontmatter.py --file functions/program-intake-spec.md
    python scripts/validate_frontmatter.py --dir engine/
    python scripts/validate_frontmatter.py --strict

Style: PEP 8
Deviations: None
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


SPEC_REQUIRED_FIELDS = [
    "resource_type",
    "version",
    "domain",
    "triggers",
    "inputs",
    "outputs",
    "governed_by",
]

AGENT_REQUIRED_FIELDS = [
    "name",
    "description",
    "model",
]

ALLOWED_DOMAINS = {
    "program-management",
    "session-management",
    "agent-initialization",
    "portfolio-management",
    "agent-infrastructure",
    "quality-assurance",
    "compliance",
    "communications",
    "vendor-management",
    "risk-management",
    "intelligence",
}

GOVERNED_BY_CANONICAL = "config/constitution.md"

VERSION_PATTERN = re.compile(r"^\d+\.\d+$")

ALLOWED_AGENT_ROLES = {
    "program",
    "framework",
    "evidence",
    "intelligence",
    "communications",
    "audit",
    "review",
    "coordination",
    "infrastructure",
}

ALLOWED_DEPLOYMENT_MODES = {"ide", "deployed", "both"}

SPEC_DIRS = ["engine", "functions"]
AGENT_DIRS = ["agents"]


def resolve_repo_root() -> Path:
    """Walk up from script location to find repo root."""
    here = Path(__file__).resolve().parent
    anchors = {"config", "engine", "functions", "scripts"}
    for candidate in [here.parent, here, here.parent.parent]:
        if sum(1 for a in anchors if (candidate / a).exists()) >= 3:
            return candidate
    return Path.cwd()


def extract_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Extract YAML frontmatter from a markdown file.

    Returns (parsed_dict, error_message). If no frontmatter found or parse
    fails, returns (None, reason).
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"Cannot read file: {exc}"

    if not text.startswith("---"):
        return None, "No YAML frontmatter block (file does not start with ---)"

    end = text.find("\n---", 3)
    if end == -1:
        return None, "Unclosed frontmatter block (no closing ---)"

    raw = text[3:end].strip()
    if not raw:
        return None, "Empty frontmatter block"

    if yaml is not None:
        try:
            parsed = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            return None, f"YAML parse error: {exc}"
    else:
        parsed = _fallback_parse(raw)

    if not isinstance(parsed, dict):
        return None, f"Frontmatter is not a mapping (got {type(parsed).__name__})"

    return parsed, None


def _fallback_parse(raw: str) -> dict[str, Any]:
    """Minimal YAML-like parser when PyYAML is not available.

    Handles simple key: value pairs and key: [list items starting with -].
    Good enough for validation; not a full YAML parser.
    """
    result: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- "):
            if current_key and current_list is not None:
                current_list.append(stripped[2:].strip())
            continue

        match = re.match(r"^(\w[\w_]*)\s*:\s*(.*)", stripped)
        if match:
            if current_key and current_list is not None:
                result[current_key] = current_list

            key = match.group(1)
            value = match.group(2).strip()

            if not value:
                current_key = key
                current_list = []
            else:
                current_key = None
                current_list = None
                if value in ("true", "True"):
                    result[key] = True
                elif value in ("false", "False"):
                    result[key] = False
                else:
                    result[key] = value.strip('"').strip("'")

    if current_key and current_list is not None:
        result[current_key] = current_list

    return result


def validate_spec(fm: dict[str, Any], rel_path: str) -> list[str]:
    """Validate a spec frontmatter dict. Returns list of findings."""
    findings: list[str] = []

    for field in SPEC_REQUIRED_FIELDS:
        if field not in fm:
            findings.append(f"Missing required field: {field}")

    if "resource_type" in fm and fm["resource_type"] != "spec":
        findings.append(
            f'resource_type must be "spec", got "{fm["resource_type"]}"'
        )

    if "version" in fm:
        v = str(fm["version"])
        if not VERSION_PATTERN.match(v):
            findings.append(
                f'version must match N.N format, got "{v}"'
            )

    if "domain" in fm and fm["domain"] not in ALLOWED_DOMAINS:
        findings.append(
            f'domain "{fm["domain"]}" not in allowed set: '
            f'{sorted(ALLOWED_DOMAINS)}'
        )

    if "governed_by" in fm:
        gb = fm["governed_by"]
        if gb != GOVERNED_BY_CANONICAL:
            findings.append(
                f'governed_by must be "{GOVERNED_BY_CANONICAL}", '
                f'got "{gb}"'
            )

    for field in ["invokes", "depends_on", "depends_on_optional", "invoked_by"]:
        if field not in fm:
            continue
        refs = fm[field] if isinstance(fm[field], list) else [fm[field]]
        for ref in refs:
            if not isinstance(ref, str):
                continue
            if ref.startswith("/"):
                findings.append(
                    f'{field} path "{ref}" uses leading slash — '
                    f"use relative path from repo root"
                )
            if ref.endswith(".md") and "/" not in ref:
                findings.append(
                    f'{field} path "{ref}" is a bare filename — '
                    f"use relative path with directory prefix "
                    f"(e.g. functions/{ref} or engine/{ref})"
                )

    if "agent_role" in fm and fm["agent_role"] not in ALLOWED_AGENT_ROLES:
        findings.append(
            f'agent_role "{fm["agent_role"]}" not in allowed set: '
            f'{sorted(ALLOWED_AGENT_ROLES)}'
        )

    if "deployment_modes" in fm:
        modes = fm["deployment_modes"]
        if isinstance(modes, list):
            for mode in modes:
                if mode not in ALLOWED_DEPLOYMENT_MODES:
                    findings.append(
                        f'deployment_modes value "{mode}" not in allowed set: '
                        f'{sorted(ALLOWED_DEPLOYMENT_MODES)}'
                    )

    if "triggers" in fm:
        t = fm["triggers"]
        if not isinstance(t, list) or not t:
            findings.append("triggers must be a non-empty list")

    if "inputs" in fm:
        i = fm["inputs"]
        if not isinstance(i, list):
            findings.append("inputs must be a list")

    if "outputs" in fm:
        o = fm["outputs"]
        if not isinstance(o, list):
            findings.append("outputs must be a list")

    return findings


def validate_agent(fm: dict[str, Any], rel_path: str) -> list[str]:
    """Validate an agent definition frontmatter dict."""
    findings: list[str] = []

    for field in AGENT_REQUIRED_FIELDS:
        if field not in fm:
            findings.append(f"Missing required field: {field}")

    if "governed_by" in fm and fm["governed_by"] != GOVERNED_BY_CANONICAL:
        findings.append(
            f'governed_by must be "{GOVERNED_BY_CANONICAL}", '
            f'got "{fm["governed_by"]}"'
        )

    return findings


def collect_files(
    repo_root: Path,
    target_file: str | None = None,
    target_dir: str | None = None,
) -> list[tuple[Path, str]]:
    """Collect (absolute_path, file_type) tuples for validation.

    file_type is "spec" or "agent".
    """
    files: list[tuple[Path, str]] = []

    if target_file:
        p = repo_root / target_file
        if not p.exists():
            p = Path(target_file)
        parent = p.parent.name
        ftype = "agent" if parent in AGENT_DIRS else "spec"
        files.append((p, ftype))
        return files

    dirs_to_scan: list[tuple[str, str]] = []

    if target_dir:
        d = target_dir.rstrip("/")
        ftype = "agent" if d in AGENT_DIRS else "spec"
        dirs_to_scan.append((d, ftype))
    else:
        for d in SPEC_DIRS:
            dirs_to_scan.append((d, "spec"))
        for d in AGENT_DIRS:
            dirs_to_scan.append((d, "agent"))

    for dirname, ftype in dirs_to_scan:
        dirpath = repo_root / dirname
        if not dirpath.exists():
            continue
        for md in sorted(dirpath.glob("*.md")):
            if md.name.lower() == "readme.md":
                continue
            files.append((md, ftype))

    return files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate YAML frontmatter in spec and agent files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        help="Validate a single file (relative to repo root).",
    )
    parser.add_argument(
        "--dir",
        help="Validate all .md files in a directory (e.g. engine/, functions/).",
    )
    parser.add_argument(
        "--repo",
        help="Repo root path. Auto-detected if omitted.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (non-zero exit on any finding).",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve() if args.repo else resolve_repo_root()
    files = collect_files(repo_root, args.file, args.dir)

    if not files:
        print("No files found to validate.", file=sys.stderr)
        return 1

    total_findings = 0
    total_errors = 0
    results: list[tuple[str, list[str], str | None]] = []

    for fpath, ftype in files:
        rel = str(fpath.relative_to(repo_root)) if fpath.is_relative_to(repo_root) else str(fpath)
        fm, parse_error = extract_frontmatter(fpath)

        if parse_error:
            results.append((rel, [parse_error], None))
            total_errors += 1
            continue

        assert fm is not None
        if ftype == "agent":
            findings = validate_agent(fm, rel)
        else:
            findings = validate_spec(fm, rel)

        results.append((rel, findings, ftype))
        total_findings += len(findings)
        if findings:
            total_errors += 1

    print(f"\nFrontmatter Validation — {repo_root.name}")
    print(f"{'─' * 50}")

    for rel, findings, ftype in results:
        if not findings:
            print(f"  ✓ {rel}")
        else:
            print(f"  ✗ {rel}")
            for f in findings:
                print(f"      → {f}")

    print(f"\n{'─' * 50}")
    print(
        f"  Files: {len(results)}  |  "
        f"Pass: {len(results) - total_errors}  |  "
        f"Fail: {total_errors}  |  "
        f"Findings: {total_findings}"
    )

    if total_errors > 0:
        print("\nFrontmatter validation FAILED.")
        return 1

    print("\nAll files passed frontmatter validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
