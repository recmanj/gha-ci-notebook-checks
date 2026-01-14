#!/usr/bin/env python3
"""
DOI Checker for Jupyter Notebooks

Checks if notebooks that use datasets with DOI metadata properly cite those DOIs (Criterion 1.2.5).

Usage:
    python doi_checker.py notebook1.ipynb notebook2.ipynb ...
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


def check_doi(notebook_path: str) -> str:
    """
    Check for DOI citations in a notebook.

    Returns: "success", "failure", or "skipped"
    """
    # DOI regex patterns
    doi_patterns = [
        r'10\.\d{4,9}/[-._;()/:A-Z0-9]+',  # Standard DOI format
        r'doi\.org/(10\.\d{4,9}/[-._;()/:A-Z0-9]+)',  # doi.org URLs
        r'https?://(?:dx\.)?doi\.org/(10\.\d{4,9}/[-._;()/:A-Z0-9]+)'  # Full DOI URLs
    ]

    # Metadata fields that might contain DOI references
    metadata_fields = ['references', 'citation', 'doi', 'reference', 'Attributes']

    try:
        nb_data = read_notebook(notebook_path)
    except Exception as e:
        print(f"❌ Error reading {notebook_path}: {e}")
        return "failure"

    # First, check if dataset metadata contains DOI references
    has_dataset_doi_metadata = False

    for cell in nb_data.get('cells', []):
        if cell.get('cell_type') == 'code':
            for output in cell.get('outputs', []):
                # Check text outputs for dataset metadata with DOIs
                if 'text' in output:
                    text = output['text']
                    if isinstance(text, list):
                        text = ''.join(text)
                    if any(field in text for field in metadata_fields):
                        for pattern in doi_patterns:
                            if re.search(pattern, text, re.IGNORECASE):
                                has_dataset_doi_metadata = True
                                break

                # Check data outputs for metadata
                data = output.get('data', {})
                for key, value in data.items():
                    if isinstance(value, (str, list)):
                        if isinstance(value, list):
                            value = ''.join(value)
                        if any(field in value for field in metadata_fields):
                            for pattern in doi_patterns:
                                if re.search(pattern, value, re.IGNORECASE):
                                    has_dataset_doi_metadata = True
                                    break

                if has_dataset_doi_metadata:
                    break

        if has_dataset_doi_metadata:
            break

    if not has_dataset_doi_metadata:
        print(f"⏭️  No dataset DOI metadata found in {notebook_path}, skipping")
        return "skipped"

    found_dois = set()

    # Search in all cells for DOI citations
    for cell in nb_data.get('cells', []):
        if cell.get('cell_type') == 'markdown':
            source = extract_cell_source(cell)
            for pattern in doi_patterns:
                matches = re.findall(pattern, source, re.IGNORECASE)
                found_dois.update(matches)

        if cell.get('cell_type') == 'code':
            for output in cell.get('outputs', []):
                if 'text' in output:
                    text = output['text']
                    if isinstance(text, list):
                        text = ''.join(text)
                    for pattern in doi_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        found_dois.update(matches)

                data = output.get('data', {})
                for key, value in data.items():
                    if isinstance(value, (str, list)):
                        if isinstance(value, list):
                            value = ''.join(value)
                        for pattern in doi_patterns:
                            matches = re.findall(pattern, value, re.IGNORECASE)
                            found_dois.update(matches)

    # Validate DOI format
    valid_doi_pattern = re.compile(r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$', re.IGNORECASE)
    valid_dois = [doi for doi in found_dois if valid_doi_pattern.match(doi)]

    if not valid_dois:
        print(f"❌ {notebook_path}: Uses dataset with DOI metadata but doesn't cite the DOI")
        print("   Add DOI citation in markdown (format: 10.xxxx/xxxxx)")
        return "failure"
    else:
        print(f"✅ {notebook_path}: Found {len(valid_dois)} valid DOI(s)")
        for doi in sorted(valid_dois):
            print(f"   - {doi}")
        return "success"


def main():
    if len(sys.argv) < 2:
        print("Usage: doi_checker.py <notebook1.ipynb> [notebook2.ipynb ...]")
        sys.exit(1)

    notebooks = [nb for nb in sys.argv[1:] if nb.strip()]
    overall_result = 0

    for notebook in notebooks:
        result = check_doi(notebook)
        if result == "failure":
            overall_result = 1

    sys.exit(overall_result)


if __name__ == "__main__":
    main()
