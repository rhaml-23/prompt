# Memory Layer

This directory holds long-term context for active compliance programs. Each program uses three files optimized for different access patterns. The single-file model (`[program]-memory.md`) has been replaced — if you have existing files in that format, run the migration spec before using the new system.

---

## File Structure Per Program

```
memory/
  [program]-state.md          ← hot — loaded every session
  [program]-decisions.log     ← audit — queried, never fully loaded
  [program]-archive.md        ← cold — loaded only for historical context
```

---

## What Each File Does

### `[program]-state.md` — Hot Layer

Everything the agent needs at the start of every session. Current phase, health, primary risk, active blockers, pending decisions, relationship notes, deferred items, recurring patterns, and session entries from the last 90 days.

Kept small by design. If this file grows past ~100 lines of actual content, run housekeeping. The 90-day session window is the primary size control — entries older than that are compressed into the archive quarterly.

Overwritten (not appended) when state changes. This is working memory, not a log.

---

### `[program]-decisions.log` — Audit Layer

Append-only flat file. One event per line. Never modified after write. Contains four event types:

```
YYYY-MM-DD | DECISION      | what was decided             | context
YYYY-MM-DD | RISK_ACCEPTED | what risk was accepted       | rationale
YYYY-MM-DD | ONE_WAY_DOOR  | what irreversible action     | what was done
YYYY-MM-DD | ESCALATED     | what was escalated           | resolution or UNRESOLVED
```

This file is **never loaded in full**. The agent queries it:

```bash
# Recent decisions at session open
tail -20 [program]-decisions.log

# All accepted risks
grep "RISK_ACCEPTED" [program]-decisions.log

# One-way doors this year
grep "^2026.*ONE_WAY_DOOR" [program]-decisions.log

# Unresolved escalations
grep "ESCALATED.*UNRESOLVED" [program]-decisions.log
```

The decisions log is the system's audit trail. A 500-entry log costs almost nothing at session open because you only read the tail — not the full file. Never delete entries. Never edit entries after writing. If the line count decreases, the housekeeping spec treats it as an integrity failure and stops.

---

### `[program]-archive.md` — Cold Layer

Compressed session history. Sessions older than 90 days are summarized into quarterly blocks. Load this file only when historical context is explicitly needed — it is not part of the normal session load.

Each quarterly block contains: a 2–4 sentence narrative summary, verbatim copies of all decisions/risk acceptances/one-way doors/escalations from the decisions log for that period, patterns that recurred across the quarter, and key artifacts produced.

The narrative can be further compressed in future housekeeping passes. The events copied from the decisions log are never further compressed or deleted — they are permanent record.

---

## Why Three Files

The single-file model worked for small programs with few sessions. At scale it breaks in two ways:

**Token cost.** A year of active sessions in one file means loading 12 months of history on every session open — most of it irrelevant to today's work. The three-file model loads only what the current session needs. Recent sessions in the state file, recent decisions via tail, historical context only on demand.

**Compression safety.** When a single file gets too large and needs compression, there is no safe way to know what's critical and what isn't. The decisions log solves this — by writing decisions, risk acceptances, and one-way doors to an append-only log at the time they happen, compression of the session narrative is safe. The facts are already preserved elsewhere. The housekeeping spec verifies this before compressing anything.

---

## Housekeeping

Run quarterly or when the state file feels heavy:

```
PROGRAM: [slug]
DRY_RUN: yes

BEGIN MEMORY HOUSEKEEPING
```

Always run dry first. Review the report. If clean, run with `DRY_RUN: no`.

The housekeeping spec does five things:

1. **Integrity check** — verifies the decisions log hasn't been modified (line count only increases). Stops everything if the log is corrupt.
2. **Critical context extraction** — scans session entries for decisions and events that should be in the decisions log but aren't. Writes them before compressing anything.
3. **Compression** — moves sessions older than 90 days into quarterly archive blocks.
4. **State refresh** — updates Current State from the run JSON, prunes resolved deferred items and patterns.
5. **Report** — tells you what was compressed, what was preserved, and what needs your attention.

---

## Migrating from the Old Model

If you have existing `[program]-memory.md` files:

```
PROGRAM: [slug]
DRY_RUN: yes

BEGIN MEMORY MIGRATION
```

The migration spec reads your existing file completely, extracts all decisions and events into the new decisions log, preserves recent sessions in the state file, compresses older history into the archive, and renames the original to `[program]-memory.md.pre-migration` — it is never deleted. Review the migration report before committing. After 7 days without issues, delete the pre-migration file.

---

## Templates

| File | Purpose |
|---|---|
| `program-state-template.md` | Copy and rename to `[program]-state.md` for new programs |
| `program-decisions-log-template.log` | Copy and rename to `[program]-decisions.log` for new programs |
| `program-archive-template.md` | Copy and rename to `[program]-archive.md` for new programs |

---

## Governing Specs

| Spec | What it does |
|---|---|
| `functions/memory-housekeeping-spec.md` | Quarterly maintenance — compress, validate, refresh |
| `functions/memory-migration-spec.md` | One-time
migration from single-file to three-file model |
