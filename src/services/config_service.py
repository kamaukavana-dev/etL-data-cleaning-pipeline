"""
Backward-compatible wrapper around threshold loading.
"""

from pathlib import Path
from typing import Any

from src.core.config import load_config
from src.services.thresholds_service import ThresholdsService


class ConfigService:
    def __init__(self, config_path: Path | None = None):
        config, _ = load_config()
        self.config_path = config_path or config.paths.thresholds_file
        self._loader = ThresholdsService(self.config_path)
        self.config: dict[str, Any] = self._loader.load()

    def get_thresholds(self) -> dict[str, Any]:
        return self.config.get("thresholds", {})
