"""load_config() reads real environment variables; every other test fakes a Config
object instead of calling it, so this is the only place that logic is exercised."""

import pytest

from app import config as config_module
from app.config import DEFAULT_SYNC_INTERVAL_MINUTES, build_tasks_client, load_config
from app.tasks_client import AppsScriptClient

_ENV_KEYS = [
    "PLANT_DB_PATH",
    "PHOTOS_DIR",
    "ONLINE_PHOTOS",
    "GOOGLE_SCRIPT_URL",
    "GOOGLE_SCRIPT_SECRET",
    "SYNC_INTERVAL_MINUTES",
]


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Never let this touch the real project .env: point BASE_DIR at an empty
    directory (so load_dotenv finds nothing there) and clear every relevant
    OS environment variable first."""
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(config_module, "BASE_DIR", tmp_path)
    return tmp_path


def test_defaults_with_nothing_set(isolated_config):
    cfg = load_config()
    assert cfg.db_path == isolated_config / "plant_care.db"
    assert cfg.photos_dir == isolated_config / "photos"
    assert cfg.local_data_path == isolated_config / "data" / "plants.json"
    assert cfg.online_photos is True
    assert cfg.google_script_url is None
    assert cfg.google_script_secret is None
    assert cfg.google_configured is False
    assert cfg.sync_interval_minutes == DEFAULT_SYNC_INTERVAL_MINUTES


def test_db_and_photos_paths_can_be_overridden(monkeypatch, tmp_path):
    db = tmp_path / "custom.db"
    photos = tmp_path / "pics"
    monkeypatch.setenv("PLANT_DB_PATH", str(db))
    monkeypatch.setenv("PHOTOS_DIR", str(photos))
    cfg = load_config()
    assert cfg.db_path == db and cfg.photos_dir == photos


@pytest.mark.parametrize("value", ["off", "OFF", "0", "false", "False", "no"])
def test_online_photos_can_be_turned_off(monkeypatch, value):
    monkeypatch.setenv("ONLINE_PHOTOS", value)
    assert load_config().online_photos is False


@pytest.mark.parametrize("value", ["on", "ON", "1", "true", "yes", ""])
def test_online_photos_stays_on_otherwise(monkeypatch, value):
    monkeypatch.setenv("ONLINE_PHOTOS", value)
    assert load_config().online_photos is True


def test_google_is_configured_only_when_both_url_and_secret_are_set(monkeypatch):
    monkeypatch.setenv("GOOGLE_SCRIPT_URL", "https://script.google.com/macros/s/x/exec")
    assert load_config().google_configured is False  # secret still missing
    monkeypatch.setenv("GOOGLE_SCRIPT_SECRET", "s3cret")
    assert load_config().google_configured is True


def test_sync_interval_can_be_overridden(monkeypatch):
    monkeypatch.setenv("SYNC_INTERVAL_MINUTES", "3")
    assert load_config().sync_interval_minutes == 3


def test_sync_interval_below_one_is_rejected(monkeypatch):
    monkeypatch.setenv("SYNC_INTERVAL_MINUTES", "0")
    with pytest.raises(ValueError, match="at least 1"):
        load_config()


def test_sync_interval_must_be_a_number(monkeypatch):
    monkeypatch.setenv("SYNC_INTERVAL_MINUTES", "soon")
    with pytest.raises(ValueError):
        load_config()


def test_build_tasks_client_is_none_when_google_is_not_configured():
    assert build_tasks_client(load_config()) is None


def test_build_tasks_client_builds_a_real_client_when_configured(monkeypatch):
    monkeypatch.setenv("GOOGLE_SCRIPT_URL", "https://script.google.com/macros/s/x/exec")
    monkeypatch.setenv("GOOGLE_SCRIPT_SECRET", "s3cret")
    client = build_tasks_client(load_config())
    assert isinstance(client, AppsScriptClient)
