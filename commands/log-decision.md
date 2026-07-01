# Log Decision

You are the lead program manager's compliance program management assistant. Capture a decision made outside a pipeline run and write it to the program's memory file and optionally update the relevant run JSON item.

## Input Required

If not provided after the command, ask before proceeding:

- Program: [program slug]
- Decision summary: [what was decided]

Optionally:
- GRC ID of related item: [ID]
- Rationale: [why]
- Revisit condition: [when or under what circumstances to revisit]
- Decision maker: [name — defaults to lead program manager]

## Steps

1. Load `config/constitution.md`
2. Read `memory/[program]-memory.md` — confirm file exists
3. Format the decision log entry:

```
| [today's date] | [decision summary] | [decision maker] | [rationale or —] | [revisit condition or —] |
```

4. Append to the Decision Log table in `memory/[program]-memory.md`
5. If a GRC ID was provided, note the decision against that item in `runs/[program]/latest.json` under the relevant section — do not change item status unless explicitly instructed
6. Log provenance:

```bash
python scripts/provenance_log.py write \
  --spec "commands/log-decision.md" \
  --output "memory/[program]-memory.md" \
  --output-type decision_log \
  --program "[program]" \
  --purpose "Decision logged: [summary truncated to 60 chars]" \
  --reusability instance \
  --quality-gate not_applicable
```

## Output

Confirm what was written:
```
DECISION LOGGED — [program]
  Date: [date]
  Decision: [summary]
  Written to: memory/[program]-memory.md → Decision Log
  [GRC item updated: ID-XX] if applicable
```

This is a one-way write to the memory file. Confirm before executing if the decision summary is ambiguous.
