"""
Runtime Abstraction Tests
=========================
Tests for the IDE-mode runtime implementations. These tests verify
that the file-based implementations correctly implement the runtime
interfaces.

Usage:
    python -m pytest tests/test_runtime.py -v
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _create_test_repo(tmp_path: Path) -> Path:
    """Create a minimal repo structure for testing."""
    for d in ["config", "engine", "functions", "scripts", "runs", "data", "memory", "logs"]:
        (tmp_path / d).mkdir()
    (tmp_path / "config" / "constitution.md").write_text("# Constitution")
    return tmp_path


class TestFileStateBackend:
    def test_write_and_read_run(self, tmp_path):
        from runtime.ide import FileStateBackend
        repo = _create_test_repo(tmp_path)
        backend = FileStateBackend(repo)

        data = {"schema_version": "1.1", "program_state": {"overall_health": "green"}}
        path = backend.write_run("test-program", "2026-03-26", data)

        assert "2026-03-26-run.json" in path
        result = backend.read_run("test-program")
        assert result["program_state"]["overall_health"] == "green"

    def test_list_runs(self, tmp_path):
        from runtime.ide import FileStateBackend
        repo = _create_test_repo(tmp_path)
        backend = FileStateBackend(repo)

        backend.write_run("prog", "2026-03-25", {"v": 1})
        backend.write_run("prog", "2026-03-26", {"v": 2})
        runs = backend.list_runs("prog")
        assert len(runs) == 2

    def test_list_programs(self, tmp_path):
        from runtime.ide import FileStateBackend
        repo = _create_test_repo(tmp_path)
        backend = FileStateBackend(repo)

        backend.write_run("alpha", "2026-03-26", {"v": 1})
        backend.write_run("beta", "2026-03-26", {"v": 1})
        programs = backend.list_programs()
        assert "alpha" in programs
        assert "beta" in programs

    def test_portfolio_state(self, tmp_path):
        from runtime.ide import FileStateBackend
        repo = _create_test_repo(tmp_path)
        backend = FileStateBackend(repo)

        portfolio = {"schema_version": "1.0", "programs": []}
        backend.write_portfolio(portfolio)
        result = backend.read_portfolio()
        assert result["schema_version"] == "1.0"

    def test_read_missing_run_returns_empty(self, tmp_path):
        from runtime.ide import FileStateBackend
        repo = _create_test_repo(tmp_path)
        backend = FileStateBackend(repo)
        assert backend.read_run("nonexistent") == {}

    def test_work_checkpoint_roundtrip(self, tmp_path):
        from runtime.ide import FileStateBackend
        repo = _create_test_repo(tmp_path)
        backend = FileStateBackend(repo)

        payload = {
            "checkpoint_id": "test-cp",
            "program": "prog-a",
            "work_type": "custom",
            "status": "in_progress",
            "started_at": "2026-04-04T12:00:00",
            "updated_at": "2026-04-04T12:00:00",
            "next_actions": ["Continue step 2"],
        }
        backend.write_work_checkpoint("prog-a", "test-cp", payload)
        result = backend.read_work_checkpoint("prog-a", "test-cp")
        assert result["status"] == "in_progress"
        assert result["next_actions"] == ["Continue step 2"]

    def test_draft_run_roundtrip(self, tmp_path):
        from runtime.ide import FileStateBackend
        repo = _create_test_repo(tmp_path)
        backend = FileStateBackend(repo)

        draft = {
            "schema_version": "1.1",
            "run_manifest": {
                "run_date": "2026-04-04",
                "run_notes": "WIP — checkpoint — phase 2 done",
            },
        }
        backend.write_draft_run("prog-b", draft)
        assert backend.read_draft_run("prog-b")["run_manifest"]["run_notes"].startswith(
            "WIP — checkpoint"
        )
        backend.remove_draft_run("prog-b")
        assert backend.read_draft_run("prog-b") == {}


class TestFileMemoryStore:
    def test_write_and_read_state(self, tmp_path):
        from runtime.ide import FileMemoryStore
        repo = _create_test_repo(tmp_path)
        store = FileMemoryStore(repo)

        store.write_state("test-prog", "# State\nHealth: green")
        result = store.read_state("test-prog")
        assert "Health: green" in result

    def test_append_and_read_decisions(self, tmp_path):
        from runtime.ide import FileMemoryStore
        repo = _create_test_repo(tmp_path)
        store = FileMemoryStore(repo)

        (repo / "memory" / "test-prog-decisions.log").write_text(
            "# Decisions log\n"
        )
        store.append_decision("test-prog", "2026-03-26 | DECISION | Test decision | context")
        store.append_decision("test-prog", "2026-03-26 | RISK_ACCEPTED | Test risk | rationale")

        decisions = store.read_decisions("test-prog")
        assert len(decisions) == 2
        assert "DECISION" in decisions[0]

    def test_query_decisions_by_type(self, tmp_path):
        from runtime.ide import FileMemoryStore
        repo = _create_test_repo(tmp_path)
        store = FileMemoryStore(repo)

        log_path = repo / "memory" / "test-prog-decisions.log"
        log_path.write_text(
            "2026-03-25 | DECISION | First | ctx\n"
            "2026-03-26 | RISK_ACCEPTED | Second | ctx\n"
            "2026-03-26 | DECISION | Third | ctx\n"
        )

        results = store.query_decisions("test-prog", "RISK_ACCEPTED")
        assert len(results) == 1
        assert "Second" in results[0]

    def test_decision_count(self, tmp_path):
        from runtime.ide import FileMemoryStore
        repo = _create_test_repo(tmp_path)
        store = FileMemoryStore(repo)

        log_path = repo / "memory" / "test-prog-decisions.log"
        log_path.write_text("# Header\nEntry 1\nEntry 2\nEntry 3\n")
        assert store.decision_count("test-prog") == 3

    def test_list_programs(self, tmp_path):
        from runtime.ide import FileMemoryStore
        repo = _create_test_repo(tmp_path)
        store = FileMemoryStore(repo)

        (repo / "memory" / "alpha-memory.md").write_text("# Alpha")
        (repo / "memory" / "beta-memory.md").write_text("# Beta")
        programs = store.list_programs()
        assert set(programs) == {"alpha", "beta"}


class TestFileAuditLog:
    def test_write_and_tail(self, tmp_path):
        from runtime.ide import FileAuditLog
        repo = _create_test_repo(tmp_path)
        log = FileAuditLog(repo)

        entry_id = log.write_entry({
            "agent_id": "test-agent",
            "action": "test_action",
            "program": "test-prog",
        })
        assert entry_id

        entries = log.tail(5)
        assert len(entries) == 1
        assert entries[0]["agent_id"] == "test-agent"

    def test_hash_chain(self, tmp_path):
        from runtime.ide import FileAuditLog
        repo = _create_test_repo(tmp_path)
        log = FileAuditLog(repo)

        log.write_entry({"agent_id": "a1", "action": "first"})
        log.write_entry({"agent_id": "a2", "action": "second"})
        log.write_entry({"agent_id": "a3", "action": "third"})

        valid, msg = log.verify_integrity()
        assert valid, msg

    def test_query_by_program(self, tmp_path):
        from runtime.ide import FileAuditLog
        repo = _create_test_repo(tmp_path)
        log = FileAuditLog(repo)

        log.write_entry({"agent_id": "a1", "action": "run", "program": "alpha"})
        log.write_entry({"agent_id": "a1", "action": "run", "program": "beta"})
        log.write_entry({"agent_id": "a1", "action": "run", "program": "alpha"})

        results = log.query(program="alpha")
        assert len(results) == 2

    def test_summary(self, tmp_path):
        from runtime.ide import FileAuditLog
        repo = _create_test_repo(tmp_path)
        log = FileAuditLog(repo)

        log.write_entry({"agent_id": "a1", "action": "run"})
        log.write_entry({"agent_id": "a2", "action": "review"})

        summary = log.summary()
        assert summary["total_entries"] == 2
        assert summary["unique_agents"] == 2


class TestFileMessageBus:
    def test_send_and_receive(self, tmp_path):
        from runtime.ide import FileMessageBus
        repo = _create_test_repo(tmp_path)
        bus = FileMessageBus(repo)

        msg_id = bus.send(
            target="review-agent",
            message_type="REVIEW_REQUEST",
            payload={"program": "test"},
            sender="program-agent",
        )
        assert msg_id

        messages = bus.receive("review-agent")
        assert len(messages) == 1
        assert messages[0]["type"] == "REVIEW_REQUEST"

    def test_acknowledge(self, tmp_path):
        from runtime.ide import FileMessageBus
        repo = _create_test_repo(tmp_path)
        bus = FileMessageBus(repo)

        msg_id = bus.send("agent-a", "TEST", {"data": 1}, "agent-b")
        bus.acknowledge(msg_id, "agent-a")

        messages = bus.receive("agent-a")
        assert len(messages) == 0

    def test_escalate(self, tmp_path):
        from runtime.ide import FileMessageBus
        repo = _create_test_repo(tmp_path)
        bus = FileMessageBus(repo)

        esc_id = bus.escalate(
            finding="Critical gap in AC-2",
            context={"program": "fedramp-high"},
            severity="critical",
            sender="program-agent",
        )
        assert esc_id

        messages = bus.receive("lead program manager", ["ESCALATION"])
        assert len(messages) == 1
        assert messages[0]["payload"]["severity"] == "critical"


class TestFleetMetricsCollector:
    def test_cascade_allowed_under_limit(self):
        from runtime.metrics import FleetMetricsCollector
        collector = FleetMetricsCollector()
        result = collector.check_cascade("agent-a", 3)
        assert result["allowed"] is True
        assert result["depth"] == 3
        assert not collector.decision_audit_trail(decision_type="circuit_breaker")

    def test_cascade_blocked_at_limit(self):
        from runtime.metrics import FleetMetricsCollector
        collector = FleetMetricsCollector()
        result = collector.check_cascade("agent-b", 4)
        assert result["allowed"] is False
        assert result["depth"] == 4
        trail = collector.decision_audit_trail(decision_type="circuit_breaker")
        assert len(trail) == 1
        assert trail[0]["decision_type"] == "circuit_breaker"
        assert trail[0]["agent_id"] == "agent-b"
        assert trail[0]["details"]["action"] == "halted"

    def test_cascade_allowed_well_under_limit(self):
        from runtime.metrics import FleetMetricsCollector
        collector = FleetMetricsCollector()
        for depth in (1, 2):
            result = collector.check_cascade("agent-c", depth)
            assert result["allowed"] is True, f"depth={depth} should be allowed"
        assert not collector.decision_audit_trail(decision_type="circuit_breaker")


class TestFileMemoryStoreWip:
    def test_session_wip_roundtrip(self, tmp_path):
        from runtime.ide import FileMemoryStore
        repo = _create_test_repo(tmp_path)
        store = FileMemoryStore(repo)

        store.write_session_wip("prog-a", "## WIP\n- item 1\n")
        assert store.read_session_wip("prog-a") == "## WIP\n- item 1\n"
        store.clear_session_wip("prog-a")
        assert store.read_session_wip("prog-a") == ""

    def test_session_wip_missing_returns_empty(self, tmp_path):
        from runtime.ide import FileMemoryStore
        repo = _create_test_repo(tmp_path)
        store = FileMemoryStore(repo)
        assert store.read_session_wip("nonexistent") == ""

    def test_session_wip_overwrite(self, tmp_path):
        from runtime.ide import FileMemoryStore
        repo = _create_test_repo(tmp_path)
        store = FileMemoryStore(repo)

        store.write_session_wip("prog-b", "first write\n")
        store.write_session_wip("prog-b", "second write\n")
        assert store.read_session_wip("prog-b") == "second write\n"

    def test_clear_session_wip_nonexistent_is_noop(self, tmp_path):
        from runtime.ide import FileMemoryStore
        repo = _create_test_repo(tmp_path)
        store = FileMemoryStore(repo)
        store.clear_session_wip("no-such-program")


class TestRuntimeFactory:
    def test_create_ide_runtime(self, tmp_path):
        from runtime.factory import create_runtime
        repo = _create_test_repo(tmp_path)
        rt = create_runtime("ide", repo)
        assert rt.mode == "ide"
        assert rt.state is not None
        assert rt.bus is not None
        assert rt.memory is not None
        assert rt.audit is not None

    def test_deployed_requires_env_vars(self, tmp_path):
        from runtime.factory import create_runtime
        repo = _create_test_repo(tmp_path)
        with pytest.raises((EnvironmentError, ImportError)):
            create_runtime("deployed", repo)

    def test_invalid_mode(self, tmp_path):
        from runtime.factory import create_runtime
        repo = _create_test_repo(tmp_path)
        with pytest.raises(ValueError):
            create_runtime("invalid", repo)
