## c3s-reusable workflows

This repository contains reusable GitHub Actions workflows for C3S projects. There is currently one CI workflow for Jupyter Notebook QA automation.


### notebook-qa

This workflow implements QA automation for Jupyter Notebooks. The checks below run automatically — all checks that are not skipped or disabled must pass for the workflow to succeed.

#### Checks

**Code linting** (`linter`) — Runs `ruff check` via `nbqa` on all code cells. No Python lint violations allowed.

**Code formatting** (`formatter`) — Runs `ruff format --check` via `nbqa`. Code cells must conform to `ruff` formatting rules.

**Notebook linting** (`pynblint`) — Runs `pynblint` on each notebook. Checks notebook-level quality issues such as non-linear execution order, empty cells, or untitled notebooks.

**DOI citation** (`doi`) — Checks that dataset DOIs found in code cell outputs are valid and cited. Notebooks must be committed with outputs for this check to work. Each DOI must resolve via `doi.org` and appear in at least one markdown cell. Skipped if no dataset DOI metadata is found in outputs.

**Link availability** (`links`) — Runs `lychee` against all notebooks. Every URL in markdown and code cells must be reachable.

**Notebook execution** (`execute`) — Executes each notebook end-to-end with `ploomber-engine`. The notebook must run without errors. Memory usage and runtime are profiled per cell and uploaded as an artifact.

**Version metadata** (`metadata`) — Looks for `**Last updated:** YYYY-MM-DD` (e.g. `**Last updated:** 2025-01-15`) in the first markdown cell(s) before any code cell. Falls back to a `README.md` in the same directory if not found in the notebook.

**Tests & coverage** (`tests`) — If test files exist (`test_*.py`, `*_test.py`, `tests/*.py`), runs `pytest` with coverage. Coverage must meet the configured threshold (default 80%). When no test files exist the check passes by default, unless `require_tests: true` is set in the config.

**Accessibility** (`accessibility`) — Runs WCAG compliance checks on notebooks using `jupyterlab-a11y-checker`.

**Figure attribution** (`figures`) — Every figure output (PNG/JPEG) in code cells must have source attribution in a nearby markdown cell (within 2 cells). Recognized attribution patterns include `source:`, `credit:`, `data from:`, `attribution:`, `reference:`, `dataset:`, a DOI, or a URL.

**License file** (`license`) — A non-empty `LICENSE` file must exist in the repository root.

**Changelog file** (`changelog`) — A non-empty `CHANGELOG.md` file must exist in the repository root.

#### How to use `notebook-qa.yml` workflow

Configure the target repository which you want to run the QA check against using this format:

```
.github/workflows/qa.yml

------------------------

name: Notebook QA

on:
  push:
    branches:
      - develop
  pull_request:
    branches:
      - develop
  workflow_dispatch:
    inputs:
      notebooks:
        description: 'Comma-separated list of notebook paths to check (e.g., ./notebook1.ipynb,./folder/notebook2.ipynb). Leave empty to check all notebooks.'
        required: false
        type: string
        default: ''

jobs:
  notebook-qa:
    uses: recmanj-org/c3s-reusable-workflows/.github/workflows/notebook-qa.yml@main
    with:
      notebooks: ${{ inputs.notebooks || '' }}
    secrets: inherit
```

This sets up automated checks on new pull requests and merges/pushes into `develop` branch. It also allows manual Action runs in the GitHub Actions UI.


#### Configuration

You can customize check behavior by adding a `.github/notebook-qa.yml` config file in the consuming repository:

```yaml
# Globally disable specific checks
disabled_checks:
  - linter
  - formatter

# Notebooks to skip entirely (all checks), supports glob patterns
skip_notebooks:
  - "notebooks/draft.ipynb"
  - "notebooks/experimental/**"

# Per-notebook check configuration
notebooks:
  "notebooks/example.ipynb":
    skip:
      - doi
      - figures

# Test configuration
require_tests: false     # Set true to fail when no test files exist
coverage_threshold: 80   # Minimum coverage percentage for pytest-cov

# Pynblint rule configuration
pynblint:
  exclude:                    # Additional rules to suppress (extends baseline)
    - untitled-notebook
  exclude_mode: extend        # "extend" (default) or "override"
```

The baseline pynblint exclusion list suppresses `missing-h1-MD-heading` (MyST notebooks use YAML frontmatter for titles). In `extend` mode (default), your `exclude` list is merged with the baseline. In `override` mode, your list fully replaces the baseline.

Available pynblint rule slugs: `non-linear-execution`, `notebook-too-long`, `untitled-notebook`, `non-portable-chars-in-nb-name`, `notebook-name-too-long`, `imports-beyond-first-cell`, `missing-h1-MD-heading`, `missing-opening-MD-text`, `missing-closing-MD-text`, `too-few-MD-cells`, `duplicate-notebook-not-renamed`, `invalid-python-syntax`, `non-executed-notebook`, `non-executed-cells`, `empty-cells`, `long-multiline-python-comment`, `cell-too-long`

Valid check IDs: `linter`, `formatter`, `pynblint`, `links`, `tests`, `doi`, `figures`, `metadata`, `accessibility`, `license`, `changelog`, `execute`


#### QA criteria reference

| ID    | Description               | Tool / Check           |
|-------|---------------------------|------------------------|
| 1.2.3 | Link availability         | lychee                 |
| 1.2.4 | License file              | LICENSE existence       |
| 1.2.5 | DOI citation              | doi_checker.py         |
| 1.2.6 | Version metadata          | metadata_checker.py    |
| 2.2.1 | Code execution            | ploomber-engine        |
| 2.2.3 | Code style                | ruff, pynblint         |
| 2.2.4 | Execution profiling       | ploomber-engine        |
| 2.2.6 | Memory profiling          | ploomber-engine        |
| 2.3.1 | Test existence            | pytest                 |
| 2.3.2 | Coverage threshold        | pytest-cov             |
| 3.1.3 | Accessibility             | jupyterlab-a11y-checker|
| 3.3.2 | Figure attribution        | figure_checker.py      |
| 4.2.3 | Changelog                 | CHANGELOG.md existence |


### How to configure access to cdsapi for notebook execution check

The action responsible for notebook execution allows setting a `cdsapi` key via `CDSAPI_KEY` secret set either on repository or organisation level.


### How to setup c3s-reusable-workflows repository in GitHub organisation

1. Fork this repository into your organisation
2. Leave the fork network in the newly forked repository settings
