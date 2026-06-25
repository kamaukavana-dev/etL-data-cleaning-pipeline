#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt >/dev/null
python -m pip check
python -m pip_audit
