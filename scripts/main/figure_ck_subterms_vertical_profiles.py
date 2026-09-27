#!/usr/bin/env python3
"""Compatibility entry point for the corrected all-EP Ck subterm figures.

The former implementation mixed corrected total-Ck profiles with an EP1-only
side run of the subterms. That result is superseded. The authoritative analysis
now lives in ``scripts/ck_subterms_analysis`` and covers EP1, EP2, and EP3 from
the same complete corrected climatology.

Running this file regenerates the three all-pattern figures, then mirrors the
vertical-profile figure to the historical ``figures/main`` destination so old
automation does not silently publish the withdrawn EP1-only graphic.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ck_subterms_analysis.step3_subterm_figures import main as build_figures  # noqa: E402


SOURCE = (
    PROJECT_ROOT
    / "figures"
    / "ck_subterms_corrected"
    / "ck_subterms_vertical_profiles.png"
)
DESTINATION = PROJECT_ROOT / "figures" / "main" / "ck_subterms_vertical_profiles.png"


def main() -> int:
    exit_code = build_figures()
    if exit_code != 0:
        return exit_code

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, DESTINATION)
    print(f"  mirrored {SOURCE.relative_to(PROJECT_ROOT)}")
    print(f"       to {DESTINATION.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
