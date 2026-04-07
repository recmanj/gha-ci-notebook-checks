#!/usr/bin/env python3
"""
Metadata Checker for Jupyter Notebooks

Checks that notebooks have a 'Last updated' date in the first markdown cell (Criterion 1.2.6).

Expected format in first markdown cell:
    **Last updated:** YYYY-MM-DD

Usage:
    python metadata_checker.py [--config CONFIG] notebook1.ipynb notebook2.ipynb ...
"""

import argparse
import re
import sys
from pathlib import Path

from qa_config import filter_notebooks, is_check_disabled, load_config
from utils import extract_cell_source, read_notebook


def check_metadata(notebook_path: str) -> tuple[str, str | None]:
    """
    Check for 'Last updated' date in a notebook's first markdown cell.

    Returns: ("success"|"failure"|"warning", date_found_or_None)
    """
    date_pattern = r"\*\*Last updated:\*\*\s*(\d{4}-\d{2}-\d{2})"

    try:
        nb_data = read_notebook(notebook_path)
    except Exception as e:
        print(f"❌ Error reading {notebook_path}: {e}")
        return ("failure", None)

    cells = nb_data.get("cells", [])

    # Check all markdown cells before the first code cell
    for cell in cells:
        if cell.get("cell_type") == "code":
            break  # Stop searching once we hit code
        if cell.get("cell_type") == "markdown":
            source = extract_cell_source(cell)
            match = re.search(date_pattern, source)
            if match:
                date = match.group(1)
                print(f"✅ {notebook_path}: Last updated {date}")
                return ("success", date)

    # Fallback: check README.md in same directory
    readme_path = Path(notebook_path).parent / "README.md"
    if readme_path.exists():
        try:
            readme_text = readme_path.read_text(encoding="utf-8")
            match = re.search(date_pattern, readme_text)
            if match:
                date = match.group(1)
                print(f"✅ {notebook_path}: Last updated {date} (from README.md)")
                return ("success", date)
        except Exception:
            pass

    print(f"❌ {notebook_path}: No 'Last updated' date found")
    print("")
    print("   To fix this, add the following to the FIRST markdown cell of your notebook:")
    print("")
    print("       **Last updated:** YYYY-MM-DD")
    print("")
    print("   Example:")
    print("       **Last updated:** 2025-01-15")
    print("")
    return ("failure", None)


def main():
    parser = argparse.ArgumentParser(
        description="Check for Last updated metadata in Jupyter notebooks"
    )
    parser.add_argument("notebooks", nargs="*", help="Notebook files to check")
    parser.add_argument(
        "--config",
        default=".github/notebook-qa.yml",
        help="Path to QA configuration file (default: .github/notebook-qa.yml)",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    # Check if metadata check is globally disabled
    if is_check_disabled(config, "metadata"):
        print("Metadata check is disabled by configuration")
        sys.exit(0)

    # Filter notebooks based on config
    notebooks = filter_notebooks(config, "metadata", args.notebooks)

    if not notebooks:
        print("All notebooks skipped by configuration")
        sys.exit(0)

    results = []
    for notebook in notebooks:
        result, _ = check_metadata(notebook)
        results.append(result)

    # Exit 0 even for warnings (non-blocking check)
    # Change to exit(1) if this should be a blocking check
    if "failure" in results:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
