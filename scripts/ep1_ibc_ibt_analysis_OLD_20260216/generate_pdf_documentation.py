"""
Generate PDF documentation from SCIENTIFIC_NOTES_STEP4.md

This script converts the scientific documentation to PDF format using pandoc.
The output is saved with a descriptive name indicating the analysis chapter.

Requirements:
- pandoc (install with: brew install pandoc)
- BasicTeX or MacTeX (install with: brew install --cask basictex)

Author: Danilo Couto de Souza
Date: February 2026
"""

import subprocess
from pathlib import Path
import sys

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_FILE = BASE_DIR / "scripts" / "ep1_ibc_ibt_analysis" / "SCIENTIFIC_NOTES_STEP4.md"
OUTPUT_DIR = BASE_DIR / "docs"
OUTPUT_FILE = OUTPUT_DIR / "Chapter_EP1_Instability_Diagnostics_Scientific_Notes.pdf"

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def check_dependencies():
    """Check if pandoc and LaTeX are installed."""
    
    print("Checking dependencies...")
    
    # Check pandoc
    try:
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"  ✓ pandoc: {result.stdout.split()[1]}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ❌ pandoc not found. Install with: brew install pandoc")
        return False
    
    # Check LaTeX (try xelatex first, then pdflatex)
    latex_engine = None
    for engine in ['xelatex', 'pdflatex']:
        try:
            subprocess.run([engine, '--version'], 
                         capture_output=True, check=True)
            print(f"  ✓ {engine} found")
            latex_engine = engine
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    if latex_engine is None:
        print("  ❌ LaTeX not found. Install with: brew install --cask basictex")
        print("     After install, run: sudo tlmgr update --self && sudo tlmgr install collection-fontsrecommended")
        return False
    
    return True


def generate_pdf():
    """Generate PDF from Markdown using pandoc."""
    
    print(f"\nGenerating PDF...")
    print(f"  Input:  {INPUT_FILE.name}")
    print(f"  Output: {OUTPUT_FILE.name}")
    
    # Pandoc command - use xelatex for Unicode support
    cmd = [
        'pandoc',
        str(INPUT_FILE),
        '-o', str(OUTPUT_FILE),
        '--pdf-engine=xelatex',  # XeLaTeX handles Unicode better
        '--toc',                  # Table of contents
        '--number-sections',      # Numbered sections
        '-V', 'geometry:margin=1in',  # 1-inch margins
    ]
    
    print(f"\n  Running pandoc with XeLaTeX engine...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              check=True, timeout=120)  # 2 min timeout
        print(f"\n  ✓ PDF generated successfully!")
        print(f"  Location: {OUTPUT_FILE}")
        return True
    except subprocess.TimeoutExpired:
        print(f"\n  ❌ PDF generation timed out (>2 min)")
        print(f"  This may indicate missing LaTeX packages.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"\n  ❌ PDF generation failed:")
        if e.stderr:
            # Show only relevant error lines
            error_lines = e.stderr.strip().split('\n')
            for line in error_lines[-15:]:
                if line.strip():
                    print(f"    {line}")
        return False


def main():
    """Main function."""
    
    print("="*80)
    print("PDF DOCUMENTATION GENERATOR")
    print("="*80)
    print(f"\nChapter: EP1 Instability Diagnostics - Scientific Notes")
    print(f"Source:  {INPUT_FILE.relative_to(BASE_DIR)}")
    print(f"Output:  {OUTPUT_FILE.relative_to(BASE_DIR)}\n")
    
    # Check if input exists
    if not INPUT_FILE.exists():
        print(f"❌ Error: Input file not found: {INPUT_FILE}")
        return 1
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Missing dependencies. Please install required software.")
        return 1
    
    # Generate PDF
    if not generate_pdf():
        return 1
    
    print("\n" + "="*80)
    print("✓ Documentation generated successfully!")
    print("="*80)
    print(f"\nTo view: open {OUTPUT_FILE}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
