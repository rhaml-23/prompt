"""
Runtime abstraction layer for the compliance agent fleet.

Provides four core interfaces that decouple agent specs from their deployment target:
- StateBackend: read/write/query operations for program and portfolio state
- MessageBus: inter-agent communication (request work, emit results, escalate)
- MemoryStore: session memory operations (state, decisions, archive)
- AuditLog: provenance and audit trail operations

Each interface has two implementations:
- IDE mode: file-based (markdown, JSON, JSONL) — runtime/ide.py
- Deployed mode: database/queue backed (PostgreSQL, NATS) — runtime/deployed.py

Phase 3 additions:
- DynamicRouter / PriorityQueue: load-aware, priority-based work routing
- TrustManager: graduated autonomy with trust levels 1-3
- FleetMetricsCollector: operational metrics and cost tracking
- CommonControlCatalog: cross-framework control mapping and impact analysis

Agents reference the interface, never the implementation. The runtime mode
is selected at startup via runtime/factory.py.
"""

from runtime.interfaces import (
    AuditLog,
    MemoryStore,
    MessageBus,
    StateBackend,
)

__all__ = [
    "StateBackend",
    "MessageBus",
    "MemoryStore",
    "AuditLog",
]
