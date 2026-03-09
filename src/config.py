from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml


class ConfigError(Exception):
    pass


def load_config(path: str | Path = "config.yaml") -> Dict[str, Any]:
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise ConfigError(f"Config file not found: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        raise ConfigError("Invalid config format")
    return config


def ensure_directories(config: Dict[str, Any]) -> None:
    for key in ["input_pdfs", "daily_json", "weekly_reports", "logs"]:
        Path(config["paths"][key]).mkdir(parents=True, exist_ok=True)
