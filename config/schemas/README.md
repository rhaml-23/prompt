# Schemas

Versioned JSON Schemas for the compliance fleet data types. These schemas define the contracts between agents and are validated at runtime and in CI.

**Path:** `config/schemas`

## Contents

| File | Version | Purpose |
|------|---------|---------|
| **portfolio-state.schema.json** | 1.0 | Cross-program portfolio state produced by the coordinator |
| **run-output.schema.json** | 1.1 | Pipeline run output envelope (runs/[PROGRAM]/*.json) |
| **agent-message.schema.json** | 1.0 | Inter-agent message envelope for the message bus (37 types) |
| **audit-entry.schema.json** | 1.0 | Append-only audit log entry (provenance.jsonl) |
| **common-control-catalog.schema.json** | 1.0 | Cross-framework control mappings (CCC) |
| **evidence-record.schema.json** | 1.0 | Evidence lifecycle tracking per program |
| **trust-state.schema.json** | 1.0 | Agent trust levels and promotion/demotion history |
| **fleet-metrics.schema.json** | 1.0 | Fleet operational metrics (agents, programs, costs) |
| **work-checkpoint.schema.json** | 1.0 | Generic resumability checkpoint (`data/[program]/checkpoints/*.json`) |

## Versioning

Schemas are versioned independently from specs. Schema version is embedded in the data (`schema_version` field). Breaking changes require a major version bump and a migration path.

## Validation

Schemas can be validated using any JSON Schema 2020-12 compatible validator. In Python:

```python
import json
import jsonschema

with open("config/schemas/run-output.schema.json") as f:
    schema = json.load(f)

with open("runs/program/latest.json") as f:
    data = json.load(f)

jsonschema.validate(data, schema)
```
