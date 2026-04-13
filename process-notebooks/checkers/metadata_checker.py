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
from utils import extract_cell_source, read_notebook, write_notebook


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


def update_metadata_date(notebook_path: str, new_date: str) -> bool:
    """Update the 'Last updated' date in a notebook's first markdown cell.

    Returns True if a date was found and updated, False otherwise.
    """
    date_pattern = r"(\*\*Last updated:\*\*\s*)\d{4}-\d{2}-\d{2}"

    try:
        nb_data = read_notebook(notebook_path)
    except Exception as e:
        print(f"Error reading {notebook_path}: {e}")
        return False

    cells = nb_data.get("cells", [])

    for cell in cells:
        if cell.get("cell_type") == "code":
            break
        if cell.get("cell_type") == "markdown":
            source = cell.get("source", [])
            is_list = isinstance(source, list)
            text = "".join(source) if is_list else str(source)

            if re.search(date_pattern, text):
                updated_text = re.sub(date_pattern, rf"\g<1>{new_date}", text)
                if is_list:
                    cell["source"] = updated_text.splitlines(keepends=True)
                else:
                    cell["source"] = updated_text

                write_notebook(notebook_path, nb_data)
                print(f"Updated {notebook_path}: Last updated -> {new_date}")
                return True

    print(f"No 'Last updated' date found in {notebook_path} to update")
    return False


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
    parser.add_argument(
        "--update",
        metavar="YYYY-MM-DD",
        help="Update the 'Last updated' date in notebooks (in-place)",
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

    if args.update:
        if not re.match(r"\d{4}-\d{2}-\d{2}$", args.update):
            print(f"Error: Invalid date format '{args.update}', expected YYYY-MM-DD")
            sys.exit(1)
        updated_count = 0
        for notebook in notebooks:
            if update_metadata_date(notebook, args.update):
                updated_count += 1
        print(f"Updated {updated_count}/{len(notebooks)} notebook(s)")
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
