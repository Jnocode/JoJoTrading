"""Compatibility configuration loader for legacy tests."""

from __future__ import annotations

from typing import Any, Dict


class ConfigLoader:
    """Minimal config facade used by legacy verification scripts."""

    def __init__(self) -> None:
        self.config: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Return a config value or default."""
        return self.config.get(key, default)
