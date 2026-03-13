#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compile_docs.py — Compile all repository READMEs into a consolidated PDF user guide.

Collects READMEs in a defined order, combines them into a single Markdown file
(docs/user_guide_combined.md), then converts it to PDF via pandoc + pdflatex.

Usage (from any directory):
    python scripts/documentation/compile_docs.py

Requirements:
    - pandoc  (https://pandoc.org/)
    - pdflatex (part of a TeX distribution, e.g. TeX Live or MiKTeX)
"""

import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Locate project root regardless of working directory
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = PROJECT_ROOT / "docs"
COMBINED_MD = DOCS_DIR / "user_guide_combined.md"
OUTPUT_PDF = DOCS_DIR / "user_guide_repository_readmes.pdf"

# ---------------------------------------------------------------------------
# READMEs to include, in order
# Each entry: (relative_path_from_project_root, section_name)
# ---------------------------------------------------------------------------
READMES = [
    ("README.md",                                               "Project Overview"),
    ("data/README.md",                                          "Data"),
    ("scripts/README.md",                                       "Scripts"),
    ("scripts/main/README.md",                                  "scripts/main"),
    ("scripts/exploratory/README.md",                           "scripts/exploratory"),
    ("scripts/cluster_analysis_energy_patterns/README.md",      "scripts/cluster_analysis_energy_patterns"),
    ("scripts/ep_structure_analysis/README.md",                 "scripts/ep_structure_analysis"),
    ("scripts/ck_subterms_analysis/README.md",                  "scripts/ck_subterms_analysis"),
    ("scripts/preprocess_data/README.md",                       "scripts/preprocess_data"),
]

TITLE_HEADER = (
    "# Repository User Guide\n\n"
    "**Paper: Energetic Patterns of Cyclones in the Southwestern Atlantic**\n\n"
    "*Auto-generated from repository READMEs*\n\n"
    "---\n\n"
)

PANDOC_OPTIONS = [
    "--toc",
    "--toc-depth=2",
    "-V", "geometry:margin=2.5cm",
    "-V", "fontsize=11pt",
    "--pdf-engine=xelatex",
]


def check_dependencies() -> None:
    """Verify pandoc and xelatex are available; exit with error if not."""
    missing = []
    for tool in ("pandoc", "xelatex"):
        if shutil.which(tool) is None:
            missing.append(tool)
    if missing:
        print(
            f"ERROR: The following required tools are not available on PATH: "
            f"{', '.join(missing)}\n"
            "Install pandoc from https://pandoc.org/ and a TeX distribution "
            "(e.g. TeX Live) to provide xelatex.",
            file=sys.stderr,
        )
        sys.exit(1)


def collect_readmes() -> str:
    """Read each README file and assemble the combined Markdown string."""
    sections: list[str] = [TITLE_HEADER]

    for rel_path, section_name in READMES:
        readme_path = PROJECT_ROOT / rel_path
        if not readme_path.exists():
            print(f"WARNING: README not found, skipping: {rel_path}")
            continue

        content = readme_path.read_text(encoding="utf-8")
        section_block = (
            f"## Section: {section_name}\n\n"
            f"> Source: `{rel_path}`\n\n"
            f"{content}\n\n"
            "---\n\n"
        )
        sections.append(section_block)

    return "".join(sections)


def write_combined_md(combined: str) -> None:
    """Write the combined Markdown to docs/user_guide_combined.md."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    COMBINED_MD.write_text(combined, encoding="utf-8")
    print(f"Combined Markdown written to: {COMBINED_MD.relative_to(PROJECT_ROOT)}")


def convert_to_pdf() -> None:
    """Run pandoc to convert the combined Markdown to PDF."""
    cmd = [
        "pandoc",
        str(COMBINED_MD),
        "-o", str(OUTPUT_PDF),
    ] + PANDOC_OPTIONS

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR: pandoc conversion failed.", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)


def main() -> None:
    check_dependencies()
    combined = collect_readmes()
    write_combined_md(combined)
    convert_to_pdf()
    print(f"\n✅ PDF generated successfully: {OUTPUT_PDF.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
