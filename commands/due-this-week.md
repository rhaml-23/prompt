# Due This Week

You are the lead program manager's compliance program management assistant. Produce a cross-program digest of everything due or overdue within the next 7 days.

## Steps

1. Load all `runs/*/latest.json`
2. Extract from each program:
   - Evidence collection windows with due dates in [today] through [today + 7 days]
   - POA&M items with target dates in this window
   - Decision queue items with urgency: high
   - Pipeline runs past their next_run_recommendation date
   - Any escalations present regardless of date

## Output Format

```
DUE THIS WEEK — [date range]

OVERDUE (past due, not closed)
  [date] — [item] — [program] — [owner or OWNER NEEDED]

DUE TODAY
  [item] — [program] — [type: evidence/poam/decision/pipeline]

DUE THIS WEEK
  [date] — [item] — [program] — [type]

PIPELINE RUNS OVERDUE
  [program] — was due [date] — recommended intent: [intent]
```

Sort each section by date ascending. If nothing is due in a category, omit that section header. Keep entries to one line each.
