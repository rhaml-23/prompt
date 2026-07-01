"""
Abstract interfaces for the compliance fleet runtime abstraction layer.

These interfaces define the contract between agent specs and their runtime
environment. Concrete implementations are selected at startup based on
deployment mode (IDE vs deployed).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class StateBackend(ABC):
    """Interface for reading and writing program and portfolio state.

    IDE implementation: markdown/JSON files in runs/, data/
    Deployed implementation: PostgreSQL or S3-backed object store
    """

    @abstractmethod
    def read_run(self, program: str, run_id: str = "latest") -> dict[str, Any]:
        """Read a run JSON for a program. Defaults to latest."""
        ...

    @abstractmethod
    def write_run(
        self, program: str, run_date: str, data: dict[str, Any]
    ) -> str:
        """Write a run JSON. Returns the path/key of the written state."""
        ...

    @abstractmethod
    def list_runs(self, program: str) -> list[str]:
        """List available run IDs for a program, most recent first."""
        ...

    @abstractmethod
    def read_portfolio(self) -> dict[str, Any]:
        """Read the current portfolio state."""
        ...

    @abstractmethod
    def write_portfolio(self, data: dict[str, Any]) -> str:
        """Write portfolio state. Returns path/key."""
        ...

    @abstractmethod
    def list_programs(self) -> list[str]:
        """List all known program slugs."""
        ...

    @abstractmethod
    def read_data(self, path: str) -> Any:
        """Read arbitrary data by path (relative to data root)."""
        ...

    @abstractmethod
    def write_data(self, path: str, data: Any) -> str:
        """Write arbitrary data. Returns path/key."""
        ...

    @abstractmethod
    def query(
        self, collection: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Query state by collection and optional filters."""
        ...


class MessageBus(ABC):
    """Interface for inter-agent communication.

    IDE implementation: spec invocation chains, human routing
    Deployed implementation: NATS/Kafka message queue or gRPC
    """

    @abstractmethod
    def send(
        self,
        target: str,
        message_type: str,
        payload: dict[str, Any],
        sender: str = "",
    ) -> str:
        """Send a message to a target agent. Returns message ID."""
        ...

    @abstractmethod
    def receive(
        self, agent_id: str, message_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Receive pending messages for an agent, optionally filtered by type."""
        ...

    @abstractmethod
    def broadcast(
        self,
        message_type: str,
        payload: dict[str, Any],
        sender: str = "",
    ) -> str:
        """Broadcast a message to all agents. Returns message ID."""
        ...

    @abstractmethod
    def escalate(
        self,
        finding: str,
        context: dict[str, Any],
        severity: str = "normal",
        sender: str = "",
    ) -> str:
        """Escalate a finding to the lead program manager. Returns escalation ID."""
        ...

    @abstractmethod
    def acknowledge(self, message_id: str, agent_id: str) -> None:
        """Acknowledge receipt and processing of a message."""
        ...


class MemoryStore(ABC):
    """Interface for session memory operations.

    IDE implementation: three-file markdown model (memory/)
    Deployed implementation: structured DB with TTL and archival
    """

    @abstractmethod
    def read_state(self, program: str) -> str:
        """Read the hot layer state for a program."""
        ...

    @abstractmethod
    def write_state(self, program: str, content: str) -> None:
        """Write/overwrite the hot layer state for a program."""
        ...

    @abstractmethod
    def read_decisions(
        self, program: str, limit: int = 20
    ) -> list[str]:
        """Read recent decision log entries (tail). Returns lines."""
        ...

    @abstractmethod
    def append_decision(self, program: str, entry: str) -> None:
        """Append a single entry to the decisions log."""
        ...

    @abstractmethod
    def query_decisions(
        self, program: str, event_type: str | None = None
    ) -> list[str]:
        """Query decisions log, optionally filtered by event type."""
        ...

    @abstractmethod
    def read_archive(self, program: str) -> str:
        """Read the cold layer archive for a program."""
        ...

    @abstractmethod
    def write_archive(self, program: str, content: str) -> None:
        """Write/overwrite the archive for a program."""
        ...

    @abstractmethod
    def list_programs(self) -> list[str]:
        """List all programs with memory files."""
        ...

    @abstractmethod
    def decision_count(self, program: str) -> int:
        """Return the number of entries in the decisions log."""
        ...


class AuditLog(ABC):
    """Interface for provenance and audit trail operations.

    IDE implementation: logs/provenance.jsonl (append-only JSONL)
    Deployed implementation: append-only event store with query API
    """

    @abstractmethod
    def write_entry(self, entry: dict[str, Any]) -> str:
        """Append an audit entry. Returns entry ID.

        Required fields: agent_id, spec_version, action, timestamp
        Recommended fields: input_hash, output_hash, constitution_version,
                          trust_level, program, output_path
        """
        ...

    @abstractmethod
    def query(
        self,
        program: str | None = None,
        agent_id: str | None = None,
        action: str | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Query audit entries with optional filters."""
        ...

    @abstractmethod
    def tail(self, n: int = 10) -> list[dict[str, Any]]:
        """Return the most recent n entries."""
        ...

    @abstractmethod
    def summary(
        self, program: str | None = None
    ) -> dict[str, Any]:
        """Return summary statistics for the audit log."""
        ...

    @abstractmethod
    def verify_integrity(self) -> tuple[bool, str]:
        """Verify the audit log has not been tampered with.

        Returns (is_valid, detail_message).
        For chained logs, verifies hash chain continuity.
        """
        ...
