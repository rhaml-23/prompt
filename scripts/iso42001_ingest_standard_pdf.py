#!/usr/bin/env python3
# ISO 42001 PDF — normative reference indexer
# Purpose: SHA-256, page-bounded text extract, clause/Annex A index JSON, markdown comparison report.
# Style: PEP 8
# Deviations: None
#
# Dependencies: pypdf (see runtime/requirements.txt). Optional: pdftotext if added to PATH later.
# Usage:
#   python3 scripts/iso42001_ingest_standard_pdf.py
#   python3 scripts/iso42001_ingest_standard_pdf.py --pdf data/ISO42001/Planning/ISO_IEC_42001_2023\\(en\\)-1.pdf
#
# Environment: none required.

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = REPO_ROOT / "data/ISO42001/Planning/ISO_IEC_42001_2023(en)-1.pdf"
OUT_DIR = REPO_ROOT / "data/ISO42001/references"
INDEX_JSON = OUT_DIR / "ISO-IEC-42001-2023-index.json"
REPORT_MD = OUT_DIR / "ISO-IEC-42001-2023-ingestion-report.md"
LAYER1 = REPO_ROOT / "data/ISO42001/gemara/iso42001-layer1.yaml"
HYPERPROOF_CSV = (
    REPO_ROOT
    / "data/ISO42001/Resources/Automation Tools/git pipeline/Artifacts/ISO42001-ControlExport.csv"
)

# Main body clauses (normative Clauses 4–10) — line-start headings in ISO layout.
RE_MAIN_HEADING = re.compile(
    r"^((?:[4-9]|10)\.\d+(?:\.\d+)?)\s+(\S.{2,180})$",
    re.MULTILINE,
)

# Annex A control IDs (Table A.1) — allow PDF line-break artifacts "A .7.2".
RE_ANNEX_ID_LOOSE = re.compile(
    r"A\s*\.\s*(\d+(?:\s*\.\s*\d+)+)",
    re.IGNORECASE,
)


def _require_pypdf():
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except ImportError as e:
        sys.stderr.write(
            "Missing dependency: pypdf.\n"
            "Install: python3 -m venv .venv && .venv/bin/pip install -r runtime/requirements.txt\n"
        )
        raise SystemExit(1) from e
    return PdfReader


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_annex_fragment(s: str) -> str | None:
    """Turn 'A .7. 2' or 'A.7.2' into 'A.7.2'."""
    m = RE_ANNEX_ID_LOOSE.search(s)
    if not m:
        return None
    nums = re.sub(r"\s+", "", m.group(1))
    if not re.fullmatch(r"\d+(?:\.\d+)*", nums):
        return None
    return "A." + nums


def extract_pages(reader) -> list[str]:
    texts: list[str] = []
    for i, page in enumerate(reader.pages):
        t = page.extract_text() or ""
        texts.append(t)
    return texts


def clean_title_excerpt(title: str) -> str:
    """Remove TOC dot leaders and printed page columns from PDF extract."""
    t = title.strip()
    t = re.sub(r"\.{2,}.*$", "", t)  # dot leaders + rest of line
    t = re.sub(r"\s+\d{1,3}\s*$", "", t)  # trailing printed page number
    t = re.sub(r"\s+", " ", t)
    return t[:200]


def find_main_clause_headings(full_text: str) -> OrderedDict[str, dict]:
    """First occurrence wins; page derived from form-feed split."""
    found: OrderedDict[str, dict] = OrderedDict()
    for m in RE_MAIN_HEADING.finditer(full_text):
        cid = m.group(1)
        title = clean_title_excerpt(m.group(2))
        if cid not in found:
            found[cid] = {"title_excerpt": title, "char_offset": m.start()}
    return found


def page_for_offset(page_offsets: list[int], char_pos: int) -> int:
    """0-based page index."""
    for i in range(len(page_offsets) - 1, -1, -1):
        if char_pos >= page_offsets[i]:
            return i
    return 0


# Table A.1 uses control rows like A.2.2; PDF also prints subsection headings A.6.1 / A.6.2 (not Table rows).
ANNEX_HEADING_ONLY = frozenset({"A.6.1", "A.6.2"})


def annex_control_ids_from_text(text: str) -> OrderedDict[str, None]:
    """Collect Annex A control IDs in document order."""
    ids: OrderedDict[str, None] = OrderedDict()
    for line in text.splitlines():
        # Fast path: lines containing A.x
        if "A." not in line and "A ." not in line:
            continue
        # Multiple IDs per line possible
        for m in RE_ANNEX_ID_LOOSE.finditer(line):
            span = m.group(0)
            cid = normalize_annex_fragment(span)
            if not cid:
                continue
            if cid in ANNEX_HEADING_ONLY:
                continue
            # Filter: Annex A controls are A.2–A.10 with at least two numeric segments
            parts = cid.split(".")
            if len(parts) < 3:
                continue
            try:
                major = int(parts[1])
            except ValueError:
                continue
            if major < 2 or major > 10:
                continue
            if cid not in ids:
                ids[cid] = None
    return ids


def load_layer1_annex_ids(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r'^  - id: "(A\.\d+(?:\.\d+)*)"', text, re.MULTILINE))


def load_hyperproof_annex_ids(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"ISO42001-(A\.\d+(?:\.\d+)*)", text))


def build_index(pdf_path: Path) -> dict:
    PdfReader = _require_pypdf()
    reader = PdfReader(str(pdf_path))
    pages = extract_pages(reader)
    page_offsets: list[int] = []
    pos = 0
    chunks: list[str] = []
    for i, t in enumerate(pages):
        page_offsets.append(pos)
        chunks.append(f"\n---PAGE {i + 1}---\n")
        chunks.append(t)
        pos += len(chunks[-2]) + len(chunks[-1])
    full_text = "".join(chunks)

    sha = sha256_file(pdf_path)
    main = find_main_clause_headings(full_text)
    annex_ids = annex_control_ids_from_text(full_text)

    main_entries: list[dict] = []
    sorted_main = sorted(main.items(), key=lambda kv: kv[1]["char_offset"])
    for idx, (cid, meta) in enumerate(sorted_main):
        off = meta["char_offset"]
        p0 = page_for_offset(page_offsets, off)
        p1 = (
            page_for_offset(page_offsets, sorted_main[idx + 1][1]["char_offset"] - 1)
            if idx + 1 < len(sorted_main)
            else len(pages) - 1
        )
        main_entries.append(
            {
                "id": cid,
                "title_excerpt": meta["title_excerpt"],
                "page_start": p0 + 1,
                "page_end": p1 + 1,
                "pdf_sha256": sha,
            }
        )

    annex_entries: list[dict] = []
    for cid in annex_ids.keys():
        # Find first occurrence char offset in full_text
        needle = cid.replace(".", r"\.")
        needle_loose = r"A\s*\.\s*" + r"\s*\.\s*".join(
            re.escape(x) for x in cid.split(".")[1:]
        )
        m = re.search(needle_loose, full_text)
        if not m:
            m = re.search(re.escape(cid), full_text)
        if not m:
            continue
        off = m.start()
        p0 = page_for_offset(page_offsets, off)
        annex_entries.append(
            {
                "id": cid,
                "title_excerpt": "[EXCERPT — internal use] see PDF Table A.1",
                "page_start": p0 + 1,
                "page_end": p0 + 1,
                "pdf_sha256": sha,
            }
        )

    layer1 = load_layer1_annex_ids(LAYER1)
    pdf_annex_set = set(annex_ids.keys())
    in_pdf_not_layer1 = sorted(pdf_annex_set - layer1)
    in_layer1_not_pdf = sorted(layer1 - pdf_annex_set)
    hyperproof = load_hyperproof_annex_ids(HYPERPROOF_CSV)
    in_hyperproof_not_pdf = sorted(hyperproof - pdf_annex_set)
    in_pdf_not_hyperproof = sorted(pdf_annex_set - hyperproof)

    return {
        "standard": "ISO/IEC 42001:2023",
        "pdf_path": str(pdf_path.relative_to(REPO_ROOT)),
        "pdf_filename": pdf_path.name,
        "pdf_sha256": sha,
        "page_count": len(pages),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "main_clause_index": main_entries,
        "annex_a_control_index": annex_entries,
        "comparison": {
            "annex_in_pdf_not_layer1_yaml": in_pdf_not_layer1,
            "annex_in_layer1_yaml_not_pdf": in_layer1_not_pdf,
            "annex_in_hyperproof_csv_not_pdf": in_hyperproof_not_pdf,
            "annex_in_pdf_not_hyperproof_csv": in_pdf_not_hyperproof,
        },
    }


def write_report(index: dict, path: Path) -> None:
    c = index["comparison"]
    lines = [
        "# ISO/IEC 42001:2023 — PDF ingestion report",
        "",
        "> **Excerpt policy:** This report and the JSON index contain **no** full reproduction of the normative standard. "
        "Titles are short excerpts or pointers only. The controlled copy is the PDF in `data/ISO42001/Planning/`.",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| PDF | `{index['pdf_path']}` |",
        f"| SHA-256 | `{index['pdf_sha256']}` |",
        f"| Pages | {index['page_count']} |",
        f"| Ingested (UTC) | {index['ingested_at']} |",
        "",
        "## Annex A — set comparison",
        "",
        f"- **Annex A IDs found in PDF (heuristic):** {len(index['annex_a_control_index'])}",
        f"- **Annex A IDs in Gemara Layer 1:** derived from `{LAYER1.relative_to(REPO_ROOT)}`",
        f"- **Annex A IDs in Hyperproof export:** derived from `{HYPERPROOF_CSV.relative_to(REPO_ROOT)}`",
        "",
        "### In PDF but not in Layer 1 YAML",
        "",
        ("- " + "\n- ".join(c["annex_in_pdf_not_layer1_yaml"]) if c["annex_in_pdf_not_layer1_yaml"] else "- *(none)*"),
        "",
        "### In Layer 1 YAML but not detected in PDF",
        "",
        ("- " + "\n- ".join(c["annex_in_layer1_yaml_not_pdf"]) if c["annex_in_layer1_yaml_not_pdf"] else "- *(none)*"),
        "",
        "### In Hyperproof CSV but not detected in PDF",
        "",
        ("- " + "\n- ".join(c["annex_in_hyperproof_csv_not_pdf"]) if c["annex_in_hyperproof_csv_not_pdf"] else "- *(none)*"),
        "",
        "### In PDF but not in Hyperproof CSV",
        "",
        ("- " + "\n- ".join(c["annex_in_pdf_not_hyperproof_csv"]) if c["annex_in_pdf_not_hyperproof_csv"] else "- *(none)*"),
        "",
        "## Stakeholder label mapping (generative-AI audit themes)",
        "",
        "Per **Table A.1** in the licensed PDF, Annex A **does not** define controls **A.3.4**, **A.4.1**, or a separate "
        "**A.5.3** distinct from the documented **A.5.3 Documentation of AI system impact assessments** (title in PDF). "
        "If stakeholders used \"A.3.4 / A.4.1\" as shorthand, map them explicitly:",
        "",
        "| Stakeholder label | Map to ISO/IEC 42001:2023 (Annex A / body) | PDF note |",
        "|---|---|---|",
        "| A.3.4 (bias/fairness) | **Not an Annex A control ID** — treat as theme; closest Table A.1 topics: **A.5.x** impacts, **A.6.x** / **A.7.x** data and life cycle (bias in data per Annex B.7 guidance) | Cross-check Annex B |",
        "| A.4.1 (resilience/adversarial) | **Not an Annex A control ID** — treat as theme; map testing and robustness evidence to **A.6.2.x** (operation, monitoring, technical documentation) and user/system information **A.8.2** | Annex A Table A.1 |",
        "| A.5.3 (transparency) | **A.5.3** in ISO/IEC 42001:2023 is *Documentation of AI system impact assessments* — not a generic \"transparency\" label; for transparency/disclosure use **A.8.2**, **A.8.5**, **A.10.4** | See PDF Table A.1 (~pp. 24–27) |",
        "",
        "## Refresh rule",
        "",
        "When the PDF edition changes: re-run this script, commit updated `references/` outputs, update SHA citations in "
        "`iso42001-layer1.yaml` and `data/ISO42001/README.md`, and append a `DECISION` line to `memory/iso42001-decisions.log`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Index ISO/IEC 42001:2023 PDF for iso42001 program.")
    ap.add_argument(
        "--pdf",
        type=Path,
        default=DEFAULT_PDF,
        help="Path to licensed PDF",
    )
    args = ap.parse_args()
    pdf_path: Path = args.pdf
    if not pdf_path.is_file():
        sys.stderr.write(f"PDF not found: {pdf_path}\n")
        raise SystemExit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index = build_index(pdf_path.resolve())
    INDEX_JSON.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(index, REPORT_MD)
    print(f"Wrote {INDEX_JSON.relative_to(REPO_ROOT)}")
    print(f"Wrote {REPORT_MD.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
