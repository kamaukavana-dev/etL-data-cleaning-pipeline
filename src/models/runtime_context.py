from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeContext:
    run_id: str
    environment: str
    correlation_id: str
    profile: str

