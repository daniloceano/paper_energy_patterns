"""Top-level scripts package for the paper_energy_patterns project.

This file makes `scripts` a proper package so submodule imports like
`from scripts.utils.load_data import load_tracks` work reliably when
running scripts from the project root or other working directories.
"""

__all__ = ["utils", "analysis"]
"""
Scripts package for paper_energy_patterns
"""
