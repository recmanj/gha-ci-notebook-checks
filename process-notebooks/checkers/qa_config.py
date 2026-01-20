#!/usr/bin/env python3
"""
QA Configuration Parser for Notebook Checks

Loads and parses .github/notebook-qa.yml configuration file to support
disabling specific checks globally, per-notebook, or skipping notebooks entirely.

Config file format:
    # .github/notebook-qa.yml

    # Globally disable specific checks (applies to all notebooks)
    disabled_checks:
      - linter
      - formatter

    # Notebooks to skip entirely (all checks)
    skip_notebooks:
      - "notebooks/draft.ipynb"
      - "notebooks/experimental/**"  # glob patterns supported

    # Per-notebook check configuration
    notebooks:
      "notebooks/example.ipynb":
        skip:
          - doi
          - figures
"""

import os
from fnmatch import fnmatch
from typing import Any

# Optional YAML import - falls back gracefully if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_config(config_path: str = ".github/notebook-qa.yml") -> dict[str, Any]:
    """
    Load QA configuration from YAML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Configuration dictionary, or empty dict if file doesn't exist
    """
    if not os.path.exists(config_path):
        return {}

    if not HAS_YAML:
        print(f"Warning: PyYAML not installed, cannot load {config_path}")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except Exception as e:
        print(f"Warning: Failed to load {config_path}: {e}")
        return {}


def is_check_disabled(config: dict[str, Any], check_id: str) -> bool:
    """
    Check if a specific check is globally disabled.

    Args:
        config: Configuration dictionary
        check_id: Check identifier (e.g., 'linter', 'doi', 'figures')

    Returns:
        True if check is globally disabled, False otherwise
    """
    disabled_checks = config.get('disabled_checks', [])
    return check_id in disabled_checks


def is_notebook_skipped(config: dict[str, Any], notebook: str) -> bool:
    """
    Check if a notebook should be skipped entirely (all checks).

    Args:
        config: Configuration dictionary
        notebook: Path to the notebook file

    Returns:
        True if notebook should be skipped, False otherwise
    """
    skip_patterns = config.get('skip_notebooks', [])
    for pattern in skip_patterns:
        if fnmatch(notebook, pattern):
            return True
    return False


def is_check_skipped_for_notebook(
    config: dict[str, Any], check_id: str, notebook: str
) -> bool:
    """
    Check if a specific check should be skipped for a specific notebook.

    Args:
        config: Configuration dictionary
        check_id: Check identifier
        notebook: Path to the notebook file

    Returns:
        True if check should be skipped for this notebook, False otherwise
    """
    per_notebook = config.get('notebooks', {})
    for pattern, settings in per_notebook.items():
        if fnmatch(notebook, pattern):
            skip_checks = settings.get('skip', [])
            if check_id in skip_checks:
                return True
    return False


def filter_notebooks(
    config: dict[str, Any], check_id: str, notebooks: list[str]
) -> list[str]:
    """
    Filter a list of notebooks based on configuration.

    Removes notebooks that should be skipped either:
    - Entirely (via skip_notebooks)
    - For this specific check (via per-notebook skip)

    Note: Does NOT check if the check is globally disabled.
          Use is_check_disabled() separately for that.

    Args:
        config: Configuration dictionary
        check_id: Check identifier
        notebooks: List of notebook paths

    Returns:
        Filtered list of notebooks that should be checked
    """
    result = []
    for notebook in notebooks:
        # Skip if notebook matches skip_notebooks patterns
        if is_notebook_skipped(config, notebook):
            continue

        # Skip if per-notebook config says skip this check
        if is_check_skipped_for_notebook(config, check_id, notebook):
            continue

        result.append(notebook)

    return result


def get_filtered_notebooks_for_check(
    config: dict[str, Any], check_id: str, notebooks: list[str]
) -> tuple[bool, list[str]]:
    """
    Get filtered notebooks for a check, including global disable check.

    This is a convenience function that combines is_check_disabled()
    and filter_notebooks() for typical use cases.

    Args:
        config: Configuration dictionary
        check_id: Check identifier
        notebooks: List of notebook paths

    Returns:
        Tuple of (should_skip_entirely, filtered_notebooks)
        - should_skip_entirely: True if check is globally disabled
        - filtered_notebooks: List of notebooks to check (empty if skipped)
    """
    if is_check_disabled(config, check_id):
        return (True, [])

    filtered = filter_notebooks(config, check_id, notebooks)
    return (False, filtered)
