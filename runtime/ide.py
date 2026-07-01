"""
IDE-mode implementations of the runtime abstraction interfaces.

File-based implementations using markdown, JSON, and JSONL files
in the existing repo structure. These are the implementations used
when running in Cursor or any other IDE/local environment.
"""

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.interfaces import AuditLog, MemoryStore, MessageBus, StateBackend


def _resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    anchors = {"config", "engine", "functions", "scripts"}
    for candidate in [here.parent, here, here.parent.parent]:
        if sum(1 for a in anchors if (candidate / a).exists()) >= 3:
            return candidate
    return Path.cwd()


def atomic_write_json(path: Path, data: dict[str, Any] | list[Any]) -> None:
    """Write JSON atomically: temp file in the same directory, then replace.

    Prevents torn reads if the process dies mid-write. Used for checkpoints
    and draft run files per engine/crash-resilience-spec.md.
    """
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=False)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


class FileStateBackend(StateBackend):
    """File-based state backend using runs/ and data/ directories."""

    def __init__(self, repo_root: Path | None = None):
        self.root = repo_root or _resolve_repo_root()
        self.runs_dir = self.root / "runs"
        self.data_dir = self.root / "data"

    def read_run(self, program: str, run_id: str = "latest") -> dict[str, Any]:
        path = self.runs_dir / program / f"{run_id}.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def write_run(
        self, program: str, run_date: str, data: dict[str, Any]
    ) -> str:
        program_dir = self.runs_dir / program
        program_dir.mkdir(parents=True, exist_ok=True)

        dated_path = program_dir / f"{run_date}-run.json"
        latest_path = program_dir / "latest.json"

        content = json.dumps(data, indent=2, ensure_ascii=False)
        dated_path.write_text(content, encoding="utf-8")
        latest_path.write_text(content, encoding="utf-8")

        return str(dated_path.relative_to(self.root))

    def list_runs(self, program: str) -> list[str]:
        program_dir = self.runs_dir / program
        if not program_dir.exists():
            return []
        runs = [
            f.stem
            for f in sorted(program_dir.glob("*.json"), reverse=True)
            if f.name != "latest.json"
        ]
        return runs

    def read_portfolio(self) -> dict[str, Any]:
        path = self.data_dir / "portfolio" / "latest.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def write_portfolio(self, data: dict[str, Any]) -> str:
        path = self.data_dir / "portfolio" / "latest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(data, indent=2, ensure_ascii=False)
        path.write_text(content, encoding="utf-8")
        return str(path.relative_to(self.root))

    def list_programs(self) -> list[str]:
        if not self.runs_dir.exists():
            return []
        return sorted(
            d.name
            for d in self.runs_dir.iterdir()
            if d.is_dir() and (d / "latest.json").exists()
        )

    def read_data(self, path: str) -> Any:
        full_path = self.data_dir / path
        if not full_path.exists():
            return None
        if full_path.suffix == ".json":
            return json.loads(full_path.read_text(encoding="utf-8"))
        return full_path.read_text(encoding="utf-8")

    def write_data(self, path: str, data: Any) -> str:
        full_path = self.data_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, (dict, list)):
            content = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            content = str(data)
        full_path.write_text(content, encoding="utf-8")
        return str(full_path.relative_to(self.root))

    def query(
        self, collection: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        results = []
        collection_dir = self.data_dir / collection
        if not collection_dir.exists():
            return results
        for f in collection_dir.rglob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    if filters:
                        if all(data.get(k) == v for k, v in filters.items()):
                            results.append(data)
                    else:
                        results.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        return results

    def write_work_checkpoint(
        self, program: str, checkpoint_id: str, data: dict[str, Any]
    ) -> str:
        """Write data/[program]/checkpoints/[checkpoint_id].json atomically."""
        out = self.data_dir / program / "checkpoints" / f"{checkpoint_id}.json"
        atomic_write_json(out, data)
        return str(out.relative_to(self.root))

    def read_work_checkpoint(
        self, program: str, checkpoint_id: str
    ) -> dict[str, Any]:
        path = self.data_dir / program / "checkpoints" / f"{checkpoint_id}.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def write_draft_run(self, program: str, data: dict[str, Any]) -> str:
        """Write runs/[program]/draft-run.json atomically (WIP pipeline envelope)."""
        program_dir = self.runs_dir / program
        program_dir.mkdir(parents=True, exist_ok=True)
        out = program_dir / "draft-run.json"
        atomic_write_json(out, data)
        return str(out.relative_to(self.root))

    def read_draft_run(self, program: str) -> dict[str, Any]:
        path = self.runs_dir / program / "draft-run.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def remove_draft_run(self, program: str) -> None:
        path = self.runs_dir / program / "draft-run.json"
        if path.exists():
            path.unlink()


class FileMessageBus(MessageBus):
    """File-based message bus for IDE mode.

    In IDE mode, messages are primarily human-routed through the composer.
    This implementation logs messages for traceability and supports
    the escalation protocol.
    """

    def __init__(self, repo_root: Path | None = None):
        self.root = repo_root or _resolve_repo_root()
        self.messages_dir = self.root / "data" / "messages"
        self.messages_dir.mkdir(parents=True, exist_ok=True)

    def send(
        self,
        target: str,
        message_type: str,
        payload: dict[str, Any],
        sender: str = "",
    ) -> str:
        msg_id = str(uuid.uuid4())[:8]
        message = {
            "id": msg_id,
            "target": target,
            "type": message_type,
            "sender": sender,
            "timestamp": datetime.now(tz=None).astimezone().isoformat(),
            "payload": payload,
            "acknowledged": False,
        }
        path = self.messages_dir / f"{msg_id}.json"
        path.write_text(
            json.dumps(message, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return msg_id

    def receive(
        self, agent_id: str, message_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        messages = []
        for f in sorted(self.messages_dir.glob("*.json")):
            try:
                msg = json.loads(f.read_text(encoding="utf-8"))
                if msg.get("target") != agent_id:
                    continue
                if msg.get("acknowledged"):
                    continue
                if message_types and msg.get("type") not in message_types:
                    continue
                messages.append(msg)
            except (json.JSONDecodeError, OSError):
                continue
        return messages

    def broadcast(
        self,
        message_type: str,
        payload: dict[str, Any],
        sender: str = "",
    ) -> str:
        msg_id = str(uuid.uuid4())[:8]
        message = {
            "id": msg_id,
            "target": "__broadcast__",
            "type": message_type,
            "sender": sender,
            "timestamp": datetime.now(tz=None).astimezone().isoformat(),
            "payload": payload,
            "acknowledged": False,
        }
        path = self.messages_dir / f"{msg_id}.json"
        path.write_text(
            json.dumps(message, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return msg_id

    def escalate(
        self,
        finding: str,
        context: dict[str, Any],
        severity: str = "normal",
        sender: str = "",
    ) -> str:
        return self.send(
            target="lead program manager",
            message_type="ESCALATION",
            payload={"finding": finding, "severity": severity, **context},
            sender=sender,
        )

    def acknowledge(self, message_id: str, agent_id: str) -> None:
        path = self.messages_dir / f"{message_id}.json"
        if path.exists():
            msg = json.loads(path.read_text(encoding="utf-8"))
            msg["acknowledged"] = True
            msg["acknowledged_by"] = agent_id
            msg["acknowledged_at"] = datetime.now(tz=None).astimezone().isoformat()
            path.write_text(
                json.dumps(msg, indent=2, ensure_ascii=False), encoding="utf-8"
            )


class FileMemoryStore(MemoryStore):
    """File-based memory store using the three-file model in memory/."""

    def __init__(self, repo_root: Path | None = None):
        self.root = repo_root or _resolve_repo_root()
        self.memory_dir = self.root / "memory"

    def read_state(self, program: str) -> str:
        path = self.memory_dir / f"{program}-memory.md"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def write_state(self, program: str, content: str) -> None:
        path = self.memory_dir / f"{program}-memory.md"
        path.write_text(content, encoding="utf-8")

    def read_decisions(self, program: str, limit: int = 20) -> list[str]:
        path = self.memory_dir / f"{program}-decisions.log"
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        non_comment = [l for l in lines if l.strip() and not l.startswith("#")]
        return non_comment[-limit:]

    def append_decision(self, program: str, entry: str) -> None:
        path = self.memory_dir / f"{program}-decisions.log"
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry.rstrip("\n") + "\n")

    def query_decisions(
        self, program: str, event_type: str | None = None
    ) -> list[str]:
        path = self.memory_dir / f"{program}-decisions.log"
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        if event_type:
            return [l for l in lines if event_type in l]
        return [l for l in lines if l.strip() and not l.startswith("#")]

    def read_archive(self, program: str) -> str:
        path = self.memory_dir / f"{program}-archive.md"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def write_archive(self, program: str, content: str) -> None:
        path = self.memory_dir / f"{program}-archive.md"
        path.write_text(content, encoding="utf-8")

    def list_programs(self) -> list[str]:
        programs = set()
        for f in self.memory_dir.glob("*-memory.md"):
            slug = f.name.replace("-memory.md", "")
            if slug != "program":
                programs.add(slug)
        return sorted(programs)

    def decision_count(self, program: str) -> int:
        path = self.memory_dir / f"{program}-decisions.log"
        if not path.exists():
            return 0
        lines = path.read_text(encoding="utf-8").splitlines()
        return len([l for l in lines if l.strip() and not l.startswith("#")])

    def write_session_wip(self, program: str, content: str) -> None:
        """Write in-progress session notes to [program]-wip.md (overwrite each update)."""
        path = self.memory_dir / f"{program}-wip.md"
        path.write_text(content, encoding="utf-8")

    def read_session_wip(self, program: str) -> str:
        path = self.memory_dir / f"{program}-wip.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def clear_session_wip(self, program: str) -> None:
        """Remove WIP file after successful session close."""
        path = self.memory_dir / f"{program}-wip.md"
        if path.exists():
            path.unlink()


class FileAuditLog(AuditLog):
    """File-based audit log using logs/provenance.jsonl."""

    def __init__(self, repo_root: Path | None = None):
        self.root = repo_root or _resolve_repo_root()
        self.log_path = self.root / "logs" / "provenance.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def write_entry(self, entry: dict[str, Any]) -> str:
        entry_id = str(uuid.uuid4())[:12]
        entry["id"] = entry_id
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now(tz=None).astimezone().isoformat()

        prior_hash = self._last_hash()
        entry["prior_hash"] = prior_hash
        entry_json = json.dumps(entry, ensure_ascii=False)
        entry_hash = hashlib.sha256(entry_json.encode()).hexdigest()[:16]
        entry["entry_hash"] = entry_hash

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry_id

    def query(
        self,
        program: str | None = None,
        agent_id: str | None = None,
        action: str | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        entries = self._read_all()
        results = []
        for e in reversed(entries):
            if program and e.get("program") != program:
                continue
            if agent_id and e.get("agent_id") != agent_id:
                continue
            if action and e.get("action") != action:
                continue
            if since:
                ts = e.get("timestamp", "")
                try:
                    entry_time = datetime.fromisoformat(ts)
                    if entry_time < since:
                        continue
                except ValueError:
                    continue
            results.append(e)
            if len(results) >= limit:
                break
        return results

    def tail(self, n: int = 10) -> list[dict[str, Any]]:
        entries = self._read_all()
        return entries[-n:]

    def summary(self, program: str | None = None) -> dict[str, Any]:
        entries = self._read_all()
        if program:
            entries = [e for e in entries if e.get("program") == program]
        agents = set(e.get("agent_id", "") for e in entries)
        actions = {}
        for e in entries:
            a = e.get("action", "unknown")
            actions[a] = actions.get(a, 0) + 1
        return {
            "total_entries": len(entries),
            "unique_agents": len(agents),
            "actions": actions,
            "earliest": entries[0].get("timestamp") if entries else None,
            "latest": entries[-1].get("timestamp") if entries else None,
        }

    def verify_integrity(self) -> tuple[bool, str]:
        entries = self._read_all()
        if not entries:
            return True, "Empty log — no entries to verify."

        for i, entry in enumerate(entries):
            if i == 0:
                continue
            expected_prior = entries[i - 1].get("entry_hash", "")
            actual_prior = entry.get("prior_hash", "")
            if expected_prior and actual_prior and expected_prior != actual_prior:
                return (
                    False,
                    f"Hash chain broken at entry {i}: "
                    f"expected prior_hash={expected_prior}, "
                    f"got {actual_prior}",
                )

        return True, f"Integrity verified — {len(entries)} entries, chain intact."

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        entries = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries

    def _last_hash(self) -> str:
        entries = self._read_all()
        if not entries:
            return "genesis"
        return entries[-1].get("entry_hash", "unknown")
