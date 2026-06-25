from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - depends on runtime image
    yaml = None

from src.core.constants import (
    DEFAULT_ALERT_THRESHOLDS,
    DEFAULT_DROP_RATE_THRESHOLDS,
    DEFAULT_SEVERITY_LABELS,
)
from src.core.exceptions import ConfigurationError


class ThresholdsService:
    def __init__(self, thresholds_file: Path) -> None:
        self.thresholds_file = thresholds_file

    def load(self) -> dict[str, Any]:
        if yaml is None:
            return self._defaults()
        if not self.thresholds_file.exists():
            return self._defaults()
        if not self.thresholds_file.is_file():
            raise ConfigurationError(
                "Threshold configuration path is not a file.",
                error_code="CFG_THRESHOLDS_PATH_INVALID",
                context={"attempted_path": str(self.thresholds_file)},
            )
        try:
            with self.thresholds_file.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except yaml.YAMLError as exc:
            raise ConfigurationError(
                "Threshold configuration is malformed YAML.",
                error_code="CFG_THRESHOLDS_MALFORMED",
                context={"attempted_path": str(self.thresholds_file)},
            ) from exc
        except OSError as exc:
            raise ConfigurationError(
                "Threshold configuration could not be read.",
                error_code="CFG_THRESHOLDS_READ_FAILED",
                context={"attempted_path": str(self.thresholds_file)},
            ) from exc

        merged = self._defaults()
        merged_thresholds = merged["thresholds"]
        user_thresholds = data.get("thresholds", {})

        for key in ("drop_rate", "alerts", "severity_labels"):
            user_section = user_thresholds.get(key, {})
            if isinstance(user_section, dict):
                merged_thresholds[key].update(user_section)

        return merged

    @staticmethod
    def _defaults() -> dict[str, Any]:
        return {
            "thresholds": {
                "drop_rate": dict(DEFAULT_DROP_RATE_THRESHOLDS),
                "alerts": dict(DEFAULT_ALERT_THRESHOLDS),
                "severity_labels": dict(DEFAULT_SEVERITY_LABELS),
            }
        }
