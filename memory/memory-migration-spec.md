---
resource_type: spec
version: "1.0"
domain: agent-infrastructure
triggers:
  - memory_migration
  - migrate_memory
inputs:
  - existing_memory_file
outputs:
  - program_state_file
  - decisions_log
  - archive_file
governed_by: config/constitution.md
standalone: true
entry_point: true
---

# Memory Migration Spec
**Version:** 1.0
**Purpose:** Convert an existing single-file `[program]-memory.md` to the three-file memory model. Extracts all critical context into the decisions log, preserves recent sessions in the state file, compresses older history into the archive. Non-destructive — source file is renamed, not deleted.
**Governed by:** `config/constitution.md`

---

## Constitutional Guidance

Prefer reversibility (IV.3) — source file is renamed to `[program]-memory.md.pre-migration` before any writes. Migration can be fully reversed by restoring the source file. Protect the downstream (IV.2) — no decision, accepted risk, or one-way door from the source file may be lost in migration.

---

## Persona Definition

Migration agent. Read the source memory file completely before writing anything. Extract all critical context. Write the three target files. Verify completeness before renaming source. Never delete — rename.

---

## Parameters

```
PROGRAM:    [program slug]
SOURCE:     [memory/[PROGRAM]-memory.md — default]
DRY_RUN:    [yes | no — default: no]
```

---

## Pass 1 — Source File Audit

Read the entire source memory file. Catalog:

- Total session entries and date range
- All decisions recorded (Decision Log table + any in session entries)
- All deferred items (Deferred Items table + any in session entries)
- All patterns mentioned across session entries
- Standing Context paragraph
- Any accepted risks or one-way door actions mentioned
- Approximate total line count

Report:
```
[MIGRATE] Source: memory/[PROGRAM]-memory.md
[MIGRATE] Sessions: [n] entries spanning [first date] to [last date]
[MIGRATE] Decision Log entries: [n]
[MIGRATE] Deferred items: [n]
[MIGRATE] Total lines: [n]
[MIGRATE] Proceeding to extraction...
```

---

## Pass 2 — Critical Context Extraction

Scan every section of the source file. For each critical event found:

| Signal | Extract | Write to |
|---|---|---|
| Decision Log table row | `DECISION \| [decision] \| [rationale]` | decisions log |
| Any session entry describing a decision | `DECISION \| [decision] \| [context from session date]` | decisions log |
| Any accepted risk | `RISK_ACCEPTED \| [risk] \| [rationale]` | decisions log |
| Any one-way door action | `ONE_WAY_DOOR \| [action] \| [context]` | decisions log |
| Any escalation with resolution | `ESCALATED \| [item] \| [resolution]` | decisions log |

Each entry prefixed with the date from the Decision Log or session entry where it appeared.

Deduplicate — if the same decision appears in both the Decision Log table and a session entry, write it once with the earlier date.

After extraction, report:
```
[MIGRATE] Extracted to decisions log:
  DECISION:      [n]
  RISK_ACCEPTED: [n]
  ONE_WAY_DOOR:  [n]
  ESCALATED:     [n]
```

---

## Pass 3 — Session Triage

Divide session entries into two groups:

**Recent (≤ 90 days old):** Move to state file Recent Sessions section — full fidelity, no compression.

**Historical (> 90 days old):** Compress into quarterly blocks for the archive.

For historical entries, group by quarter and apply the quarterly block format from the housekeeping spec:
- 2–4 sentence summary of the quarter's work
- Decisions, risk acceptances, one-way doors, escalations copied verbatim from the decisions log entries for that date range
- Patterns that recurred across sessions in the quarter
- Key artifacts produced (if provenance log data available)

---

## Pass 4 — Write Target Files

**Step 1 — Create decisions log**
Write `memory/[PROGRAM]-decisions.log` from template with all extracted entries.
Entries in chronological order (oldest first — append-only style).

**Step 2 — Create archive**
Write `memory/[PROGRAM]-archive.md` from template.
Append quarterly blocks for all historical sessions (most recent quarter first).

**Step 3 — Create state file**
Write `memory/[PROGRAM]-state.md` from template:
- Current State block — populate from Standing Context and most recent session's "State at close"
- Active Context — populate from Standing Context paragraph
- Deferred Items table — copy from source Deferred Items table
- Patterns table — extract from source, populate Times Deferred from recurrence count
- Recent Sessions — copy sessions ≤ 90 days old verbatim

**Step 4 — Verify completeness**
Before renaming source:
- Count decisions in source Decision Log + session entries
- Count decisions in new decisions log
- If counts match: proceed
- If counts do not match: report discrepancy, do not rename source, require principal review

```
[MIGRATE] Verification:
  Source decisions: [n] | Migrated: [n] | [✓ match | ✗ MISMATCH — do not rename]
```

**Step 5 — Rename source (only if verification passes)**
```bash
mv memory/[PROGRAM]-memory.md memory/[PROGRAM]-memory.md.pre-migration
```

If `DRY_RUN: yes` — report what would be written without writing or renaming anything.

---

## Pass 5 — Migration Report

```
MEMORY MIGRATION — [PROGRAM]
Run date: [today] | Mode: [live | dry run]

SOURCE
  File: memory/[PROGRAM]-memory.md
  Sessions: [n] spanning [date range]
  Renamed to: memory/[PROGRAM]-memory.md.pre-migration [✓ | not renamed — dry run]

DECISIONS LOG
  memory/[PROGRAM]-decisions.log
  Total entries: [n] (DECISION: [n] | RISK_ACCEPTED: [n] | ONE_WAY_DOOR: [n] | ESCALATED: [n])

ARCHIVE
  memory/[PROGRAM]-archive.md
  Quarterly blocks: [n] covering [date range]
  Sessions compressed: [n]

STATE FILE
  memory/[PROGRAM]-state.md
  Recent sessions preserved: [n] ([date range])
  Deferred items: [n]
  Patterns: [n]

VERIFICATION: [✓ all decisions accounted for | ✗ MISMATCH — source not renamed]

NEXT STEPS
  1. Review memory/[PROGRAM]-state.md — confirm Current State and Active Context are accurate
  2. Review memory/[PROGRAM]-decisions.log — spot check 5 entries for accuracy
  3. Update session-init-spec routing to load [PROGRAM]-state.md instead of [PROGRAM]-memory.md
  4. Run /daily-brief to confirm agent loads new files correctly
  5. After 7 days without issues: delete memory/[PROGRAM]-memory.md.pre-migration
```

---

## Trigger

```
PROGRAM: [slug]
DRY_RUN: yes

BEGIN MEMORY MIGRATION
```

Run dry first. Review the report. If clean, run with `DRY_RUN: no`.

---

## Companion Specs
- Governed by: `config/constitution.md`
- Reads: `memory/[PROGRAM]-memory.md`
- Writes: `memory/[PROGRAM]-state.md`, `memory/[PROGRAM]-decisions.log`, `memory/[PROGRAM]-archive.md`
- Renames: `memory/[PROGRAM]-memory.md` → `memory/[PROGRAM]-memory.md.pre-migration`
- Invokes after: `functions/memory-housekeeping-spec.md` for ongoing maintenance
