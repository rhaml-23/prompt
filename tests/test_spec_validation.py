"""
Spec Validation Tests
=====================
Verifies structural integrity of the spec system:
- All spec files have valid YAML frontmatter
- All frontmatter conforms to the canonical schema
- Cross-references between specs resolve to existing files
- Routing table is complete and consistent
- Agent definitions have valid frontmatter

Usage:
    python -m pytest tests/test_spec_validation.py -v
    python -m pytest tests/test_spec_validation.py -v -k frontmatter
"""

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _spec_files():
    """Collect all spec .md files in engine/ and functions/."""
    specs = []
    for d in ["engine", "functions"]:
        dirpath = REPO_ROOT / d
        if not dirpath.exists():
            continue
        for md in sorted(dirpath.glob("*.md")):
            if md.name.lower() == "readme.md":
                continue
            specs.append(md)
    return specs


def _agent_files():
    """Collect all agent .md files in agents/."""
    dirpath = REPO_ROOT / "agents"
    if not dirpath.exists():
        return []
    return [md for md in sorted(dirpath.glob("*.md")) if md.name.lower() != "readme.md"]


def _extract_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    try:
        import yaml
        return yaml.safe_load(text[3:end])
    except ImportError:
        return None


class TestFrontmatterPresence:
    @pytest.mark.parametrize("spec_file", _spec_files(), ids=lambda p: p.name)
    def test_spec_has_frontmatter(self, spec_file):
        text = spec_file.read_text(encoding="utf-8")
        assert text.startswith("---"), f"{spec_file.name} missing YAML frontmatter"
        end = text.find("\n---", 3)
        assert end > 0, f"{spec_file.name} has unclosed frontmatter"

    @pytest.mark.parametrize("agent_file", _agent_files(), ids=lambda p: p.name)
    def test_agent_has_frontmatter(self, agent_file):
        text = agent_file.read_text(encoding="utf-8")
        assert text.startswith("---"), f"{agent_file.name} missing YAML frontmatter"


class TestFrontmatterSchema:
    REQUIRED_SPEC_FIELDS = ["resource_type", "version", "domain", "triggers", "inputs", "outputs", "governed_by"]
    REQUIRED_AGENT_FIELDS = ["name", "description", "model"]

    @pytest.mark.parametrize("spec_file", _spec_files(), ids=lambda p: p.name)
    def test_spec_required_fields(self, spec_file):
        fm = _extract_frontmatter(spec_file)
        if fm is None:
            pytest.skip("Could not parse frontmatter (PyYAML may not be installed)")
        for field in self.REQUIRED_SPEC_FIELDS:
            assert field in fm, f"{spec_file.name} missing required field: {field}"

    @pytest.mark.parametrize("spec_file", _spec_files(), ids=lambda p: p.name)
    def test_spec_governed_by(self, spec_file):
        fm = _extract_frontmatter(spec_file)
        if fm is None:
            pytest.skip("Could not parse frontmatter")
        assert fm.get("governed_by") == "config/constitution.md", (
            f"{spec_file.name}: governed_by must be 'config/constitution.md'"
        )

    @pytest.mark.parametrize("spec_file", _spec_files(), ids=lambda p: p.name)
    def test_spec_no_bare_paths(self, spec_file):
        fm = _extract_frontmatter(spec_file)
        if fm is None:
            pytest.skip("Could not parse frontmatter")
        for field in ["invokes", "depends_on", "depends_on_optional", "invoked_by"]:
            if field not in fm:
                continue
            refs = fm[field] if isinstance(fm[field], list) else [fm[field]]
            for ref in refs:
                if isinstance(ref, str) and ref.endswith(".md"):
                    assert "/" in ref, (
                        f"{spec_file.name}: {field} has bare filename '{ref}' — "
                        f"use relative path with directory prefix"
                    )

    @pytest.mark.parametrize("agent_file", _agent_files(), ids=lambda p: p.name)
    def test_agent_required_fields(self, agent_file):
        fm = _extract_frontmatter(agent_file)
        if fm is None:
            pytest.skip("Could not parse frontmatter")
        for field in self.REQUIRED_AGENT_FIELDS:
            assert field in fm, f"{agent_file.name} missing required field: {field}"


class TestCrossReferences:
    def test_orchestrator_invokes_exist(self):
        orchestrator = REPO_ROOT / "engine" / "program-pipeline-orchestrator.md"
        fm = _extract_frontmatter(orchestrator)
        if fm is None:
            pytest.skip("Could not parse frontmatter")
        for invoke in fm.get("invokes", []):
            path = REPO_ROOT / invoke
            if not path.exists():
                bare = invoke.split("/")[-1]
                found = any(
                    (REPO_ROOT / d / bare).exists()
                    for d in ["engine", "functions"]
                )
                assert found, f"Orchestrator invokes missing file: {invoke}"

    def test_spec_invoked_by_exists(self):
        for spec_file in _spec_files():
            fm = _extract_frontmatter(spec_file)
            if fm is None or "invoked_by" not in fm:
                continue
            refs = fm["invoked_by"] if isinstance(fm["invoked_by"], list) else [fm["invoked_by"]]
            for ref in refs:
                if isinstance(ref, str) and ref.endswith(".md"):
                    path = REPO_ROOT / ref
                    assert path.exists(), (
                        f"{spec_file.name}: invoked_by references missing file: {ref}"
                    )

    def test_routing_targets_exist(self):
        session_init = REPO_ROOT / "engine" / "session-init-spec.md"
        if not session_init.exists():
            pytest.skip("session-init-spec.md not found")
        text = session_init.read_text(encoding="utf-8")
        table_pattern = re.compile(r"^\|\s*(.+?)\s*\|\s*`([^`]+)`\s*\|", re.MULTILINE)
        for match in table_pattern.finditer(text):
            label = match.group(1).strip()
            target = match.group(2).strip()
            if label.startswith("---") or label == "Work Pattern":
                continue
            if target.endswith(".py") or target.startswith("scripts/"):
                continue
            if target == "Ask one clarifying question":
                continue
            path = REPO_ROOT / target
            assert path.exists(), (
                f"Routing target missing on disk: {target} (from: '{label}')"
            )


class TestSchemas:
    def _load_schema(self, name: str) -> dict:
        path = REPO_ROOT / "config" / "schemas" / name
        assert path.exists(), f"Schema file missing: {name}"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_portfolio_schema_valid(self):
        schema = self._load_schema("portfolio-state.schema.json")
        assert schema.get("$schema"), "Missing $schema field"
        assert "programs" in schema.get("properties", {}), "Missing programs property"

    def test_run_schema_valid(self):
        schema = self._load_schema("run-output.schema.json")
        assert "run_manifest" in schema.get("required", [])

    def test_message_schema_valid(self):
        schema = self._load_schema("agent-message.schema.json")
        assert "type" in schema.get("required", [])

    def test_audit_schema_valid(self):
        schema = self._load_schema("audit-entry.schema.json")
        assert "prior_hash" in schema.get("properties", {})
