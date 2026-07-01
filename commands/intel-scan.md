# Intel Scan

You are the lead program manager's compliance program management assistant. Run an external intelligence scan against one or all active programs.

## Input Required

If not provided after the command, ask before proceeding:

- Scope: [program slug | all]
- Lookback window in days (default 14): [days]

## Steps

1. Load `config/constitution.md` — apply Article IV.16 (External Signal Synthesis)
2. If scope is a single program, load `runs/[program]/latest.json` and `memory/[program]-memory.md`
   If scope is all, load all `runs/*/latest.json` files
3. Build program context fingerprints (framework, control families, tech stack)
4. Execute `functions/external-intel-spec.md` with:

```
PROGRAMS: [program slug or all]
LOOKBACK_WINDOW: [days]
SESSION_MODE: briefing
BEGIN INTEL SCAN
```

The external-intel-spec handles all source scanning, relevance scoring, and risk delta generation per its defined passes.

## Output

The intel scan produces its own structured output per the external-intel-spec format. After completion, summarize:

```
INTEL SCAN COMPLETE — [date]
Programs scanned: [n] | Sources scanned: [list categories]
Critical findings: [n] | High: [n] | Medium: [n]

[Risk delta blocks for Critical and High findings]

Staged for weekly session agenda: [n] items
Stakeholder drafts generated: [n] — in drafts/ awaiting review
Report written to: data/[program]/intel/[date]-intel-report.md
```

If scope is all and findings overlap multiple programs, surface the cross-program intel signals section from the external-intel-spec output.
