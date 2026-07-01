"""
Runtime factory — selects concrete implementations based on deployment mode.

Usage:
    from runtime.factory import create_runtime

    rt = create_runtime("ide")  # or "deployed"
    state = rt.state.read_run("fedramp-high")
    rt.audit.write_entry({...})
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.interfaces import AuditLog, MemoryStore, MessageBus, StateBackend


@dataclass
class Runtime:
    """Container for all runtime interface implementations."""

    state: StateBackend
    bus: MessageBus
    memory: MemoryStore
    audit: AuditLog
    mode: str


def create_runtime(
    mode: str | None = None, repo_root: Path | None = None
) -> Runtime:
    """Create a Runtime with implementations matching the deployment mode.

    Args:
        mode: "ide" or "deployed". If None, reads COMPLIANCE_RUNTIME_MODE
              env var, defaulting to "ide".
        repo_root: Override repo root path. Auto-detected if None.
    """
    if mode is None:
        mode = os.environ.get("COMPLIANCE_RUNTIME_MODE", "ide")

    if mode == "ide":
        return _create_ide_runtime(repo_root)
    elif mode == "deployed":
        return _create_deployed_runtime(repo_root)
    else:
        raise ValueError(
            f'Unknown runtime mode: "{mode}". Must be "ide" or "deployed".'
        )


def _create_ide_runtime(repo_root: Path | None) -> Runtime:
    from runtime.ide import (
        FileAuditLog,
        FileMemoryStore,
        FileMessageBus,
        FileStateBackend,
    )

    return Runtime(
        state=FileStateBackend(repo_root),
        bus=FileMessageBus(repo_root),
        memory=FileMemoryStore(repo_root),
        audit=FileAuditLog(repo_root),
        mode="ide",
    )


def _create_deployed_runtime(repo_root: Path | None) -> Runtime:
    """Deployed mode — PostgreSQL/S3/NATS backed implementations.

    Requires environment variables:
    - DATABASE_URL — PostgreSQL connection string
    - NATS_URL — NATS server URL
    - S3_BUCKET (optional) — S3 bucket for large artifact storage
    - S3_ENDPOINT (optional) — S3-compatible endpoint URL
    """
    from runtime.deployed import (
        DbAuditLog,
        DbMemoryStore,
        DbStateBackend,
        NatsMessageBus,
    )

    return Runtime(
        state=DbStateBackend(),
        bus=NatsMessageBus(),
        memory=DbMemoryStore(),
        audit=DbAuditLog(),
        mode="deployed",
    )
