#!/usr/bin/env python3
"""
Figure Checker for Jupyter Notebooks

Checks for figure labels and source attribution (Criterion 3.3.2).

Usage:
    python figure_checker.py [--config CONFIG] notebook1.ipynb notebook2.ipynb ...
"""

import argparse
import json
import re
import sys

from qa_config import load_config, filter_notebooks, is_check_disabled


def read_notebook(notebook_path: str) -> dict:
    """Read and parse a Jupyter notebook file."""
    with open(notebook_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_cell_source(cell: dict) -> str:
    """Extract source code/markdown from a cell as a single string."""
    source = cell.get('source', [])
    if isinstance(source, list):
        return ''.join(source)
    return str(source)


def check_figures(notebook_path: str) -> str:
    """
    Check for figure labels and source attribution in a notebook.

    Returns: "success" or "failure"
    """
    # Source attribution patterns
    source_patterns = [
        r'source:?\s+\S+',
        r'data\s+from:?\s*',
        r'doi:?\s*10\.\d+',
        r'https?://\S+',
        r'credit:?\s*',
        r'attribution:?\s*',
        r'reference:?\s*',
        r'dataset:?\s*',
    ]

    try:
        nb_data = read_notebook(notebook_path)
    except Exception as e:
        print(f"❌ Error reading {notebook_path}: {e}")
        return "failure"

    issues = []
    cells = nb_data.get('cells', [])

    for cell_idx, cell in enumerate(cells):
        if cell.get('cell_type') == 'code':
            outputs = cell.get('outputs', [])

            for output in outputs:
                if output.get('output_type') in ['display_data', 'execute_result']:
                    data = output.get('data', {})

                    # Check if this is a figure output
                    if 'image/png' in data or 'image/jpeg' in data or 'image/jpg' in data:
                        # Check nearby markdown cells for source attribution
                        has_source = False

                        # Check 2 cells before and after
                        for offset in [-2, -1, 1, 2]:
                            check_idx = cell_idx + offset
                            if 0 <= check_idx < len(cells):
                                check_cell = cells[check_idx]
                                if check_cell.get('cell_type') == 'markdown':
                                    source = extract_cell_source(check_cell)

                                    # Check for source patterns
                                    for pattern in source_patterns:
                                        if re.search(pattern, source, re.IGNORECASE):
                                            has_source = True
                                            break

                                if has_source:
                                    break

                        if not has_source:
                            issues.append(f"Cell {cell_idx}: Figure missing source attribution")

    if not issues:
        print(f"✅ {notebook_path}: All figures have proper labels and sources")
        return "success"
    else:
        print(f"❌ {notebook_path}: {len(issues)} figure labeling issue(s)")
        for issue in issues:
            print(f"   - {issue}")
        print("   Add source attribution in markdown cells near figures")
        print("   Patterns: 'Source:', 'Data from:', DOI, URL, 'Credit:', etc.")
        return "failure"


def main():
    parser = argparse.ArgumentParser(
        description='Check for figure labels and source attribution in Jupyter notebooks'
    )
    parser.add_argument(
        'notebooks',
        nargs='*',
        help='Notebook files to check'
    )
    parser.add_argument(
        '--config',
        default='.github/notebook-qa.yml',
        help='Path to QA configuration file (default: .github/notebook-qa.yml)'
    )
    args = parser.parse_args()

    config = load_config(args.config)

    # Check if figures check is globally disabled
    if is_check_disabled(config, 'figures'):
        print("Figure check is disabled by configuration")
        sys.exit(0)

    # Filter notebooks based on config
    notebooks = filter_notebooks(config, 'figures', args.notebooks)

    if not notebooks:
        print("All notebooks skipped by configuration")
        sys.exit(0)

    overall_result = 0

    for notebook in notebooks:
        result = check_figures(notebook)
        if result == "failure":
            overall_result = 1

    sys.exit(overall_result)


if __name__ == "__main__":
    main()
