# /kanban

Invokes the project manager agent to view, update, or initialize a program's kanban board. When called without a program, produces a cross-program blocked/overdue summary across all active boards.

## Usage

```
/kanban [program] [operation] [card-id]
```

All arguments are optional. The command prompts for anything it needs.

## Argument Reference

| Argument | Values | Effect |
|----------|--------|--------|
| `program` | program slug | Scope to one program's board |
| `operation` | `init` `add` `update` `export` `sprint` `status` | Explicit operation; defaults to `status` |
| `card-id` | e.g. `PM-019` | Pre-select a card for `update` |

## Operations

### `/kanban` (no arguments)
Cross-program summary. Reads all `data/[program]/kanban.yaml` files and surfaces:
- All blocked cards across all programs (title, blocker reason, assignee, age)
- All overdue cards (title, due date, days overdue, program)
- In-progress count per program
- Jira project key if synced

### `/kanban [program]` — Board Status
One-program view. Surfaces current column counts, active sprint progress, blocked and overdue detail, and velocity (cards closed this sprint).

### `/kanban [program] init`
Initialize a new kanban board for the program. Scaffolds cards from the latest run JSON (decision queue, action-needed items, overdue POA&M, control gaps). Requires confirmation before writing.

### `/kanban [program] add`
Add a new card to the board. Prompts for type, title, priority, acceptance criteria, assignee, due date, sprint, and optional compliance links (controls, POA&M ID). Assigns the next PM-NNN ID. Requires confirmation.

### `/kanban [program] update [card-id]`
Update an existing card. Shows current state, prompts for the change (column move, progress note, assignee, due date, blocked_by, story points). Moving to `done` or `canceled` requires explicit confirmation. Cards linked to active POA&M items are flagged as one-way door moves.

### `/kanban [program] export`
Generate a Jira import file. If the Jira MCP (`plugin-atlassian-atlassian`) is available and `jira_project_key` is set on the board, routes directly to Jira. Otherwise produces:
- `drafts/[program]-jira-import-[date].csv` — Jira bulk importer format
- `drafts/[program]-jira-import-[date].json` — Jira REST API batch format (optional)
Cards with an existing `jira_key` are skipped (already in Jira).

### `/kanban [program] sprint`
Sprint management: create a new sprint, close the active sprint (with card rollover confirmation), or view sprint velocity.

## Examples

```
/kanban
/kanban fedramp-high
/kanban fedramp-high init
/kanban fedramp-high add
/kanban fedramp-high update PM-019
/kanban fedramp-high export
/kanban fedramp-high sprint
```

## Jira Integration

When `plugin-atlassian-atlassian` MCP is active and the board has a `jira_project_key`:
- `add` and `update` route to Jira MCP instead of writing YAML
- The returned Jira `key` is written back to `kanban.yaml` as `jira_key`
- `export` creates issues directly in Jira instead of producing a CSV

When Jira MCP is not active, all operations write to `data/[program]/kanban.yaml` only. The YAML is always kept as the offline-readable copy.

## File Locations

- Board: `data/[program]/kanban.yaml`
- Schema: `config/schemas/kanban.schema.json`
- Spec: `functions/kanban-spec.md`
- Agent: `agents/project-manager.md`
- Renderer: `scripts/kanban_renderer.py`
- Jira exports: `drafts/[program]-jira-import-[date].csv`
- Dashboard: rendered by `scripts/kanban_renderer.py` → `ui/[program]-kanban-[date].html`

## Governing Constraints

All operations governed by `config/constitution.md`. Moves to `done` or `canceled` on cards linked to POA&M items during active audit windows require explicit confirmation — these are one-way door actions. All writes are logged to `logs/provenance.jsonl`.
