import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@dataclass
class AppConfig:
    lock_interval_mins: int
    auto_unlock_mins: int
    password_hash: str
    daily_limit_mins: int = 0

    def check_password(self, password: str) -> bool:
        return hash_password(password) == self.password_hash


class ConfigStore:
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            if sys.platform == "win32":
                appdata = Path(os.environ.get("APPDATA", str(Path.home())))
                config_dir = appdata / "ScreenTimer"
            elif sys.platform == "darwin":
                config_dir = Path.home() / "Library" / "Application Support" / "ScreenTimer"
            else:
                xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
                config_dir = Path(xdg) / "ScreenTimer"
        self._path = Path(config_dir) / "config.json"
        self._usage_path = Path(config_dir) / "daily_usage.json"

    def load(self) -> Optional[AppConfig]:
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return AppConfig(
                lock_interval_mins=data["lock_interval_mins"],
                auto_unlock_mins=data["auto_unlock_mins"],
                password_hash=data["password_hash"],
                daily_limit_mins=data.get("daily_limit_mins", 0),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def save(self, config: AppConfig) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({
                "lock_interval_mins": config.lock_interval_mins,
                "auto_unlock_mins": config.auto_unlock_mins,
                "password_hash": config.password_hash,
                "daily_limit_mins": config.daily_limit_mins,
            }, indent=2),
            encoding="utf-8",
        )

    def load_daily_used_secs(self) -> int:
        """Returns accumulated active seconds for today; resets if the date changed."""
        if not self._usage_path.exists():
            return 0
        try:
            data = json.loads(self._usage_path.read_text(encoding="utf-8"))
            if data.get("date") == str(date.today()):
                return int(data.get("used_secs", 0))
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        return 0

    def save_daily_used_secs(self, used_secs: int) -> None:
        self._usage_path.parent.mkdir(parents=True, exist_ok=True)
        self._usage_path.write_text(
            json.dumps({"date": str(date.today()), "used_secs": used_secs}, indent=2),
            encoding="utf-8",
        )
