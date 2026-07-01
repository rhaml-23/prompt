"""
Unit tests for the four CI validation scripts.

Each test class targets one script, importing its internal functions directly
(no subprocess) so that coverage is attributed to the source files and
failure messages point to exact lines.

Coverage targets:
    scripts/integrity_check.py
    scripts/validate_frontmatter.py
    scripts/validate_schema_drift.py
    scripts/spec_coverage.py
"""

import importlib
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make scripts/ importable regardless of working directory
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ===========================================================================
# integrity_check
# ===========================================================================

class TestIntegrityCheck:
    """Tests for scripts/integrity_check.py."""

    @pytest.fixture(autouse=True)
    def _import(self):
        import integrity_check as ic
        self.ic = ic

    def _write(self, tmp_path: Path, content: str) -> Path:
        p = tmp_path / "constitution.md"
        p.write_text(content, encoding="utf-8")
        return p

    # --- extract_headings ---

    def test_extract_headings_finds_all_levels(self, tmp_path):
        p = self._write(tmp_path, "# H1\n## H2\n### H3\nsome body\n")
        assert self.ic.extract_headings(p) == ["# H1", "## H2", "### H3"]

    def test_extract_headings_empty_file(self, tmp_path):
        p = tmp_path / "empty.md"
        p.write_text("", encoding="utf-8")
        assert self.ic.extract_headings(p) == []

    def test_extract_headings_ignores_body_text(self, tmp_path):
        p = self._write(tmp_path, "# Title\nThis is not a heading.\n#also not\n")
        assert self.ic.extract_headings(p) == ["# Title"]

    def test_extract_headings_strips_trailing_whitespace(self, tmp_path):
        p = self._write(tmp_path, "# Title   \n## Sub  \n")
        assert self.ic.extract_headings(p) == ["# Title", "## Sub"]

    # --- check_file ---

    def test_check_file_all_present(self, tmp_path):
        content = "# H1\n## H2\n### H3\n"
        p = tmp_path / "test.md"
        p.write_text(content, encoding="utf-8")
        manifest = {"test.md": ["# H1", "## H2", "### H3"]}
        original = self.ic.MANIFEST.copy()
        self.ic.MANIFEST["test.md"] = manifest["test.md"]
        try:
            missing = self.ic.check_file("test.md", p)
        finally:
            self.ic.MANIFEST.clear()
            self.ic.MANIFEST.update(original)
        assert missing == []

    def test_check_file_one_missing(self, tmp_path):
        p = tmp_path / "constitution.md"
        p.write_text("# Professional Intent Constitution\n## Preamble\n", encoding="utf-8")
        missing = self.ic.check_file("constitution.md", p)
        assert "## Article I — Core Values" in missing

    def test_check_file_file_not_found(self, tmp_path):
        missing = self.ic.check_file("constitution.md", tmp_path / "nonexistent.md")
        assert any("FILE NOT FOUND" in m for m in missing)

    def test_check_file_match_is_exact_not_substring(self, tmp_path):
        p = tmp_path / "constitution.md"
        p.write_text("# Professional Intent Constitutionextra\n", encoding="utf-8")
        missing = self.ic.check_file("constitution.md", p)
        assert "# Professional Intent Constitution" in missing

    # --- find_file ---

    def test_find_file_finds_file(self, tmp_path):
        (tmp_path / "sub").mkdir()
        target = tmp_path / "sub" / "constitution.md"
        target.write_text("content", encoding="utf-8")
        found = self.ic.find_file("constitution.md", tmp_path)
        assert found == target

    def test_find_file_returns_none_when_missing(self, tmp_path):
        assert self.ic.find_file("doesnotexist.md", tmp_path) is None

    def test_find_file_prefers_shallowest(self, tmp_path):
        shallow = tmp_path / "constitution.md"
        shallow.write_text("a", encoding="utf-8")
        deep_dir = tmp_path / "a" / "b"
        deep_dir.mkdir(parents=True)
        deep = deep_dir / "constitution.md"
        deep.write_text("b", encoding="utf-8")
        found = self.ic.find_file("constitution.md", tmp_path)
        assert found == shallow


# ===========================================================================
# validate_frontmatter
# ===========================================================================

class TestValidateFrontmatter:
    """Tests for scripts/validate_frontmatter.py."""

    @pytest.fixture(autouse=True)
    def _import(self):
        import validate_frontmatter as vf
        self.vf = vf

    def _spec_file(self, tmp_path: Path, content: str) -> Path:
        p = tmp_path / "test-spec.md"
        p.write_text(content, encoding="utf-8")
        return p

    VALID_SPEC_FM = """\
---
resource_type: spec
version: "1.0"
domain: compliance
triggers:
  - manual
inputs:
  - program_state
outputs:
  - report
governed_by: config/constitution.md
---
# Body
"""

    VALID_AGENT_FM = """\
---
name: test-agent
description: A test agent.
model: claude-3
governed_by: config/constitution.md
---
# Body
"""

    # --- extract_frontmatter ---

    def test_extract_frontmatter_valid(self, tmp_path):
        p = self._spec_file(tmp_path, self.VALID_SPEC_FM)
        fm, err = self.vf.extract_frontmatter(p)
        assert err is None
        assert fm["resource_type"] == "spec"

    def test_extract_frontmatter_no_block(self, tmp_path):
        p = self._spec_file(tmp_path, "# No frontmatter here\n")
        fm, err = self.vf.extract_frontmatter(p)
        assert fm is None
        assert "No YAML frontmatter" in err

    def test_extract_frontmatter_unclosed_block(self, tmp_path):
        p = self._spec_file(tmp_path, "---\nkey: value\n")
        fm, err = self.vf.extract_frontmatter(p)
        assert fm is None
        assert "Unclosed" in err

    def test_extract_frontmatter_empty_block(self, tmp_path):
        p = self._spec_file(tmp_path, "---\n\n---\n# Body\n")
        fm, err = self.vf.extract_frontmatter(p)
        assert fm is None
        assert "Empty" in err

    # --- validate_spec ---

    def test_validate_spec_clean(self, tmp_path):
        p = self._spec_file(tmp_path, self.VALID_SPEC_FM)
        fm, _ = self.vf.extract_frontmatter(p)
        findings = self.vf.validate_spec(fm, "test-spec.md")
        assert findings == []

    def test_validate_spec_missing_required_field(self, tmp_path):
        content = self.VALID_SPEC_FM.replace("governed_by: config/constitution.md\n", "")
        p = self._spec_file(tmp_path, content)
        fm, _ = self.vf.extract_frontmatter(p)
        findings = self.vf.validate_spec(fm, "test-spec.md")
        assert any("governed_by" in f for f in findings)

    def test_validate_spec_wrong_resource_type(self, tmp_path):
        content = self.VALID_SPEC_FM.replace("resource_type: spec", "resource_type: widget")
        p = self._spec_file(tmp_path, content)
        fm, _ = self.vf.extract_frontmatter(p)
        findings = self.vf.validate_spec(fm, "test-spec.md")
        assert any("resource_type" in f for f in findings)

    def test_validate_spec_bad_version_format(self, tmp_path):
        content = self.VALID_SPEC_FM.replace('version: "1.0"', 'version: "v1"')
        p = self._spec_file(tmp_path, content)
        fm, _ = self.vf.extract_frontmatter(p)
        findings = self.vf.validate_spec(fm, "test-spec.md")
        assert any("version" in f for f in findings)

    def test_validate_spec_invalid_domain(self, tmp_path):
        content = self.VALID_SPEC_FM.replace("domain: compliance", "domain: notadomain")
        p = self._spec_file(tmp_path, content)
        fm, _ = self.vf.extract_frontmatter(p)
        findings = self.vf.validate_spec(fm, "test-spec.md")
        assert any("domain" in f for f in findings)

    def test_validate_spec_wrong_governed_by(self, tmp_path):
        content = self.VALID_SPEC_FM.replace(
            "governed_by: config/constitution.md",
            "governed_by: /constitution.md",
        )
        p = self._spec_file(tmp_path, content)
        fm, _ = self.vf.extract_frontmatter(p)
        findings = self.vf.validate_spec(fm, "test-spec.md")
        assert any("governed_by" in f for f in findings)

    def test_validate_spec_invokes_leading_slash(self, tmp_path):
        # invokes must be inside the frontmatter block (before the closing ---)
        content = (
            "---\n"
            "resource_type: spec\n"
            'version: "1.0"\n'
            "domain: compliance\n"
            "triggers:\n  - manual\n"
            "inputs:\n  - program_state\n"
            "outputs:\n  - report\n"
            "governed_by: config/constitution.md\n"
            "invokes:\n  - /functions/foo-spec.md\n"
            "---\n# Body\n"
        )
        p = self._spec_file(tmp_path, content)
        fm, _ = self.vf.extract_frontmatter(p)
        findings = self.vf.validate_spec(fm, "test-spec.md")
        assert any("leading slash" in f for f in findings)

    def test_validate_spec_invokes_bare_filename(self, tmp_path):
        content = (
            "---\n"
            "resource_type: spec\n"
            'version: "1.0"\n'
            "domain: compliance\n"
            "triggers:\n  - manual\n"
            "inputs:\n  - program_state\n"
            "outputs:\n  - report\n"
            "governed_by: config/constitution.md\n"
            "invokes:\n  - foo-spec.md\n"
            "---\n# Body\n"
        )
        p = self._spec_file(tmp_path, content)
        fm, _ = self.vf.extract_frontmatter(p)
        findings = self.vf.validate_spec(fm, "test-spec.md")
        assert any("bare filename" in f for f in findings)

    # --- validate_agent ---

    def test_validate_agent_clean(self, tmp_path):
        p = self._spec_file(tmp_path, self.VALID_AGENT_FM)
        fm, _ = self.vf.extract_frontmatter(p)
        findings = self.vf.validate_agent(fm, "test-agent.md")
        assert findings == []

    def test_validate_agent_missing_name(self, tmp_path):
        content = self.VALID_AGENT_FM.replace("name: test-agent\n", "")
        p = self._spec_file(tmp_path, content)
        fm, _ = self.vf.extract_frontmatter(p)
        findings = self.vf.validate_agent(fm, "test-agent.md")
        assert any("name" in f for f in findings)

    def test_validate_agent_wrong_governed_by(self, tmp_path):
        content = self.VALID_AGENT_FM.replace(
            "governed_by: config/constitution.md",
            "governed_by: wrong/path.md",
        )
        p = self._spec_file(tmp_path, content)
        fm, _ = self.vf.extract_frontmatter(p)
        findings = self.vf.validate_agent(fm, "test-agent.md")
        assert any("governed_by" in f for f in findings)

    # --- collect_files ---

    def test_collect_files_excludes_readme(self, tmp_path):
        engine = tmp_path / "engine"
        engine.mkdir()
        (engine / "README.md").write_text("# Readme", encoding="utf-8")
        (engine / "real-spec.md").write_text("content", encoding="utf-8")
        files = self.vf.collect_files(tmp_path)
        names = [p.name for p, _ in files]
        assert "README.md" not in names
        assert "real-spec.md" in names

    def test_collect_files_agents_get_agent_type(self, tmp_path):
        agents = tmp_path / "agents"
        agents.mkdir()
        (agents / "my-agent.md").write_text("content", encoding="utf-8")
        files = self.vf.collect_files(tmp_path)
        types = {p.name: t for p, t in files}
        assert types.get("my-agent.md") == "agent"


# ===========================================================================
# validate_schema_drift
# ===========================================================================

class TestValidateSchemaDrift:
    """Tests for scripts/validate_schema_drift.py."""

    @pytest.fixture(autouse=True)
    def _import(self):
        import validate_schema_drift as vsd
        self.vsd = vsd

    # --- collect_schema_keys ---

    def test_collect_schema_keys_top_level(self):
        schema = {"properties": {"foo": {}, "bar": {}}}
        keys = self.vsd.collect_schema_keys(schema)
        assert keys == {"foo", "bar"}

    def test_collect_schema_keys_recurses_into_defs(self):
        schema = {
            "$defs": {
                "MyDef": {"properties": {"nested_key": {}}}
            }
        }
        keys = self.vsd.collect_schema_keys(schema)
        assert "nested_key" in keys

    def test_collect_schema_keys_recurses_into_items(self):
        schema = {"items": {"properties": {"item_field": {}}}}
        keys = self.vsd.collect_schema_keys(schema)
        assert "item_field" in keys

    def test_collect_schema_keys_deep_nesting(self):
        schema = {
            "properties": {
                "top": {
                    "properties": {
                        "middle": {
                            "properties": {"deep": {}}
                        }
                    }
                }
            }
        }
        keys = self.vsd.collect_schema_keys(schema)
        assert {"top", "middle", "deep"} <= keys

    def test_collect_schema_keys_empty_schema(self):
        assert self.vsd.collect_schema_keys({}) == set()

    # --- extract_key_accesses ---

    def test_extract_dot_get(self):
        source = 'x = d.get("my_key")'
        keys = self.vsd.extract_key_accesses(source)
        assert "my_key" in keys

    def test_extract_bracket_access(self):
        source = 'x = d["my_key"]'
        keys = self.vsd.extract_key_accesses(source)
        assert "my_key" in keys

    def test_extract_safe_get(self):
        source = 'x = safe_get(obj, "key_one", "key_two")'
        keys = self.vsd.extract_key_accesses(source)
        assert "key_one" in keys
        assert "key_two" in keys

    def test_generic_exclusions_not_returned(self, tmp_path):
        # Filtering happens in load_renderer_keys, not extract_key_accesses
        source = 'd.get("type")\nd.get("default")\nd["encoding"]\nd["real_key"]'
        f = tmp_path / "renderer.py"
        f.write_text(source, encoding="utf-8")
        keys, err = self.vsd.load_renderer_keys(f)
        assert err is None
        for excluded in self.vsd.GENERIC_EXCLUSIONS:
            assert excluded not in keys
        assert "real_key" in keys

    def test_loader_injected_keys_not_returned(self, tmp_path):
        source = 'd.get("_source")\nd["_program_slug"]\nd["real_field"]'
        f = tmp_path / "renderer.py"
        f.write_text(source, encoding="utf-8")
        keys, err = self.vsd.load_renderer_keys(f)
        assert err is None
        assert "_source" not in keys
        assert "_program_slug" not in keys
        assert "real_field" in keys

    def test_keys_with_spaces_excluded(self, tmp_path):
        source = 'd.get("has space")\nd["normal_key"]'
        f = tmp_path / "renderer.py"
        f.write_text(source, encoding="utf-8")
        keys, err = self.vsd.load_renderer_keys(f)
        assert err is None
        assert "has space" not in keys
        assert "normal_key" in keys

    # --- load_schema ---

    def test_load_schema_valid(self, tmp_path):
        schema = {"properties": {"alpha": {}, "beta": {}}}
        f = tmp_path / "test.schema.json"
        f.write_text(json.dumps(schema), encoding="utf-8")
        keys, err = self.vsd.load_schema(f)
        assert err is None
        assert keys == {"alpha", "beta"}

    def test_load_schema_missing_file(self, tmp_path):
        keys, err = self.vsd.load_schema(tmp_path / "missing.json")
        assert keys == set()
        assert err is not None
        assert "not found" in err.lower()

    def test_load_schema_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{not valid json", encoding="utf-8")
        keys, err = self.vsd.load_schema(f)
        assert keys == set()
        assert err is not None


# ===========================================================================
# spec_coverage
# ===========================================================================

class TestSpecCoverage:
    """Tests for scripts/spec_coverage.py."""

    @pytest.fixture(autouse=True)
    def _import(self):
        import spec_coverage as sc
        self.sc = sc

    def _make_repo(self, tmp_path: Path) -> Path:
        """Scaffold a minimal repo structure."""
        for d in ["engine", "functions", "agents", "scripts", "config"]:
            (tmp_path / d).mkdir()
        return tmp_path

    # --- collect_spec_files ---

    def test_collect_spec_files_finds_specs(self, tmp_path):
        repo = self._make_repo(tmp_path)
        (repo / "functions" / "foo-spec.md").write_text("content", encoding="utf-8")
        (repo / "engine" / "bar-spec.md").write_text("content", encoding="utf-8")
        specs = self.sc.collect_spec_files(repo)
        assert "functions/foo-spec.md" in specs
        assert "engine/bar-spec.md" in specs

    def test_collect_spec_files_excludes_readme(self, tmp_path):
        repo = self._make_repo(tmp_path)
        (repo / "functions" / "README.md").write_text("# Readme", encoding="utf-8")
        (repo / "functions" / "real-spec.md").write_text("content", encoding="utf-8")
        specs = self.sc.collect_spec_files(repo)
        assert "functions/README.md" not in specs
        assert "functions/real-spec.md" in specs

    def test_collect_spec_files_missing_dir_skipped(self, tmp_path):
        repo = self._make_repo(tmp_path)
        specs = self.sc.collect_spec_files(repo)
        assert specs == set()

    def test_collect_spec_files_covers_all_dirs(self, tmp_path):
        repo = self._make_repo(tmp_path)
        for d in ["engine", "functions", "agents", "memory"]:
            (repo / d).mkdir(exist_ok=True)
            (repo / d / f"{d}-doc.md").write_text("content", encoding="utf-8")
        specs = self.sc.collect_spec_files(repo)
        assert "engine/engine-doc.md" in specs
        assert "functions/functions-doc.md" in specs
        assert "agents/agents-doc.md" in specs
        assert "memory/memory-doc.md" in specs

    # --- extract_routing_targets ---

    def test_extract_routing_targets_parses_table(self, tmp_path):
        content = (
            "# Session Init\n\n"
            "| Foo pattern | `functions/foo-spec.md` |\n"
            "| Bar pattern | `functions/bar-spec.md` |\n"
        )
        f = tmp_path / "session-init-spec.md"
        f.write_text(content, encoding="utf-8")
        targets = self.sc.extract_routing_targets(f)
        assert "functions/foo-spec.md" in targets
        assert "functions/bar-spec.md" in targets

    def test_extract_routing_targets_skips_scripts(self, tmp_path):
        content = (
            "| Scripted | `scripts/something.py` |\n"
            "| Real | `functions/real-spec.md` |\n"
        )
        f = tmp_path / "session-init-spec.md"
        f.write_text(content, encoding="utf-8")
        targets = self.sc.extract_routing_targets(f)
        assert "scripts/something.py" not in targets
        assert "functions/real-spec.md" in targets

    def test_extract_routing_targets_skips_clarify(self, tmp_path):
        content = "| Unknown | `Ask one clarifying question` |\n"
        f = tmp_path / "session-init-spec.md"
        f.write_text(content, encoding="utf-8")
        targets = self.sc.extract_routing_targets(f)
        assert "Ask one clarifying question" not in targets

    # --- extract_orchestrator_invokes ---

    def test_extract_orchestrator_invokes_parses_list(self, tmp_path):
        content = (
            "---\n"
            "invokes:\n"
            "  - functions/foo-spec.md\n"
            "  - functions/bar-spec.md\n"
            "---\n"
            "# Body\n"
        )
        f = tmp_path / "orchestrator.md"
        f.write_text(content, encoding="utf-8")
        invokes = self.sc.extract_orchestrator_invokes(f)
        assert "functions/foo-spec.md" in invokes
        assert "functions/bar-spec.md" in invokes

    def test_extract_orchestrator_invokes_no_frontmatter(self, tmp_path):
        f = tmp_path / "orchestrator.md"
        f.write_text("# No frontmatter\n", encoding="utf-8")
        invokes = self.sc.extract_orchestrator_invokes(f)
        assert invokes == []
