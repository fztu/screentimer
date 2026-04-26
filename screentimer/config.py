import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@dataclass
class AppConfig:
    lock_interval_mins: int
    auto_unlock_mins: int
    password_hash: str

    def check_password(self, password: str) -> bool:
        return hash_password(password) == self.password_hash


class ConfigStore:
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            appdata = Path(os.environ.get("APPDATA", str(Path.home())))
            config_dir = appdata / "ScreenTimer"
        self._path = Path(config_dir) / "config.json"

    def load(self) -> Optional[AppConfig]:
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return AppConfig(
                lock_interval_mins=data["lock_interval_mins"],
                auto_unlock_mins=data["auto_unlock_mins"],
                password_hash=data["password_hash"],
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
            }, indent=2),
            encoding="utf-8",
        )
