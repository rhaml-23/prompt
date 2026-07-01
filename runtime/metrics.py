"""
Fleet observability metrics collection and reporting (Phase 3f).

Collects and aggregates operational metrics across the agent fleet:
- Agent health (active/idle/error states, last activity)
- Decision audit trail (routing decisions, escalations, authority checks)
- Performance metrics (time-to-resolution, finding-to-remediation velocity)
- Cost tracking (token usage per agent/program/framework)
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class AgentMetrics:
    """Operational metrics for a single agent."""

    agent_id: str
    agent_type: str
    status: str = "idle"
    last_active: str = ""
    total_actions: int = 0
    actions_24h: int = 0
    errors_24h: int = 0
    escalations_24h: int = 0
    avg_action_duration_ms: float = 0
    tokens_used_session: int = 0
    tokens_used_24h: int = 0
    trust_level: int = 1
    current_task: str = ""

    @property
    def error_rate_24h(self) -> float:
        if self.actions_24h == 0:
            return 0.0
        return self.errors_24h / self.actions_24h

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "last_active": self.last_active,
            "total_actions": self.total_actions,
            "actions_24h": self.actions_24h,
            "errors_24h": self.errors_24h,
            "error_rate_24h": round(self.error_rate_24h, 4),
            "escalations_24h": self.escalations_24h,
            "avg_action_duration_ms": round(self.avg_action_duration_ms, 1),
            "tokens_used_session": self.tokens_used_session,
            "tokens_used_24h": self.tokens_used_24h,
            "trust_level": self.trust_level,
            "current_task": self.current_task,
        }


@dataclass
class ProgramMetrics:
    """Performance metrics for a single program."""

    program: str
    health: str = "unknown"
    total_runs: int = 0
    runs_30d: int = 0
    avg_run_duration_min: float = 0
    open_findings: int = 0
    resolved_findings_30d: int = 0
    avg_finding_resolution_days: float = 0
    evidence_coverage_pct: float = 0
    stale_evidence_count: int = 0
    tokens_used_30d: int = 0
    last_run_date: str = ""

    @property
    def finding_velocity(self) -> float:
        """Net finding velocity — negative means resolving faster than creating."""
        if self.runs_30d == 0:
            return 0.0
        return (self.open_findings - self.resolved_findings_30d) / self.runs_30d

    def to_dict(self) -> dict[str, Any]:
        return {
            "program": self.program,
            "health": self.health,
            "total_runs": self.total_runs,
            "runs_30d": self.runs_30d,
            "avg_run_duration_min": round(self.avg_run_duration_min, 1),
            "open_findings": self.open_findings,
            "resolved_findings_30d": self.resolved_findings_30d,
            "avg_finding_resolution_days": round(self.avg_finding_resolution_days, 1),
            "finding_velocity": round(self.finding_velocity, 2),
            "evidence_coverage_pct": round(self.evidence_coverage_pct, 1),
            "stale_evidence_count": self.stale_evidence_count,
            "tokens_used_30d": self.tokens_used_30d,
            "last_run_date": self.last_run_date,
        }


@dataclass
class CostRecord:
    """Token usage record for cost tracking."""

    agent_id: str
    program: str
    framework: str
    action: str
    tokens_input: int = 0
    tokens_output: int = 0
    timestamp: str = ""

    @property
    def total_tokens(self) -> int:
        return self.tokens_input + self.tokens_output


MAX_CASCADE_DEPTH = 3


class FleetMetricsCollector:
    """Collects and aggregates metrics across the compliance fleet."""

    def __init__(self):
        self._agent_metrics: dict[str, AgentMetrics] = {}
        self._program_metrics: dict[str, ProgramMetrics] = {}
        self._cost_records: list[CostRecord] = []
        self._decision_trail: list[dict[str, Any]] = []

    def register_agent(self, agent_id: str, agent_type: str) -> None:
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(
                agent_id=agent_id, agent_type=agent_type
            )

    def record_action(
        self,
        agent_id: str,
        action: str,
        program: str = "",
        duration_ms: float = 0,
        tokens_input: int = 0,
        tokens_output: int = 0,
        error: bool = False,
        escalated: bool = False,
    ) -> None:
        if agent_id in self._agent_metrics:
            m = self._agent_metrics[agent_id]
            m.total_actions += 1
            m.actions_24h += 1
            if error:
                m.errors_24h += 1
            if escalated:
                m.escalations_24h += 1
            m.tokens_used_session += tokens_input + tokens_output
            m.tokens_used_24h += tokens_input + tokens_output
            m.last_active = datetime.now(tz=None).astimezone().isoformat()
            total = m.total_actions
            m.avg_action_duration_ms = (
                (m.avg_action_duration_ms * (total - 1) + duration_ms) / total
            )

        if tokens_input + tokens_output > 0:
            self._cost_records.append(CostRecord(
                agent_id=agent_id,
                program=program,
                framework="",
                action=action,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                timestamp=datetime.now(tz=None).astimezone().isoformat(),
            ))

    def check_cascade(self, initiator: str, depth: int) -> dict[str, Any]:
        """Return allowed=True/False and log a circuit_breaker decision if triggered."""
        if depth <= MAX_CASCADE_DEPTH:
            return {"allowed": True, "depth": depth}
        self.record_decision("circuit_breaker", initiator, {
            "cascade_depth": depth, "limit": MAX_CASCADE_DEPTH,
            "action": "halted"
        })
        return {"allowed": False, "depth": depth, "limit": MAX_CASCADE_DEPTH}

    def record_decision(
        self,
        decision_type: str,
        agent_id: str,
        details: dict[str, Any],
    ) -> None:
        self._decision_trail.append({
            "timestamp": datetime.now(tz=None).astimezone().isoformat(),
            "decision_type": decision_type,
            "agent_id": agent_id,
            "details": details,
        })

    def update_program(self, program: str, **kwargs: Any) -> None:
        if program not in self._program_metrics:
            self._program_metrics[program] = ProgramMetrics(program=program)
        pm = self._program_metrics[program]
        for key, val in kwargs.items():
            if hasattr(pm, key):
                setattr(pm, key, val)

    def agent_health_dashboard(self) -> dict[str, Any]:
        agents = {}
        for agent_id, m in self._agent_metrics.items():
            agents[agent_id] = m.to_dict()

        active = sum(1 for m in self._agent_metrics.values() if m.status == "active")
        errored = sum(1 for m in self._agent_metrics.values() if m.error_rate_24h > 0.1)

        return {
            "timestamp": datetime.now(tz=None).astimezone().isoformat(),
            "fleet_summary": {
                "total_agents": len(self._agent_metrics),
                "active": active,
                "idle": len(self._agent_metrics) - active,
                "high_error_rate": errored,
            },
            "agents": agents,
        }

    def program_performance_dashboard(self) -> dict[str, Any]:
        programs = {}
        for prog, m in self._program_metrics.items():
            programs[prog] = m.to_dict()

        return {
            "timestamp": datetime.now(tz=None).astimezone().isoformat(),
            "programs": programs,
        }

    def cost_report(
        self,
        group_by: str = "agent",
    ) -> dict[str, Any]:
        totals: dict[str, dict[str, int]] = {}

        for r in self._cost_records:
            if group_by == "agent":
                key = r.agent_id
            elif group_by == "program":
                key = r.program or "unscoped"
            elif group_by == "action":
                key = r.action
            else:
                key = r.agent_id

            if key not in totals:
                totals[key] = {"tokens_input": 0, "tokens_output": 0, "total": 0, "count": 0}
            totals[key]["tokens_input"] += r.tokens_input
            totals[key]["tokens_output"] += r.tokens_output
            totals[key]["total"] += r.total_tokens
            totals[key]["count"] += 1

        return {
            "group_by": group_by,
            "period": "session",
            "totals": totals,
            "grand_total": {
                "tokens_input": sum(r.tokens_input for r in self._cost_records),
                "tokens_output": sum(r.tokens_output for r in self._cost_records),
                "total": sum(r.total_tokens for r in self._cost_records),
                "records": len(self._cost_records),
            },
        }

    def decision_audit_trail(
        self, limit: int = 50, decision_type: str | None = None
    ) -> list[dict[str, Any]]:
        trail = self._decision_trail
        if decision_type:
            trail = [d for d in trail if d["decision_type"] == decision_type]
        return trail[-limit:]

    def fleet_overview(self) -> dict[str, Any]:
        """Combined fleet overview for the observability dashboard."""
        return {
            "timestamp": datetime.now(tz=None).astimezone().isoformat(),
            "agent_health": self.agent_health_dashboard(),
            "program_performance": self.program_performance_dashboard(),
            "cost_summary": self.cost_report("agent"),
            "recent_decisions": self.decision_audit_trail(limit=10),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_metrics": {
                k: v.to_dict() for k, v in self._agent_metrics.items()
            },
            "program_metrics": {
                k: v.to_dict() for k, v in self._program_metrics.items()
            },
            "cost_records": [
                {
                    "agent_id": r.agent_id,
                    "program": r.program,
                    "action": r.action,
                    "tokens_input": r.tokens_input,
                    "tokens_output": r.tokens_output,
                    "timestamp": r.timestamp,
                }
                for r in self._cost_records
            ],
            "decision_trail": self._decision_trail,
        }
