#!/usr/bin/env python3
"""
Accessibility Checker for Jupyter Notebooks

Checks for images without alt text in markdown cells (Criterion 3.1.3).

Usage:
    python accessibility_checker.py notebook1.ipynb notebook2.ipynb ...
"""

import json
import re
import sys


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


def check_accessibility(notebook_path: str) -> str:
    """
    Check for accessibility issues in a notebook.

    Returns: "success" or "failure"
    """
    try:
        nb_data = read_notebook(notebook_path)
    except Exception as e:
        print(f"Warning: Could not check {notebook_path}: {e}")
        return "success"  # Don't fail on read errors

    issues = []

    for cell_idx, cell in enumerate(nb_data.get('cells', [])):
        if cell.get('cell_type') == 'markdown':
            source = extract_cell_source(cell)

            # Check for images without alt text: ![]( pattern
            if re.search(r'!\[\]\(', source):
                issues.append(f"Cell {cell_idx}: Image without alt text")

            # Check HTML img tags without alt attribute
            img_tags = re.findall(r'<img[^>]*>', source, re.IGNORECASE)
            for img_tag in img_tags:
                if not re.search(r'\balt\s*=', img_tag, re.IGNORECASE):
                    issues.append(f"Cell {cell_idx}: HTML img without alt attribute")

    if not issues:
        print(f"✅ {notebook_path}: All images have alt text")
        return "success"
    else:
        print(f"❌ {notebook_path}: {len(issues)} accessibility issue(s)")
        for issue in issues:
            print(f"   - {issue}")
        print("   Add alt text to images: ![description](image.png)")
        print("   For HTML: <img src=\"...\" alt=\"description\">")
        return "failure"


def main():
    if len(sys.argv) < 2:
        print("Usage: accessibility_checker.py <notebook1.ipynb> [notebook2.ipynb ...]")
        sys.exit(1)

    notebooks = [nb for nb in sys.argv[1:] if nb.strip()]
    overall_result = 0

    for notebook in notebooks:
        result = check_accessibility(notebook)
        if result == "failure":
            overall_result = 1

    sys.exit(overall_result)


if __name__ == "__main__":
    main()
