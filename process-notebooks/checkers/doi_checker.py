#!/usr/bin/env python3
"""
DOI Checker for Jupyter Notebooks

Checks if notebooks that use datasets with DOI metadata properly cite those DOIs (Criterion 1.2.5).

Usage:
    python doi_checker.py [--config CONFIG] notebook1.ipynb notebook2.ipynb ...
"""

import argparse
import json
import re
import sys
from typing import Optional

import requests

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


# DOI regex patterns - include both uppercase and lowercase letters
DOI_PATTERNS = [
    r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+',  # Standard DOI format
    r'doi\.org/(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)',  # doi.org URLs
    r'https?://(?:dx\.)?doi\.org/(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)'  # Full DOI URLs
]

# Pattern for validating DOI format
VALID_DOI_PATTERN = re.compile(r'^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$', re.IGNORECASE)


def validate_doi_resolves(doi: str, timeout: int = 10) -> Optional[bool]:
    """
    Check if a DOI resolves via doi.org.

    Args:
        doi: The DOI string to validate (e.g., "10.1234/example")
        timeout: Request timeout in seconds

    Returns:
        True if DOI resolves (200, 301, 302 status)
        False if DOI doesn't exist (404)
        None if network error (can't verify)
    """
    try:
        response = requests.head(
            f"https://doi.org/{doi}",
            allow_redirects=False,
            timeout=timeout,
            headers={'User-Agent': 'NotebookQA/1.0'}
        )
        return response.status_code in [200, 301, 302]
    except requests.RequestException:
        return None  # Network error, can't verify


def extract_dois_from_text(text: str) -> set:
    """Extract all DOIs from a text string."""
    dois = set()
    for pattern in DOI_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dois.update(matches)
    return dois


def check_doi(notebook_path: str) -> str:
    """
    Check for DOI citations in a notebook.

    Validates that:
    1. DOIs found in dataset metadata are syntactically valid
    2. DOIs resolve via doi.org (exist in DOI registry)
    3. Dataset DOIs are properly cited in markdown cells

    Returns: "success", "failure", or "skipped"
    """
    # Metadata fields that might contain DOI references
    metadata_fields = ['references', 'citation', 'doi', 'reference', 'Attributes']

    try:
        nb_data = read_notebook(notebook_path)
    except Exception as e:
        print(f"Error reading {notebook_path}: {e}")
        return "failure"

    # Step 1: Find DOIs in dataset metadata (code cell outputs)
    dataset_dois = set()

    for cell in nb_data.get('cells', []):
        if cell.get('cell_type') != 'code':
            continue

        for output in cell.get('outputs', []):
            # Check text outputs for dataset metadata with DOIs
            if 'text' in output:
                text = output['text']
                if isinstance(text, list):
                    text = ''.join(text)
                if any(field in text for field in metadata_fields):
                    dataset_dois.update(extract_dois_from_text(text))

            # Check data outputs for metadata
            data = output.get('data', {})
            for key, value in data.items():
                if isinstance(value, (str, list)):
                    if isinstance(value, list):
                        value = ''.join(value)
                    if any(field in value for field in metadata_fields):
                        dataset_dois.update(extract_dois_from_text(value))

    # Filter to only valid DOI format
    dataset_dois = {doi for doi in dataset_dois if VALID_DOI_PATTERN.match(doi)}

    if not dataset_dois:
        print(f"  No dataset DOI metadata found in {notebook_path}, skipping")
        return "skipped"

    print(f"  Checking {notebook_path}")
    print("    Dataset DOIs found in metadata:")
    for doi in sorted(dataset_dois):
        print(f"      - {doi}")

    # Step 2: Find DOIs cited in markdown cells
    cited_dois = set()

    for cell in nb_data.get('cells', []):
        if cell.get('cell_type') == 'markdown':
            source = extract_cell_source(cell)
            cited_dois.update(extract_dois_from_text(source))

    # Filter to only valid DOI format
    cited_dois = {doi for doi in cited_dois if VALID_DOI_PATTERN.match(doi)}

    if cited_dois:
        print("    DOIs cited in markdown:")
        for doi in sorted(cited_dois):
            print(f"      - {doi}")
    else:
        print("    DOIs cited in markdown: (none)")

    # Step 3: Validate that dataset DOIs resolve via doi.org
    failed = False
    unresolved_dois = []

    print("    Validating DOIs resolve via doi.org...")
    for doi in sorted(dataset_dois):
        resolves = validate_doi_resolves(doi)
        if resolves is True:
            print(f"      {doi}: resolves")
        elif resolves is False:
            print(f"      {doi}: DOES NOT RESOLVE (404)")
            unresolved_dois.append(doi)
            failed = True
        else:
            print(f"      {doi}: could not verify (network error)")
            # Don't fail on network errors - validation is best-effort

    # Step 4: Check if dataset DOIs are cited in markdown
    # Normalize DOIs for comparison (case-insensitive)
    dataset_dois_lower = {doi.lower() for doi in dataset_dois}
    cited_dois_lower = {doi.lower() for doi in cited_dois}

    uncited_dois = dataset_dois_lower - cited_dois_lower

    if uncited_dois:
        print("    Dataset DOIs NOT cited in markdown:")
        for doi in sorted(uncited_dois):
            print(f"      - {doi}")
        failed = True

    # Final result
    if failed:
        if unresolved_dois:
            print(f"  FAIL: {notebook_path}")
            print(f"    - {len(unresolved_dois)} DOI(s) do not resolve")
        if uncited_dois:
            print(f"  FAIL: {notebook_path}")
            print(f"    - {len(uncited_dois)} dataset DOI(s) not cited in markdown")
            print("    Add DOI citation in markdown (e.g., https://doi.org/10.xxxx/xxxxx)")
        return "failure"
    else:
        print(f"  PASS: {notebook_path}")
        print(f"    - All {len(dataset_dois)} dataset DOI(s) are valid and cited")
        return "success"


def main():
    parser = argparse.ArgumentParser(
        description='Check for DOI citations in Jupyter notebooks'
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

    # Check if DOI check is globally disabled
    if is_check_disabled(config, 'doi'):
        print("DOI check is disabled by configuration")
        sys.exit(0)

    # Filter notebooks based on config
    notebooks = filter_notebooks(config, 'doi', args.notebooks)

    if not notebooks:
        print("All notebooks skipped by configuration")
        sys.exit(0)

    overall_result = 0

    for notebook in notebooks:
        result = check_doi(notebook)
        if result == "failure":
            overall_result = 1

    sys.exit(overall_result)


if __name__ == "__main__":
    main()
