"""
Cross-framework intelligence engine.

Builds and maintains the Common Control Catalog (CCC) — a mapping of equivalent
controls across frameworks. Enables:
- Satisfy-once-apply-many evidence reuse
- Cross-framework impact analysis (change in one framework propagates to others)
- Efficiency reporting (show where one action resolves findings across certifications)

Works with framework specialist agents via CROSSWALK_REQUEST/CROSSWALK_RESPONSE
messages defined in the agent-message schema.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ControlMapping:
    """A single control from a specific framework."""

    framework_id: str
    control_id: str
    control_title: str
    mapping_type: str = "equivalent"
    mapping_notes: str = ""
    framework_specific_requirements: list[str] = field(default_factory=list)


@dataclass
class CommonControl:
    """A framework-neutral control that maps to controls across multiple frameworks."""

    common_control_id: str
    control_family: str
    control_objective: str
    framework_mappings: list[ControlMapping] = field(default_factory=list)
    confidence: str = "strong"
    impact_scope: list[str] = field(default_factory=list)
    evidence_reusable: bool = True
    reuse_type: str = "full"
    shared_evidence_types: list[str] = field(default_factory=list)

    @property
    def frameworks_covered(self) -> int:
        return len(set(m.framework_id for m in self.framework_mappings))

    def add_mapping(self, mapping: ControlMapping) -> None:
        existing = [
            m for m in self.framework_mappings
            if m.framework_id == mapping.framework_id
            and m.control_id == mapping.control_id
        ]
        if not existing:
            self.framework_mappings.append(mapping)

    def to_dict(self) -> dict[str, Any]:
        return {
            "common_control_id": self.common_control_id,
            "control_family": self.control_family,
            "control_objective": self.control_objective,
            "framework_mappings": [
                {
                    "framework_id": m.framework_id,
                    "control_id": m.control_id,
                    "control_title": m.control_title,
                    "mapping_type": m.mapping_type,
                    "mapping_notes": m.mapping_notes,
                    "framework_specific_requirements": m.framework_specific_requirements,
                }
                for m in self.framework_mappings
            ],
            "evidence_reuse": {
                "reusable": self.evidence_reusable,
                "reuse_type": self.reuse_type,
                "shared_evidence_types": self.shared_evidence_types,
            },
            "impact_scope": self.impact_scope,
            "confidence": self.confidence,
        }


class CommonControlCatalog:
    """The Common Control Catalog (CCC).

    Central registry of control equivalences across frameworks.
    Built incrementally from crosswalk responses from framework specialists.
    """

    def __init__(self):
        self.entries: dict[str, CommonControl] = {}
        self.frameworks: dict[str, dict[str, Any]] = {}

    def register_framework(
        self,
        framework_id: str,
        framework_name: str,
        version: str,
        total_controls: int = 0,
        specialist_agent: str = "",
    ) -> None:
        self.frameworks[framework_id] = {
            "framework_id": framework_id,
            "framework_name": framework_name,
            "version": version,
            "total_controls": total_controls,
            "mapped_controls": 0,
            "specialist_agent": specialist_agent,
        }

    def add_common_control(self, control: CommonControl) -> None:
        self.entries[control.common_control_id] = control
        self._update_framework_counts()

    def find_by_framework_control(
        self, framework_id: str, control_id: str
    ) -> list[CommonControl]:
        """Find all common controls that include a specific framework control."""
        results = []
        for cc in self.entries.values():
            for m in cc.framework_mappings:
                if m.framework_id == framework_id and m.control_id == control_id:
                    results.append(cc)
                    break
        return results

    def find_by_family(self, control_family: str) -> list[CommonControl]:
        return [
            cc for cc in self.entries.values()
            if cc.control_family.lower() == control_family.lower()
        ]

    def impact_analysis(
        self, framework_id: str, control_id: str, finding_type: str = "gap"
    ) -> dict[str, Any]:
        """When a control finding changes, propagate impact across all frameworks."""
        affected = self.find_by_framework_control(framework_id, control_id)
        if not affected:
            return {
                "source": {"framework": framework_id, "control": control_id},
                "finding_type": finding_type,
                "impact": "none",
                "affected_frameworks": [],
                "affected_programs": [],
            }

        impacted_frameworks: list[dict[str, str]] = []
        impacted_programs: set[str] = set()

        for cc in affected:
            for m in cc.framework_mappings:
                if m.framework_id != framework_id or m.control_id != control_id:
                    impacted_frameworks.append({
                        "framework_id": m.framework_id,
                        "control_id": m.control_id,
                        "control_title": m.control_title,
                        "common_control_id": cc.common_control_id,
                        "mapping_type": m.mapping_type,
                    })
            impacted_programs.update(cc.impact_scope)

        return {
            "source": {"framework": framework_id, "control": control_id},
            "finding_type": finding_type,
            "impact": "cross_framework",
            "affected_common_controls": [cc.common_control_id for cc in affected],
            "affected_frameworks": impacted_frameworks,
            "affected_programs": sorted(impacted_programs),
            "recommendation": (
                f"Finding on {framework_id}:{control_id} affects "
                f"{len(impacted_frameworks)} controls across "
                f"{len(set(f['framework_id'] for f in impacted_frameworks))} frameworks "
                f"and {len(impacted_programs)} programs."
            ),
        }

    def efficiency_report(self) -> dict[str, Any]:
        """Show where one action resolves findings across multiple certifications."""
        opportunities = []
        for cc in self.entries.values():
            if cc.frameworks_covered >= 2 and cc.evidence_reusable:
                opportunities.append({
                    "common_control_id": cc.common_control_id,
                    "control_family": cc.control_family,
                    "control_objective": cc.control_objective,
                    "frameworks_covered": cc.frameworks_covered,
                    "programs_affected": len(cc.impact_scope),
                    "reuse_type": cc.reuse_type,
                    "shared_evidence_types": cc.shared_evidence_types,
                })

        opportunities.sort(
            key=lambda x: (x["frameworks_covered"], x["programs_affected"]),
            reverse=True,
        )

        total_mappings = sum(
            len(cc.framework_mappings) for cc in self.entries.values()
        )
        reusable_count = sum(
            1 for cc in self.entries.values() if cc.evidence_reusable
        )
        reuse_pct = (reusable_count / len(self.entries) * 100) if self.entries else 0

        return {
            "total_common_controls": len(self.entries),
            "total_framework_controls_mapped": total_mappings,
            "reusable_evidence_percentage": round(reuse_pct, 1),
            "top_efficiency_opportunities": opportunities[:10],
            "cross_framework_coverage": {
                fid: round(info["mapped_controls"] / max(info["total_controls"], 1) * 100, 1)
                for fid, info in self.frameworks.items()
                if info["total_controls"] > 0
            },
        }

    def to_schema_dict(self) -> dict[str, Any]:
        """Export as a dict conforming to common-control-catalog.schema.json."""
        stats = self.efficiency_report()
        return {
            "schema_version": "1.0",
            "generated_at": datetime.now(tz=None).astimezone().isoformat(),
            "generated_by": "crosswalk-engine",
            "framework_coverage": list(self.frameworks.values()),
            "catalog_entries": [cc.to_dict() for cc in self.entries.values()],
            "statistics": stats,
        }

    def _update_framework_counts(self) -> None:
        for fid in self.frameworks:
            count = 0
            seen: set[str] = set()
            for cc in self.entries.values():
                for m in cc.framework_mappings:
                    if m.framework_id == fid:
                        key = f"{m.framework_id}:{m.control_id}"
                        if key not in seen:
                            seen.add(key)
                            count += 1
            self.frameworks[fid]["mapped_controls"] = count

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommonControlCatalog":
        """Load a catalog from a schema-conformant dict."""
        catalog = cls()
        for fw in data.get("framework_coverage", []):
            catalog.register_framework(
                fw["framework_id"],
                fw["framework_name"],
                fw["version"],
                fw.get("total_controls", 0),
                fw.get("specialist_agent", ""),
            )
        for entry in data.get("catalog_entries", []):
            mappings = [
                ControlMapping(
                    framework_id=m["framework_id"],
                    control_id=m["control_id"],
                    control_title=m["control_title"],
                    mapping_type=m.get("mapping_type", "equivalent"),
                    mapping_notes=m.get("mapping_notes", ""),
                    framework_specific_requirements=m.get(
                        "framework_specific_requirements", []
                    ),
                )
                for m in entry.get("framework_mappings", [])
            ]
            reuse = entry.get("evidence_reuse", {})
            cc = CommonControl(
                common_control_id=entry["common_control_id"],
                control_family=entry["control_family"],
                control_objective=entry["control_objective"],
                framework_mappings=mappings,
                confidence=entry.get("confidence", "strong"),
                impact_scope=entry.get("impact_scope", []),
                evidence_reusable=reuse.get("reusable", True),
                reuse_type=reuse.get("reuse_type", "full"),
                shared_evidence_types=reuse.get("shared_evidence_types", []),
            )
            catalog.entries[cc.common_control_id] = cc
        catalog._update_framework_counts()
        return catalog
