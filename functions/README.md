# Functions

Discrete callable work specs. Each encodes one domain. Invoked by the engine when work matches their domain.

**Path:** `functions/`

## Contents

| File | Domain | Standalone | Purpose |
|------|--------|------------|---------|
| **auditor-view-spec.md** | Compliance | ✓ | Read-only auditor compliance posture dashboard |
| **calendar-output-spec.md** | Compliance | ✓ | LLM fallback calendar generation |
| **compliance-doc-generator-spec.md** | Compliance | ✓ | Orchestrated CSV/MD compliance output generation |
| **compliance-entropy-spec.md** | Compliance | ✓ | Longitudinal compliance analysis |
| **compliance-redteam-spec.md** | Compliance | ✓ | Adversarial artifact review |
| **control-assessment-spec.md** | Compliance | ✓ | Auditor template filling from framework + product docs |
| **control-coverage-spec.md** | Compliance | ✓ | Control mapping and gap analysis |
| **external-intel-spec.md** | Intelligence | ✓ | External source monitoring and risk deltas |
| **management-system-assembler-spec.md** | Compliance | ✓ | ISMS/AIMS document assembly from artifacts |
| **program-comms-spec.md** | Communications | ✓ | Status reports, recaps, requests |
| **program-intake-spec.md** | Program Management | — | Program onboarding and full build |
| **program-monitoring-spec.md** | Program Management | — | Ongoing oversight and escalations |
| **risk-register-spec.md** | Compliance | ✓ | Risk register and POA&M starter |
| **vendor-management-spec.md** | Vendor Management | — | Vendor scoring and remediation |
| **post-audit-spec.md** | Program Management | ✓ | Post-audit lessons learned, corrective actions, and feed-forward for next cycle |
| **product-evidence-spec.md** | Compliance | ✓ | Product documentation as evidence: mapping product artifacts to control narratives |
| **kanban-spec.md** | Program Management | ✓ | Per-program kanban boards, Jira export |
| **program-dashboard-spec.md** | Program Management | ✓ | Per-program + portfolio HTML dashboard generation, light-theme renderer |

> **Note:** `quality-gate-spec.md` lives in `engine/`, not here. It is an engine spec applied before every delivery.
