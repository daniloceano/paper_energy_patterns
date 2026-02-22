"""
Generate PDF from Scientific Notes (SCIENTIFIC_NOTES.md)

Uses pandoc with XeLaTeX for high-quality mathematical typesetting
and native Unicode support (handles superscripts like ⁻¹, ², etc.).

Requirements:
  - pandoc (https://pandoc.org/)
  - XeLaTeX (part of TeX Live or BasicTeX)

Install on macOS:
  brew install pandoc basictex

Install on Linux:
  sudo apt install pandoc texlive-xetex

Usage:
  python generate_scientific_notes_pdf.py

Output:
  docs/scientific_notes_ep_structure.pdf

Author: Danilo Couto de Souza
Date: February 2026
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "ep_structure_analysis"
DOCS_DIR = PROJECT_ROOT / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

SCIENTIFIC_NOTES_MD = SCRIPT_DIR / "SCIENTIFIC_NOTES.md"
OUTPUT_PDF = DOCS_DIR / "scientific_notes_ep_structure.pdf"

# Pandoc options for high-quality PDF
PANDOC_OPTIONS = [
    "--from=markdown",
    "--to=pdf",
    "--pdf-engine=xelatex",  # xelatex supports Unicode natively
    "--number-sections",
    "--toc",
    "--toc-depth=2",
    "-V", "geometry:margin=2.5cm",
    "-V", "fontsize=11pt",
    "-V", "documentclass=article",
    "-V", "papersize=a4",
    "-V", "colorlinks=true",
    "-V", "linkcolor=blue",
    "-V", "urlcolor=blue",
    "-V", "citecolor=blue",
    "--metadata", f"date={datetime.now().strftime('%B %d, %Y')}",
]

# ============================================================================
# FUNCTIONS
# ============================================================================

def check_dependencies():
    """Check if pandoc and pdflatex are installed."""
    try:
        subprocess.run(
            ["pandoc", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: pandoc is not installed.")
        print("\nInstall pandoc:")
        print("  macOS:   brew install pandoc")
        print("  Ubuntu:  sudo apt install pandoc")
        print("  Windows: https://pandoc.org/installing.html")
        sys.exit(1)

    try:
        subprocess.run(
            ["xelatex", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: xelatex (LaTeX) is not installed.")
        print("\nInstall LaTeX:")
        print("  macOS:   brew install basictex  (includes xelatex)")
        print("  Ubuntu:  sudo apt install texlive-xetex")
        print("  Windows: https://miktex.org/")
        sys.exit(1)


def generate_pdf():
    """Generate PDF from Markdown using pandoc."""
    if not SCIENTIFIC_NOTES_MD.exists():
        print(f"❌ Error: {SCIENTIFIC_NOTES_MD} not found.")
        sys.exit(1)

    print(f"📄 Generating PDF from {SCIENTIFIC_NOTES_MD.name}...")
    print(f"   Output: {OUTPUT_PDF}")

    # Build pandoc command
    cmd = ["pandoc", str(SCIENTIFIC_NOTES_MD)] + PANDOC_OPTIONS + ["-o", str(OUTPUT_PDF)]

    # Run pandoc from the script directory so relative image paths work
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(SCRIPT_DIR),  # Run from script directory for relative paths
        )
        
        print(f"\n✅ PDF generated successfully!")
        print(f"   Location: {OUTPUT_PDF}")
        print(f"   Size: {OUTPUT_PDF.stat().st_size / 1024:.1f} KB")
        
        return OUTPUT_PDF
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error generating PDF:")
        print(f"   {e.stderr}")
        
        # Fallback: try minimal options
        print("\n⚠️  Retrying with minimal options...")
        cmd_fallback = [
            "pandoc",
            str(SCIENTIFIC_NOTES_MD),
            "--from=markdown",
            "--to=pdf",
            "--pdf-engine=xelatex",
            "--number-sections",
            "--toc",
            "-o",
            str(OUTPUT_PDF),
        ]
        
        try:
            subprocess.run(
                cmd_fallback, 
                check=True, 
                stderr=subprocess.PIPE,
                cwd=str(SCRIPT_DIR),
            )
            print(f"✅ PDF generated (basic formatting)")
            print(f"   Location: {OUTPUT_PDF}")
            return OUTPUT_PDF
        except subprocess.CalledProcessError as e2:
            print(f"❌ Fallback also failed:")
            print(f"   {e2.stderr}")
            sys.exit(1)


def open_pdf():
    """Open PDF in default viewer (macOS/Linux)."""
    import platform
    
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(OUTPUT_PDF)])
        elif system == "Linux":
            subprocess.run(["xdg-open", str(OUTPUT_PDF)])
        elif system == "Windows":
            subprocess.run(["start", str(OUTPUT_PDF)], shell=True)
        else:
            print(f"\n💡 Open the PDF manually: {OUTPUT_PDF}")
    except Exception as e:
        print(f"\n💡 Open the PDF manually: {OUTPUT_PDF}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("SCIENTIFIC NOTES → PDF CONVERTER")
    print("=" * 70)
    
    # Check dependencies
    check_dependencies()
    
    # Generate PDF
    pdf_path = generate_pdf()
    
    # Ask to open
    print("\n" + "=" * 70)
    response = input("Open PDF? [y/N]: ").strip().lower()
    if response in ['y', 'yes']:
        open_pdf()
    
    print("=" * 70)


if __name__ == "__main__":
    main()
