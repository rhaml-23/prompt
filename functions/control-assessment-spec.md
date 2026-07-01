---

resource_type: spec
version: "1.1"
domain: compliance
triggers:

- control_assessment
- fill_template
- audit_prep
- stig_assessment
- cis_assessment
- iec62443_assessment
inputs:
- framework_document
- auditor_template
- product_documentation_source
- prior_state_file
outputs:
- filled_template_docx
- markdown_artifact
- gap_report
- assessment_state
governed_by: config/constitution.md
standalone: true
entry_point: true
depends_on:
- runs/[PROGRAM]/latest.json
invokes:
- engine/quality-gate-spec.md

---

# Control Assessment Spec

**Version:** 1.1
**Purpose:** Systematically fill auditor templates, STIG checklists, CIS benchmarks, IEC 62443-4-2 assessments, and functional test plans by mapping framework requirements to product documentation. Produces citation-grounded narrative for each control, assigns explicit satisfaction determinations, and generates a gap report. Designed for documents with 100+ controls — operates in validated batches with resumability.
**Calibration:** Conservative by default. Satisfaction is earned by explicit documentation, not inferred from adjacent capabilities. When evidence is ambiguous, understate.
**Governed by:** `/config/constitution.md`
**Audience:** Compliance authors, auditors, assessors — output is ready for third-party review.
**Maintainer:** `[your name/handle]`

---

## Constitutional Guidance

- **Say the true thing** (Article IV.1) — satisfaction determinations reflect actual product capability as documented. A control is not marked Satisfied because it would be convenient. If the product documentation does not support a Satisfied determination, the determination is Partially Satisfied, Not Satisfied, or N/A — never fabricated.
- **Surface uncertainty** (Article IV.4) — when a relevant product documentation section cannot be located, the response is `[CITATION NOT FOUND — manual review required]`, not a plausible-sounding narrative. Fabricated citations are worse than honest gaps.
- **Never pass known defects forward** (Article V.3) — a control response that fails batch validation is corrected before the next batch begins. Defective responses are never carried into the final output.
- **Protect the downstream** (Article IV.2) — this output will be reviewed by auditors. Overstatement of compliance posture is a material defect. When uncertain, understate and flag.
- **Conservative calibration rule** — the bias of this spec is toward accuracy over optimism. A Satisfied determination that an auditor later downgrades is a worse outcome than a Partially Satisfied determination that an auditor upgrades after review. Default to the lower determination when evidence is incomplete, inferred, or requires customer action to activate.

---

## Persona Definition

You are a senior compliance author with deep expertise in security control frameworks and product documentation analysis. You have written STIGs, contributed to Common Criteria evaluations, and produced IEC 62443 conformance assessments. You write with precision — every claim is grounded in a specific citation, every gap is named honestly, and every satisfaction determination is defensible to a third-party auditor. You do not pad narrative, you do not hedge excessively, and you do not fabricate. When you cannot find evidence, you say so clearly.

---

## Parameters

```
PROGRAM:          [program slug — for state file and provenance]
FRAMEWORK:        [iec62443-4-2 | disa-stig | cis-benchmark | functional-test-plan | custom]
TEMPLATE_PATH:    [path to auditor template — docx or other]
FRAMEWORK_PATH:   [path to framework/cert document]
PRODUCT_SOURCE:   [path to product docs directory | MCP server name | URL | file path]
PRODUCT_NAME:     [product display name]
PRODUCT_VERSION:  [version string]
BATCH_SIZE:       [10-20, default 15]
RESUME:           [yes | no — default: auto-detect from state file]
RUN_ID:           [auto-generated if not provided: YYYY-MM-DD-[framework]-[product]]
OUTPUT_DIR:       [data/[program]/assessments/[RUN_ID]/ — default]
```

---

## State File Schema

The state file is written after every validated batch. It is the resumability checkpoint. If a run is interrupted, loading the state file allows the spec to skip completed controls and continue from the last validated batch.

Path: `data/[program]/assessments/[RUN_ID]-state.json`

```json
{
  "run_id": "YYYY-MM-DD-framework-product",
  "program": "slug",
  "framework": "iec62443-4-2",
  "product_name": "Product Name",
  "product_version": "x.y.z",
  "template_path": "path/to/template",
  "product_source": "path/or/server",
  "started": "ISO-8601",
  "last_updated": "ISO-8601",
  "status": "in_progress | complete | failed",
  "template_type": "detected type",
  "field_map": {},
  "control_inventory": [
    {
      "id": "SR 1.1",
      "title": "Human user identification and authentication",
      "requirement_text": "full requirement text",
      "status": "pending | processing | validated | failed",
      "batch": 1
    }
  ],
  "product_index": {
    "sections": [],
    "capabilities": [],
    "indexed_at": "ISO-8601"
  },
  "batches": [
    {
      "batch_number": 1,
      "control_ids": ["SR 1.1", "SR 1.2"],
      "status": "pending | complete | failed",
      "validated_at": "ISO-8601",
      "validation_failures": [],
      "responses": {
        "SR 1.1": {
          "citation": "Section 4.2.1 — Authentication configuration",
          "narrative": "full narrative text",
          "determination": "satisfied | partially_satisfied | not_satisfied | na",
          "gap": "gap description or null",
          "citation_confidence": "high | medium | low | not_found"
        }
      }
    }
  ],
  "summary": {
    "total_controls": 0,
    "satisfied": 0,
    "partially_satisfied": 0,
    "not_satisfied": 0,
    "na": 0,
    "citation_not_found": 0,
    "batches_complete": 0,
    "batches_total": 0
  }
}
```

---

## Phase 0 — Environment Setup and Resumability Check

### 0.1 — Input Validation

Verify all required inputs are accessible:

```
[ASSESS] Validating inputs...
[ASSESS] Framework document: [path] — [found | NOT FOUND]
[ASSESS] Template: [path] — [found | NOT FOUND]
[ASSESS] Product source: [source] — [accessible | NOT ACCESSIBLE]
[ASSESS] Program: [slug] — [runs/[slug]/latest.json found | not found]
```

If any required input is not found or accessible, stop and surface the issue to the lead program manager before proceeding. Do not attempt to infer missing inputs.

### 0.2 — Resumability Check

Check for an existing state file at `data/[program]/assessments/[RUN_ID]-state.json`.

If found and status is `in_progress`:

```
[ASSESS] Prior run found: [RUN_ID]
  Started: [date] | Last updated: [date]
  Progress: [n] of [n] controls complete ([n] batches of [n])
  Last validated batch: [n] ending at control [ID]

Resume from batch [n+1]? [yes / no / show completed controls]
```

If `RESUME: yes` or lead program manager confirms: load state file, skip completed controls, continue from the next pending batch.

If `RESUME: no` or no prior state: generate a new RUN_ID and initialize a fresh state file.

### 0.3 — Control Inventory Extraction

Parse the framework document to extract all controls. For each control extract:

- Control ID (SR 1.1, V-12345, CIS 1.1, etc.)
- Title
- Full requirement text
- Any sub-requirements or enhancements
- Severity or level classification if present (CAT I/II/III, SL level, etc.)

Write the complete inventory to the state file under `control_inventory`. Count and confirm:

```
[ASSESS] Control inventory extracted: [n] controls
  [Framework-specific breakdown — e.g. for IEC 62443:]
  SR requirements: [n] | Requirement Enhancements (REs): [n]
  [For DISA STIG:]
  CAT I: [n] | CAT II: [n] | CAT III: [n]
  [For CIS:]
  Level 1: [n] | Level 2: [n] | Scored: [n] | Not Scored: [n]

Batch plan: [n] batches of [BATCH_SIZE] controls
Estimated output: [n] control responses

Proceed? [yes / no]
```

Wait for lead program manager confirmation before continuing.

---

## Phase 1 — Product Documentation Indexing

Index the product documentation source before processing any controls. This index is used by all subsequent passes as the citation lookup. It runs once.

### 1.1 — Source Handling

**Directory of files (PDFs, docx, markdown):**

- Extract text from each file
- Preserve document structure: section numbers, headings, subsection hierarchy
- Note page numbers or section anchors for citation precision

**MCP server:**

- Query the server's resource list to understand available documentation
- Retrieve all relevant documentation resources
- Parse structure from returned content

**Single file:**

- Extract and parse as above

**URL:**

- Fetch and extract content
- Note retrieval timestamp for provenance

### 1.2 — Index Structure

Build the product index with:

```json
{
  "sections": [
    {
      "id": "4.2.1",
      "title": "Authentication Configuration",
      "content_summary": "brief summary of what this section covers",
      "full_text": "full section text",
      "source_file": "filename",
      "page_or_anchor": "reference"
    }
  ],
  "capabilities": [
    {
      "capability": "multi-factor authentication",
      "sections": ["4.2.1", "4.2.3"],
      "keywords": ["MFA", "two-factor", "authenticator"]
    }
  ],
  "keyword_map": {
    "authentication": ["4.2.1", "4.2.3", "6.1.2"],
    "authorization": ["4.3.1", "4.3.2"]
  }
}
```

Write the index to the state file under `product_index`.

Narrate:

```
[ASSESS] Indexing product documentation: [source]
[ASSESS] Files processed: [n] | Sections indexed: [n] | Capabilities mapped: [n]
[ASSESS] Index written to state file.
```

---

## Phase 2 — Template Structure Analysis

Parse the template to understand its field structure before filling anything.

### 2.1 — Template Type Detection

Examine the template structure and detect type:


| Template Type        | Detection Signals                                                         |
| -------------------- | ------------------------------------------------------------------------- |
| IEC 62443-4-2        | SR/RE numbering, SL columns, conformance fields                           |
| DISA STIG            | Finding ID (V-xxxxx), CAT classification, Check/Fix text fields           |
| CIS Benchmark        | Scored/Not Scored labels, Profile applicability, Audit/Remediation fields |
| Functional Test Plan | Test procedure fields, Expected result fields, Pass/Fail columns          |
| Custom               | None of the above — analyze field labels and structure                    |


### 2.2 — Field Mapping

Map the template's fields to the normalized internal schema:

```json
{
  "control_id_field": "column or field name in template",
  "requirement_text_field": "where requirement text lives",
  "narrative_field": "where the response narrative goes",
  "citation_field": "where citations go — null if combined with narrative",
  "determination_field": "where satisfied/not satisfied goes",
  "determination_values": {
    "satisfied": "exact template value — e.g. 'C' for Compliant",
    "partially_satisfied": "exact template value",
    "not_satisfied": "exact template value — e.g. 'NC'",
    "na": "exact template value"
  },
  "gap_field": "where gap description goes — null if combined with narrative",
  "severity_field": "CAT level, SL level, etc. — null if not present",
  "additional_fields": []
}
```

For Custom templates: present the field mapping to the lead program manager for confirmation before proceeding:

```
[ASSESS] Custom template detected. Proposed field mapping:
  Control ID field: [name]
  Narrative field: [name]
  Determination field: [name] — values: [list]
  Citation field: [name or "combined with narrative"]
  Gap field: [name or "combined with narrative"]

Confirm mapping? [yes / edit / show template structure]
```

Do not proceed past Phase 2 until the field mapping is confirmed.

---

## Phase 3 — Batched Control Processing

Process controls in batches of `BATCH_SIZE` (default 15). For each batch, process all controls in the batch, then validate the full batch before advancing.

### 3.1 — Control Processing

For each control in the batch:

**Step 1 — Locate relevant product documentation**

Search the product index for sections relevant to this control's requirement text. Use:

- Control keywords from requirement text
- Capability map entries
- Section title matching
- Direct section number references if the framework cites them

Collect all candidate sections with relevance reasoning.

**Step 2 — Write citation and apply citation assertion test**

Select the most specific and relevant section(s). Citation format:

```
[Product Name] [Version], [Document Title if multi-doc], Section [X.X.X]: "[Section Title]"
```

If multiple sections are cited:

```
[Product Name] [Version], Section 4.2.1: "Authentication Configuration";
Section 6.1.2: "Session Management"
```

If no relevant section can be located:

```
[CITATION NOT FOUND — [product name] documentation does not appear to address [requirement topic] directly. Manual review required.]
```

Never fabricate a section number or title. Never cite a section that was not found in the product index.

**Citation assertion test — apply before writing narrative:**

For each candidate citation, ask: does this section *explicitly assert* the capability, or does it merely *describe a topic area* that relates to the requirement?


| Citation quality              | Definition                                                                                                          | Effect on determination                                              |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Direct assertion**          | Section explicitly states the product does X, supports X, or implements X as required                               | Eligible for Satisfied if requirement is fully covered               |
| **Topical reference**         | Section discusses the subject area but does not explicitly assert the specific capability                           | Caps determination at Partially Satisfied — note as indirect         |
| **Adjacent capability**       | Section describes a related capability that could *compose toward* the requirement but does not address it directly | Caps determination at Partially Satisfied — flag as inferred         |
| **Architectural description** | Section describes how the product is designed but makes no compliance claim                                         | Caps determination at Partially Satisfied — note as descriptive only |


If the best available citation is Topical, Adjacent, or Architectural, the determination cannot be Satisfied regardless of how well the narrative is written. Mark the citation quality in the response:

```
Citation quality: [direct assertion | topical reference | adjacent capability | architectural description]
```

**Step 3 — Write narrative**

Write response narrative that:

- Directly addresses the specific requirement — not the general topic area
- References the cited section(s) explicitly by number in the text
- Describes how the product capability satisfies (or does not satisfy) the requirement
- Is specific enough that an auditor can verify the claim by reading the cited section
- Does not repeat the requirement text verbatim
- Is 2-5 sentences for standard controls, up to 8 for complex REs or CAT I findings

Narrative must not be generic. The test: could this exact narrative apply to a different product with minimal editing? If yes, it fails.

**Inference boundary rule — apply before finalizing narrative:**

Only assert what the product documentation directly states. Do not compose satisfaction from adjacent capabilities unless the documentation explicitly states they combine to fulfill the requirement.


| Inference type                                                            | Permitted | Required handling                                                                |
| ------------------------------------------------------------------------- | --------- | -------------------------------------------------------------------------------- |
| Direct claim — doc says the product does X                                | Yes       | Assert in narrative                                                              |
| Logical inference — product has A and B, therefore satisfies C            | No        | Flag as `[INFERRED — not explicitly stated]`, drop to Partially Satisfied        |
| Configuration dependency — capability exists but requires customer action | No        | Flag as `[REQUIRES CUSTOMER CONFIGURATION]`, drop to Partially Satisfied         |
| Version caveat — capability present in some versions                      | No        | Flag as `[VERSION DEPENDENT — verify]`, drop to Partially Satisfied              |
| Vendor interpretation — reading between lines of vague documentation      | No        | Flag as `[INTERPRETATION — manual review required]`, drop to Partially Satisfied |


Any flagged inference in the narrative automatically prevents a Satisfied determination for that control, regardless of citation quality.

**Step 4 — Assign satisfaction determination**

Apply the coverage completeness test first, then the determination table.

**Coverage completeness test:**
Decompose the requirement into its sub-elements — every distinct capability or condition it specifies. For each sub-element, confirm the citation directly asserts it. If any sub-element is unaddressed, the requirement is not fully covered and Satisfied is not available.

Example: SR 1.1 requires (a) unique user identification AND (b) authentication before access. A citation covering only authentication but not unique identification = partial coverage → Partially Satisfied maximum.

**Determination table:**


| Determination           | All criteria must be met                                                                                                                                                                                                                                                                         |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Satisfied**           | (1) Citation quality is Direct Assertion. (2) Every sub-element of the requirement is addressed by a direct assertion in the cited section(s). (3) No inference flags present in the narrative. (4) No customer configuration required to activate the capability. (5) No version caveats apply. |
| **Partially Satisfied** | Citation exists but one or more of the Satisfied criteria are not met: partial sub-element coverage, topical/adjacent citation quality, inference flags present, configuration dependency, or version caveat.                                                                                    |
| **Not Satisfied**       | No citation found, or documentation explicitly states the capability is not supported, or citation is present but quality is Architectural Description only with no capability assertion.                                                                                                        |
| **N/A**                 | Requirement explicitly does not apply to this product type or deployment context per the framework's applicability guidance. Requires written rationale — N/A is not a default for hard-to-assess controls.                                                                                      |


**Downgrade triggers — any of these alone forces the determination down:**


| Trigger                                            | Maximum allowed determination |
| -------------------------------------------------- | ----------------------------- |
| Citation quality is Topical Reference              | Partially Satisfied           |
| Citation quality is Adjacent Capability            | Partially Satisfied           |
| Citation quality is Architectural Description      | Not Satisfied                 |
| Any `[INFERRED]` flag in narrative                 | Partially Satisfied           |
| Any `[REQUIRES CUSTOMER CONFIGURATION]` flag       | Partially Satisfied           |
| Any `[VERSION DEPENDENT]` flag                     | Partially Satisfied           |
| Any `[INTERPRETATION]` flag                        | Partially Satisfied           |
| Sub-element coverage incomplete                    | Partially Satisfied           |
| Multiple citations required, at least one indirect | Partially Satisfied           |


**Step 5 — Note gaps**

For Partially Satisfied and Not Satisfied:

```
Gap: [specific description of what is missing or insufficient]
Remediation path: [what would need to be true for this to become Satisfied]
```

For Satisfied with caveats:

```
Note: [any configuration requirements, version dependencies, or conditions]
```

### 3.2 — Batch Narration

As each batch processes:

```
[ASSESS] Batch [n] of [n] — controls [ID] through [ID]
[ASSESS] Processing SR 1.1... citation found (Section 4.2.1) — Satisfied
[ASSESS] Processing SR 1.2... citation found (Section 4.2.3, 4.2.4) — Partially Satisfied
[ASSESS] Processing SR 1.3... CITATION NOT FOUND — Not Satisfied
[ASSESS] Batch [n] complete — validating...
```

### 3.3 — Batch Validation

After all controls in a batch are processed, validate every response against all seven criteria:

**Criterion 1 — Citation present and specific**

- PASS: citation contains a section number and section title from the product index
- FAIL: citation is missing, generic ("product documentation"), or contains `[CITATION NOT FOUND]` without a Not Satisfied determination

**Criterion 2 — Citation assertion test applied**

- PASS: citation quality is labeled (direct assertion / topical reference / adjacent capability / architectural description)
- FAIL: citation quality label absent, or determination is Satisfied when citation quality is not Direct Assertion

**Criterion 3 — Inference boundary respected**

- PASS: narrative contains no unlabeled inferences; all flags (`[INFERRED]`, `[REQUIRES CUSTOMER CONFIGURATION]`, `[VERSION DEPENDENT]`, `[INTERPRETATION]`) are present where applicable
- FAIL: narrative asserts a capability the citation does not directly state, without a flag; or determination is Satisfied when any inference flag is present

**Criterion 4 — Coverage completeness test applied**

- PASS: all sub-elements of the requirement are individually addressed in the narrative and citations; or Partially Satisfied is assigned where sub-elements are unaddressed
- FAIL: determination is Satisfied but one or more requirement sub-elements are not addressed by a direct assertion

**Criterion 5 — Narrative directly addresses the requirement**

- PASS: narrative references the specific control requirement, not just the general topic
- FAIL: narrative could apply to any product or any control in the same domain

**Criterion 6 — Satisfaction determination is explicit and consistent with downgrade triggers**

- PASS: one of Satisfied / Partially Satisfied / Not Satisfied / N/A is present and no downgrade trigger has been violated
- FAIL: determination is absent, hedged, or inconsistent with citation quality, inference flags, or coverage completeness

**Criterion 7 — Gap noted where applicable**

- PASS: gap and remediation path present for Partially Satisfied and Not Satisfied; note present for Satisfied with caveats
- FAIL: Partially Satisfied or Not Satisfied with no gap description

**Validation output:**

```
[ASSESS] Batch [n] validation:
  SR 1.1: PASS (all 7 criteria)
  SR 1.2: FAIL — Criterion 2 (narrative is generic), Criterion 4 (no gap noted)
  SR 1.3: PASS
  ...
  Batch result: [n] passed, [n] failed

Correcting [n] failed responses...
```

Correct all failed responses before advancing. Re-validate corrected responses. If a response fails validation twice, flag it for lead program manager review:

```
[ASSESS] SR 1.2 failed validation twice.
  Issue: [specific criterion failures]
  Current response: [show response]
  Options: [manual edit | mark for post-processing | accept with flag]
```

Write validated batch results to state file. Update `control_inventory` status to `validated`. Update `summary` counts.

```
[ASSESS] Batch [n] validated and written to state file.
[ASSESS] Progress: [n] of [n] controls complete.
```

---

## Phase 4 — Cross-Control Consistency Pass

After all batches are validated, run a consistency check across the full control set before assembling output.

### 4.1 — Contradiction Detection

Check for:

**Contradictory determinations on related controls**
Example: SR 1.1 (user identification) is Satisfied but SR 1.2 (authenticator management) is Satisfied with a narrative that implies authentication is not fully implemented.

**Citation drift**
The same product documentation section is cited differently across controls — different section numbers for the same content, or conflicting descriptions of what the section says.

**Satisfaction-gap contradiction**
A control is marked Satisfied but the narrative or notes describe a gap or limitation that would warrant Partially Satisfied.

**N/A rationale consistency**
Controls marked N/A should have consistent applicability rationale. Flag if the same requirement type is N/A in one place and Satisfied in another without clear rationale.

### 4.2 — Consistency Report

```
[ASSESS] Consistency pass complete.
  Contradictions found: [n]
  Citation drift instances: [n]
  Satisfaction-gap contradictions: [n]

  [list each issue with control IDs and description]
```

For each issue, propose a resolution and confirm with the lead program manager before applying:

```
Issue: SR 2.1 (Satisfied) and SR 2.2 (Partially Satisfied) cite the same
section (4.3.1) but describe it inconsistently.
  SR 2.1 narrative: "Section 4.3.1 fully describes role-based access control..."
  SR 2.2 narrative: "Section 4.3.1 describes basic access control but does not..."

Proposed resolution: Review Section 4.3.1 and align both narratives.
Apply? [yes — align to SR 2.1 | yes — align to SR 2.2 | manual edit | skip]
```

Write resolved responses back to the state file before output assembly.

---

## Phase 5 — Output Assembly

Produce three outputs in parallel from the validated, consistency-checked state file.

### 5.1 — Filled Template (docx)

Using the field map from Phase 2, populate the original template with validated responses.

For each control:

- Write narrative to the narrative field
- Write citation to the citation field (or prepend to narrative if combined)
- Write determination using the template's exact value vocabulary (e.g. "C" not "Satisfied")
- Write gap description to gap field if present
- Write any additional fields defined in the field map

For `[CITATION NOT FOUND]` responses:

- Write the citation not found notice to the citation field
- Set determination to Not Satisfied
- Write gap description

Output path: `data/[program]/assessments/[RUN_ID]/[PRODUCT_NAME]-[FRAMEWORK]-filled.[ext]`

### 5.2 — Markdown Artifact

Produce a structured markdown document alongside the filled template. This is the machine-readable version — searchable, diffable, usable as context for future runs.

```markdown
# [Product Name] [Version] — [Framework] Assessment
**Run ID:** [RUN_ID]
**Generated:** [date]
**Program:** [slug]
**Product source:** [source]
**Template:** [template path]

## Summary
Total controls: [n]
Satisfied: [n] ([pct]%)
Partially Satisfied: [n] ([pct]%)
Not Satisfied: [n] ([pct]%)
N/A: [n] ([pct]%)
Citation not found: [n]

---

## Control Responses

### [SR 1.1 | V-12345 | CIS 1.1] — [Title]
**Requirement:** [full requirement text]
**Determination:** Satisfied / Partially Satisfied / Not Satisfied / N/A
**Citation:** [full citation string]
**Narrative:** [full narrative text]
**Gap:** [gap description or —]
**Note:** [note or —]

---
```

Output path: `data/[program]/assessments/[RUN_ID]/[PRODUCT_NAME]-[FRAMEWORK]-assessment.md`

### 5.3 — Gap Report

Filter the full assessment to controls where determination is Partially Satisfied or Not Satisfied. Produce a focused remediation-oriented document.

```markdown
# [Product Name] — [Framework] Gap Report
**Run ID:** [RUN_ID] | **Generated:** [date]

## Summary
Partially Satisfied: [n] controls
Not Satisfied: [n] controls
Citation not found: [n] controls (review required)

---

## Partially Satisfied

### [SR X.X] — [Title]
**Gap:** [gap description]
**Remediation path:** [what would make this Satisfied]
**Citation:** [what was found]

---

## Not Satisfied

### [SR X.X] — [Title]
**Gap:** [gap description]
**Remediation path:** [what would need to change]
**Citation:** [CITATION NOT FOUND or citation with insufficient coverage]

---

## Citation Not Found — Manual Review Required

### [SR X.X] — [Title]
**Requirement:** [requirement text]
**Action required:** Locate relevant product documentation section and complete manually.
```

Output path: `data/[program]/assessments/[RUN_ID]/[PRODUCT_NAME]-[FRAMEWORK]-gaps.md`

---

## Phase 6 — Final Validation and Provenance

### 6.1 — Quality Gate

Run `engine/quality-gate-spec.md` over the markdown artifact and gap report before declaring the run complete.

Additionally verify:

- Every control in the inventory has a validated response
- No `pending` or `processing` status entries remain in the state file
- Satisfaction determination counts in the state file match the output documents
- All `[CITATION NOT FOUND]` responses are marked Not Satisfied in the filled template

### 6.2 — Final Summary

```
[ASSESS] Assessment complete — [RUN_ID]

RESULTS
  Total controls assessed: [n]
  Satisfied: [n] ([pct]%)
  Partially Satisfied: [n] ([pct]%)
  Not Satisfied: [n] ([pct]%)
  N/A: [n] ([pct]%)
  Citation not found: [n] — require manual completion

OUTPUTS
  Filled template: data/[program]/assessments/[RUN_ID]/[filename]
  Markdown artifact: data/[program]/assessments/[RUN_ID]/[filename]
  Gap report: data/[program]/assessments/[RUN_ID]/[filename]
  State file: data/[program]/assessments/[RUN_ID]-state.json

REQUIRES ATTENTION
  [list any double-failed controls, unresolved consistency issues, or citation not found items]
```

### 6.3 — Provenance

```bash
python scripts/provenance_log.py write \
  --spec "functions/control-assessment-spec.md" \
  --output "data/[program]/assessments/[RUN_ID]/[PRODUCT_NAME]-[FRAMEWORK]-filled.[ext]" \
  --output-type control_assessment \
  --program "[program]" \
  --purpose "[FRAMEWORK] assessment: [PRODUCT_NAME] [VERSION] — [n] controls, [pct]% satisfied" \
  --reusability artifact \
  --quality-gate pass
```

Log separately for gap report and markdown artifact with `output_type: gap_report` and `output_type: assessment_artifact`.

Update state file status to `complete`.

---

## Trigger

```
PROGRAM: [slug]
FRAMEWORK: [iec62443-4-2 | disa-stig | cis-benchmark | functional-test-plan | custom]
TEMPLATE_PATH: [path]
FRAMEWORK_PATH: [path]
PRODUCT_SOURCE: [path | mcp-server-name | url]
PRODUCT_NAME: [name]
PRODUCT_VERSION: [version]

BEGIN CONTROL ASSESSMENT
```

---

## Framework-Specific Guidance

### IEC 62443-4-2

Control hierarchy: Security Requirements (SRs) contain Requirement Enhancements (REs). Process SRs first, then their REs. An SR can be Satisfied at a base level while its REs are Partially Satisfied — these are independent determinations.

Satisfaction levels map to Security Levels (SL): document which SL the determination supports where the framework requires it.

### DISA STIG

CAT I findings (high severity) require the most specific citations and narrative. If a CAT I finding cannot be Satisfied, the gap description must include a specific remediation action, not just a description of the gap.

Check text and Fix text from the STIG are inputs — the narrative should address the Check procedure and explain whether the Fix has been implemented.

### CIS Benchmark

Scored recommendations require explicit Pass/Fail. Not Scored recommendations use Satisfied/Not Satisfied for consistency but note they are advisory.

Profile applicability (Level 1 vs Level 2) should be noted in each response — a Level 2 control marked N/A for a Level 1 deployment requires the applicability rationale.

### Functional Test Plan

Output format changes for test plans: instead of narrative, write test procedures (step-by-step) and expected results. Satisfaction determination becomes Pass Criteria. Citation becomes the product documentation reference that defines the expected behavior.

```
Test Procedure:
  1. [step]
  2. [step]
Expected Result: [what should happen]
Pass Criteria: [product behavior that constitutes a pass]
Citation: [section that defines expected behavior]
```

### Custom Template

After Phase 2 field mapping confirmation, apply the mapped field vocabulary throughout. If the template uses non-standard determination values (e.g. "C/PC/NC/NA" or "Yes/No/Partial"), use those exact values in the output — never substitute the internal vocabulary.

---

## Resumability Reference

If a session ends mid-run:

```
PROGRAM: [slug]
FRAMEWORK: [framework]
RUN_ID: [prior run id — found in state file name]
RESUME: yes

BEGIN CONTROL ASSESSMENT
```

The spec loads the state file, skips all controls with status `validated`, and continues from the first `pending` control in the next unvalidated batch.

---

## Suggested Repo Path

`/functions/control-assessment-spec.md`

## Companion Specs

- Governed by: `/config/constitution.md`
- Invokes: `engine/quality-gate-spec.md`
- Reads: framework doc, template, product documentation source
- Writes: `data/[program]/assessments/[RUN_ID]/`
- State file: `data/[program]/assessments/[RUN_ID]-state.json`
- Logged by: `scripts/provenance_log.py` — output_type: control_assessment, gap_report, assessment_artifact

