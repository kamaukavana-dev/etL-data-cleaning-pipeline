from __future__ import annotations

from src.core.config import AppConfig, bootstrap_filesystem, diagnostics, load_config


def bootstrap_runtime() -> tuple[AppConfig, dict[str, object]]:
    """Explicit startup lifecycle: config load -> filesystem bootstrap -> diagnostics payload."""
    config, warnings = load_config()
    bootstrap_filesystem(config)
    return config, diagnostics(config, warnings)

