# Config

Rules the system runs under. Loaded before any other file. Never overridden by any spec or agent instruction.

**Path:** `config/`

## Contents

| File | Purpose |
|------|---------|
| **constitution.md** | Professional Intent Constitution v1.5 — behavioral and ethical governance. Load first, always. |
| **spec-frontmatter-schema.yaml** | Canonical YAML frontmatter schema for all spec and agent definition files. Validated by `scripts/validate_frontmatter.py`. |
| **tool-requirements.md** | Tool development contract v1.1 — when and how to build scripts and tools. |
