# Agentic Compliance System — Governance Overview
**Document type:** Human-AI Collaboration Governance Statement
**Intended audience:** Auditors, compliance reviewers, program oversight stakeholders
**Prepared by:** Alex Langston, Lead program manager Compliance Program Manager
**Version:** 1.0

---

## What This Document Is

This document describes how an LLM-assisted agentic system is used in compliance program management. It is not a claim of accuracy, automation rate, or AI performance. It describes the system's intended scope, where human judgment is required, where handoffs between human and agent occur, and where the system can fail — and how those failures are detected and contained.

The goal is transparency about how the system works, not promotion of what it can do.

---

## What the System Is

The system is a set of structured instructions — called specifications, or "specs" — written in plain-language markdown files. These specs are executed by a large language model (LLM), which reads them and follows their instructions to perform defined tasks: extracting information from program documents, generating compliance artifacts, drafting communications, and monitoring external sources for relevant risk signals.

The LLM is not an autonomous agent in the sense of operating independently. It is more accurately described as a configured executor — it follows the instructions in the specs, operates within boundaries defined by a governing document (the "constitution"), and surfaces outputs for human review before any consequential action is taken.

The system does not make decisions. It organizes information, drafts materials, and identifies gaps — all subject to human review and approval before use.

---

## The Five Operational Concepts

### Boundary Sensing

**What it means:** Knowing where the system's capability ends and human judgment begins — and updating that boundary as the underlying model changes.

**How it is implemented here:** The system's governing document (the constitution) defines explicit authority boundaries. The agent is authorized to act autonomously only when an action is reversible, internal, and within a defined spec's scope. All other actions — communications sent to external parties, decisions that cannot be undone, actions affecting another person's standing — require explicit human approval before execution.

These are called "one-way door" decisions. The agent is constitutionally prohibited from executing them without the program manager's sign-off. No exceptions are built into the system.

The boundary is also version-controlled. When the underlying LLM model is updated or replaced, the specs and constitution are reviewed to confirm the boundary assumptions still hold. This is not a one-time assessment — it is an ongoing maintenance obligation.

---

### Seam Design

**What it means:** Structuring the work so that handoffs between the agent and the human are clean, explicit, and auditable — not ambiguous transitions where it's unclear who is responsible for what.

**How it is implemented here:** Every spec defines what it receives as input, what it produces as output, and what triggers human review. The outputs are staged, not sent. Draft communications are written to a `drafts/` directory and flagged for review. The agent narrates what it is doing as it works, so the program manager can see each step before the next one begins.

The seams are:

| Agent does | Human does |
|---|---|
| Extracts scope, people, and commitments from raw materials | Reviews and corrects the extracted skeleton |
| Generates control coverage matrix from framework and available evidence | Reviews gap classifications and fills ownership gaps |
| Produces risk register and POA&M starter from coverage gaps | Accepts, modifies, or rejects risk ratings and remediation categories |
| Drafts stakeholder communications | Reviews, edits, and sends — agent never sends directly |
| Scans external sources and generates risk deltas | Decides which findings require action and at what priority |
| Proposes a weekly session agenda | Approves, modifies, or redirects the agenda before work begins |

Nothing crosses the seam from agent to external without the program manager's explicit decision.

---

### Failure Model Maintenance

**What it means:** Understanding how the system fails — not catastrophically, but subtly — and building detection mechanisms that surface failure before it causes harm.

**How it is implemented here:** The system has three categories of failure, each with a detection mechanism.

**Structural regression:** A future LLM or human editor removes a required section from a governing document, silently degrading the system's behavior. Detected by `integrity_check.py`, a script that maintains a manifest of required headings in protected files and flags any that are missing. Runs before any edit to a protected file. If a heading is missing, the agent is instructed to restore it and notify the program manager before proceeding.

**Output quality failure:** The agent produces an output that violates formatting standards, omits required sections, or fails constitutional alignment. Detected by the quality gate spec, which validates every output before delivery. Outputs that fail are regenerated with a correction brief. If they fail a second time, the agent escalates to the program manager rather than delivering a substandard output.

Gate 6 of the quality gate also scans every output for documented AI writing patterns (vocabulary clusters, vague attribution, promotional language, knowledge-gap speculation) that undermine evidentiary neutrality in compliance artifacts. Any Tier 1 pattern triggers regeneration before delivery.

**Relevance drift:** The agent makes a connection between an external finding and a program that is plausible but not defensible. Detected by a structured relevance scoring system that requires framework or technology stack match before a finding is classified as relevant. Confidence levels and source quality are labeled on every finding so the program manager can assess the basis for any flagged item.

**Hallucination:** The agent fabricates a citation, a control requirement, or a person's name. Mitigated by a constitutional mandate that all inferences are labeled `[INFERRED]`, all missing data is labeled `[DATA NEEDED: source]`, and citations that cannot be confidently named are classified as "training knowledge" rather than attributed to a specific source. The program manager is expected to verify any `[INFERRED]` item before acting on it.

The system does not claim to eliminate these failure modes. It claims to surface them visibly so a human can catch and correct them.

---

### Capability Forecasting

**What it means:** Anticipating how the system's useful boundary will shift as the underlying model improves — and designing the system to expand gracefully rather than break.

**How it is implemented here:** The specs are written in portable, plain-language markdown. They do not depend on any specific LLM vendor, model version, or API. The same spec runs on Claude, GPT, Gemini, or a locally-hosted open model. This means the system's capability grows as models improve, without requiring the system to be redesigned.

The constitution's Article VIII defines an amendment process for when the system's boundaries need to be updated — either because the model has become more capable and the lead program manager wants to extend autonomous authority, or because a failure has been identified and a new constraint is needed.

The system is designed to be extended, not replaced. New work patterns are added as new specs in the `functions/` directory. New behavioral instructions are added as mandates in the constitution. The architecture anticipates growth.

---

### Leverage Calibration

**What it means:** Knowing where applying the agent produces disproportionate value — and where human judgment is so essential that agent involvement adds risk rather than capacity.

**How it is implemented here:** The system is applied to high-volume, structured, repeatable compliance work: extracting requirements from documents, mapping controls to evidence, generating first-draft artifacts, monitoring sources, and maintaining program state across time. These are tasks where the agent's speed and consistency create genuine force multiplication.

The system is explicitly not applied to: final risk acceptance decisions, audit findings responses that carry legal weight, communications that establish regulatory commitments, vendor contract decisions, and any action where being wrong has consequences that cannot be reversed.

The practical result: when a program scope change arrives unexpectedly, the agent can produce a complete program skeleton, control coverage matrix, risk register, evidence calendar, and draft communications within hours. The program manager then spends their time reviewing and deciding — not building from scratch. The leverage is in the setup work. The judgment stays with the human.

---

## What the System Does Not Do

For clarity, the following are outside the system's scope and not performed by the agent under any configuration:

- Send communications to external parties without human approval
- Accept or reject audit findings on behalf of the organization
- Make risk acceptance decisions
- Modify contracts or vendor agreements
- Access live production systems or data
- Retain information between sessions without explicit memory files that the program manager controls and can inspect
- Operate on a schedule without human initiation

---

## Human Oversight Summary

Every consequential output of this system passes through at least one human checkpoint before it affects anything outside the program management workflow. The agent is a drafting and organizing capability, not a decision-making one.

The program manager remains accountable for all program outcomes. The system is a tool that reduces the time required to do structured work — it does not reduce the accountability for the work's quality or accuracy.

---

*This document reflects the design intent of the system as of the version date above. Material changes to the system's authority boundaries, failure detection mechanisms, or scope will be reflected in an updated version of this document.*
