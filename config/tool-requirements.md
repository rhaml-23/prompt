---
resource_type: requirements
version: "1.1"
scope: all scripts and tools
governed_by: config/constitution.md
audience: LLMs generating tools
---

# Tool Development Requirements
**Version:** 1.1
**Purpose:** Behavioral contract for all scripts and tools in this repo. Read before building any tool over ~200 lines.
**Scope:** Python, Bash/Shell, Node.js — any language.

---

## When to Build a Tool

Build and commit a script when any of these are true:
- Logic exceeds ~200 lines
- The operation runs more than once
- It reads or writes files, JSON, or external state
- It requires argument parsing, error handling, or logging
- Output must be consistent and reproducible across sessions

Under ~200 lines used once: inline code is sufficient. Do not create files for throwaway logic.

---

## Before Writing Any Code

Present a plan and wait for confirmation before implementing any tool over ~200 lines:

```
TOOL PLAN
Name:            [filename and repo path]
Purpose:         [one sentence]
Language:        [language]
Style:           [declared standard — language best practices unless deviation noted]
Inputs:          [args, files, stdin]
Outputs:         [files, stdout, exit codes]
Dependencies:    [external packages — justify each]
Security:        [credentials, user data, or sensitive inputs handled?]
Estimated lines: [approximate]
Integration:     [which specs or scripts invoke this]
```

---

## Standards Declaration

Every tool declares its style standard in the file header. Apply the recognized best-practice standard for the language (PEP 8 for Python, Google Shell Style Guide for Bash, etc.). List any intentional deviations with justification. An unjustified deviation is a defect.

```
# [Tool Name]
# Purpose: [one sentence]
# Style: [standard name]
# Deviations: [list with justification | None]
```

Apply the standard as a competent practitioner would — type hints, docstrings, proper error handling, idiomatic patterns. Do not quote the standard back; embody it.

---

## Security — Non-Negotiable

**No credentials in code.** API keys, tokens, passwords, and connection strings are always read from environment variables. Never hardcoded. Never in committed `.env` files.

```python
# Correct
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set")
```

Document required environment variables in the tool header.

**No sensitive data in logs.** Log paths, operation names, counts, and status. Never credentials, tokens, or raw request/response bodies that may contain sensitive content. Use log levels correctly — DEBUG for development detail, INFO for normal operation, WARNING for recoverable issues, ERROR for failures.

---

## Error Handling

- All file operations and external calls handle failure explicitly
- Errors produce a meaningful message to stderr and exit non-zero
- Never silently swallow exceptions

---

## Structure

- **Header:** Every tool begins with name, purpose, usage examples, dependencies, repo path
- **Functions:** One responsibility per function. If it exceeds ~40 lines, split it
- **Naming:** Descriptive, not abbreviated. `load_run` not `lr`. Constants in `UPPER_SNAKE_CASE`
- **Dependencies:** Standard library preferred. Every third-party dependency justified in the plan and pinned in `requirements.txt` or `package.json`
- **CLI:** `--help` supported, long-form flags, required arguments validated with clear failure messages, exit 0 on success / non-zero on failure

---

## Repo Integration

When committing a new tool:

1. Place in `scripts/` unless a subdirectory is justified
2. Update README — Script Reference section with usage examples
3. Update `provenance_log.py OUTPUT_TYPES` if the tool produces a new deliverable type
4. Update calling specs — add to companion specs section of any spec that invokes this tool

---

## Self-Check Before Delivery

```
TOOL SELF-CHECK
□ Plan presented and confirmed before implementation
□ Standards declaration in header — deviations listed or "None"
□ No hardcoded credentials — environment variables used
□ No sensitive data in logs
□ Error handling on all file and external operations
□ Module/file docstring and public function docstrings present
□ CLI uses flags with --help — exit codes meaningful
□ README update identified
□ Calling specs updated if applicable
□ Dependencies pinned if new packages added
```

---

## Suggested Repo Path
`/config/tool-requirements.md`
