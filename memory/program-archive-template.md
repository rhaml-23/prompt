# Program Archive — [PROGRAM_NAME]
**Slug:** [program-slug]
**Created:** [YYYY-MM-DD]

This file contains compressed session history for sessions older than 90 days.
Raw session entries are summarized into quarterly blocks.
All decisions, accepted risks, one-way door actions, and escalations from archived
sessions are preserved verbatim in `memory/[program-slug]-decisions.log`.
Context that does not appear in the decisions log is summarized here — it may be
further compressed in future housekeeping passes but is never deleted.

---

<!-- QUARTERLY BLOCK FORMAT:
## [YYYY] Q[N] — [Month] through [Month]
**Sessions:** [n] | **Compressed:** [YYYY-MM-DD]

**Summary:**
[2-4 sentences capturing the quarter's primary focus, significant changes,
and program trajectory. Written by the housekeeping spec — not manually edited.]

**Decisions made this quarter:**
[List decisions from decisions log in this date range — copied verbatim]

**Risks accepted this quarter:**
[List RISK_ACCEPTED entries in this date range — copied verbatim]

**One-way doors:**
[List ONE_WAY_DOOR entries — copied verbatim]

**Patterns that recurred:**
[List any patterns from the period that repeated across sessions]

**Key artifacts produced:**
[List significant deliverables from provenance log for this period]
-->

