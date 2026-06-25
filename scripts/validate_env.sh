#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Environment file not found: ${ENV_FILE}" >&2
  exit 1
fi

required_keys=("DATA_FILE")
for key in "${required_keys[@]}"; do
  if ! grep -q "^${key}=" "${ENV_FILE}"; then
    echo "Missing required key in ${ENV_FILE}: ${key}" >&2
    exit 1
  fi
done

if grep -Eiq "SMTP_PASSWORD=(changeme|password|secret)$" "${ENV_FILE}"; then
  echo "Refusing weak placeholder SMTP password value in ${ENV_FILE}" >&2
  exit 1
fi

echo "Environment validation passed for ${ENV_FILE}"
