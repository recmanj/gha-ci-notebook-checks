#!/usr/bin/env python3
"""Shared utilities for notebook QA checkers."""

import json


def read_notebook(notebook_path: str) -> dict:
    """Read and parse a Jupyter notebook file."""
    with open(notebook_path, encoding="utf-8") as f:
        return json.load(f)


def extract_cell_source(cell: dict) -> str:
    """Extract source code/markdown from a cell as a single string."""
    source = cell.get("source", [])
    if isinstance(source, list):
        return "".join(source)
    return str(source)
