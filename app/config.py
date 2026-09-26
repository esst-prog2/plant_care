from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SYNC_INTERVAL_MINUTES = 10


@dataclass(frozen=True)
class Config:
    db_path: Path
    photos_dir: Path
    local_data_path: Path
    online_photos: bool = True
    google_script_url: str | None = None
    google_script_secret: str | None = None
    sync_interval_minutes: int = DEFAULT_SYNC_INTERVAL_MINUTES

    @property
    def google_configured(self) -> bool:
        return bool(self.google_script_url and self.google_script_secret)


def _opt(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def load_config() -> Config:
    load_dotenv(BASE_DIR / ".env")
    interval = int(_opt("SYNC_INTERVAL_MINUTES") or DEFAULT_SYNC_INTERVAL_MINUTES)
    if interval < 1:
        raise ValueError("SYNC_INTERVAL_MINUTES must be at least 1")
    return Config(
        db_path=Path(os.environ.get("PLANT_DB_PATH") or BASE_DIR / "plant_care.db"),
        photos_dir=Path(os.environ.get("PHOTOS_DIR") or BASE_DIR / "photos"),
        local_data_path=BASE_DIR / "data" / "plants.json",
        online_photos=(_opt("ONLINE_PHOTOS") or "on").lower() not in {"0", "off", "false", "no"},
        google_script_url=_opt("GOOGLE_SCRIPT_URL"),
        google_script_secret=_opt("GOOGLE_SCRIPT_SECRET"),
        sync_interval_minutes=interval,
    )


def build_tasks_client(config: Config):
    """The real Google Tasks client, or None when Google reminders are not set up."""
    if not config.google_configured:
        return None
    from .tasks_client import AppsScriptClient

    return AppsScriptClient(config.google_script_url, config.google_script_secret)
