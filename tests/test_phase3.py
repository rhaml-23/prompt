"""
Phase 3 Tests
=============
Tests for Phase 3 runtime components:
- Dynamic router and priority queue (3a)
- Cross-framework intelligence / Common Control Catalog (3c)
- Trust manager / graduated autonomy (3e)
- Fleet metrics collector (3f)

Evidence lifecycle (3b) and predictive health (3d) are tested via their
respective scripts and agent validation in test_spec_validation.py.

Usage:
    python -m pytest tests/test_phase3.py -v
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ── 3a: Dynamic Router ─────────────────────────────────────────────

class TestDynamicRouter:
    def test_route_monitoring_request(self):
        from runtime.router import DynamicRouter, WorkItem
        router = DynamicRouter()
        work = WorkItem(description="Run monitoring for fedramp-high", program="fedramp-high")
        decision = router.route(work)
        assert decision.target_spec == "engine/program-pipeline-orchestrator.md"
        assert decision.target_agent == "program"

    def test_route_intel_scan(self):
        from runtime.router import DynamicRouter, WorkItem
        router = DynamicRouter()
        work = WorkItem(description="Run an intel scan for vulnerabilities")
        decision = router.route(work)
        assert decision.target_spec == "functions/external-intel-spec.md"
        assert decision.target_agent == "intelligence"

    def test_route_portfolio_briefing(self):
        from runtime.router import DynamicRouter, WorkItem
        router = DynamicRouter()
        work = WorkItem(description="Portfolio briefing for all programs")
        decision = router.route(work)
        assert decision.target_spec == "engine/portfolio-orchestrator.md"
        assert decision.target_agent == "coordinator"

    def test_route_unknown_work(self):
        from runtime.router import DynamicRouter, WorkItem
        router = DynamicRouter()
        work = WorkItem(description="Something completely unrelated to compliance")
        decision = router.route(work)
        assert decision.confidence == 0.0
        assert decision.requires_confirmation

    def test_priority_elevation_red_program(self):
        from runtime.router import DynamicRouter, WorkItem, Priority
        states = {
            "critical-prog": {
                "program_state": {"overall_health": "red"}
            }
        }
        router = DynamicRouter(program_states=states)
        work = WorkItem(
            description="Run monitoring", program="critical-prog",
            urgency="this_week"
        )
        decision = router.route(work)
        assert decision.priority <= Priority.HIGH

    def test_trust_level_affects_confirmation(self):
        from runtime.router import DynamicRouter, WorkItem
        router = DynamicRouter(trust_levels={"program": 3})
        work = WorkItem(description="Run monitoring for test-prog", program="test-prog")
        decision = router.route(work)
        assert not decision.requires_confirmation

    def test_trust_level_1_requires_confirmation(self):
        from runtime.router import DynamicRouter, WorkItem
        router = DynamicRouter(trust_levels={"program": 1})
        work = WorkItem(description="Run monitoring for test-prog", program="test-prog")
        decision = router.route(work)
        assert decision.requires_confirmation

    def test_route_batch_priority_order(self):
        from runtime.router import DynamicRouter, WorkItem, Priority
        router = DynamicRouter()
        items = [
            WorkItem(description="Run monitoring", urgency="no_deadline"),
            WorkItem(description="Run intel scan", urgency="immediate"),
            WorkItem(description="Run portfolio briefing", urgency="this_week"),
        ]
        decisions = router.route_batch(items)
        assert len(decisions) == 3
        assert decisions[0].priority <= decisions[1].priority <= decisions[2].priority

    def test_route_evidence_check(self):
        from runtime.router import DynamicRouter, WorkItem
        router = DynamicRouter()
        work = WorkItem(description="Check evidence staleness for fedramp")
        decision = router.route(work)
        assert "evidence" in decision.target_agent or "evidence" in decision.target_spec

    def test_route_crosswalk(self):
        from runtime.router import DynamicRouter, WorkItem
        router = DynamicRouter()
        work = WorkItem(description="Cross-framework crosswalk analysis")
        decision = router.route(work)
        assert decision.target_agent == "intelligence"


class TestPriorityQueue:
    def test_enqueue_dequeue(self):
        from runtime.router import PriorityQueue, WorkItem
        q = PriorityQueue()
        w = WorkItem(description="Test work")
        q.enqueue(w)
        result = q.dequeue()
        assert result is not None
        assert result[0].description == "Test work"

    def test_priority_ordering(self):
        from runtime.router import PriorityQueue, WorkItem
        q = PriorityQueue()
        q.enqueue(WorkItem(description="Low priority", urgency="no_deadline"))
        q.enqueue(WorkItem(description="Critical", urgency="immediate"))
        q.enqueue(WorkItem(description="Normal", urgency="this_week"))

        first = q.dequeue()
        assert first[0].description == "Critical"
        second = q.dequeue()
        assert second[0].description == "Normal"
        third = q.dequeue()
        assert third[0].description == "Low priority"

    def test_empty_dequeue(self):
        from runtime.router import PriorityQueue
        q = PriorityQueue()
        assert q.dequeue() is None

    def test_size_and_items(self):
        from runtime.router import PriorityQueue, WorkItem
        q = PriorityQueue()
        q.enqueue(WorkItem(description="A", urgency="immediate"))
        q.enqueue(WorkItem(description="B", urgency="no_deadline"))
        assert q.size == 2
        counts = q.items_by_priority()
        assert counts["critical"] == 1
        assert counts["low"] == 1


# ── 3c: Cross-Framework Intelligence ───────────────────────────────

class TestCommonControlCatalog:
    def test_create_and_query(self):
        from runtime.crosswalk import CommonControlCatalog, CommonControl, ControlMapping

        catalog = CommonControlCatalog()
        catalog.register_framework("nist-800-53", "NIST SP 800-53", "Rev 5", 1189)
        catalog.register_framework("iso-27001", "ISO 27001", "2022", 93)

        cc = CommonControl(
            common_control_id="CCC-AC-001",
            control_family="Access Control",
            control_objective="Manage user access to information systems",
            framework_mappings=[
                ControlMapping("nist-800-53", "AC-2", "Account Management"),
                ControlMapping("iso-27001", "A.9.2.1", "User registration and de-registration"),
            ],
            shared_evidence_types=["access_review", "config_audit"],
        )
        catalog.add_common_control(cc)

        results = catalog.find_by_framework_control("nist-800-53", "AC-2")
        assert len(results) == 1
        assert results[0].common_control_id == "CCC-AC-001"

    def test_impact_analysis(self):
        from runtime.crosswalk import CommonControlCatalog, CommonControl, ControlMapping

        catalog = CommonControlCatalog()
        catalog.register_framework("nist-800-53", "NIST SP 800-53", "Rev 5", 1189)
        catalog.register_framework("soc2", "SOC 2", "2017", 64)

        cc = CommonControl(
            common_control_id="CCC-AC-001",
            control_family="Access Control",
            control_objective="Account management",
            framework_mappings=[
                ControlMapping("nist-800-53", "AC-2", "Account Management"),
                ControlMapping("soc2", "CC6.1", "Logical and Physical Access Controls"),
            ],
            impact_scope=["fedramp-high", "soc2-prod"],
        )
        catalog.add_common_control(cc)

        impact = catalog.impact_analysis("nist-800-53", "AC-2", "gap")
        assert impact["impact"] == "cross_framework"
        assert len(impact["affected_frameworks"]) >= 1
        assert "fedramp-high" in impact["affected_programs"]

    def test_no_impact(self):
        from runtime.crosswalk import CommonControlCatalog
        catalog = CommonControlCatalog()
        impact = catalog.impact_analysis("nist-800-53", "AC-99")
        assert impact["impact"] == "none"

    def test_efficiency_report(self):
        from runtime.crosswalk import CommonControlCatalog, CommonControl, ControlMapping

        catalog = CommonControlCatalog()
        catalog.register_framework("fw1", "Framework 1", "1.0", 100)
        catalog.register_framework("fw2", "Framework 2", "1.0", 50)

        for i in range(5):
            cc = CommonControl(
                common_control_id=f"CCC-TEST-{i:03d}",
                control_family="Test",
                control_objective=f"Test control {i}",
                framework_mappings=[
                    ControlMapping("fw1", f"FW1-{i}", f"Control {i}"),
                    ControlMapping("fw2", f"FW2-{i}", f"Control {i}"),
                ],
                evidence_reusable=True,
            )
            catalog.add_common_control(cc)

        report = catalog.efficiency_report()
        assert report["total_common_controls"] == 5
        assert report["reusable_evidence_percentage"] == 100.0

    def test_serialize_roundtrip(self):
        from runtime.crosswalk import CommonControlCatalog, CommonControl, ControlMapping

        catalog = CommonControlCatalog()
        catalog.register_framework("fw1", "Framework 1", "1.0", 50)
        catalog.register_framework("fw2", "Framework 2", "1.0", 30)
        cc = CommonControl(
            common_control_id="CCC-RT-001",
            control_family="Test",
            control_objective="Roundtrip test",
            framework_mappings=[
                ControlMapping("fw1", "C1", "Control 1"),
                ControlMapping("fw2", "C1", "Control 1"),
            ],
        )
        catalog.add_common_control(cc)

        exported = catalog.to_schema_dict()
        restored = CommonControlCatalog.from_dict(exported)
        assert len(restored.entries) == 1
        assert "CCC-RT-001" in restored.entries

    def test_find_by_family(self):
        from runtime.crosswalk import CommonControlCatalog, CommonControl, ControlMapping

        catalog = CommonControlCatalog()
        cc1 = CommonControl("CCC-AC-001", "Access Control", "Obj 1",
                            [ControlMapping("fw1", "AC-1", "C1"), ControlMapping("fw2", "AC-1", "C1")])
        cc2 = CommonControl("CCC-AU-001", "Audit", "Obj 2",
                            [ControlMapping("fw1", "AU-1", "C1"), ControlMapping("fw2", "AU-1", "C1")])
        catalog.add_common_control(cc1)
        catalog.add_common_control(cc2)

        results = catalog.find_by_family("Access Control")
        assert len(results) == 1


# ── 3e: Trust Manager ──────────────────────────────────────────────

class TestTrustManager:
    def test_default_level(self):
        from runtime.trust import TrustManager
        tm = TrustManager(default_level=1)
        assert tm.get_level("new-agent") == 1

    def test_set_and_get_level(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        tm.set_level("agent-a", 2, "Manual promotion")
        assert tm.get_level("agent-a") == 2

    def test_level_clamping(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        tm.set_level("agent-a", 5, "Over max")
        assert tm.get_level("agent-a") == 3
        tm.set_level("agent-b", 0, "Under min")
        assert tm.get_level("agent-b") == 1

    def test_per_action_type_trust(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        tm.set_level("agent-a", 2, "Promote monitoring", action_type="monitoring_run")
        tm.set_level("agent-a", 1, "Keep default", action_type="full_run")
        assert tm.get_level("agent-a", "monitoring_run") == 2
        assert tm.get_level("agent-a", "full_run") == 1

    def test_promotion_insufficient_actions(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        for _ in range(5):
            tm.record_action("agent-a", "run", quality_gate_passed=True)
        result = tm.evaluate_promotion("agent-a", "run")
        assert not result["eligible"]
        assert "Insufficient" in result["reason"]

    def test_promotion_eligible(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        for _ in range(25):
            tm.record_action("agent-a", "run", quality_gate_passed=True)
        result = tm.evaluate_promotion("agent-a", "run")
        assert result["eligible"]
        assert result["proposed_level"] == 2

    def test_promote_method(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        for _ in range(25):
            tm.record_action("agent-a", "__default__", quality_gate_passed=True)
        record = tm.promote("agent-a")
        assert record is not None
        assert record.new_level == 2
        assert tm.get_level("agent-a") == 2

    def test_demotion_quality_gate_failure(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        tm.set_level("agent-a", 3, "Start high")
        record = tm.demote("agent-a", "quality_gate_failure", details="Failed gate check")
        assert record is not None
        assert record.new_level == 2

    def test_demotion_constitutional_violation(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        tm.set_level("agent-a", 3, "Start high")
        record = tm.demote("agent-a", "constitutional_violation", details="Violated Art V.5")
        assert record is not None
        assert record.new_level == 1

    def test_requires_review_flags(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        assert tm.requires_human_review("agent-a")
        assert not tm.is_autonomous("agent-a")
        tm.set_level("agent-a", 3, "Promote to autonomous")
        assert tm.is_autonomous("agent-a")
        assert not tm.requires_human_review("agent-a")

    def test_fleet_trust_state(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        tm.set_level("agent-a", 2, "Promote")
        tm.set_level("agent-b", 1, "Default")
        state = tm.fleet_trust_state()
        assert "agent-a" in state["agents"]
        assert state["total_changes"] == 2

    def test_serialize_roundtrip(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        tm.set_level("agent-a", 2, "Promote")
        for _ in range(5):
            tm.record_action("agent-a", "run", quality_gate_passed=True)
        data = tm.to_dict()
        restored = TrustManager.from_dict(data)
        assert restored.get_level("agent-a") == 2

    def test_already_max_level(self):
        from runtime.trust import TrustManager
        tm = TrustManager()
        tm.set_level("agent-a", 3, "Max")
        result = tm.evaluate_promotion("agent-a")
        assert not result["eligible"]


# ── 3f: Fleet Metrics ──────────────────────────────────────────────

class TestFleetMetricsCollector:
    def test_register_and_record(self):
        from runtime.metrics import FleetMetricsCollector
        mc = FleetMetricsCollector()
        mc.register_agent("prog-1", "program")
        mc.record_action("prog-1", "pipeline_run", program="fedramp",
                         tokens_input=5000, tokens_output=2000)

        dashboard = mc.agent_health_dashboard()
        assert "prog-1" in dashboard["agents"]
        assert dashboard["agents"]["prog-1"]["actions_24h"] == 1
        assert dashboard["agents"]["prog-1"]["tokens_used_24h"] == 7000

    def test_cost_report_by_agent(self):
        from runtime.metrics import FleetMetricsCollector
        mc = FleetMetricsCollector()
        mc.register_agent("a1", "program")
        mc.register_agent("a2", "review")
        mc.record_action("a1", "run", tokens_input=1000, tokens_output=500)
        mc.record_action("a2", "review", tokens_input=2000, tokens_output=1000)

        report = mc.cost_report("agent")
        assert report["totals"]["a1"]["total"] == 1500
        assert report["totals"]["a2"]["total"] == 3000
        assert report["grand_total"]["total"] == 4500

    def test_decision_trail(self):
        from runtime.metrics import FleetMetricsCollector
        mc = FleetMetricsCollector()
        mc.record_decision("routing", "coordinator", {"target": "prog-agent"})
        mc.record_decision("escalation", "prog-agent", {"severity": "high"})

        trail = mc.decision_audit_trail()
        assert len(trail) == 2
        assert trail[0]["decision_type"] == "routing"

    def test_program_metrics(self):
        from runtime.metrics import FleetMetricsCollector
        mc = FleetMetricsCollector()
        mc.update_program("fedramp", health="green", open_findings=5,
                          resolved_findings_30d=10, runs_30d=4)

        dashboard = mc.program_performance_dashboard()
        assert "fedramp" in dashboard["programs"]
        assert dashboard["programs"]["fedramp"]["finding_velocity"] < 0

    def test_fleet_overview(self):
        from runtime.metrics import FleetMetricsCollector
        mc = FleetMetricsCollector()
        mc.register_agent("a1", "program")
        mc.record_action("a1", "run", tokens_input=100, tokens_output=50)
        mc.record_decision("routing", "coordinator", {})

        overview = mc.fleet_overview()
        assert "agent_health" in overview
        assert "program_performance" in overview
        assert "cost_summary" in overview
        assert "recent_decisions" in overview

    def test_error_rate(self):
        from runtime.metrics import FleetMetricsCollector
        mc = FleetMetricsCollector()
        mc.register_agent("a1", "program")
        mc.record_action("a1", "run", error=False)
        mc.record_action("a1", "run", error=True)

        dashboard = mc.agent_health_dashboard()
        assert dashboard["agents"]["a1"]["error_rate_24h"] == 0.5


# ── Schema Validation ──────────────────────────────────────────────

class TestPhase3Schemas:
    def _load_schema(self, name: str) -> dict:
        path = REPO_ROOT / "config" / "schemas" / name
        assert path.exists(), f"Schema file missing: {name}"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_common_control_catalog_schema(self):
        schema = self._load_schema("common-control-catalog.schema.json")
        assert schema.get("$schema")
        assert "catalog_entries" in schema.get("required", [])
        assert "framework_coverage" in schema.get("required", [])

    def test_evidence_record_schema(self):
        schema = self._load_schema("evidence-record.schema.json")
        assert schema.get("$schema")
        assert "records" in schema.get("required", [])

    def test_trust_state_schema(self):
        schema = self._load_schema("trust-state.schema.json")
        assert schema.get("$schema")
        assert "trust_state" in schema.get("required", [])

    def test_fleet_metrics_schema(self):
        schema = self._load_schema("fleet-metrics.schema.json")
        assert schema.get("$schema")
        assert "timestamp" in schema.get("required", [])

    def test_agent_message_schema_new_types(self):
        schema = self._load_schema("agent-message.schema.json")
        message_types = schema["properties"]["type"]["enum"]
        new_types = [
            "EVIDENCE_CHECK", "EVIDENCE_ALERT", "EVIDENCE_REPORT",
            "CCC_UPDATE", "IMPACT_ANALYSIS",
            "TRUST_PROMOTION", "TRUST_DEMOTION",
            "METRICS_REPORT", "PREDICTION_REPORT",
            "ROUTING_DECISION", "CIRCUIT_BREAKER",
        ]
        for mt in new_types:
            assert mt in message_types, f"Missing message type: {mt}"


# ── Predictive Health (script) ─────────────────────────────────────

class TestPredictiveHealth:
    def test_health_trajectory_insufficient_data(self):
        from scripts.predictive_health import analyze_health_trajectory
        result = analyze_health_trajectory([])
        assert result["trajectory"] == "insufficient_data"

    def test_health_trajectory_stable(self):
        from scripts.predictive_health import analyze_health_trajectory
        runs = [
            {"program_state": {"overall_health": "green"}, "run_manifest": {"run_date": f"2026-03-{20+i:02d}"}}
            for i in range(5)
        ]
        result = analyze_health_trajectory(runs)
        assert result["trajectory"] == "stable"

    def test_health_trajectory_declining(self):
        from scripts.predictive_health import analyze_health_trajectory
        runs = [
            {"program_state": {"overall_health": "green"}, "run_manifest": {"run_date": "2026-03-20"}},
            {"program_state": {"overall_health": "green"}, "run_manifest": {"run_date": "2026-03-21"}},
            {"program_state": {"overall_health": "green"}, "run_manifest": {"run_date": "2026-03-22"}},
            {"program_state": {"overall_health": "yellow"}, "run_manifest": {"run_date": "2026-03-23"}},
            {"program_state": {"overall_health": "red"}, "run_manifest": {"run_date": "2026-03-24"}},
            {"program_state": {"overall_health": "red"}, "run_manifest": {"run_date": "2026-03-25"}},
        ]
        result = analyze_health_trajectory(runs)
        assert result["trajectory"] == "declining"

    def test_audit_readiness_score(self):
        from scripts.predictive_health import compute_audit_readiness_score
        run = {
            "program_state": {"overall_health": "green"},
            "flags": {},
        }
        result = compute_audit_readiness_score(run)
        assert result["score"] == 100
        assert result["readiness"] == "audit_ready"

    def test_audit_readiness_score_red(self):
        from scripts.predictive_health import compute_audit_readiness_score
        run = {
            "program_state": {"overall_health": "red"},
            "flags": {
                "owner_needed": ["AC-2", "AC-3", "AC-4"],
                "unresolved_from_prior_run": ["IR-1", "IR-2"],
            },
        }
        result = compute_audit_readiness_score(run)
        assert result["score"] < 50
        assert result["readiness"] in ("significant_gaps", "not_ready")

    def test_certification_timeline_insufficient(self):
        from scripts.predictive_health import predict_certification_timeline
        result = predict_certification_timeline([])
        assert result["prediction"] == "insufficient_data"

    def test_resource_contention_forecast(self):
        from scripts.predictive_health import forecast_resource_contention
        portfolio = {
            "programs": [
                {"program_slug": "prog-a", "vendors": [{"name": "Vendor X"}], "next_run_recommended": "2026-04-01"},
                {"program_slug": "prog-b", "vendors": [{"name": "Vendor X"}], "next_run_recommended": "2026-04-02"},
            ]
        }
        contention = forecast_resource_contention(portfolio)
        assert len(contention) >= 1
        assert any(c["type"] == "shared_vendor" for c in contention)


# ── Evidence Agent Validation ──────────────────────────────────────

class TestEvidenceAgent:
    def test_evidence_agent_has_frontmatter(self):
        agent_file = REPO_ROOT / "agents" / "evidence-agent.md"
        assert agent_file.exists(), "evidence-agent.md not found"
        text = agent_file.read_text(encoding="utf-8")
        assert text.startswith("---"), "Missing YAML frontmatter"

    def test_evidence_agent_required_fields(self):
        agent_file = REPO_ROOT / "agents" / "evidence-agent.md"
        text = agent_file.read_text(encoding="utf-8")
        end = text.find("\n---", 3)
        assert end > 0
        try:
            import yaml
            fm = yaml.safe_load(text[3:end])
            assert "name" in fm
            assert "description" in fm
            assert "model" in fm
            assert fm.get("agent_role") == "evidence"
            assert fm.get("governed_by") == "config/constitution.md"
        except ImportError:
            pytest.skip("PyYAML not installed")


# ── Routing Table Completeness ─────────────────────────────────────

class TestPhase3RoutingTable:
    def test_new_routing_entries_exist(self):
        session_init = REPO_ROOT / "engine" / "session-init-spec.md"
        text = session_init.read_text(encoding="utf-8")
        expected_entries = [
            "Evidence lifecycle check",
            "Cross-framework crosswalk",
            "Common control catalog",
            "Predictive health analysis",
            "Fleet dashboard",
            "Trust level report",
        ]
        for entry in expected_entries:
            assert entry in text, f"Missing routing entry: {entry}"
