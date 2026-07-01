# Engine

The runtime layer. These specs run on every session regardless of what work is being done. Handles session management, pipeline routing, output validation, portfolio aggregation, and system extension.

**Path:** `engine/`

## Contents

| File | Purpose |
|------|---------|
| **portfolio-orchestrator.md** | Cross-program portfolio briefing and triage |
| **program-pipeline-orchestrator.md** | Pipeline entry point and routing |
| **quality-gate-spec.md** | Output validation — runs before every delivery |
| **session-init-spec.md** | Cursor agent initialization and classification |
| **spec-creation-spec.md** | How to build new specs and extend the system |
| **weekly-session-spec.md** | Weekly focused work session |
