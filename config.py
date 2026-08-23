"""Configuration management for TerraFish.

Presets are stored as sections in an INI file under ~/.terrafish/config.ini.
This module wraps configparser with validation, sane defaults, and a
dataclass so the rest of the app never touches configparser directly and
never has two disagreeing copies of a setting floating around.
"""
from __future__ import annotations

import configparser
import logging
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_PRESET = "Default"

CONFIG_DIR = Path.home() / ".terrafish"
CONFIG_PATH = CONFIG_DIR / "config.ini"

_LEGACY_ALIASES = {
    "threshold": "treshold",
    "sensitivity": "sensivity",
    "drink_key": "button_to_drink",
}


@dataclass
class PresetSettings:
    screen_x: int = 850
    screen_y: int = 850
    threshold: int = 6
    sensitivity: int = 55
    drink_potions: bool = False
    drink_delay: int = 185
    drink_key: str = "b"

    @classmethod
    def from_dict(cls, data: dict) -> "PresetSettings":
        defaults = cls()
        kwargs = {}
        for f in fields(cls):
            raw = data.get(f.name)
            if raw is None:
                raw = data.get(_LEGACY_ALIASES.get(f.name, ""))
            if raw is None:
                kwargs[f.name] = getattr(defaults, f.name)
                continue
            try:
                if f.type == "int":
                    kwargs[f.name] = int(raw)
                elif f.type == "bool":
                    kwargs[f.name] = str(raw).strip().lower() == "true"
                else:
                    kwargs[f.name] = str(raw)
            except (ValueError, TypeError):
                logger.warning("Invalid value %r for %s, using default", raw, f.name)
                kwargs[f.name] = getattr(defaults, f.name)
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return {k: str(v) for k, v in asdict(self).items()}


class ConfigManager:
    def __init__(self, path: Path = CONFIG_PATH):
        self.path = path
        self._parser = configparser.ConfigParser()
        self.reload()

    def reload(self) -> None:
        self._parser = configparser.ConfigParser()
        if self.path.exists():
            try:
                self._parser.read(self.path)
            except configparser.Error as exc:
                logger.error("Could not parse %s: %s", self.path, exc)
        if not self._parser.sections():
            self._parser.add_section(DEFAULT_PRESET)
            self._write()

    def preset_names(self) -> list[str]:
        return list(self._parser.sections())

    def has_preset(self, name: str) -> bool:
        return self._parser.has_section(name)

    def load(self, name: str) -> PresetSettings:
        if not self._parser.has_section(name):
            self._parser.add_section(name)
        return PresetSettings.from_dict(dict(self._parser.items(name)))

    def save(self, name: str, settings: PresetSettings) -> None:
        if not self._parser.has_section(name):
            self._parser.add_section(name)
        for key, value in settings.to_dict().items():
            self._parser.set(name, key, value)
        self._write()

    def add_preset(self, name: str, settings: Optional[PresetSettings] = None) -> None:
        if not self._parser.has_section(name):
            self._parser.add_section(name)
        for key, value in (settings or PresetSettings()).to_dict().items():
            self._parser.set(name, key, value)
        self._write()

    def rename_preset(self, old: str, new: str) -> bool:
        if old == DEFAULT_PRESET or not self._parser.has_section(old):
            return False
        if self._parser.has_section(new):
            return False
        self._parser.add_section(new)
        for key, value in self._parser.items(old):
            self._parser.set(new, key, value)
        self._parser.remove_section(old)
        self._write()
        return True

    def delete_preset(self, name: str) -> bool:
        if name == DEFAULT_PRESET or not self._parser.has_section(name):
            return False
        self._parser.remove_section(name)
        self._write()
        return True

    def _write(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w") as fh:
                self._parser.write(fh)
        except OSError as exc:
            logger.error("Could not write config to %s: %s", self.path, exc)
