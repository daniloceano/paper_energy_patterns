#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step7_build_report_pdf.py — Render the technical report as a shareable PDF.

Converts docs/lec_rerun_comparison_report.md into
docs/lec_rerun_comparison_report.pdf, with the figures embedded, so the report
can be sent to co-authors as a single file.

There is no pandoc or LaTeX in this environment, so the PDF is built directly
with ReportLab over the subset of Markdown the report actually uses: headings,
paragraphs, bullet lists, pipe tables, images and the inline emphasis, code and
link spans. DejaVu Sans is taken from the matplotlib installation, which keeps
the LEC symbols (∂, Φ, Δ, →, ⁻²) rendering correctly without depending on the
system fonts.

Usage
-----
    python scripts/lec_rerun_comparison/step7_build_report_pdf.py
    python scripts/lec_rerun_comparison/step7_build_report_pdf.py --output /tmp/draft.pdf

Requires
--------
    reportlab (pip install reportlab)

Author: Danilo Couto de Souza
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as PdfImage,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_rerun_comparison.common import BASE_DIR, REPORT_PATH  # noqa: E402

OUTPUT_PDF = REPORT_PATH.with_suffix(".pdf")
PAGE_MARGIN = 1.9 * cm
FRAME_WIDTH = A4[0] - 2 * PAGE_MARGIN
ACCENT = colors.HexColor("#1F3A5F")


def register_fonts() -> tuple[str, str, str]:
    """Register DejaVu from matplotlib so the LEC symbols survive."""
    import matplotlib

    fonts = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    faces = {
        "DejaVu": "DejaVuSans.ttf",
        "DejaVu-Bold": "DejaVuSans-Bold.ttf",
        "DejaVu-Oblique": "DejaVuSans-Oblique.ttf",
        "DejaVu-BoldOblique": "DejaVuSans-BoldOblique.ttf",
        "DejaVuMono": "DejaVuSansMono.ttf",
    }
    for name, filename in faces.items():
        pdfmetrics.registerFont(TTFont(name, fonts / filename))
    pdfmetrics.registerFontFamily(
        "DejaVu", normal="DejaVu", bold="DejaVu-Bold",
        italic="DejaVu-Oblique", boldItalic="DejaVu-BoldOblique",
    )
    return "DejaVu", "DejaVu-Bold", "DejaVuMono"


def build_styles(regular: str, bold: str, mono: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["BodyText"]
    # Left-aligned rather than justified: the report is full of long file paths
    # inside code spans, which justification blows apart into rivers of space.
    body = ParagraphStyle(
        "body", parent=base, fontName=regular, fontSize=9.4, leading=13.4,
        alignment=TA_LEFT, spaceAfter=6,
    )
    return {
        "body": body,
        "title": ParagraphStyle("title", parent=body, fontName=bold, fontSize=17,
                                leading=21, alignment=TA_LEFT, spaceAfter=10,
                                textColor=ACCENT),
        "h2": ParagraphStyle("h2", parent=body, fontName=bold, fontSize=12.5,
                             leading=16, alignment=TA_LEFT, spaceBefore=14, spaceAfter=5,
                             textColor=ACCENT),
        "h3": ParagraphStyle("h3", parent=body, fontName=bold, fontSize=10.6,
                             leading=14, alignment=TA_LEFT, spaceBefore=10, spaceAfter=4),
        "caption": ParagraphStyle("caption", parent=body, fontName=regular,
                                  fontSize=8.2, leading=11, alignment=TA_CENTER,
                                  textColor=colors.HexColor("#4A4A4A"),
                                  spaceBefore=3, spaceAfter=12),
        "cell": ParagraphStyle("cell", parent=body, fontName=regular, fontSize=8.0,
                               leading=10.4, alignment=TA_LEFT, spaceAfter=0),
        "cellhead": ParagraphStyle("cellhead", parent=body, fontName=bold,
                                   fontSize=8.0, leading=10.4, alignment=TA_LEFT,
                                   spaceAfter=0),
        "mono": mono,
    }


# ── inline markdown ───────────────────────────────────────────────────────────
def inline(text: str, mono: str) -> str:
    """Translate the inline Markdown the report uses into ReportLab markup."""
    text = text.replace("\\|", "❘")
    placeholders: list[str] = []

    def stash(markup: str) -> str:
        placeholders.append(markup)
        return f"\x00{len(placeholders) - 1}\x00"

    # code spans first: their content must not be re-parsed
    text = re.sub(
        r"`([^`]+)`",
        lambda m: stash(f'<font face="{mono}" size="8.4">{html.escape(m.group(1))}</font>'),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda m: stash(
            f'<link href="{html.escape(m.group(2), quote=True)}" color="#1F5FA8">'
            f"{html.escape(m.group(1))}</link>"
        ),
        text,
    )
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<i>\1</i>", text)
    text = text.replace("❘", "|")
    return re.sub(r"\x00(\d+)\x00", lambda m: placeholders[int(m.group(1))], text)


# ── block markdown ────────────────────────────────────────────────────────────
IMAGE_RE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)\s*$")
CAPTION_RE = re.compile(r"^\*(Figure \d+\..*)\*\s*$")


def scaled_image(path: Path, max_height: float) -> PdfImage:
    with Image.open(path) as handle:
        width, height = handle.size
    scale = min(FRAME_WIDTH / width, max_height / height)
    return PdfImage(str(path), width=width * scale, height=height * scale)


def column_widths(rows: list[list[str]]) -> list[float]:
    """Share the frame width out in proportion to the longest cell per column.

    Uniform columns force long file paths to wrap mid-token; weighting by the
    longest word keeps them intact where the table can afford it.
    """
    columns = max(len(row) for row in rows)
    weights = []
    for index in range(columns):
        cells = [row[index] for row in rows if index < len(row)]
        longest_word = max((len(word) for cell in cells for word in cell.split()), default=1)
        weights.append(max(longest_word, min(max((len(cell) for cell in cells), default=1), 28)))
    total = sum(weights)
    return [FRAME_WIDTH * weight / total for weight in weights]


def table_flowable(rows: list[list[str]], styles: dict) -> Table:
    header, *body = rows
    data = [[Paragraph(inline(cell, styles["mono"]), styles["cellhead"]) for cell in header]]
    data += [[Paragraph(inline(cell, styles["mono"]), styles["cell"]) for cell in row]
             for row in body]
    table = Table(data, colWidths=column_widths(rows), repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF1F6")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, ACCENT),
                ("LINEBELOW", (0, 1), (-1, -2), 0.25, colors.HexColor("#D5D5D5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def split_row(line: str) -> list[str]:
    """Split a pipe table row, honouring cells that contain an escaped ``\|``."""
    protected = line.strip().replace("\\|", "\x01")
    return [
        cell.strip().replace("\x01", "\\|")
        for cell in protected.strip("|").split("|")
    ]


def is_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:|-]+\|", line.strip()))


def parse(markdown: str, styles: dict, base_dir: Path) -> list:
    story: list = []
    lines = markdown.splitlines()
    index = 0
    paragraph: list[str] = []
    bullets: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            story.append(Paragraph(inline(" ".join(paragraph), styles["mono"]), styles["body"]))
            paragraph = []

    def flush_bullets() -> None:
        nonlocal bullets
        if bullets:
            story.append(
                ListFlowable(
                    [
                        ListItem(
                            Paragraph(inline(item, styles["mono"]), styles["body"]),
                            leftIndent=12,
                        )
                        for item in bullets
                    ],
                    bulletType="bullet", start="•", leftIndent=14, bulletFontName="DejaVu",
                )
            )
            story.append(Spacer(1, 4))
            bullets = []

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_bullets()
            index += 1
            continue

        image = IMAGE_RE.match(stripped)
        if image:
            flush_paragraph()
            flush_bullets()
            path = (base_dir / image.group("path")).resolve()
            caption = ""
            look = index + 1
            while look < len(lines) and not lines[look].strip():
                look += 1
            if look < len(lines):
                found = CAPTION_RE.match(lines[look].strip())
                if found:
                    caption = found.group(1)
                    index = look
            if path.is_file():
                block = [scaled_image(path, 22.5 * cm if caption else 24 * cm)]
                if caption:
                    block.append(Paragraph(inline(caption, styles["mono"]), styles["caption"]))
                story.append(KeepTogether(block))
            index += 1
            continue

        if stripped.startswith("|") and index + 1 < len(lines) and is_separator(lines[index + 1]):
            flush_paragraph()
            flush_bullets()
            rows = [split_row(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(split_row(lines[index]))
                index += 1
            story.append(table_flowable(rows, styles))
            story.append(Spacer(1, 9))
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            flush_bullets()
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            style = {1: "title", 2: "h2"}.get(level, "h3")
            story.append(Paragraph(inline(text, styles["mono"]), styles[style]))
            index += 1
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            bullets.append(stripped[2:])
            index += 1
            while index < len(lines) and lines[index].startswith("  ") and lines[index].strip():
                bullets[-1] += " " + lines[index].strip()
                index += 1
            continue

        if set(stripped) == {"-"} and len(stripped) >= 3:
            flush_paragraph()
            flush_bullets()
            index += 1
            continue

        flush_bullets()
        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    flush_bullets()
    return story


def footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("DejaVu", 7.5)
    canvas.setFillColor(colors.HexColor("#7A7A7A"))
    canvas.drawString(PAGE_MARGIN, 1.1 * cm,
                      "Legacy vs corrected LEC climatology — technical report")
    canvas.drawRightString(A4[0] - PAGE_MARGIN, 1.1 * cm, f"{document.page}")
    canvas.restoreState()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PDF)
    args = parser.parse_args()

    if not args.report.is_file():
        raise SystemExit(f"{args.report} not found; run step 4 first")

    regular, bold, mono = register_fonts()
    styles = build_styles(regular, bold, mono)
    story = parse(args.report.read_text(encoding="utf-8"), styles, args.report.parent)

    document = SimpleDocTemplate(
        str(args.output),
        pagesize=A4,
        leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
        topMargin=1.7 * cm, bottomMargin=1.8 * cm,
        title="Legacy vs corrected LEC climatology — technical report",
        author="Danilo Couto de Souza",
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    size = args.output.stat().st_size / 1e6
    print(f"wrote {args.output} ({size:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
