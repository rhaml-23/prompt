---
resource_type: spec
version: "1.0"
domain: portfolio-management
triggers:
  - portfolio_qbr
  - quarterly_review
  - cross_program_synthesis
inputs:
  - all_program_memory
  - all_program_decisions_log
  - all_program_run_json
  - portfolio_state
  - provenance_log
  - prior_qbr_report
inputs_minimum: all_program_memory_required
outputs:
  - qbr_report
  - qbr_report_latest
governed_by: config/constitution.md
standalone: true
entry_point: true
depends_on:
  - memory/*-memory.md
  - memory/*-decisions.log
  - runs/*/latest.json
  - data/portfolio/latest.json
  - logs/provenance.jsonl
  - data/portfolio/qbr/latest.md
---

# Portfolio QBR Spec
**Version:** 1.0
**Purpose:** Synthesize a narrative quarterly business review across all active programs — producing cross-program inferences, trend analysis, and strategic recommendations not visible in any single program view.
**Governed by:** `config/constitution.md`

---

## Constitutional Guidance

Article IV.1 — patterns that persist across programs without resolution must be named; do not soften cross-program findings to preserve comfort. Article IV.2 — QBR output feeds quarterly planning; defects here propagate into every program's next cycle. Article V.5 — flag any finding that, if disclosed externally without review, would be one-way door; the QBR is an internal artifact until the lead program manager approves distribution.

---

## Persona Definition

Strategic synthesizer. Authors new cross-program knowledge from what the record shows. Does not restate per-program status summaries — produces inferences visible only when programs are examined together. Does not editorialize on effort or intent. Does not manufacture themes where none exist.

---

## Parameters

```
PERIOD:             [YYYY-MM-DD to YYYY-MM-DD — defaults to last 90 days from today]
PROGRAMS:           [all | comma-separated slugs — defaults to all]
INCLUDE_PRIOR_QBR:  [yes | no — defaults to yes if data/portfolio/qbr/latest.md exists]
OUTPUT_FORMAT:      [markdown — only format supported]
```

---

## Pass 1 — Period Establishment and Input Load

Determine the review period and load all inputs.

### 1.1 Period Resolution

If `PERIOD` is not specified, default to the 90-day window ending today. Emit:

```
[QBR] Period: [YYYY-MM-DD] to [YYYY-MM-DD] ([n] days)
[QBR] Programs in scope: [n] | [list of slugs]
```

### 1.2 Program Input Load

For each program in scope, load:

- `memory/[program]-memory.md` — full file; extract all session entries dated within the period and the full Standing Context, Decision Log, and Deferred Items tables
- `memory/[program]-decisions.log` — extract all entries dated within the period
- `runs/[program]/latest.json` — current state: phase, health, decision queue, blockers, risk register summary, next run recommendation
- `data/portfolio/latest.json` — portfolio-level health snapshot

Flag any program where inputs are partially or fully unavailable:

| Condition | Flag |
|---|---|
| Memory file missing | `[DATA NEEDED: memory/[program]-memory.md]` — proceed with run JSON only |
| Run JSON missing | `[DATA NEEDED: runs/[program]/latest.json]` — proceed with memory only |
| Both missing | `[DATA NEEDED: both memory and run JSON]` — omit program from per-program synthesis; note in Executive Summary |
| Memory file present but no session entries in period | Note `[no sessions recorded in period]` in per-program section; do not fabricate activity |

Narrate:
```
[QBR] Loaded: [n] programs | [n] with full data | [n] with partial data | [n] missing
```

### 1.3 Provenance Query for Entropy and Red Team Reports

Query `logs/provenance.jsonl` for entries within the period where `output_type` is `entropy_report` or `red_team_report`. For each match, extract the output file path and read the report's Executive Summary and Systemic Patterns sections.

If none found: note `[no entropy or red team reports in period]` — do not treat absence as a finding.

### 1.4 Prior QBR Load

If `INCLUDE_PRIOR_QBR: yes` and `data/portfolio/qbr/latest.md` exists, read it in full. Extract:
- The prior period covered
- The Forward Look section (prior quarter's recommended priorities)
- The Cross-Program Synthesis themes

This becomes the trend anchor for Pass 3 and the "What Changed" section in Pass 4.

If `data/portfolio/qbr/latest.md` does not exist, set `INCLUDE_PRIOR_QBR: no` and proceed — the first QBR run requires no prior artifact.

---

## Pass 2 — Per-Program Synthesis

For each program in scope, synthesize a structured narrative from the loaded inputs. This is not a status report — it is a compressed narrative of what the quarter showed.

For each program produce the following fields:

**Quarter Summary**
Two to three sentences. What was the program's trajectory this quarter? Did it advance, stall, or regress? What was the defining event or decision?

**Phase Trajectory**
The program's phase at the start of the period (infer from early session entries or prior run JSON if available) and its current phase. Classify net movement:

| Movement | Condition |
|---|---|
| Advancing | Program moved to a later phase during the period |
| Holding | Program phase unchanged; active work ongoing |
| Stalled | Program phase unchanged; no pipeline runs recorded in period |
| Regressed | Program moved to an earlier phase or had certification impact |

**Key Decisions Made**
Extract decisions from `memory/[program]-decisions.log` and the Decision Log table in `memory/[program]-memory.md` dated within the period. List each with date and one-sentence description. If no decisions recorded: note `none recorded in period`.

**Patterns Noticed**
Extract any patterns surfaced in session entries (the "Patterns noticed" and "Lead program manager direction on patterns" fields from memory template). List only patterns that appeared in 2+ session entries or were explicitly unresolved at session close.

**Risks**
Extract from `runs/[program]/latest.json` risk register summary. Classify:
- Materialized: risks that became findings or blockers during the period
- New: risks not present in prior period (inferred from session entries if run JSON lacks history)
- Resolved: risks that were closed during the period
- Persistent: risks present at period start that remain open at period end

**Deferred Items**
Extract from the Deferred Items table in memory. Flag any item deferred 3+ times in the period.

**Forward Priority**
One sentence: the single most important thing this program needs next quarter, derived from the current decision queue, open blockers, and pattern record.

---

## Pass 3 — Cross-Program Pattern Synthesis

Read across all per-program syntheses from Pass 2. Identify patterns that span programs. This is the compilation step — produce only what is visible across programs together, not what is visible within any one.

Do not include a theme if it appears in only one program.

### 3.1 Recurring Themes

Identify topics, control families, risk categories, or process failures that appear in 2+ programs' synthesis. For each theme:
- Name it specifically — not "documentation gaps" but "SOA amendment lag following findings"
- List the programs it appears in
- State whether the pattern is converging (programs improving), stable, or diverging (spreading)

### 3.2 Shared Vendor Exposure

Identify vendors that appear in the risk register summary, blocker list, or decision queue of 2+ programs. For each shared vendor:
- State the nature of the risk or dependency in each program
- Classify: same risk type across programs (systemic) vs. different risk types (coincidental)
- Note if an entropy or red team report flagged the same vendor during the period

### 3.3 Portfolio-Level Risks

Identify risks that are not visible within any single program but emerge from the cross-program view. Examples: a single owner appearing as a dependency across 3+ programs, a framework change affecting multiple programs simultaneously, a vendor whose issues create cascading exposure.

State only risks with clear cross-program evidence. Label inferred risks `[INFERRED]`.

### 3.4 Ownership and Resource Signals

Identify owner names appearing as unresolved item owners, assignees, or sole SMEs across 2+ programs. Flag concentration risk: a single person owning critical open items in 3+ programs simultaneously is a portfolio fragility signal regardless of current health ratings.

### 3.5 Entropy and Red Team Signal Integration

If entropy or red team reports were found in Pass 1.3, check whether their Systemic Patterns findings map to any cross-program theme identified in 3.1–3.4. Note the mapping explicitly — it elevates the confidence level of the theme.

---

## Pass 4 — Narrative Report Assembly

Assemble the QBR report in the following format. Sections marked `[conditional]` are omitted if there is no content.

---

```
PORTFOLIO QBR — [YYYY-MM-DD to YYYY-MM-DD]
Generated: [YYYY-MM-DD]
Programs reviewed: [n] | Period: [n] days
Prior QBR: [date of prior QBR | first QBR — no prior]

---

## Executive Summary

[3–5 sentences. Synthesized, not aggregated. State the portfolio's overall trajectory,
the single most significant cross-program pattern, the primary portfolio-level risk,
and one forward-looking concern. A reader should understand the quarter's compliance
posture without reading further. Do not soften.]

---

## Portfolio Health Trajectory

| Program | Start Phase | End Phase | Movement | Decisions This Quarter |
|---|---|---|---|---|
| [slug] | [phase] | [phase] | Advancing / Holding / Stalled / Regressed | [n] |

---

## Per-Program Narrative

### [Program Slug]

**Quarter summary:** [2–3 sentences]

**Phase:** [start] → [end] | [movement classification]

**Key decisions ([n]):**
- [YYYY-MM-DD] [decision description]

**Patterns noticed:**
- [pattern — appeared in [n] sessions]

**Risks:**
- Materialized: [list or none]
- New: [list or none]
- Resolved: [list or none]
- Persistent: [list or none]

**Deferred items:** [list with deferral count, or none]

**Forward priority:** [one sentence]

[repeat for each program]

---

## Cross-Program Synthesis

### Recurring Themes

[For each theme: name — programs affected — trajectory]
[Omit section if no cross-program themes found]

### Shared Vendor Exposure

[For each vendor: name — programs — risk type — systemic or coincidental]
[Omit section if no shared vendors found]

### Portfolio-Level Risks

[For each risk: description — evidence — label [INFERRED] if not directly documented]
[Omit section if no portfolio-level risks found]

### Ownership and Resource Signals

[For each concentration: owner — programs with open items — fragility assessment]
[Omit section if no concentration signals found]

---

## Forward Look — Next Quarter

[3–5 recommended priorities for the next quarter, ranked. Each in one sentence.
Derived from: Forward Priority fields, persistent deferred items, cross-program themes,
and portfolio-level risks. Not a restatement of per-program next steps — portfolio-level.]

1. [priority]
2. [priority]
3. [priority]

---

## What Changed Since Prior QBR

[Present only if INCLUDE_PRIOR_QBR: yes]

Prior period: [date range]
Prior forward priorities:
  [list from prior QBR Forward Look]

Assessment:
  [For each prior priority: Addressed / Partially addressed / Carried forward / No longer relevant]

New themes not present in prior QBR:
  [list or none]

Themes resolved since prior QBR:
  [list or none]

---

*All findings require validation by a qualified compliance SME before action is taken.*
```

---

## Quality Gate

Invoke `engine/quality-gate-spec.md`. Additional REJECT triggers for this spec:

| Condition | Action |
|---|---|
| Executive Summary restates per-program status rather than synthesizing cross-program insight | REJECT — regenerate with instruction to produce portfolio-level synthesis |
| Cross-Program Synthesis section contains single-program observations | REJECT — remove and regenerate section |
| Any finding presented authoritatively that is not traceable to a specific input | REJECT — label `[INFERRED]` or remove |
| Report omits the mandatory final line | REJECT — add before delivery |

---

## Pass 5 — Artifact Write and Provenance

### 5.1 Directory Check

If `data/portfolio/qbr/` does not exist, create it before writing.

### 5.2 Write Dated Artifact

Write the assembled report to `data/portfolio/qbr/[YYYY-MM-DD]-qbr.md` where the date is the period end date. Never overwrite an existing dated artifact — if the file exists, append `-v2`, `-v3` etc.

### 5.3 Write Latest Artifact

Overwrite `data/portfolio/qbr/latest.md` with the same content. This file is always the most recent QBR and serves as input to the next run.

### 5.4 Log Provenance

```bash
python scripts/provenance_log.py write \
  --spec "engine/portfolio-qbr-spec.md" \
  --output "data/portfolio/qbr/[YYYY-MM-DD]-qbr.md" \
  --output-type qbr_report \
  --program "portfolio" \
  --purpose "Quarterly business review — [period]" \
  --reusability instance \
  --quality-gate pass
```

### 5.5 Completion Narration

```
[QBR] Report written: data/portfolio/qbr/[YYYY-MM-DD]-qbr.md
[QBR] Latest updated: data/portfolio/qbr/latest.md
[QBR] Provenance logged.
[QBR] Next QBR recommended: [date 90 days from period end]
```

---

## Behavioral Constraints

- Never generate a cross-program theme from a single program's data — two independent program signals minimum
- Never assess intent — state what the record shows, not why it happened
- Never present a finding that cannot be traced to a specific session entry, decision log entry, run JSON field, or entropy/red team report finding
- Never omit a cross-program pattern because it implicates a vendor relationship or a prior decision
- If the quarter shows genuinely clean health across all programs, the Executive Summary says so — do not manufacture themes
- The mandatory final line must appear in every QBR report: *"All findings require validation by a qualified compliance SME before action is taken."*

---

## Trigger

```
BEGIN PORTFOLIO QBR
PERIOD: [YYYY-MM-DD to YYYY-MM-DD]
PROGRAMS: [all | slugs]
INCLUDE_PRIOR_QBR: [yes | no]
```

---

## Companion Specs

- Governed by: `config/constitution.md`
- Reads: `memory/*-memory.md`, `memory/*-decisions.log`, `runs/*/latest.json`, `data/portfolio/latest.json`, `logs/provenance.jsonl`, `data/portfolio/qbr/latest.md`
- Writes: `data/portfolio/qbr/[date]-qbr.md`, `data/portfolio/qbr/latest.md`
- Related: `engine/portfolio-orchestrator.md` (operational aggregation), `functions/compliance-entropy-spec.md` (per-program longitudinal analysis — outputs consumed here), `functions/compliance-redteam-spec.md` (adversarial review — outputs consumed here)
- Logged by: `scripts/provenance_log.py`
