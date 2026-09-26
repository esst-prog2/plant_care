from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.config import BASE_DIR, Config
from app.db import Database
from app.main import create_app
from app.providers.composite import CareDataService
from app.providers.local_json import LocalProvider
from tests.fakes import FakeTasksClient

TODAY = date(2026, 9, 10)


class Clock:
    def __init__(self, today: date = TODAY):
        self.today = today

    def __call__(self) -> date:
        return self.today


@pytest.fixture
def config(tmp_path) -> Config:
    return Config(
        db_path=tmp_path / "test.db",
        photos_dir=tmp_path / "photos",
        local_data_path=BASE_DIR / "data" / "plants.json",
    )


@pytest.fixture
def db(config) -> Database:
    database = Database(config.db_path)
    database.init()
    return database


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def tasks() -> FakeTasksClient:
    return FakeTasksClient()


@pytest.fixture
def make_client(config, db, clock):
    def factory(service: CareDataService | None = None, tasks_client=None) -> TestClient:
        service = service or CareDataService(LocalProvider(config.local_data_path))
        app = create_app(
            config,
            service=service,
            db=db,
            tasks_client=tasks_client,
            clock=clock,
            start_scheduler=False,
        )
        return TestClient(app)

    return factory


@pytest.fixture
def client(make_client) -> TestClient:
    return make_client()


def add_ready(db: Database, name="Monstera", interval=7, watered: date = TODAY, source="local"):
    """Insert a fully loaded plant that was last watered on `watered`."""
    plant = db.add_plant(f"local:{name.lower()}", name, watered)
    db.complete_plant(plant.id, "/static/placeholder.svg", "Bright light", interval, source)
    return db.get_plant(plant.id)
