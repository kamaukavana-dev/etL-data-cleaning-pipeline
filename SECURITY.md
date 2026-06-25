# Security Policy

## Secret management

Do not commit real secrets to this repository.

- `.env` is local-only and ignored by git.
- `.env.example` is safe template only.
- Docker build context excludes `.env` files via `.dockerignore`.

Production secrets must be injected at runtime from a managed secret system:

- HashiCorp Vault
- AWS Secrets Manager
- GCP Secret Manager

## Responsible disclosure

If you discover a vulnerability, report it privately to the maintainers and avoid public disclosure until remediation is complete.

## Security controls in this repository

- Bandit static security analysis in CI.
- pip-audit dependency vulnerability scanning in CI.
- Non-root container runtime.
- Structured logging without secret values.
