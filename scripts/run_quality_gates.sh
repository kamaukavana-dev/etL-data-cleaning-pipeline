#!/usr/bin/env bash
set -euo pipefail

ruff check src tests
black --check src tests
mypy src tests
pytest
bandit -r src -x tests
pip-audit -r requirements.txt
