---
resource_type: spec
version: "1.0"
domain: agent-infrastructure
triggers:
  - memory_housekeeping
  - memory_maintenance
  - quarterly_cleanup
inputs:
  - program_state_file
  - decisions_log
  - archive_file
  - provenance_log
outputs:
  - updated_state_file
  - updated_archive_file
  - housekeeping_report
governed_by: config/constitution.md
standalone: true
entry_point: true
depends_on:
  - memory/[PROGRAM]-state.md
  - memory/[PROGRAM]-decisions.log
  - memory/[PROGRAM]-archive.md
  - logs/provenance.jsonl
---

# Memory Housekeeping Spec
**Version:** 1.0
**Purpose:** Maintain the three-file memory model for active programs. Compresses session entries older than 90 days into the archive, validates decisions log integrity, refreshes state file, and surfaces stagnant patterns. Designed to run quarterly or on demand. Never loses critical context.
**Governed by:** `config/constitution.md`

---

## Constitutional Guidance

Protect the downstream (IV.2) — memory files are the agent's long-term context. Compression that silently loses a decision or accepted risk is a defect that propagates into every future session. Say the true thing (IV.1) — the housekeeping report states what was compressed, what was preserved, and what requires principal attention. Prefer reversibility (IV.3) — archive before compress, never delete source entries until the archive write is confirmed.

---

## Persona Definition

Memory archivist. Compress session history without losing critical context. Validate the decisions log is append-only and unmodified. Surface patterns that have persisted without resolution. Leave the state file small, current, and accurate.

---

## Parameters

```
PROGRAM:              [program slug]
COMPRESSION_AGE_DAYS: [days after which sessions compress — default: 90]
DRY_RUN:              [yes | no — default: no. yes = report without writing]
```

---

## Three-File Model

```
memory/[PROGRAM]-state.md       ← hot — loaded every session
memory/[PROGRAM]-decisions.log  ← audit — queried, never fully loaded
memory/[PROGRAM]-archive.md     ← cold — loaded only for historical context
```

**Load rules (enforced by session init and weekly session spec):**
- `[PROGRAM]-state.md` — always loaded for this program's sessions
- `[PROGRAM]-decisions.log` — never fully loaded; query by grep or tail
  - At session open: `tail -20 [PROGRAM]-decisions.log` for recent decisions
  - On demand: `grep "DECISION\|RISK_ACCEPTED" [PROGRAM]-decisions.log`
- `[PROGRAM]-archive.md` — load only when historical context is explicitly needed

---

## Pass 1 — File Integrity Check

Before any modification, verify file integrity.

### State file checks:
- File exists at `memory/[PROGRAM]-state.md`
- Required sections present: Current State, Active Context, Deferred Items, Patterns, Recent Sessions
- Last updated date is parseable
- No session entries missing the required fields

### Decisions log checks:
- File exists at `memory/[PROGRAM]-decisions.log`
- All lines follow format: `YYYY-MM-DD | TYPE | DESCRIPTION | CONTEXT`
- No lines have been modified after initial write — check by confirming no entries have future dates relative to their sequential position
- All event types are valid: `DECISION | RISK_ACCEPTED | ONE_WAY_DOOR | ESCALATED`
- Line count has not decreased since last housekeeping (cannot delete from an append-only log)

**If decisions log line count has decreased:**
```
[HOUSEKEEPING] INTEGRITY FAILURE — decisions log line count decreased.
Expected ≥ [prior count] lines. Found [n] lines.
This indicates manual deletion from an append-only log.
Do not proceed. Notify principal immediately.
```
Stop and escalate. Do not compress anything until the log is restored.

### Archive file checks:
- File exists at `memory/[PROGRAM]-archive.md` (create from template if missing)
- Quarterly blocks are in descending order (most recent first)

Narrate:
```
[HOUSEKEEPING] Integrity check: state ✓ | decisions log ✓ ([n] entries) | archive ✓
[HOUSEKEEPING] Proceeding to compression check...
```

---

## Pass 2 — Critical Context Extraction (pre-compression safety)

Before compressing any session entry, extract all critical context from it.
This pass runs even if no compression is needed — it validates the decisions log is complete.

For each session entry in Recent Sessions, scan for:

| Signal | Extract | Write to |
|---|---|---|
| Any decision described | `DECISION \| [description] \| [context]` | decisions log if not already present |
| Any risk acceptance | `RISK_ACCEPTED \| [risk] \| [acceptance rationale]` | decisions log if not already present |
| Any one-way door action | `ONE_WAY_DOOR \| [action] \| [what was done]` | decisions log if not already present |
| Any escalation and resolution | `ESCALATED \| [item] \| [resolution or UNRESOLVED]` | decisions log if not already present |
| Any deferred item | — | Verify in Deferred Items table |
| Any pattern surfaced | — | Verify in Patterns table |

**Write rule:** If the critical event is already in the decisions log (same date and description), skip. If not found, append it before compressing the session entry.

**Deferred item check:** Every item in session entries marked as deferred must appear in the Deferred Items table. If missing, add it before compressing.

**Pattern check:** Every pattern surfaced in session entries must appear in the Patterns table with a count. If a pattern appears in 3+ session entries with no principal resolution, flag it:
```
[HOUSEKEEPING] Pattern persisting without resolution: "[pattern]"
First noted: [date] | Sessions unresolved: [n]
Recommend: surface at next session open as primary risk candidate.
```

Narrate:
```
[HOUSEKEEPING] Critical context scan: [n] decisions | [n] risk acceptances | [n] one-way doors | [n] escalations
[HOUSEKEEPING] [n] new entries written to decisions log
[HOUSEKEEPING] [n] deferred items verified | [n] patterns verified
```

---

## Pass 3 — Compression

Identify session entries older than `COMPRESSION_AGE_DAYS` days.

If none qualify: skip to Pass 4.

### Compression sequence (per qualifying quarter):

**Step 1 — Identify the quarter's entries**
Group sessions by calendar quarter (Q1: Jan–Mar, Q2: Apr–Jun, Q3: Jul–Sep, Q4: Oct–Dec).
Only compress complete quarters — never compress a partial quarter.

**Step 2 — Retrieve supporting data**
Query provenance log for artifacts produced in this quarter:
```bash
grep '"program":"[PROGRAM]"' logs/provenance.jsonl | \
  awk -F'"timestamp":"' '{print $2}' | \
  grep "^[QUARTER_YEAR]" | ...
```

Query decisions log for this quarter's events:
```bash
grep "^[YYYY-Q-START]" memory/[PROGRAM]-decisions.log | \
  grep -v "^#"
```

**Step 3 — Write quarterly block to archive**

Append to `memory/[PROGRAM]-archive.md` (most recent quarter at top):

```markdown
## [YYYY] Q[N] — [Month] through [Month]
**Sessions:** [n] | **Compressed:** [today's date]

**Summary:**
[2–4 sentences: primary focus of the quarter, significant state changes,
program trajectory. Factual — no editorial.]

**Decisions made:**
[Copy verbatim from decisions log — all DECISION entries in date range]

**Risks accepted:**
[Copy verbatim from decisions log — all RISK_ACCEPTED entries in date range]

**One-way doors:**
[Copy verbatim from decisions log — all ONE_WAY_DOOR entries in date range]

**Escalations:**
[Copy verbatim from decisions log — all ESCALATED entries in date range]

**Patterns that recurred:**
[From session entries — any pattern appearing 2+ times in the quarter]

**Key artifacts produced:**
[From provenance log — output_type, purpose, date for significant artifacts]
```

**Step 4 — Verify archive write**
Confirm the quarterly block is present and readable in the archive file before removing session entries from the state file.

**Step 5 — Remove compressed entries from state file**
Remove session entries covered by the archived quarter from the Recent Sessions section.

If `DRY_RUN: yes` — report what would be compressed but do not write or remove anything.

Narrate:
```
[HOUSEKEEPING] Compressing [n] sessions from [quarter]
[HOUSEKEEPING] Archive block written: [YYYY] Q[N]
[HOUSEKEEPING] [n] entries removed from state file
```

---

## Pass 4 — State File Refresh

Update the state file to reflect current program state:

1. Read `runs/[PROGRAM]/latest.json` — update Current State block:
   - Phase from `phase`
   - Health from `overall_health`
   - Next pipeline run from `next_run_recommendation`

2. Verify Active Context is current:
   - Primary risk — confirm it matches the top risk from `risk_register.items` by severity
   - Active blockers — reconcile with `monitoring_output.watch_list`
   - Pending decisions — reconcile with `monitoring_output.decision_queue`

3. Update `Last updated` and `Updated by: housekeeping` in the header.

4. Prune Deferred Items table:
   - Remove items where the run JSON shows the item is now closed or resolved
   - Flag items deferred 3+ times with `⚠` prefix

5. Prune Patterns table:
   - Remove patterns where principal direction is recorded as resolved
   - Flag patterns unresolved after 3+ sessions

Narrate:
```
[HOUSEKEEPING] State file refreshed from run JSON
[HOUSEKEEPING] [n] deferred items pruned (resolved) | [n] flagged (3+ deferrals)
[HOUSEKEEPING] [n] patterns pruned (resolved) | [n] flagged (3+ sessions unresolved)
```

---

## Pass 5 — Housekeeping Report

```
MEMORY HOUSEKEEPING — [PROGRAM]
Run date: [today] | Mode: [live | dry run]

INTEGRITY
  State file:     [✓ clean | ✗ issues found]
  Decisions log:  [✓ clean | ✗ INTEGRITY FAILURE — see above]
  Archive:        [✓ clean | created new]

CRITICAL CONTEXT
  Decisions extracted to log:    [n] new entries
  Risk acceptances logged:       [n]
  One-way doors logged:          [n]
  Escalations logged:            [n]

COMPRESSION
  Sessions compressed:  [n] ([quarter range])
  Archive blocks added: [n]
  State file reduced:   [n] entries removed

STATE REFRESH
  Phase:             [current]
  Health:            [current]
  Deferred pruned:   [n] resolved | [n] flagged (3+)
  Patterns pruned:   [n] resolved | [n] flagged (3+)

REQUIRES PRINCIPAL ATTENTION
  [List any: decisions log integrity failure, persistent patterns,
   3+ deferred items, unresolved escalations]

NEXT HOUSEKEEPING: [today + 90 days]
```

---

## Provenance

```bash
python scripts/provenance_log.py write \
  --spec "functions/memory-housekeeping-spec.md" \
  --output "memory/[PROGRAM]-state.md" \
  --output-type memory_maintenance \
  --program "[PROGRAM]" \
  --purpose "Memory housekeeping: [n] sessions compressed | [n] decisions logged" \
  --reusability instance \
  --quality-gate pass
```

---

## Trigger

```
PROGRAM: [slug]
DRY_RUN: [yes | no]

BEGIN MEMORY HOUSEKEEPING
```

---

## Companion Specs
- Governed by: `config/constitution.md`
- Reads: `memory/[PROGRAM]-state.md`, `memory/[PROGRAM]-decisions.log`, `memory/[PROGRAM]-archive.md`, `logs/provenance.jsonl`, `runs/[PROGRAM]/latest.json`
- Writes: `memory/[PROGRAM]-state.md`, `memory/[PROGRAM]-decisions.log` (append only), `memory/[PROGRAM]-archive.md`
- Logged by: `scripts/provenance_log.py` — output_type: `memory_maintenance`
