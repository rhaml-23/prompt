---
resource_type: spec
version: "1.1"
domain: quality-assurance
triggers:
  - quality_gate_gate6
inputs:
  - any_spec_output_text
outputs:
  - style_finding_list
governed_by: config/constitution.md
standalone: false
invoked_by:
  - engine/quality-gate-spec.md
depends_on: []
---

# Document Style Guide
**Version:** 1.1
**Purpose:** Scan compliance document outputs for empirically documented AI writing patterns that undermine credibility, neutrality, and evidentiary precision. Also scan instructional and escalation prose for indirect binding, unexplained shorthand, and undecidable scope rules.
**Governed by:** `config/constitution.md`

---

## Constitutional Guidance

IV.1 — outputs must state true things; inflated, vague, or promotional language corrupts that obligation. V.3 — credibility failures must be stopped here, not passed forward.

---

## Persona Definition

Language auditor. Scans output text against Tier 1 pattern tables and Tier 2 scan criteria. Produces findings with excerpts. Does not rewrite — flags only.

---

## Why This Spec Exists

Large language models produce statistically predictable language. In compliance documents, these patterns are not merely stylistic problems — they are credibility and evidentiary failures. A control narrative that inflates significance, vaguely attributes claims, or pads analysis with promotional language is not a defensible audit artifact, regardless of whether its underlying facts are correct.

This spec encodes findings from systematic study of AI writing tells (source: Wikipedia:Signs of AI writing and supporting empirical research on LLM vocabulary distribution) into actionable scan criteria calibrated for compliance document contexts.

---

## Severity Model

| Tier | Gate Result | Action |
|---|---|---|
| Tier 1 — Critical | REJECT | Any single Tier 1 finding triggers regeneration |
| Tier 2 — Caution | FLAG | Noted in validation report; triggers REJECT only when Gate 4 (Tone) also fails |

---

## Tier 1 — Critical Patterns (REJECT)

### AI Vocabulary Cluster

**Trigger:** 3 or more flagged words appearing in any contiguous 200-word passage.

Flagged word list (empirically documented as overrepresented in LLM output post-2022):

```
additionally (sentence-initial only)
align with / aligns with
bolstered
crucial
delve / delves / delved
emphasizing / emphasizes
enduring
enhance / enhances / enhanced
foster / fosters / fostered
garner / garners / garnered
highlight (as verb) / highlights / highlighted
interplay
intricate / intricacies
landscape (abstract usage — "the regulatory landscape")
meticulous / meticulously
pivotal
showcase / showcases / showcasing
tapestry (abstract usage)
testament
underscore (as verb) / underscores / underscored
valuable (as filler modifier)
vibrant
```

Detection: count occurrences within any 200-word window. Three or more = finding.

Note: words on this list used in their literal, non-figurative sense (e.g., "underscore" as a typographic character, "landscape" as a physical terrain feature) are not violations.

---

### Vague Attribution

**Trigger:** Any claim attributed to an unnamed collective rather than a traceable source.

Prohibited constructions:

```
Industry reports indicate / suggest / show
Experts argue / suggest / note / believe
Observers have noted / cited / suggested
Several sources indicate / report / suggest
Some critics argue / contend / maintain
Analysts believe / expect / project
Many researchers have found
It is widely recognized / accepted / understood
Studies show (without citation)
```

In compliance documents, every factual claim must trace to a named source or be labeled `[INFERRED]`. Vague attribution substitutes rhetorical weight for evidentiary traceability.

---

### Promotional Language

**Trigger:** Any promotional or advertisement-like descriptor applied to a compliance subject.

Prohibited terms and constructions:

```
boasts (meaning "has")
vibrant (as a modifier for organizations, programs, or ecosystems)
rich (as puffery: "rich history", "rich tapestry", "rich culture")
profound (as puffery: "profound impact", "profound commitment")
groundbreaking
renowned / world-renowned
nestled
in the heart of
diverse array of
commitment to excellence / commitment to quality
natural beauty
showcasing its dedication
exemplifies
```

These terms have no place in control narratives, gap analyses, risk assessments, or audit artifacts.

---

### Collaborative Preamble

**Trigger:** Any phrase indicating the output was generated as AI correspondence rather than a compliance artifact.

Prohibited constructions:

```
Certainly!
Absolutely!
Of course!
Great question!
I hope this helps
I hope this finds you well
Would you like me to
Let me know if
Is there anything else
Here is a detailed breakdown
Here is a comprehensive overview
As an AI / As a language model
I should note that my knowledge
```

These patterns indicate unreviewed LLM output that was not authored as a compliance document.

---

### Knowledge-Gap Speculation

**Trigger:** Any passage that speculates about undocumented information rather than flagging the gap with `[DATA NEEDED]`.

Prohibited constructions:

```
While specific details are not extensively documented...
While information is limited / scarce / not widely available...
Not widely documented / disclosed / reported
Likely due to limited mainstream exposure
Maintains a low profile / keeps details private (as a data gap filler)
Based on available information (when used to justify speculation)
While specific [X] are not included in the provided sources, [X] likely...
Details are not publicly available, however it is probable that...
```

The correct handling for missing data is `[DATA NEEDED: source]` — not speculative filler.

---

## Tier 2 — Caution Patterns (FLAG)

### Significance Inflation

Constructions that inflate the importance of a compliance subject beyond what evidence supports:

```
stands as a testament to
serves as a testament to
is a testament to
pivotal moment in
marks a shift in
key turning point
evolving landscape
focal point
indelible mark
deeply rooted
underscores its importance / significance
contributing to the broader [trend / movement / narrative]
reflects broader [trends / patterns]
setting the stage for
symbolizing its ongoing / enduring / lasting [quality]
```

In compliance documents, a control either satisfies a requirement or it does not. Inflated framing obscures that determination.

---

### Superficial -ing Appends

Factual sentence immediately followed by a participial phrase that asserts significance rather than adding evidentiary content.

Pattern: `[factual claim], [present-participle phrase asserting importance].`

Examples of the prohibited structure:
- "The organization completed its annual review, highlighting its commitment to continuous improvement."
- "The control was implemented in Q3, contributing to the organization's security posture."
- "The audit found no material gaps, reflecting the maturity of the program."

The participial phrase adds no evidentiary content. Remove it. State the fact; let the evidence speak.

---

### Challenges Boilerplate

Section or paragraph matching the formula: *"Despite its [positive/promotional words], [subject] faces challenges including..."* followed by a speculative future-outlook paragraph.

Indicators:
```
Despite its [strength / success / progress], [subject] faces challenges...
Despite these challenges, [subject] continues to...
Challenges and Future Prospects / Challenges and Opportunities (as section heading)
Future Outlook (as section heading paired with challenge framing)
Moving forward, [subject] will need to...
As [subject] continues to evolve...
```

Compliance documents state findings and recommendations. They do not apply a narrative arc of adversity and redemption.

---

### Negative Parallelisms

Constructions that frame a compliance statement as correcting an implied misconception:

```
Not just X, but also Y
Not only X, but Y
It's not about X, it's about Y
This isn't merely X — it's Y
Not X, but Y
No X, no Y, just Z
```

These add rhetorical structure where specificity is required.

---

### Rule of Three (Padding)

Three-item adjective or noun-phrase clusters used to inflate the apparent comprehensiveness of a thin observation:

Pattern: `[adj], [adj], and [adj]` or `[phrase], [phrase], and [phrase]` where the three items are near-synonyms or add no independent information.

Examples:
- "The program is robust, comprehensive, and effective."
- "Controls are documented, reviewed, and maintained."
- "The policy is clear, actionable, and enforceable."

Each item must carry independent evidentiary weight. If it cannot be removed without losing meaning, it may stay.

---

### Copulative Avoidance

Replacing `is` / `are` with more elaborate constructions when the simpler verb is correct:

```
serves as [a/an]   →  is
stands as [a/an]   →  is
marks [a/an]       →  is / represents (when literal)
represents [a/an]  →  is (when used to inflate)
boasts [a/an]      →  has
features           →  has / contains (in descriptive prose)
offers             →  has / provides (in descriptive prose)
```

Preference: use `is`, `are`, `has`, `contains`. Reserve elaborate copulative constructions for cases where they carry genuine semantic distinction.

---

### Elegant Variation

Rotating synonyms for a defined compliance term to avoid repetition, when the repetition is correct and the variation introduces ambiguity:

Common compliance terms subject to this pattern:
```
control / safeguard / measure / mechanism / protection (rotating for same item)
requirement / obligation / criterion / mandate (rotating for same regulatory clause)
finding / observation / issue / concern (rotating for same audit item)
evidence / artifact / documentation / record (rotating for same proof element)
```

Use the term the framework or regulation uses. Consistency is an evidentiary property in compliance documents.

---

### Overuse of Boldface

Bold applied to non-critical-finding, non-defined-term text:

- More than one bolded phrase per paragraph in prose sections
- Bolding used for rhetorical emphasis rather than to mark a defined term or critical finding
- "Key takeaways" bold patterns where every noun in a list is bolded

Permitted bold: defined terms at first use, critical findings in executive summaries, section callouts defined by the governing spec.

---

### Em Dash Clusters

Three or more em dashes (—) on a single page in non-tabular text.

Em dashes used for formulaic emphasis — especially in pairs — that could be replaced with commas, colons, or parentheses are a documented AI writing tell. One or two per page is unremarkable; clusters signal AI-generated rhetorical punctuation.

---

### Indirect binding guidance

**Trigger:** Instructional passages (numbered steps, "when to escalate," "guardrail," "baseline," "field teams," boundaries, or obligations to the reader) where the binding rule is not stated in direct, active form up front.

**Principle:** Say what is allowed and what is not before narrative motivation or background. Prefer explicit modals over passive setup or example-only implication.

Preferred patterns (non-exhaustive):

```
It is permitted to … / It is not permitted to …
You must … / Do not … / Never …
Escalate when … / You may proceed without escalation when …
Notify [role] before … / No notification is required when …
```

**FLAG when:**

- The first operative sentence in an instructional block is not a direct rule (for example, it opens with background such as "it is an established …" or "there is a regulatory difference …" without an immediate permitted / not-permitted or must / do-not statement); or
- Permitted vs. prohibited behavior appears only after a vague lead or only by implication from a downstream example.

Readers in compliance contexts need the operative line first; rationale follows.

---

### Metaphor or shorthand without plain-language anchor

**Trigger:** Regulatory, enforcement, or operational shorthand that does not state what the phrase means for the reader in plain language in the same sentence or the sentence immediately after.

Examples of shorthand that often needs anchoring (regulatory or risk sense, not literal usage):

```
target (e.g., "enforcement target")
territory (e.g., "GPAI territory")
crosshairs / line in the sand / red flag (figurative)
guardrail (when not a defined technical control)
```

**FLAG when** the sentence uses such shorthand but does not spell out the consequence or action for the reader (for example: regulators may treat the conduct as subject to investigation or civil penalties; the practice may constitute a deceptive representation; the engagement requires legal review).

**Required fix:** Replace or follow the shorthand with a concrete statement of risk, obligation, or next step. Abstract "landscape" and similar items remain covered by the Tier 1 AI vocabulary cluster when they appear in cluster counts; this category applies to metaphorical enforcement and scope shorthand regardless of cluster rules.

---

### Incomplete operational criterion

**Trigger:** A paragraph ties escalation or mandatory review (escalate, notify, stop, halt, legal review, compliance review) to subjective scope language without giving the reader a way to classify the gray case.

Subjective scope indicators (non-exhaustive):

```
broad / narrow / diverse / general-purpose
across use cases / scoped / specific (without objective tests)
```

**FLAG when** the paragraph omits at least one of:

- **Inverse case** — the same class of activity (for example, fine-tuning) when escalation is *not* required; or
- **Testable criteria or worked examples** that disambiguate narrow vs. diverse scope; or
- **Uncertainty default** — explicit instruction such as: if classification is unclear, treat as in-scope for escalation (or out-of-scope) until Legal or the named compliance function confirms.

**Good pattern (illustrative):**

```
- Escalate when: [concrete triggers]
- No escalation required when: [concrete triggers]
- If unsure: [default until confirmed]
```

---

## Scan Protocol

Execute in order. Do not skip either tier even if Tier 1 findings are present.

```
Step 1 — Tier 1 Scan
  For each Tier 1 category:
    Apply detection rule
    If match: record finding — category, offending excerpt (verbatim, ≤30 words), approximate location

Step 2 — Tier 2 Scan
  For each Tier 2 category:
    Apply detection rule
    If match: record flag — category, offending excerpt (verbatim, ≤30 words), approximate location

Step 3 — Output
  Produce STYLE SCAN RESULT block (see Output Format)
  Return to quality gate for gate result determination
```

---

## Output Format

```
STYLE SCAN RESULT
Output: [output type and generating spec]
Scanned: [date]

Tier 1 — Critical: [n findings | none]
  - [category]: "[offending excerpt]" — [location]
  - [category]: "[offending excerpt]" — [location]

Tier 2 — Caution: [n flags | none]
  - [category]: "[offending excerpt]" — [location]
  - [category]: "[offending excerpt]" — [location]

Result: PASS | REJECT | FLAGGED
```

Result logic:
- `PASS` — no Tier 1 findings, zero or more Tier 2 flags
- `REJECT` — one or more Tier 1 findings
- `FLAGGED` — no Tier 1 findings, one or more Tier 2 flags

In the finding and flag lines, set `[category]` to the subsection title from this spec (for example, `Indirect binding guidance`, `Metaphor or shorthand without plain-language anchor`, `Incomplete operational criterion`).

---

## Correction Brief Format

When result is REJECT, produce a terse correction brief for the regeneration protocol:

```
STYLE CORRECTION BRIEF
Tier 1 violations requiring correction:
  - [category]: Replace "[offending excerpt]" — [instruction]
  - [category]: Replace "[offending excerpt]" — [instruction]

Instruction: Remove or rewrite the identified passages.
Do not introduce new instances of Tier 1 or Tier 2 patterns as replacements.
Do not change content that is not implicated by these findings.

When remediating Tier 2 flags for Indirect binding guidance, Metaphor or shorthand without plain-language anchor, or Incomplete operational criterion: restate the affected rule in permitted / not-permitted form (or equivalent explicit modals such as must / do not / escalate when) before supporting rationale; anchor any regulatory shorthand with plain-language consequence or action in the same sentence or the sentence immediately after; and supply inverse case, testable criteria, or an uncertainty default as required by Incomplete operational criterion.
```

---

## Companion Specs
- Governed by: `config/constitution.md`
- Invoked by: `engine/quality-gate-spec.md` Gate 6
- Referenced by: `agents/run-reviewer.md` D5 persona drift
- Logged by: `scripts/provenance_log.py` (via quality gate)
