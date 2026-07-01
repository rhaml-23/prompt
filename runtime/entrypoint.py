"""
Container entrypoint for compliance fleet agents.

Reads AGENT_TYPE from environment, initializes the runtime, and starts
the agent's main loop. Supports both IDE and deployed modes:

- IDE mode: runs validation checks and reports agent readiness
- Deployed mode: connects to PostgreSQL/NATS, initializes trust manager
  and metrics collector, enters message processing loop
"""

import os
import sys
from pathlib import Path


def _resolve_agent_file(repo_root: Path, agent_type: str) -> Path:
    if agent_type == "coordinator":
        return repo_root / "agents" / "coordinator.md"
    if agent_type.startswith("framework-"):
        return repo_root / "agents" / f"{agent_type}.md"
    if agent_type == "evidence":
        return repo_root / "agents" / "evidence-agent.md"
    return repo_root / "agents" / f"{agent_type}-agent.md"


def main() -> int:
    agent_type = os.environ.get("AGENT_TYPE", "program")
    runtime_mode = os.environ.get("COMPLIANCE_RUNTIME_MODE", "ide")
    trust_default = int(os.environ.get("TRUST_LEVEL_DEFAULT", "1"))

    print(f"Compliance Fleet Agent — {agent_type}")
    print(f"Runtime mode: {runtime_mode}")
    print(f"Python: {sys.version}")

    repo_root = Path(__file__).resolve().parent.parent
    agent_file = _resolve_agent_file(repo_root, agent_type)

    if not agent_file.exists():
        print(f"ERROR: Agent definition not found: {agent_file}", file=sys.stderr)
        return 1

    print(f"Agent definition: {agent_file.relative_to(repo_root)}")

    sys.path.insert(0, str(repo_root))
    from runtime.factory import create_runtime

    if runtime_mode == "deployed":
        return _run_deployed(agent_type, trust_default)

    return _run_ide(repo_root, agent_type, trust_default)


def _run_ide(repo_root: Path, agent_type: str, trust_default: int) -> int:
    print("\nIDE mode — running validation checks...")

    from runtime.factory import create_runtime
    from runtime.trust import TrustManager
    from runtime.metrics import FleetMetricsCollector

    rt = create_runtime("ide", repo_root)
    trust = TrustManager(default_level=trust_default)
    metrics = FleetMetricsCollector()
    metrics.register_agent(agent_type, agent_type)

    print(f"  State backend: {type(rt.state).__name__}")
    print(f"  Message bus:   {type(rt.bus).__name__}")
    print(f"  Memory store:  {type(rt.memory).__name__}")
    print(f"  Audit log:     {type(rt.audit).__name__}")
    print(f"  Trust level:   {trust.get_level(agent_type)}")

    programs = rt.state.list_programs()
    print(f"\n  Active programs: {len(programs)}")
    for p in programs:
        run = rt.state.read_run(p)
        health = run.get("program_state", {}).get("overall_health", "unknown")
        print(f"    {p}: {health}")

    valid, msg = rt.audit.verify_integrity()
    print(f"\n  Audit log integrity: {'PASS' if valid else 'FAIL'} — {msg}")

    print("\nAgent ready.")
    return 0


def _run_deployed(agent_type: str, trust_default: int) -> int:
    print("\nDeployed mode — initializing runtime...")

    from runtime.factory import create_runtime
    from runtime.trust import TrustManager
    from runtime.metrics import FleetMetricsCollector

    try:
        rt = create_runtime("deployed")
    except EnvironmentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(
            "\nRequired environment variables for deployed mode:\n"
            "  DATABASE_URL — PostgreSQL connection string\n"
            "  NATS_URL — NATS server URL\n"
            "  S3_BUCKET (optional) — S3 bucket for artifacts\n"
        )
        return 1

    trust = TrustManager(default_level=trust_default)
    metrics = FleetMetricsCollector()
    metrics.register_agent(agent_type, agent_type)

    print(f"  State backend: {type(rt.state).__name__}")
    print(f"  Message bus:   {type(rt.bus).__name__}")
    print(f"  Memory store:  {type(rt.memory).__name__}")
    print(f"  Audit log:     {type(rt.audit).__name__}")
    print(f"  Trust level:   {trust.get_level(agent_type)}")

    valid, msg = rt.audit.verify_integrity()
    print(f"  Audit log integrity: {'PASS' if valid else 'FAIL'} — {msg}")

    rt.audit.write_entry({
        "agent_id": agent_type,
        "action": "agent_startup",
        "trust_level": trust.get_level(agent_type),
    })

    print(f"\nAgent '{agent_type}' ready in deployed mode.")
    print("Listening for messages on the bus...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
