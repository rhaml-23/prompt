# Cursor Agent Use Guide

**Audience:** Collaborators — program managers, people managers, product security engineers  
**Purpose:** Getting started guide for working alongside the lead program manager in the compliance agent system

---

## What this system is

This repo is a structured compliance program management system operated through the Cursor IDE. An AI agent reads the program's specifications, memory files, and run data, then executes defined workflows: drafting communications, filling control templates, monitoring external sources, and maintaining program state. The agent does not make decisions — it organizes, drafts, and surfaces gaps for human review. Every consequential output is staged for approval before it affects anything outside the program.

The lead program manager (Alex Langston) remains accountable for all program outcomes. Your role as a collaborator is to use the system to do your part of the work faster and with better visibility into what you own, what's due, and what's blocking.

---

## Setup

1. Install [Cursor](https://cursor.sh) if you don't have it.
2. Get read/write access to this repository from the lead program manager.
3. Open the repo root (`Portfolio/`) as the Cursor workspace. Skills and slash commands load only when this is the workspace root — opening a subfolder breaks the agent's context.
4. Open the Agent composer: `Cmd+L` → select **Agent** mode.
5. Type `/init` and press Enter. The agent loads the system state and confirms which programs are active. A structured response with program health and pending items means setup is complete.

---

## Quick starts by role

Arguments shown in `[brackets]` are optional — the agent will ask for them if you omit them.

### Program manager

**Check status of a program you own**

```
/program-status [program]
```

Returns: health status, control coverage, open risks, pending decisions, blockers, and upcoming deadlines in a single view.

**See what's due this week across all programs**

```
/due-this-week
```

Returns: evidence windows, POA&M target dates, overdue items, and escalations due in the next 7 days.

**Log a decision from a meeting**

```
/log-decision [program]
```

The agent will ask for the decision summary, GRC ID (optional), and rationale. Appends to the program decision log and provenance. Use this whenever a decision is made in a meeting, email, or Slack thread that should be on record.

**Update a GRC item**

```
/update-item [program] [ID]
```

Shows the item's current state before making any change. Prompts for updated status, owner, or notes. Requires confirmation before writing.

**Debrief a meeting**

Place meeting notes in `data/[program]/materials/meeting-debrief.md`, then run:

```
/meeting-debrief [program]
```

The agent extracts decisions, action items with owners, new risks, and date commitments. Decisions and memory notes write immediately. Run JSON changes are grouped and confirmed before writing.

---

### People manager

**Prep for a 1:1**

```
/meeting-prep "[person name]" [program] [days]
```

Returns: open items owned by that person, completed work, upcoming evidence windows, blockers, and three data-derived talking points. Talking points reflect what is in the program state — not performance commentary.

**Draft a status update for your stakeholders**

```
/draft-status-update [program] [audience]
```

Audience options: `executive` `technical` `auditor` `vendor` `all-hands`. The output is always a draft in `drafts/` — it is never sent automatically. Review it, edit as needed, and send it yourself.


| Audience    | Format                                                    |
| ----------- | --------------------------------------------------------- |
| `executive` | 3 paragraphs: health, one metric, one ask                 |
| `technical` | Coverage metrics, GRC IDs, evidence gaps                  |
| `auditor`   | Monitoring cadence, coverage %, closure rate              |
| `vendor`    | Their systems only, open items, what you need and by when |
| `all-hands` | Plain language, no jargon                                 |


**See what your team owns and what's blocked**

```
/kanban [program]
```

Returns: board column counts, blocked and overdue cards, sprint velocity. Each card shows the assigned owner. Omit the program argument for a cross-program view of all blocked and overdue cards.

---

### Product security engineer

**Run a control assessment**

```
/control-assessment
```

The agent prompts for program, framework type, template path, product documentation source, product name, and version. Framework options: `iec62443-4-2` `disa-stig` `cis-benchmark` `functional-test-plan` `custom`. Output lands in `data/[program]/assessments/`. If the run is interrupted, re-run with `RUN_ID` and `RESUME: yes` to continue from the last validated batch.

**Check what evidence is coming due**

```
/evidence-due [program] [days]
```

Returns: upcoming collection windows within the specified day horizon, plus any overdue windows regardless of date.

**Scan for CVEs, KEV entries, or framework changes**

```
/intel-scan [program]
```

Scans CISA KEV, NVD, MITRE ATT&CK, NIST, and threat feeds. Scores relevance against the program's framework and tech stack. Critical and High findings generate draft communications written to `drafts/`. Lookback window defaults to 14 days. Use `all` as the scope argument to scan across every active program.

**Generate an auditor dashboard**

```
/auditor-view [program]
```

Produces a static HTML file at `ui/[program]-auditor-[date].html`. Covers the provenance log, control coverage, risk register summary, and evidence calendar. Print to PDF from browser for auditor submission.

---

## Active programs


| Slug                      | Program                 |
| ------------------------- | ----------------------- |
| `62443`                   | IEC 62443               |
| `hds`                     | HDS                     |
| `iso42001`                | ISO 42001               |
| `customer-portal-ugc-sso` | Customer Portal UGC SSO |


Use the slug exactly as shown when a command asks for `[program]`.

---

## How to read outputs

Every agent output is either a staged draft for your review or a read-only view of current state. The agent annotates outputs with flags when information is incomplete or uncertain. These are not errors — they are explicit signals that require your attention before the output is used.


| Flag                    | Meaning                                                           | Action required                                                     |
| ----------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| `[DATA NEEDED: source]` | A piece of information is missing — it was not fabricated         | Provide the data from the named source before acting on this output |
| `[OWNER NEEDED]`        | No owner is assigned to this item                                 | Assign an owner before it moves forward                             |
| `[INFERRED]`            | Not explicitly stated in source material — the agent extrapolated | Verify before treating as fact                                      |
| `[CONFLICT — VERIFY]`   | Contradictory information was found                               | Resolve the conflict before acting on either source                 |
| `[CITATION NOT FOUND]`  | A referenced section could not be located                         | Check the source document directly                                  |


Draft communications always land in `drafts/` for your review. The agent will never send anything — that step is always yours.

---

## What requires the lead program manager's approval

The agent stops and waits for explicit approval before taking actions that cannot be fully undone or that affect anything outside the program's internal workflow. These are called one-way doors.

Actions that require lead program manager approval before proceeding:

- Closing a POA&M item during an active audit window
- Moving a kanban card to `done` or `canceled` when it is linked to an open audit item
- Any draft communication flagged for external delivery
- Any action affecting a vendor relationship or contract
- Any output that materially affects another person's standing or obligations

When the agent reaches one of these points, it names the decision, presents the options, and waits. Do not work around this. If the approval requirement is wrong for a given situation, raise it with the lead program manager directly.

---

## Command reference


| Command                | What it does                                                     | Required args                                |
| ---------------------- | ---------------------------------------------------------------- | -------------------------------------------- |
| `/init`                | Session orientation — loads system state, surfaces pending items | none                                         |
| `/daily-brief`         | Morning portfolio health across all programs                     | none                                         |
| `/program-status`      | One-page status for a single program                             | program                                      |
| `/due-this-week`       | Everything due or overdue in the next 7 days, cross-program      | none                                         |
| `/meeting-prep`        | 1:1 briefing scoped to a person and program                      | person, program                              |
| `/draft-status-update` | Draft a stakeholder communication calibrated by audience         | program, audience                            |
| `/evidence-due`        | Upcoming and overdue evidence windows                            | program                                      |
| `/log-decision`        | Record a decision to program memory and provenance               | program                                      |
| `/update-item`         | Update status, owner, or notes on a GRC item                     | program, ID                                  |
| `/intel-scan`          | External source monitoring and risk deltas                       | scope                                        |
| `/auditor-view`        | Auditor-facing compliance posture dashboard as HTML              | program                                      |
| `/provenance-query`    | What the system has produced for a program                       | program                                      |
| `/meeting-debrief`     | Ingest meeting notes and update program state                    | program                                      |
| `/control-assessment`  | Fill a control template from framework and product docs          | program, framework, template, product source |
| `/kanban`              | View or update a program kanban board                            | optional: program                            |
| `/portfolio-qbr`       | Quarterly narrative synthesis across all programs                | none                                         |


All arguments are optional at invocation — the command asks for them if not supplied.

---

## Working with the agent

- **The agent narrates as it works.** You can follow along in the composer — you do not need to wait for a final answer to understand what it is doing.
- **You can paste raw context directly.** Email threads, Slack messages, meeting notes, or task descriptions pasted into the composer are classified and routed automatically. No formatting required.
- **Nothing is sent externally without your action.** The agent writes drafts to `drafts/`, state updates to `runs/` and `memory/`, and dashboards to `ui/`. No external system is touched automatically.
- **Program state is transparent.** Memory files live in `memory/[program]-memory.md` and run state in `runs/[program]/latest.json`. Both are readable markdown and JSON — you can inspect them directly at any time.
- **If you are unsure whether an action is reversible, ask before confirming.** The agent will tell you what it intends to write and where before it writes.

