"""
Integration Smoke Test
======================
Minimal canary: one synthetic run JSON and one synthetic portfolio JSON
exercise the four renderer scripts end-to-end. If this test passes, the
scripts still work after a change. If it fails, something foundational broke.

Not a full test suite — a canary.

Fixture design:
- MINIMAL_RUN  — valid against run-output.schema.json (required fields only)
- MINIMAL_PORTFOLIO — minimal portfolio structure the renderer reads

Usage:
    python -m pytest tests/test_smoke.py -v

Style: PEP 8
Deviations: None
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"

PROGRAM_SLUG = "smoke-test"
PROGRAM_NAME = "Smoke Test Program"


# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------

MINIMAL_RUN: dict = {
    "schema_version": "1.1",
    "run_manifest": {
        "run_date": "2026-04-02",
        "program_name": PROGRAM_NAME,
        "intent": "monitoring_run",
        "prior_run_date": None,
    },
    "program_state": {
        "overall_health": "green",
        "one_line_status": "All controls current. No escalations.",
        "last_updated": "2026-04-02",
    },
    "monitoring_output": {
        "decision_queue": [
            {
                "item": "Review AC-2 evidence package",
                "action_needed": "Approve collected artifacts",
                "owner": "Jane Smith",
                "due": "2026-05-15",
                "priority": "high",
            }
        ]
    },
    "flags": {
        "owner_needed": [],
        "date_needed": [],
        "escalation_path_needed": [],
        "inferred": [],
        "conflicts": [],
        "insufficient_data": [],
        "unresolved_from_prior_run": [],
    },
    "next_run_recommendation": {
        "suggested_date": "2026-05-01",
        "suggested_intent": "monitoring_run",
        "reason": "Scheduled monthly monitoring.",
    },
}

# portfolio_renderer.py reads its own key set (documented drift from schema).
MINIMAL_PORTFOLIO: dict = {
    "generated": "2026-04-02",
    "summary": {
        "total_programs": 1,
        "red": 0,
        "yellow": 0,
        "green": 1,
        "total_decisions_pending": 1,
        "total_blockers": 0,
        "total_escalations": 0,
        "nearest_deadline": "",
        "nearest_deadline_program": "",
    },
    "programs": [
        {
            "slug": PROGRAM_SLUG,
            "display_name": PROGRAM_NAME,
            "health": "green",
            "health_reason": "No escalations.",
            "one_line_status": "All controls current.",
            "last_run": "2026-04-02",
            "next_run_due": "2026-05-01",
            "run_staleness_days": 0,
            "phase": "active",
            "framework": "FedRAMP Moderate",
            "top_risk": "None identified",
            "decision_queue": [],
            "blockers": [],
            "escalations": [],
            "drafts_staged": 0,
            "intel_items_pending": 0,
            "nearest_deadline": "",
            "nearest_deadline_item": "",
        }
    ],
    "cross_program": {},
    "suggested_actions": [],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_repo(tmp_path: Path) -> Path:
    """Scaffold a minimal repo structure in tmp_path."""
    for d in ["runs", "data/portfolio", "logs", "ui"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    prog_dir = tmp_path / "runs" / PROGRAM_SLUG
    prog_dir.mkdir(parents=True)
    (prog_dir / "latest.json").write_text(
        json.dumps(MINIMAL_RUN, indent=2), encoding="utf-8"
    )

    (tmp_path / "data" / "portfolio" / "latest.json").write_text(
        json.dumps(MINIMAL_PORTFOLIO, indent=2), encoding="utf-8"
    )

    (tmp_path / "logs" / "provenance.jsonl").write_text("", encoding="utf-8")

    return tmp_path


def _run(script: str, args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a scripts/ script via subprocess and return the result."""
    cmd = [sys.executable, str(SCRIPTS / script)] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDashboardSmoke:
    """dashboard.py — reads runs/*/latest.json, writes HTML dashboard."""

    def test_exits_zero(self, tmp_path):
        repo = _make_repo(tmp_path)
        out = repo / "ui" / "dashboard.html"
        result = _run("dashboard.py", [
            "--runs", str(repo / "runs"),
            "--output", str(out),
        ])
        assert result.returncode == 0, (
            f"dashboard.py exited {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_output_file_created(self, tmp_path):
        repo = _make_repo(tmp_path)
        out = repo / "ui" / "dashboard.html"
        _run("dashboard.py", ["--runs", str(repo / "runs"), "--output", str(out)])
        assert out.exists(), "dashboard.py did not create output file"

    def test_program_name_in_output(self, tmp_path):
        repo = _make_repo(tmp_path)
        out = repo / "ui" / "dashboard.html"
        _run("dashboard.py", ["--runs", str(repo / "runs"), "--output", str(out)])
        html = out.read_text(encoding="utf-8")
        assert PROGRAM_NAME in html, (
            f"Expected program name '{PROGRAM_NAME}' not found in dashboard output"
        )

    def test_health_status_in_output(self, tmp_path):
        repo = _make_repo(tmp_path)
        out = repo / "ui" / "dashboard.html"
        _run("dashboard.py", ["--runs", str(repo / "runs"), "--output", str(out)])
        html = out.read_text(encoding="utf-8")
        assert "green" in html.lower()


class TestPortfolioRendererSmoke:
    """portfolio_renderer.py — reads portfolio JSON, writes HTML."""

    def test_exits_zero(self, tmp_path):
        repo = _make_repo(tmp_path)
        portfolio_path = repo / "data" / "portfolio" / "latest.json"
        out = repo / "ui" / "portfolio.html"
        result = _run("portfolio_renderer.py", [
            "--portfolio", str(portfolio_path),
            "--output", str(out),
        ])
        assert result.returncode == 0, (
            f"portfolio_renderer.py exited {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_output_file_created(self, tmp_path):
        repo = _make_repo(tmp_path)
        portfolio_path = repo / "data" / "portfolio" / "latest.json"
        out = repo / "ui" / "portfolio.html"
        _run("portfolio_renderer.py", [
            "--portfolio", str(portfolio_path),
            "--output", str(out),
        ])
        assert out.exists(), "portfolio_renderer.py did not create output file"

    def test_program_name_in_output(self, tmp_path):
        repo = _make_repo(tmp_path)
        portfolio_path = repo / "data" / "portfolio" / "latest.json"
        out = repo / "ui" / "portfolio.html"
        _run("portfolio_renderer.py", [
            "--portfolio", str(portfolio_path),
            "--output", str(out),
        ])
        html = out.read_text(encoding="utf-8")
        assert PROGRAM_NAME in html or PROGRAM_SLUG in html, (
            f"Neither program name nor slug found in portfolio output"
        )


class TestAuditorViewRendererSmoke:
    """auditor_view_renderer.py — reads runs/<slug>/latest.json, writes HTML.

    Runs with cwd=repo root so the script's relative path resolution works.
    """

    def test_exits_zero(self, tmp_path):
        repo = _make_repo(tmp_path)
        out = repo / "ui" / "auditor.html"
        result = _run("auditor_view_renderer.py", [
            "--program", PROGRAM_SLUG,
            "--output", str(out),
        ], cwd=repo)
        assert result.returncode == 0, (
            f"auditor_view_renderer.py exited {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_output_file_created(self, tmp_path):
        repo = _make_repo(tmp_path)
        out = repo / "ui" / "auditor.html"
        _run("auditor_view_renderer.py", [
            "--program", PROGRAM_SLUG,
            "--output", str(out),
        ], cwd=repo)
        assert out.exists(), "auditor_view_renderer.py did not create output file"

    def test_program_name_in_output(self, tmp_path):
        repo = _make_repo(tmp_path)
        out = repo / "ui" / "auditor.html"
        _run("auditor_view_renderer.py", [
            "--program", PROGRAM_SLUG,
            "--output", str(out),
        ], cwd=repo)
        html = out.read_text(encoding="utf-8")
        assert PROGRAM_NAME in html or PROGRAM_SLUG in html, (
            "Neither program name nor slug found in auditor view output"
        )


class TestProvenanceLogSmoke:
    """provenance_log.py — appends a JSONL entry to the provenance log."""

    def test_write_exits_zero(self, tmp_path):
        repo = _make_repo(tmp_path)
        log_path = repo / "logs" / "provenance.jsonl"
        result = _run("provenance_log.py", [
            "--log", str(log_path),
            "write",
            "--spec", "engine/program-pipeline-orchestrator.md",
            "--output", f"runs/{PROGRAM_SLUG}/2026-04-02-run.json",
            "--output-type", "run_json",
            "--program", PROGRAM_SLUG,
            "--purpose", "Smoke test — synthetic pipeline run",
            "--reusability", "instance",
        ])
        assert result.returncode == 0, (
            f"provenance_log.py write exited {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_entry_appended_to_log(self, tmp_path):
        repo = _make_repo(tmp_path)
        log_path = repo / "logs" / "provenance.jsonl"
        _run("provenance_log.py", [
            "--log", str(log_path),
            "write",
            "--spec", "engine/program-pipeline-orchestrator.md",
            "--output", f"runs/{PROGRAM_SLUG}/2026-04-02-run.json",
            "--output-type", "run_json",
            "--program", PROGRAM_SLUG,
            "--purpose", "Smoke test — synthetic pipeline run",
            "--reusability", "instance",
        ])
        lines = [
            l for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()
        ]
        assert len(lines) == 1, f"Expected 1 log entry, got {len(lines)}"

    def test_log_entry_is_valid_json(self, tmp_path):
        repo = _make_repo(tmp_path)
        log_path = repo / "logs" / "provenance.jsonl"
        _run("provenance_log.py", [
            "--log", str(log_path),
            "write",
            "--spec", "engine/program-pipeline-orchestrator.md",
            "--output", f"runs/{PROGRAM_SLUG}/2026-04-02-run.json",
            "--output-type", "run_json",
            "--program", PROGRAM_SLUG,
            "--purpose", "Smoke test — synthetic pipeline run",
            "--reusability", "instance",
        ])
        lines = [
            l for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()
        ]
        entry = json.loads(lines[0])
        assert entry["program"] == PROGRAM_SLUG
        assert entry["output_type"] == "run_json"
        assert "id" in entry
        assert "timestamp" in entry
