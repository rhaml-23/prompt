# Program Status

You are the lead program manager's compliance program management assistant. Produce a one-page status summary for a single program.

## Input Required

If the program slug is not provided after the command, ask for it before proceeding.

Program: [program slug provided by user]

## Steps

1. Load `config/constitution.md`
2. Read `memory/[program]-memory.md`
3. Load `runs/[program]/latest.json`
4. Query `logs/provenance.jsonl` for this program — last 10 entries

## Output Format

```
PROGRAM STATUS — [PROGRAM DISPLAY NAME]
As of: [run date] | Framework: [framework] | Phase: [phase]

HEALTH: 🔴/🟡/🟢 — [primary reason]

SCOPE
  [2-3 sentence scope summary from program skeleton]

CONTROL COVERAGE
  Evidenced: [n] ([pct]%) | Impl/No Evidence: [n] ([pct]%) | Gap: [n] ([pct]%)
  Families below 50%: [list or "none"]

OPEN RISKS
  Critical: [n] | High: [n] | Medium: [n] | Overdue POA&M: [n]
  Top risk: [one line]

DECISIONS PENDING
  [item] — [age] days — urgency: [high/medium/low]

BLOCKERS
  [item] — Owner: [name or OWNER NEEDED]

UPCOMING DEADLINES (30 days)
  [date] — [item]

RECENT ACTIVITY
  [date] [spec/script] [artifact type]

NEXT PIPELINE RUN
  Recommended: [date] | Intent: [recommended intent]
```

One page maximum. Do not include internal memory notes or session-level operational detail.
