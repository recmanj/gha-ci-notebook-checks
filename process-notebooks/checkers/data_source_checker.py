#!/usr/bin/env python3
"""
Data Source Checker for Jupyter Notebooks (Warning Only)

Checks that notebooks source data via cdsapi and/or earthkit (Criterion 1.2.8).

If data sourcing is detected but NOT via cdsapi/earthkit, emits a ::warning::
annotation. This check NEVER fails the job — it always exits 0.

Usage:
    python data_source_checker.py [--config CONFIG] notebook1.ipynb notebook2.ipynb ...
"""

import argparse
import re
import sys

from qa_config import filter_notebooks, is_check_disabled, load_config
from utils import extract_cell_source, read_notebook

# Patterns indicating data sourcing via approved sources
APPROVED_PATTERNS = [
    r"import\s+cdsapi",
    r"from\s+cdsapi",
    r"import\s+earthkit",
    r"from\s+earthkit",
    r"cds\.climate\.copernicus\.eu",
    r"ads\.atmosphere\.copernicus\.eu",
]

# Patterns indicating data sourcing via other methods
OTHER_SOURCE_PATTERNS = [
    r"requests\.get\s*\(",
    r"urllib\.request",
    r"wget",
    r"curl",
    r'open_dataset\s*\(["\']https?://',
    r'read_csv\s*\(["\']https?://',
    r"download\s*\(",
]


def check_data_source(notebook_path: str) -> str:
    """
    Check data sourcing patterns in a notebook's code cells.

    Returns: "success" | "warning" | "skipped"
    """
    try:
        nb_data = read_notebook(notebook_path)
    except Exception as e:
        print(f"::warning file={notebook_path}::Could not read notebook: {e}")
        return "skipped"

    code_cells = [
        extract_cell_source(cell)
        for cell in nb_data.get("cells", [])
        if cell.get("cell_type") == "code"
    ]
    all_code = "\n".join(code_cells)

    has_approved = any(re.search(p, all_code) for p in APPROVED_PATTERNS)
    has_other = any(re.search(p, all_code) for p in OTHER_SOURCE_PATTERNS)

    if has_approved:
        print(f"  {notebook_path}: Data sourced via cdsapi/earthkit")
        return "success"

    if has_other:
        print(
            f"::warning file={notebook_path}::"
            f"Data sourcing detected but not via cdsapi or earthkit. "
            f"Consider using cdsapi or earthkit for CDS data access."
        )
        return "warning"

    # No data sourcing detected
    return "skipped"


def main():
    parser = argparse.ArgumentParser(
        description="Check data sourcing patterns in Jupyter notebooks (warning only)"
    )
    parser.add_argument("notebooks", nargs="*", help="Notebook files to check")
    parser.add_argument(
        "--config",
        default=".github/notebook-qa.yml",
        help="Path to QA configuration file (default: .github/notebook-qa.yml)",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if is_check_disabled(config, "data_source"):
        print("Data source check is disabled by configuration")
        sys.exit(0)

    notebooks = filter_notebooks(config, "data_source", args.notebooks)

    if not notebooks:
        print("All notebooks skipped by configuration")
        sys.exit(0)

    for notebook in notebooks:
        check_data_source(notebook)

    # Warning-only check: always exit 0
    sys.exit(0)


if __name__ == "__main__":
    main()
