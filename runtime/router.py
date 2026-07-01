"""
Dynamic work router for the compliance fleet.

Replaces the static routing table in session-init-spec.md with a priority-aware,
load-balanced router that considers agent availability, program state, and urgency.

In IDE mode: presents routing recommendation with rationale to the lead program manager.
In deployed mode: routes automatically within authority boundary, escalates outside it.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any


class Priority(IntEnum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class WorkItem:
    """Incoming work to be routed."""

    description: str
    input_type: str = "unknown"
    program: str = ""
    urgency: str = "normal"
    work_pattern: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def priority(self) -> Priority:
        mapping = {
            "immediate": Priority.CRITICAL,
            "today": Priority.HIGH,
            "this_week": Priority.NORMAL,
            "no_deadline": Priority.LOW,
        }
        return mapping.get(self.urgency, Priority.NORMAL)


@dataclass
class RoutingDecision:
    """Result of the routing engine's decision."""

    target_spec: str
    target_agent: str
    priority: Priority
    rationale: str
    confidence: float
    requires_confirmation: bool = True
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentLoad:
    """Current load information for an agent."""

    agent_id: str
    active_tasks: int = 0
    last_active: datetime | None = None
    error_rate_24h: float = 0.0
    available: bool = True


ROUTING_RULES: list[dict[str, Any]] = [
    {"pattern": r"new\s+program.*full\s+build", "spec": "functions/program-intake-spec.md", "agent": "program", "intent": "full_build"},
    {"pattern": r"new\s+program", "spec": "engine/program-pipeline-orchestrator.md", "agent": "program", "intent": "new_program"},
    {"pattern": r"vendor\s+(issue|check|review|scoring)", "spec": "engine/program-pipeline-orchestrator.md", "agent": "program", "intent": "vendor_review"},
    {"pattern": r"(status\s+check|program\s+status|monitoring)", "spec": "engine/program-pipeline-orchestrator.md", "agent": "program", "intent": "monitoring_run"},
    {"pattern": r"(full\s+reassessment|full\s+run)", "spec": "engine/program-pipeline-orchestrator.md", "agent": "program", "intent": "full_run"},
    {"pattern": r"portfolio\s+(briefing|review|status)", "spec": "engine/portfolio-orchestrator.md", "agent": "coordinator", "intent": "briefing"},
    {"pattern": r"weekly\s+session", "spec": "engine/weekly-session-spec.md", "agent": "program", "intent": "weekly_session"},
    {"pattern": r"(intel|threat)\s+scan", "spec": "functions/external-intel-spec.md", "agent": "intelligence", "intent": "intel_scan"},
    {"pattern": r"control\s+coverage", "spec": "functions/control-coverage-spec.md", "agent": "program", "intent": "coverage"},
    {"pattern": r"risk\s+register|poa.?m", "spec": "functions/risk-register-spec.md", "agent": "program", "intent": "risk"},
    {"pattern": r"(red\s*team|adversarial)\s+review", "spec": "functions/compliance-redteam-spec.md", "agent": "review", "intent": "redteam"},
    {"pattern": r"entropy\s+(analysis|review)", "spec": "functions/compliance-entropy-spec.md", "agent": "review", "intent": "entropy"},
    {"pattern": r"(status\s+report|stakeholder\s+communication|meeting\s+recap|draft)", "spec": "functions/program-comms-spec.md", "agent": "program", "intent": "comms"},
    {"pattern": r"auditor\s+view", "spec": "functions/auditor-view-spec.md", "agent": "review", "intent": "auditor_view"},
    {"pattern": r"management\s+system|isms", "spec": "functions/management-system-assembler-spec.md", "agent": "review", "intent": "mgmt_system"},
    {"pattern": r"control\s+assessment|template\s+fill", "spec": "functions/control-assessment-spec.md", "agent": "program", "intent": "control_assessment"},
    {"pattern": r"compliance\s+doc(ument)?\s+gen", "spec": "functions/compliance-doc-generator-spec.md", "agent": "program", "intent": "doc_gen"},
    {"pattern": r"(post.?run|run)\s+review", "spec": "agents/run-reviewer.md", "agent": "review", "intent": "run_review"},
    {"pattern": r"calendar", "spec": "functions/calendar-output-spec.md", "agent": "program", "intent": "calendar"},
    {"pattern": r"memory\s+housekeeping", "spec": "memory/memory-housekeeping-spec.md", "agent": "program", "intent": "housekeeping"},
    {"pattern": r"memory\s+migration", "spec": "memory/memory-migration-spec.md", "agent": "program", "intent": "migration"},
    {"pattern": r"evidence\s+(check|monitor|stale|gap|lifecycle)", "spec": "functions/evidence-lifecycle-spec.md", "agent": "evidence", "intent": "evidence_check"},
    {"pattern": r"iso.?42001|aims|ai\s+management\s+system", "spec": "agents/framework-iso42001.md", "agent": "framework-iso42001", "intent": "framework_query"},
    {"pattern": r"crosswalk|cross.?framework|common\s+control", "spec": "functions/cross-framework-intel-spec.md", "agent": "intelligence", "intent": "crosswalk"},
]


class DynamicRouter:
    """Priority-aware, load-balanced work router.

    Combines pattern matching (like the static routing table) with
    dynamic signals: agent load, program health, priority queuing,
    and trust level.
    """

    def __init__(
        self,
        agent_loads: dict[str, AgentLoad] | None = None,
        program_states: dict[str, dict[str, Any]] | None = None,
        trust_levels: dict[str, int] | None = None,
    ):
        self.agent_loads = agent_loads or {}
        self.program_states = program_states or {}
        self.trust_levels = trust_levels or {}

    def route(self, work: WorkItem) -> RoutingDecision:
        rule = self._match_pattern(work)

        if rule is None:
            return RoutingDecision(
                target_spec="",
                target_agent="coordinator",
                priority=work.priority,
                rationale="No routing rule matched — escalate to coordinator for clarification.",
                confidence=0.0,
                requires_confirmation=True,
            )

        priority = self._adjust_priority(work, rule)
        confidence = self._compute_confidence(work, rule)
        agent = self._select_agent(rule["agent"], priority)
        requires_confirmation = self._needs_confirmation(agent, rule)

        return RoutingDecision(
            target_spec=rule["spec"],
            target_agent=agent,
            priority=priority,
            rationale=self._build_rationale(work, rule, priority, agent),
            confidence=confidence,
            requires_confirmation=requires_confirmation,
            context={"intent": rule.get("intent", ""), "work_pattern": work.work_pattern},
        )

    def route_batch(self, items: list[WorkItem]) -> list[RoutingDecision]:
        """Route multiple items, sorted by priority (critical first)."""
        sorted_items = sorted(items, key=lambda w: w.priority)
        return [self.route(item) for item in sorted_items]

    def _match_pattern(self, work: WorkItem) -> dict[str, Any] | None:
        text = f"{work.description} {work.work_pattern}".lower()
        for rule in ROUTING_RULES:
            if re.search(rule["pattern"], text, re.IGNORECASE):
                return rule
        return None

    def _adjust_priority(self, work: WorkItem, rule: dict[str, Any]) -> Priority:
        base = work.priority

        if work.program and work.program in self.program_states:
            state = self.program_states[work.program]
            health = state.get("program_state", {}).get("overall_health", "unknown")
            if health == "red" and base > Priority.HIGH:
                return Priority.HIGH

        if rule.get("intent") in ("intel_scan", "evidence_check"):
            if base > Priority.HIGH:
                return Priority.HIGH

        return base

    def _compute_confidence(self, work: WorkItem, rule: dict[str, Any]) -> float:
        score = 0.7
        if work.program:
            score += 0.1
        if work.work_pattern:
            score += 0.1
        if work.input_type != "unknown":
            score += 0.1
        return min(score, 1.0)

    def _select_agent(self, agent_type: str, priority: Priority) -> str:
        load = self.agent_loads.get(agent_type)
        if load and not load.available:
            if priority <= Priority.HIGH:
                return agent_type
            return "coordinator"
        return agent_type

    def _needs_confirmation(self, agent: str, rule: dict[str, Any]) -> bool:
        trust = self.trust_levels.get(agent, 1)
        if trust >= 3:
            return False
        if trust >= 2 and rule.get("intent") in (
            "monitoring_run", "intel_scan", "evidence_check",
        ):
            return False
        return True

    def _build_rationale(
        self,
        work: WorkItem,
        rule: dict[str, Any],
        priority: Priority,
        agent: str,
    ) -> str:
        parts = [f"Matched pattern → {rule['spec']}."]
        if work.program:
            health = (
                self.program_states.get(work.program, {})
                .get("program_state", {})
                .get("overall_health", "unknown")
            )
            parts.append(f"Program '{work.program}' health: {health}.")
        parts.append(f"Priority: {priority.name.lower()}.")
        parts.append(f"Assigned to: {agent} agent.")
        if not self._needs_confirmation(agent, rule):
            parts.append("Auto-routing (trust level sufficient).")
        return " ".join(parts)


class PriorityQueue:
    """Priority queue for work items awaiting routing or execution.

    Items are dequeued in priority order (CRITICAL before HIGH before
    NORMAL before LOW). Within the same priority, FIFO ordering applies.
    """

    def __init__(self):
        self._items: list[tuple[Priority, int, WorkItem, RoutingDecision | None]] = []
        self._counter = 0

    def enqueue(
        self, work: WorkItem, decision: RoutingDecision | None = None
    ) -> int:
        self._counter += 1
        self._items.append((work.priority, self._counter, work, decision))
        self._items.sort(key=lambda x: (x[0], x[1]))
        return self._counter

    def dequeue(self) -> tuple[WorkItem, RoutingDecision | None] | None:
        if not self._items:
            return None
        _, _, work, decision = self._items.pop(0)
        return work, decision

    def peek(self) -> tuple[WorkItem, RoutingDecision | None] | None:
        if not self._items:
            return None
        _, _, work, decision = self._items[0]
        return work, decision

    @property
    def size(self) -> int:
        return len(self._items)

    def items_by_priority(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for priority, _, _, _ in self._items:
            name = priority.name.lower()
            counts[name] = counts.get(name, 0) + 1
        return counts

    def to_dict(self) -> list[dict[str, Any]]:
        return [
            {
                "priority": p.name.lower(),
                "description": w.description,
                "program": w.program,
                "target": d.target_spec if d else "",
                "agent": d.target_agent if d else "",
            }
            for p, _, w, d in self._items
        ]
