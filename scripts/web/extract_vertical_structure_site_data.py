#!/usr/bin/env python3
"""Export the corrected vertical-structure summary for the Next.js site."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "results" / "vertical_structure" / "summary.json"
DESTINATION = REPO_ROOT / "web" / "src" / "content" / "vertical_structure.json"


def main() -> int:
    if not SOURCE.is_file():
        raise FileNotFoundError(
            f"vertical-structure summary not found: {SOURCE}. "
            "Run scripts/main/figure_vertical_levels.py first."
        )

    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    if payload.get("analysis") != "vertical_structure":
        raise ValueError(f"unexpected analysis identifier in {SOURCE}")
    if payload.get("population", {}).get("total") != 3820:
        raise ValueError("the website cannot publish a partial vertical-structure population")
    expected_patterns = {"EP1", "EP2", "EP3"}
    if set(payload.get("patterns", {})) != expected_patterns:
        raise ValueError("vertical-structure summary lacks one or more Energy Patterns")

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"✓ {DESTINATION.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
