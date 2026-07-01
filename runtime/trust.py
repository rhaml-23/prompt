"""
Trust level management for graduated autonomy (Phase 3e).

Implements the three-tier trust model:
- Level 1: Human reviews all outputs (default for new agents)
- Level 2: Human reviews exceptions only (earned through consistent quality)
- Level 3: Autonomous within authority boundary, human notified post-hoc

Trust levels are per-agent and per-action-type. They can be promoted based
on quality gate pass rates and revoked on quality gate failure, review
findings, or constitutional violations.

All trust level changes are logged to the audit trail.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TrustRecord:
    """A single trust level change event."""

    agent_id: str
    action_type: str
    old_level: int
    new_level: int
    reason: str
    timestamp: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(tz=None).astimezone().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "old_level": self.old_level,
            "new_level": self.new_level,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "evidence": self.evidence,
        }


PROMOTION_CRITERIA = {
    "1_to_2": {
        "min_actions": 20,
        "min_quality_gate_pass_rate": 0.95,
        "max_escalation_rate": 0.05,
        "min_review_pass_rate": 0.90,
        "window_days": 30,
    },
    "2_to_3": {
        "min_actions": 50,
        "min_quality_gate_pass_rate": 0.99,
        "max_escalation_rate": 0.02,
        "min_review_pass_rate": 0.95,
        "window_days": 60,
    },
}

DEMOTION_TRIGGERS = {
    "quality_gate_failure": {"immediate": True, "levels_down": 1},
    "review_finding_critical": {"immediate": True, "levels_down": 2},
    "review_finding_high": {"immediate": True, "levels_down": 1},
    "constitutional_violation": {"immediate": True, "levels_down": 2},
    "escalation_rate_exceeded": {"immediate": False, "levels_down": 1},
    "error_rate_exceeded": {"immediate": False, "levels_down": 1},
}


class TrustManager:
    """Manages trust levels across the agent fleet.

    Stores trust state per agent per action type. Evaluates promotion
    eligibility based on historical performance. Enforces demotion
    triggers. Logs all changes to the audit trail.
    """

    def __init__(self, default_level: int = 1):
        self.default_level = max(1, min(3, default_level))
        self._trust_state: dict[str, dict[str, int]] = {}
        self._history: list[TrustRecord] = []
        self._action_stats: dict[str, dict[str, dict[str, Any]]] = {}

    def get_level(self, agent_id: str, action_type: str = "__default__") -> int:
        agent_state = self._trust_state.get(agent_id, {})
        return agent_state.get(action_type, agent_state.get("__default__", self.default_level))

    def set_level(
        self,
        agent_id: str,
        level: int,
        reason: str,
        action_type: str = "__default__",
        evidence: dict[str, Any] | None = None,
    ) -> TrustRecord:
        level = max(1, min(3, level))
        old_level = self.get_level(agent_id, action_type)

        if agent_id not in self._trust_state:
            self._trust_state[agent_id] = {}
        self._trust_state[agent_id][action_type] = level

        record = TrustRecord(
            agent_id=agent_id,
            action_type=action_type,
            old_level=old_level,
            new_level=level,
            reason=reason,
            evidence=evidence or {},
        )
        self._history.append(record)
        return record

    def record_action(
        self,
        agent_id: str,
        action_type: str,
        quality_gate_passed: bool = True,
        escalated: bool = False,
        review_passed: bool | None = None,
    ) -> None:
        """Record an action for trust evaluation."""
        if agent_id not in self._action_stats:
            self._action_stats[agent_id] = {}
        if action_type not in self._action_stats[agent_id]:
            self._action_stats[agent_id][action_type] = {
                "total": 0,
                "quality_gate_passed": 0,
                "escalated": 0,
                "review_passed": 0,
                "review_total": 0,
            }

        stats = self._action_stats[agent_id][action_type]
        stats["total"] += 1
        if quality_gate_passed:
            stats["quality_gate_passed"] += 1
        if escalated:
            stats["escalated"] += 1
        if review_passed is not None:
            stats["review_total"] += 1
            if review_passed:
                stats["review_passed"] += 1

    def evaluate_promotion(
        self, agent_id: str, action_type: str = "__default__"
    ) -> dict[str, Any]:
        """Evaluate whether an agent qualifies for trust promotion."""
        current = self.get_level(agent_id, action_type)
        if current >= 3:
            return {"eligible": False, "reason": "Already at maximum trust level."}

        criteria_key = f"{current}_to_{current + 1}"
        criteria = PROMOTION_CRITERIA.get(criteria_key)
        if not criteria:
            return {"eligible": False, "reason": f"No promotion criteria for level {current}."}

        stats = self._action_stats.get(agent_id, {}).get(action_type, {})
        total = stats.get("total", 0)

        if total < criteria["min_actions"]:
            return {
                "eligible": False,
                "reason": f"Insufficient actions: {total}/{criteria['min_actions']}.",
                "progress": total / criteria["min_actions"],
            }

        qg_rate = stats.get("quality_gate_passed", 0) / max(total, 1)
        if qg_rate < criteria["min_quality_gate_pass_rate"]:
            return {
                "eligible": False,
                "reason": f"Quality gate pass rate {qg_rate:.1%} below threshold {criteria['min_quality_gate_pass_rate']:.0%}.",
                "quality_gate_rate": qg_rate,
            }

        esc_rate = stats.get("escalated", 0) / max(total, 1)
        if esc_rate > criteria["max_escalation_rate"]:
            return {
                "eligible": False,
                "reason": f"Escalation rate {esc_rate:.1%} exceeds threshold {criteria['max_escalation_rate']:.0%}.",
                "escalation_rate": esc_rate,
            }

        review_total = stats.get("review_total", 0)
        if review_total > 0:
            review_rate = stats.get("review_passed", 0) / review_total
            if review_rate < criteria["min_review_pass_rate"]:
                return {
                    "eligible": False,
                    "reason": f"Review pass rate {review_rate:.1%} below threshold {criteria['min_review_pass_rate']:.0%}.",
                    "review_rate": review_rate,
                }

        return {
            "eligible": True,
            "current_level": current,
            "proposed_level": current + 1,
            "stats": {
                "total_actions": total,
                "quality_gate_rate": qg_rate,
                "escalation_rate": esc_rate,
                "review_rate": (
                    stats.get("review_passed", 0) / max(review_total, 1)
                    if review_total > 0
                    else None
                ),
            },
        }

    def promote(
        self, agent_id: str, action_type: str = "__default__"
    ) -> TrustRecord | None:
        """Promote an agent if eligible. Returns the trust record or None."""
        evaluation = self.evaluate_promotion(agent_id, action_type)
        if not evaluation["eligible"]:
            return None

        return self.set_level(
            agent_id=agent_id,
            level=evaluation["proposed_level"],
            reason=f"Promoted based on performance: {evaluation['stats']}",
            action_type=action_type,
            evidence=evaluation["stats"],
        )

    def demote(
        self,
        agent_id: str,
        trigger: str,
        action_type: str = "__default__",
        details: str = "",
    ) -> TrustRecord | None:
        """Demote an agent based on a trigger event."""
        trigger_config = DEMOTION_TRIGGERS.get(trigger)
        if not trigger_config:
            return None

        current = self.get_level(agent_id, action_type)
        new_level = max(1, current - trigger_config["levels_down"])

        if new_level == current:
            return None

        return self.set_level(
            agent_id=agent_id,
            level=new_level,
            reason=f"Demoted due to {trigger}: {details}",
            action_type=action_type,
            evidence={"trigger": trigger, "details": details},
        )

    def requires_human_review(
        self, agent_id: str, action_type: str = "__default__"
    ) -> bool:
        """Check whether this agent+action requires human review."""
        level = self.get_level(agent_id, action_type)
        return level == 1

    def requires_exception_review(
        self, agent_id: str, action_type: str = "__default__"
    ) -> bool:
        """Check whether this agent+action requires review only on exceptions."""
        level = self.get_level(agent_id, action_type)
        return level == 2

    def is_autonomous(
        self, agent_id: str, action_type: str = "__default__"
    ) -> bool:
        """Check whether this agent+action can operate autonomously."""
        level = self.get_level(agent_id, action_type)
        return level == 3

    def fleet_trust_state(self) -> dict[str, Any]:
        """Return trust state for all agents."""
        return {
            "default_level": self.default_level,
            "agents": {
                agent_id: {
                    action: level
                    for action, level in actions.items()
                }
                for agent_id, actions in self._trust_state.items()
            },
            "total_changes": len(self._history),
            "recent_changes": [r.to_dict() for r in self._history[-10:]],
        }

    def agent_trust_report(self, agent_id: str) -> dict[str, Any]:
        """Detailed trust report for a specific agent."""
        state = self._trust_state.get(agent_id, {})
        stats = self._action_stats.get(agent_id, {})
        history = [r for r in self._history if r.agent_id == agent_id]

        return {
            "agent_id": agent_id,
            "trust_levels": state or {"__default__": self.default_level},
            "action_stats": stats,
            "history": [r.to_dict() for r in history],
            "promotions_available": {
                action: self.evaluate_promotion(agent_id, action)
                for action in (list(stats.keys()) or ["__default__"])
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "default_level": self.default_level,
            "trust_state": self._trust_state,
            "history": [r.to_dict() for r in self._history],
            "action_stats": self._action_stats,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrustManager":
        mgr = cls(default_level=data.get("default_level", 1))
        mgr._trust_state = data.get("trust_state", {})
        mgr._action_stats = data.get("action_stats", {})
        for h in data.get("history", []):
            mgr._history.append(TrustRecord(
                agent_id=h["agent_id"],
                action_type=h["action_type"],
                old_level=h["old_level"],
                new_level=h["new_level"],
                reason=h["reason"],
                timestamp=h.get("timestamp", ""),
                evidence=h.get("evidence", {}),
            ))
        return mgr
