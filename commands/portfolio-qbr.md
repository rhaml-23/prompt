# Portfolio QBR

You are the lead program manager's compliance program management assistant. Produce a quarterly business review that synthesizes narrative intelligence across all active programs — cross-program patterns, trend analysis, and strategic recommendations not visible in any single program view.

## Steps

1. Load `config/constitution.md`
2. Read `engine/portfolio-qbr-spec.md` in full
3. Execute the spec with the parameters below

## Parameters

```
PERIOD:             [defaults to last 90 days — override with YYYY-MM-DD to YYYY-MM-DD]
PROGRAMS:           [defaults to all — override with comma-separated slugs]
INCLUDE_PRIOR_QBR:  [defaults to yes if data/portfolio/qbr/latest.md exists, otherwise no]
```

## Trigger

```
BEGIN PORTFOLIO QBR
PERIOD: [resolved period]
PROGRAMS: [resolved program list]
INCLUDE_PRIOR_QBR: [yes | no]
```

Follow all passes in `engine/portfolio-qbr-spec.md` in order. Do not skip the quality gate. Write output to `data/portfolio/qbr/` and log provenance before presenting the report.
