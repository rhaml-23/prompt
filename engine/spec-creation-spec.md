---
resource_type: spec
version: "2.0"
domain: agent-infrastructure
triggers:
  - new_spec_needed
  - tool_reverse_engineering
  - system_extension
inputs:
  - requirement_description
  - existing_tool_or_script
  - integration_context
outputs:
  - new_spec_file
  - updated_integration_points
governed_by: config/constitution.md
standalone: true
---

# Spec Creation Spec
**Version:** 2.0
**Purpose:** Build new specs and skills that comply with repo standards. Produces fully integrated, token-efficient specs from scratch or by reverse engineering existing tools.
**Governed by:** `config/constitution.md`

---

## Step 1 — Skill or Spec?

| Build a skill if ALL are true | Build a spec if ANY are true |
|---|---|
| Single-purpose, one-pass behavior | Requires constitutional alignment checks |
| No structured JSON input/output | Reused across programs, contexts, or sessions |
| Not invoked by other specs | Multiple processing passes |
| No constitutional alignment needed | Produces artifacts written to disk |
| Not reused across programs | Invoked by or invokes other specs |

When uncertain: default to skill. Promote to spec only when the system needs the structure.

---

## Step 2 — If Skill: Define It

Skills live in the constitution (Article IV), `.cursorrules`, or the relevant spec's behavioral section. No separate file.

```
### [Skill Name]
[One to three sentences. Imperative voice. What the agent does,
when, and what it produces. No preamble.]
```

Placement:
- System-wide behavior → `config/constitution.md` Article IV
- Session-type behavior → relevant engine spec behavioral section
- Pipeline-pass behavior → relevant pass in `engine/program-pipeline-orchestrator.md`
- Cursor-specific → `.cursorrules`

---

## Step 3 — If Spec: Gather Requirements

```
SPEC_NAME:     [descriptive-kebab-case-name]
DOMAIN:        [program-management | compliance | vendor | communications |
                calendar | session-management | agent-infrastructure]
PURPOSE:       [one sentence]
TRIGGER:       [what invokes this spec]
INPUTS:        [list each]
OUTPUTS:       [list each]
PASSES:        [count and name of each processing pass]
STANDALONE:    [true | false]
ENTRY_POINT:   [true | false]
INVOKED_BY:    [calling specs if any]
INVOKES:       [specs this one calls if any]
```

**Reverse engineering an existing tool** — extract requirements by answering:
- What does it accept? → `INPUTS`
- What does it produce? → `OUTPUTS`
- What decisions does it make? → `PASSES`
- What can go wrong? → error handling per pass
- Does it need program state, prior runs, or memory? → `INVOKED_BY`, `INPUTS`

**Building a tool over ~200 lines** — read `config/tool-requirements.md` and produce a tool plan before writing code.

---

## Step 4 — Build the Spec

### 4.1 Frontmatter

```yaml
---
resource_type: spec
version: "1.0"
domain: [DOMAIN]
triggers:
  - [TRIGGER]
inputs:
  - [INPUT]
outputs:
  - [OUTPUT]
governed_by: config/constitution.md
standalone: [true|false]
entry_point: [true|false]
invoked_by:
  - [engine/ or functions/ path]
invokes:
  - [engine/ or functions/ path]
depends_on:
  - [data paths]
---
```

### 4.2 Header Block

```markdown
# [Spec Title]
**Version:** 1.0
**Purpose:** [one sentence]
**Governed by:** `config/constitution.md`
```

No Portability line. No Maintainer line unless the repo requires it.

### 4.3 Constitutional Guidance

Protected heading — required in every spec. Keep it a stub: one to three lines naming the active articles and why. Do not explain the articles — the constitution is already loaded.

```markdown
## Constitutional Guidance

[Article ref] — [one-line reason it applies here]. [Article ref] — [one-line reason].
```

### 4.4 Persona Definition

One compressed line. States role, key constraint, and what the agent does not do. Second person not required — density over convention.

```markdown
## Persona Definition

[Role]. [What it does]. [What it does not do]. [Key behavioral constraint.]
```

### 4.5 Parameters

```markdown
## Parameters

\```
PARAM_NAME: [type and description — default if applicable]
\```
```

### 4.6 Processing Passes

One section per pass. Imperative voice. Tables over prose for decision logic. Include trigger condition, instructions, flag conditions, missing-data handling, and defined output.

```markdown
## Pass [N] — [Pass Name]

[Instructions. Imperative. Specific.]

| Condition | Action |
|---|---|
| [condition] | [action] |
```

**Density standards for passes:**
- Decision logic → table, not prose
- Flag conditions → inline with the instruction that triggers them, not a separate section
- Missing data → `[DATA NEEDED: source]` inline, not a separate flags section unless flags are numerous
- Narration blocks → one line per significant event, not paragraphs

### 4.7 Quality Gate Integration

```markdown
## Quality Gate

Invoke `engine/quality-gate-spec.md`. Spec-specific REJECT triggers: [list or "standard gates only"].
```

### 4.8 Provenance

Every spec that writes output logs provenance. Include the exact script call:

```bash
python scripts/provenance_log.py write \
  --spec "functions/[spec-name].md" \
  --output "[output path]" \
  --output-type [type] \
  --program "[PROGRAM]" \
  --purpose "[context]" \
  --reusability [template|reference|instance|artifact] \
  --quality-gate [pass|fail]
```

### 4.9 Companion Specs

```markdown
## Companion Specs
- Governed by: `config/constitution.md`
- Reads: [paths]
- Writes: [paths]
- Invokes: [specs]
- Logged by: `scripts/provenance_log.py`
```

No Suggested Repo Path section — path belongs in the frontmatter and companion specs only.

---

## Step 5 — Update Integration Points

| Integration point | File | When required | What to update |
|---|---|---|---|
| Calling spec frontmatter | Any spec that invokes the new one | Always if invocation exists | Add to `invokes:` list |
| Pipeline orchestrator | `engine/program-pipeline-orchestrator.md` | If part of pipeline | Routing table, `invokes:` frontmatter |
| Session init routing | `engine/session-init-spec.md` | If principal-facing | Routing table |
| Quality gate | `engine/quality-gate-spec.md` | If new output type | Add to Gate 2 required sections |
| Constitution | `config/constitution.md` | If new system-wide behavior | Article IV mandate, quick reference |
| README | `README.md` | Always | Spec reference table, repo structure if new dir |
| Provenance log | `scripts/provenance_log.py` | If new deliverable type | Add to `OUTPUT_TYPES` |
| `.cursorrules` | `.cursorrules` | If changes session-start behavior | One-line note |

---

## Step 6 — Self-Check Before Delivery

```
SPEC SELF-CHECK

Frontmatter:
  □ resource_type, version, domain, triggers, inputs, outputs present
  □ governed_by: config/constitution.md
  □ standalone and entry_point correctly set
  □ invoked_by and invokes reflect actual relationships
  □ all paths use engine/ functions/ agents/ scripts/ config/ — no leading /

Structure:
  □ Constitutional Guidance present — stub, not prose
  □ Persona Definition present — one compressed line
  □ Each pass has trigger, instructions, and defined output
  □ Decision logic in tables not prose
  □ Quality gate section present
  □ Provenance logging block present
  □ No Suggested Repo Path section
  □ No Tone section
  □ No human setup documentation

Density:
  □ No constitutional article explanations — articles are loaded, not explained
  □ No motivational framing — imperative instructions only
  □ No trailing sentences that restate what the format already shows
  □ [DATA NEEDED] not [DATA MISSING] for missing data flags
  □ Tables used where criteria have clear condition/action pairs

Integration:
  □ Orchestrator updated if pipeline spec
  □ Session init routing table updated if principal-facing
  □ README updated
  □ Provenance log output types updated if new deliverable type
```

---

## Trigger

```
SPEC_NAME: [name]
PURPOSE: [one sentence]
[existing tool or context if reverse engineering]

BEGIN SPEC CREATION
```
