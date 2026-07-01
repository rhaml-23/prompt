"""
Predictive program health analysis (Phase 3d).

Analyzes historical patterns across all programs to produce:
- Certification timeline prediction based on current velocity and gap count
- Resource contention forecasting
- Audit readiness scoring with trajectory
- Finding velocity trends (are we getting better or worse?)

Usage:
    python scripts/predictive_health.py --runs-dir runs/ --output data/predictions.json
    python scripts/predictive_health.py --program fedramp-high --detail
    python scripts/predictive_health.py --portfolio data/portfolio/latest.json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def load_run_history(runs_dir: Path, program: str) -> list[dict[str, Any]]:
    """Load all historical runs for a program, sorted chronologically."""
    program_dir = runs_dir / program
    if not program_dir.exists():
        return []
    runs = []
    for f in sorted(program_dir.glob("*-run.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_file"] = f.name
            runs.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return runs


def analyze_health_trajectory(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze health trajectory from run history."""
    if len(runs) < 2:
        return {
            "trajectory": "insufficient_data",
            "data_points": len(runs),
            "recommendation": "Need at least 2 runs for trajectory analysis.",
        }

    health_scores = {"green": 3, "yellow": 2, "red": 1, "unknown": 0}
    scores = []
    for run in runs:
        health = run.get("program_state", {}).get("overall_health", "unknown")
        date = run.get("run_manifest", {}).get("run_date", "")
        scores.append({"date": date, "health": health, "score": health_scores.get(health, 0)})

    if len(scores) >= 3:
        recent_avg = sum(s["score"] for s in scores[-3:]) / 3
        older_avg = sum(s["score"] for s in scores[:-3]) / max(len(scores) - 3, 1) if len(scores) > 3 else scores[0]["score"]
    else:
        recent_avg = scores[-1]["score"]
        older_avg = scores[0]["score"]

    if recent_avg > older_avg + 0.3:
        trajectory = "improving"
    elif recent_avg < older_avg - 0.3:
        trajectory = "declining"
    else:
        trajectory = "stable"

    return {
        "trajectory": trajectory,
        "data_points": len(scores),
        "current_score": scores[-1]["score"],
        "recent_average": round(recent_avg, 2),
        "historical_average": round(older_avg, 2),
        "history": scores[-10:],
    }


def predict_certification_timeline(
    runs: list[dict[str, Any]], target_controls: int = 0
) -> dict[str, Any]:
    """Predict certification readiness based on gap closure velocity."""
    if len(runs) < 2:
        return {
            "prediction": "insufficient_data",
            "recommendation": "Need at least 2 runs for timeline prediction.",
        }

    gap_history = []
    for run in runs:
        flags = run.get("flags", {})
        total_gaps = (
            len(flags.get("owner_needed", []))
            + len(flags.get("date_needed", []))
            + len(flags.get("escalation_path_needed", []))
            + len(flags.get("insufficient_data", []))
            + len(flags.get("unresolved_from_prior_run", []))
        )
        date = run.get("run_manifest", {}).get("run_date", "")
        gap_history.append({"date": date, "gaps": total_gaps})

    if len(gap_history) >= 2:
        first_gaps = gap_history[0]["gaps"]
        last_gaps = gap_history[-1]["gaps"]
        runs_count = len(gap_history)

        if runs_count > 1:
            gap_velocity = (first_gaps - last_gaps) / (runs_count - 1)
        else:
            gap_velocity = 0

        if gap_velocity > 0 and last_gaps > 0:
            runs_to_zero = last_gaps / gap_velocity
            estimated_weeks = runs_to_zero * 1
            estimated_date = (
                datetime.now() + timedelta(weeks=estimated_weeks)
            ).strftime("%Y-%m-%d")
        elif last_gaps == 0:
            estimated_date = "ready"
            runs_to_zero = 0
        else:
            estimated_date = "not_converging"
            runs_to_zero = -1
    else:
        gap_velocity = 0
        estimated_date = "insufficient_data"
        runs_to_zero = -1

    return {
        "current_gaps": gap_history[-1]["gaps"] if gap_history else 0,
        "gap_velocity_per_run": round(gap_velocity, 2),
        "estimated_ready_date": estimated_date,
        "estimated_runs_remaining": round(runs_to_zero, 1) if runs_to_zero >= 0 else None,
        "gap_trend": gap_history[-5:],
        "confidence": "high" if len(gap_history) >= 5 else "medium" if len(gap_history) >= 3 else "low",
    }


def forecast_resource_contention(
    portfolio: dict[str, Any],
) -> list[dict[str, Any]]:
    """Identify upcoming resource contention across programs."""
    programs = portfolio.get("programs", [])
    contention_points = []

    owners: dict[str, list[str]] = {}
    for prog in programs:
        slug = prog.get("program_slug", "")
        for vendor in prog.get("vendors", []):
            name = vendor.get("name", "")
            if name:
                owners.setdefault(name, []).append(slug)

    for resource, progs in owners.items():
        if len(progs) >= 2:
            contention_points.append({
                "resource": resource,
                "type": "shared_vendor",
                "programs": progs,
                "severity": "high" if len(progs) >= 3 else "medium",
                "recommendation": f"Vendor '{resource}' shared across {len(progs)} programs — coordinate assessments.",
            })

    deadline_progs: dict[str, list[str]] = {}
    for prog in programs:
        next_date = prog.get("next_run_recommended", "")
        if next_date:
            week_key = next_date[:7]
            deadline_progs.setdefault(week_key, []).append(prog.get("program_slug", ""))

    for period, progs in deadline_progs.items():
        if len(progs) >= 2:
            contention_points.append({
                "resource": "schedule",
                "type": "deadline_clustering",
                "programs": progs,
                "period": period,
                "severity": "medium",
                "recommendation": f"{len(progs)} programs need runs in {period} — stagger if possible.",
            })

    return contention_points


def compute_audit_readiness_score(run: dict[str, Any]) -> dict[str, Any]:
    """Score audit readiness from 0-100 based on current program state."""
    score = 100
    reasons = []

    health = run.get("program_state", {}).get("overall_health", "unknown")
    if health == "red":
        score -= 40
        reasons.append("Program health is red (-40)")
    elif health == "yellow":
        score -= 20
        reasons.append("Program health is yellow (-20)")
    elif health == "unknown":
        score -= 30
        reasons.append("Program health is unknown (-30)")

    flags = run.get("flags", {})
    owner_gaps = len(flags.get("owner_needed", []))
    if owner_gaps > 0:
        penalty = min(owner_gaps * 3, 20)
        score -= penalty
        reasons.append(f"{owner_gaps} controls without owners (-{penalty})")

    unresolved = len(flags.get("unresolved_from_prior_run", []))
    if unresolved > 0:
        penalty = min(unresolved * 2, 15)
        score -= penalty
        reasons.append(f"{unresolved} unresolved flags from prior run (-{penalty})")

    insufficient = len(flags.get("insufficient_data", []))
    if insufficient > 0:
        penalty = min(insufficient * 3, 15)
        score -= penalty
        reasons.append(f"{insufficient} insufficient data flags (-{penalty})")

    escalations = len(flags.get("escalation_path_needed", []))
    if escalations > 0:
        penalty = min(escalations * 5, 15)
        score -= penalty
        reasons.append(f"{escalations} escalation paths needed (-{penalty})")

    score = max(0, score)

    if score >= 80:
        readiness = "audit_ready"
    elif score >= 60:
        readiness = "nearly_ready"
    elif score >= 40:
        readiness = "significant_gaps"
    else:
        readiness = "not_ready"

    return {
        "score": score,
        "readiness": readiness,
        "reasons": reasons,
    }


def generate_predictions(
    runs_dir: Path,
    portfolio_path: Path | None = None,
    program_filter: str | None = None,
) -> dict[str, Any]:
    """Generate full predictive health report."""
    programs_to_analyze = []
    if program_filter:
        programs_to_analyze = [program_filter]
    elif runs_dir.exists():
        programs_to_analyze = sorted(
            d.name for d in runs_dir.iterdir()
            if d.is_dir() and (d / "latest.json").exists()
        )

    portfolio = {}
    if portfolio_path and portfolio_path.exists():
        portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))

    program_predictions = {}
    for prog in programs_to_analyze:
        runs = load_run_history(runs_dir, prog)
        latest = runs[-1] if runs else {}

        program_predictions[prog] = {
            "health_trajectory": analyze_health_trajectory(runs),
            "certification_timeline": predict_certification_timeline(runs),
            "audit_readiness": compute_audit_readiness_score(latest),
        }

    resource_forecast = []
    if portfolio:
        resource_forecast = forecast_resource_contention(portfolio)

    return {
        "generated_at": datetime.now(tz=None).astimezone().isoformat(),
        "programs": program_predictions,
        "resource_contention_forecast": resource_forecast,
        "summary": {
            "total_programs_analyzed": len(program_predictions),
            "improving": sum(
                1 for p in program_predictions.values()
                if p["health_trajectory"].get("trajectory") == "improving"
            ),
            "declining": sum(
                1 for p in program_predictions.values()
                if p["health_trajectory"].get("trajectory") == "declining"
            ),
            "audit_ready": sum(
                1 for p in program_predictions.values()
                if p["audit_readiness"].get("readiness") == "audit_ready"
            ),
            "contention_points": len(resource_forecast),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Predictive program health analysis")
    parser.add_argument("--runs-dir", default="runs", help="Path to runs directory")
    parser.add_argument("--portfolio", help="Path to portfolio state JSON")
    parser.add_argument("--program", help="Analyze a specific program only")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--detail", action="store_true", help="Include full run history in output")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    portfolio_path = Path(args.portfolio) if args.portfolio else None

    predictions = generate_predictions(
        runs_dir=runs_dir,
        portfolio_path=portfolio_path,
        program_filter=args.program,
    )

    output = json.dumps(predictions, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Predictions written to {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
