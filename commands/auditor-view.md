# Auditor View

You are the lead program manager's compliance program management assistant. Generate a read-only auditor compliance posture dashboard for a program.

## Input Required

If not provided after the command, ask before proceeding:

- Program: [program slug]
- Lookback window in days (default 90): [days]

## Steps

1. Load `config/constitution.md`
2. Execute `functions/auditor-view-spec.md` with:

```
PROGRAM: [program slug]
REPORT_DATE: [today's date]
LOOKBACK_DAYS: [days]
BEGIN AUDITOR VIEW
```

The auditor-view-spec handles all data assembly and passes. After spec execution, run the renderer:

```bash
python scripts/auditor_view_renderer.py \
  --program [program] \
  --lookback [days] \
  --open
```

## Output

```
AUDITOR VIEW GENERATED — [program]
  Output: ui/[program]-auditor-[date].html
  Provenance entries included: [n]
  Lookback window: [n] days
  Coverage data: [available | unavailable]
  Risk register: [available | unavailable]
  Evidence calendar: [available | unavailable]

  Print to PDF: browser → Print → Save as PDF
  Provenance logged: yes
```

If any data section is unavailable, note it clearly — do not generate a dashboard that appears complete when it is not. Flag staleness if the run JSON is past its next_run_recommendation date.
