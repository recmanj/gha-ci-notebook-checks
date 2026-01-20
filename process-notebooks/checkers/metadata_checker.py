#!/usr/bin/env python3
"""
Metadata Checker for Jupyter Notebooks

Checks that notebooks have a 'Last updated' date in the first markdown cell (Criterion 1.2.6).

Expected format in first markdown cell:
    **Last updated:** YYYY-MM-DD

Usage:
    python metadata_checker.py notebook1.ipynb notebook2.ipynb ...
"""

import json
import re
import sys
from pathlib import Path


def read_notebook(notebook_path: str) -> dict:
    """Read and parse a Jupyter notebook file."""
    with open(notebook_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_cell_source(cell: dict) -> str:
    """Extract source from a cell as a single string."""
    source = cell.get('source', [])
    if isinstance(source, list):
        return ''.join(source)
    return str(source)


def check_metadata(notebook_path: str) -> tuple[str, str | None]:
    """
    Check for 'Last updated' date in a notebook's first markdown cell.

    Returns: ("success"|"failure"|"warning", date_found_or_None)
    """
    date_pattern = r'\*\*Last updated:\*\*\s*(\d{4}-\d{2}-\d{2})'

    try:
        nb_data = read_notebook(notebook_path)
    except Exception as e:
        print(f"❌ Error reading {notebook_path}: {e}")
        return ("failure", None)

    cells = nb_data.get('cells', [])

    # Check first markdown cell
    for cell in cells:
        if cell.get('cell_type') == 'markdown':
            source = extract_cell_source(cell)
            match = re.search(date_pattern, source)
            if match:
                date = match.group(1)
                print(f"✅ {notebook_path}: Last updated {date}")
                return ("success", date)
            break  # Only check the first markdown cell

    # Fallback: check README.md in same directory
    readme_path = Path(notebook_path).parent / "README.md"
    if readme_path.exists():
        try:
            readme_text = readme_path.read_text(encoding='utf-8')
            match = re.search(date_pattern, readme_text)
            if match:
                date = match.group(1)
                print(f"✅ {notebook_path}: Last updated {date} (from README.md)")
                return ("success", date)
        except Exception:
            pass

    print(f"❌ {notebook_path}: No 'Last updated' date found")
    print(f"")
    print(f"   To fix this, add the following to the FIRST markdown cell of your notebook:")
    print(f"")
    print(f"       **Last updated:** YYYY-MM-DD")
    print(f"")
    print(f"   Example:")
    print(f"       **Last updated:** 2025-01-15")
    print(f"")
    return ("failure", None)


def main():
    if len(sys.argv) < 2:
        print("Usage: metadata_checker.py <notebook1.ipynb> [notebook2.ipynb ...]")
        sys.exit(1)

    notebooks = [nb for nb in sys.argv[1:] if nb.strip()]

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
