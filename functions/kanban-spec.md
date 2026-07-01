---

resource_type: spec
version: "1.0"
domain: program-management
triggers:
  - kanban_init
  - kanban_update
  - kanban_add
  - kanban_export
  - task_tracking
inputs:
  - kanban_yaml
  - run_json
  - principal_input
outputs:
  - updated_kanban_yaml
  - jira_export_csv
  - jira_export_json
  - kanban_summary
governed_by: config/constitution.md
invoked_by:
  - agents/project-manager.md
  - engine/session-init-spec.md
depends_on:
  - functions/program-monitoring-spec.md
  - functions/risk-register-spec.md

---

# Kanban Spec

**Version:** 1.0
**Purpose:** Define the four kanban operations (init, update, add card, export to Jira) and the Jira-detection routing rule that makes the board future-proof for MCP integration.
**Governed by:** `config/constitution.md`
**Schema:** `config/schemas/kanban.schema.json`
**Board path:** `data/[program]/kanban.yaml`

---

## Constitutional Guidance

- **Protect the downstream** (IV.2) — a kanban move that closes a POA&M item linked to an active audit window is a one-way door. Halt, state the link, request confirmation before writing.
- **Surface uncertainty** (IV.4) — when a gap-to-card suggestion infers acceptance criteria from a control description, mark it `[INFERRED]`.
- **Prefer reversibility** (IV.3) — never permanently delete a card. Move to `canceled` instead. The lead program manager may hard-delete via direct file edit.

---

## Jira MCP Detection Rule

Before any write operation, check whether the Jira MCP is active in the current session:

```
IF plugin-atlassian-atlassian MCP is available in scope
  AND board.jira_project_key is not null
THEN
  → Route create/update to Jira MCP (see Operation 4 — Export for field mapping)
  → Populate jira_key on the returned card from the Jira response
  → Write the updated jira_key back to kanban.yaml
ELSE
  → Write directly to data/[program]/kanban.yaml
  → Log provenance
```

This rule applies to Operations 1, 2, and 3 below. Operation 4 (Export) is always local.

---

## Parameters

```
PROGRAM:      [program slug — required for all operations]
OPERATION:    [init | update | add | export]
```

---

## Operation 1 — Init Board

**Trigger:** `data/[program]/kanban.yaml` does not exist, or lead program manager runs `/kanban init [program]`.

### Step 1 — Load source data

Read:

- `runs/[program]/latest.json` — extract `monitoring_output.decision_queue`, `program_state.action_needed`, `program_state.overdue_poam`, `program_state.control_coverage`
- `memory/[program]-decisions.log` — last 20 lines

### Step 2 — Scaffold board header

```yaml
schema_version: "1.0"
program: [program]
board_name: "[Program Display Name] — Project Board"
updated_at: [today]
jira_project_key: null
jira_board_id: null
sprints: []
columns:
  - { id: backlog,     name: Backlog }
  - { id: to_do,       name: To Do }
  - { id: in_progress, name: In Progress }
  - { id: in_review,   name: In Review }
  - { id: done,        name: Done }
  - { id: blocked,     name: Blocked }
  - { id: canceled,    name: Canceled }
cards: []
```

### Step 3 — Convert run items to cards

For each item in the source data:


| Source                                      | Card type | Column    | Labels                |
| ------------------------------------------- | --------- | --------- | --------------------- |
| `decision_queue` item                       | `task`    | `to_do`   | `["decision-queue"]`  |
| `action_needed` item                        | `task`    | `to_do`   | `["action-needed"]`   |
| `overdue_poam` item                         | `bug`     | `to_do`   | `["poam", "overdue"]` |
| Control gap (open control with no evidence) | `story`   | `backlog` | `["control-gap"]`     |


For each card:

- `id` — `PM-001`, `PM-002`, … (sequential, program-scoped)
- `title` — from the item name/description
- `priority` — map from run JSON priority: `high` → `high`, `medium` → `medium`, `low` → `low`; if missing: `medium`
- `due` — from item `due_date` or `due` if present
- `assignee` — from item `owner` if present; otherwise null
- `linked_controls` — populate from control IDs if the source was a control gap
- `poam_id` — populate from `id` field if the source was a POA&M item
- `acceptance_criteria` — for control gaps: `["Evidence collected for [control]", "Evidence reviewed and approved"]` — mark `[INFERRED]`
- `description` — copy item description; append `[INFERRED]` where fields were derived

### Step 4 — Confirm and write

Present the proposed board to the lead program manager:

```
KANBAN INIT — [program]

Board will be created at: data/[program]/kanban.yaml
[n] cards scaffolded from run JSON:
  [n] tasks (decision queue + action needed)
  [n] bugs (overdue POA&M)
  [n] stories (control gaps)

[List first 10 cards with ID, type, title, column]
[if > 10: "… and [n] more"]

Confirm? (yes to write / no to cancel / edit to see full card list)
```

On confirmation: write `data/[program]/kanban.yaml`, log provenance.

---

## Operation 2 — Update Card

**Trigger:** Lead program manager requests a column move, progress note, assignee change, or blocker status on an existing card.

### Allowed updates


| Field                 | Constraint                                                                                                                                                                             |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `column`              | Any valid column. Moving to `done` or `canceled` requires confirmation. If card has `poam_id` and target is `done`, flag as potential one-way door — verify with lead program manager. |
| `blocked_by`          | Setting to non-null must set `column: blocked`. Clearing must move column away from `blocked`.                                                                                         |
| `progress_notes`      | Append only — never edit existing entries. Requires `date` and `note`.                                                                                                                 |
| `assignee`            | Free to set; no confirmation needed.                                                                                                                                                   |
| `due`                 | Free to set; no confirmation needed.                                                                                                                                                   |
| `sprint`              | Must reference a valid sprint ID in `sprints[]`.                                                                                                                                       |
| `story_points`        | Free to set.                                                                                                                                                                           |
| `priority`            | Free to set.                                                                                                                                                                           |
| `acceptance_criteria` | Can append items. Marking an item complete is a progress note, not a field edit.                                                                                                       |


### Protocol

1. Read current card state from `data/[program]/kanban.yaml`
2. Show current state for the affected field(s)
3. Show proposed new state
4. For `done`/`canceled` moves: require explicit confirmation and surface any `poam_id` or `linked_controls` links
5. Apply update, set `updated_at: today` on the card and on the board root
6. Apply Jira MCP detection rule
7. Log provenance

---

## Operation 3 — Add Card

**Trigger:** Lead program manager asks to add a task, story, bug, or epic.

### Prompted fields

Prompt the lead program manager for the following, in order. Fields marked `[required]` halt if not provided.

1. `type` [required] — `epic | story | task | bug | subtask`
2. `title` [required] — one-line summary (Jira Summary)
3. `priority` — default `medium`
4. `description` — optional; can be empty
5. `acceptance_criteria` — one per line; optional
6. `assignee` — optional
7. `due` — optional; format YYYY-MM-DD
8. `sprint` — select from active/future sprints, or leave unscheduled
9. `story_points` — optional
10. `linked_controls` — optional; comma-separated control IDs
11. `poam_id` — optional; if provided, verify it exists in `runs/[program]/latest.json`
12. `labels` — optional
13. `parent_id` — required if type is `subtask`; must reference an existing card ID
14. `column` — default is `backlog` (unscheduled) or `to_do` (if sprint assigned)

### ID assignment

`id` is assigned as `PM-[n+1]` where `n` is the highest existing numeric suffix across all cards. Never reuse IDs.

Apply Jira MCP detection rule after confirmation.

---

## Operation 4 — Export to Jira

**Trigger:** Lead program manager runs `/kanban export [program]` or project-manager agent calls this on demand.

**Output:** `drafts/[program]-jira-import-[date].csv` (Jira bulk CSV importer format) and optionally `drafts/[program]-jira-import-[date].json` (Jira REST API batch format).

### Jira CSV column mapping


| Jira CSV Column                      | kanban.yaml field                     | Notes                                                                            |
| ------------------------------------ | ------------------------------------- | -------------------------------------------------------------------------------- |
| `Summary`                            | `title`                               | Required                                                                         |
| `Issue Type`                         | `type`                                | Capitalize: `Epic`, `Story`, `Task`, `Bug`, `Sub-task`                           |
| `Priority`                           | `priority`                            | Map: `critical` → `Highest`, `high` → `High`, `medium` → `Medium`, `low` → `Low` |
| `Assignee`                           | `assignee`                            | Username or email; leave blank if null                                           |
| `Reporter`                           | `reporter`                            | Username or email; leave blank if null                                           |
| `Labels`                             | `labels` joined `,`                   | Space-free; Jira splits on space                                                 |
| `Components`                         | `components` joined `,`               |                                                                                  |
| `Sprint`                             | sprint name from `sprints[]` lookup   | Blank if null                                                                    |
| `Story Points`                       | `story_points`                        | Blank if null                                                                    |
| `Description`                        | `description` + acceptance criteria   | Append criteria as numbered list                                                 |
| `Due Date`                           | `due`                                 | Format: `dd/MMM/yy` for Jira                                                     |
| `Epic Link`                          | `epic_link` or parent epic `jira_key` | Jira Epic Link field                                                             |
| `Fix Version/s`                      | `fix_version`                         |                                                                                  |
| `Custom field (Acceptance Criteria)` | `acceptance_criteria` joined `\n`     | Only if Jira project has this custom field                                       |


Cards with `jira_key` already set are omitted from the CSV export (they already exist in Jira). Include a summary line at the top of the output noting how many were skipped.

### Jira REST JSON format (optional)

Produce `drafts/[program]-jira-import-[date].json` as an array of Jira issue creation payloads:

```json
[
  {
    "fields": {
      "project": { "key": "[jira_project_key]" },
      "summary": "[title]",
      "issuetype": { "name": "[Issue Type]" },
      "priority": { "name": "[Priority]" },
      "description": { "type": "doc", "version": 1, "content": [...] },
      "assignee": { "name": "[assignee]" },
      "labels": ["[label1]", "[label2]"],
      "duedate": "[due]",
      "story_points": [story_points],
      "customfield_10016": [story_points]
    }
  }
]
```

### Post-export

Log provenance:

```bash
python scripts/provenance_log.py write \
  --spec "functions/kanban-spec.md" \
  --output "drafts/[program]-jira-import-[date].csv" \
  --program "[program]" \
  --purpose "Jira import export — [n] cards" \
  --reusability instance
```

---

## Gap-to-Card Protocol

When the program-agent completes a pipeline run and new gaps or flags are detected that are not already represented by an existing card (`linked_controls` or `poam_id` check), the project-manager agent:

1. Proposes new cards for each untracked gap
2. Shows the proposal to the lead program manager in a numbered list
3. Lead program manager confirms all / selects / skips
4. Confirmed cards are appended to `data/[program]/kanban.yaml`
5. Provenance logged

This is triggered by a `KANBAN_REQUEST` message from the program-agent or coordinator.

---

## Kanban Summary Output

On demand or when aggregating for the coordinator, produce a structured summary:

```
KANBAN SUMMARY — [program] — [date]

In Progress:  [n] cards
Blocked:      [n] cards ([list titles])
Overdue:      [n] cards (due < today, column != done/canceled)
Done (sprint):[n] cards closed in active sprint
Unscheduled:  [n] cards in backlog with no sprint

Blocked detail:
  PM-012 | [title] | [blocked_by]
  PM-019 | [title] | [blocked_by]

Overdue:
  PM-007 | [title] | due [date] ([n]d overdue) | [assignee]
```

---

## Companion Specs

- **Schema:** `config/schemas/kanban.schema.json`
- **Governed by:** `config/constitution.md`
- **Invoked by:** `agents/project-manager.md`, `/kanban` command
- **Reads:** `data/[program]/kanban.yaml`, `runs/[program]/latest.json`
- **Writes:** `data/[program]/kanban.yaml`, `drafts/`
- **Logged by:** `scripts/provenance_log.py` — output_type: `kanban_update`, `jira_export`
- **Jira MCP:** `plugin-atlassian-atlassian` — detected at runtime; not a hard dependency

