from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .care import DUE, OK, OVERDUE, paginate, plant_days_left, status_of
from .config import Config, build_tasks_client, load_config
from .db import FAILED, READY, Database, Plant
from .photos import store_photo
from .providers.base import DEFAULT_INTERVAL_DAYS
from .providers.composite import SOURCE_FALLBACK, CareDataService, CareDataUnavailable
from .providers.local_json import LocalProvider
from .providers.wikipedia import WikipediaSource
from .sync import Syncer
from .tasks_client import TasksClient

log =logging.getLogger("plant_care")
APP_DIR = Path(__file__).resolve().parent


def _day_word(count: int) -> str:
    return f"{count} day{'s' if count != 1 else ''}"


def card_view(plant: Plant, today: date) -> dict:
    days = plant_days_left(plant, today)
    if days is None:
        return {"plant": plant, "loading": True, "status": "loading", "label": "Loading…"}
    status = status_of(days)
    if status == DUE:
        label = "Watering: Due today!"
    elif status == OVERDUE:
        label = f"Watering: {_day_word(-days)} overdue"
    else:
        label = f"{_day_word(days)} left"
    return {
        "plant": plant,
        "loading": False,
        "status": status,
        "label": label,
        "days": days,
        "is_due": status != OK,
    }


def create_app(
    config: Config | None = None,
    *,
    service: CareDataService | None = None,
    db: Database | None = None,
    tasks_client: TasksClient | None = None,
    clock: Callable[[], date] | None = None,
    start_scheduler: bool = True,
) -> FastAPI:
    config = config or load_config()
    clock = clock or date.today
    db = db or Database(config.db_path)
    db.init()
    db.purge_unfinished()
    if service is None:
        online = WikipediaSource() if config.online_photos else None
        service = CareDataService(LocalProvider(config.local_data_path), online)
    config.photos_dir.mkdir(parents=True, exist_ok=True)

    client = tasks_client if tasks_client is not None else build_tasks_client(config)
    syncer = Syncer(db, client, clock) if client is not None else None
    if syncer is None:
        log.warning("Google calendar reminders are not configured; the app works without them")

    scheduler = None
    if start_scheduler and syncer is not None:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            syncer.run,
            "interval",
            minutes=config.sync_interval_minutes,
            next_run_time=datetime.now(),
            max_instances=1,
            coalesce=True,
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if scheduler:
            scheduler.start()
        yield
        if scheduler:
            scheduler.shutdown(wait=False)

    app = FastAPI(title="plant_care", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
    app.mount("/photos", StaticFiles(directory=config.photos_dir), name="photos")
    templates = Jinja2Templates(directory=APP_DIR / "templates")

    def render(request: Request, template: str, headers: dict | None = None, **context):
        return templates.TemplateResponse(request, template, context, headers=headers)

    def grid(request: Request, page: int, headers: dict | None = None):
        today = clock()
        plants = db.list_plants()
        pg = paginate(len(plants), page)
        cards = [card_view(p, today) for p in plants[pg.start : pg.end]]
        return render(request, "_grid.html", headers, cards=cards, page=pg, total=len(plants))

    def details(request: Request, plant: Plant, headers: dict | None = None, watered=False):
        return render(
            request,
            "_details.html",
            headers,
            card=card_view(plant, clock()),
            watered=watered,
        )

    def ready_plant(plant_id: int) -> Plant:
        plant = db.get_plant(plant_id)
        if plant is None or plant.data_status != READY:
            raise HTTPException(status_code=404, detail="Plant not found")
        return plant

    def load_plant_data(plant_id: int, type_id: str, name: str) -> None:
        try:
            result = service.get(type_id, name)
            photo = store_photo(result.image_url, config.photos_dir, plant_id)
            source = SOURCE_FALLBACK if result.image_url and photo is None else result.source
            db.complete_plant(
                plant_id,
                photo,
                result.care.light,
                result.care.interval_days or DEFAULT_INTERVAL_DAYS,
                source,
                about=result.about,
                photo_credit=result.credit_url,
            )
            if syncer:
                syncer.run()
        except CareDataUnavailable:
            db.fail_plant(plant_id)
        except Exception:
            log.exception("Loading data for plant %s failed", plant_id)
            db.fail_plant(plant_id)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, page: int = 1):
        today = clock()
        plants = db.list_plants()
        pg = paginate(len(plants), page)
        cards = [card_view(p, today) for p in plants[pg.start : pg.end]]
        return render(request, "index.html", cards=cards, page=pg, total=len(plants))

    @app.get("/grid", response_class=HTMLResponse)
    def grid_fragment(request: Request, page: int = 1):
        return grid(request, page)

    @app.get("/add", response_class=HTMLResponse)
    def add_panel(request: Request):
        return render(request, "_add_panel.html")

    @app.get("/search", response_class=HTMLResponse)
    def search(request: Request, q: str = ""):
        return render(request, "_results.html", results=service.search(q), q=q.strip())

    @app.post("/plants", response_class=HTMLResponse)
    def add_plant(
        request: Request,
        background_tasks: BackgroundTasks,
        type_id: str = Form(...),
        name: str = Form(...),
    ):
        name = name.strip()
        if not type_id.strip() or not name:
            raise HTTPException(status_code=400, detail="A plant type is required")
        plant = db.add_plant(type_id.strip(), name, clock())
        background_tasks.add_task(load_plant_data, plant.id, plant.type_id, plant.name)
        return grid(request, page=10**9, headers={"HX-Trigger": "closeModal"})

    @app.get("/plants/{plant_id}/card", response_class=HTMLResponse)
    def card_fragment(request: Request, plant_id: int):
        plant = db.get_plant(plant_id)
        if plant is None:
            return HTMLResponse("")
        if plant.data_status == FAILED:
            db.delete_plant(plant_id)
            return render(request, "_card_failed.html", name=plant.name)
        return render(request, "_card.html", card=card_view(plant, clock()))

    @app.get("/plants/{plant_id}", response_class=HTMLResponse)
    def plant_details(request: Request, plant_id: int):
        return details(request, ready_plant(plant_id))

    @app.post("/plants/{plant_id}/watered", response_class=HTMLResponse)
    def watered(request: Request, plant_id: int, background_tasks: BackgroundTasks):
        plant = ready_plant(plant_id)
        db.mark_watered(plant.id, clock())
        if syncer:
            background_tasks.add_task(syncer.run)
        return details(
            request, db.get_plant(plant_id), headers={"HX-Trigger": "refreshGrid"}, watered=True
        )

    @app.get("/plants/{plant_id}/confirm-remove", response_class=HTMLResponse)
    def confirm_remove(request: Request, plant_id: int):
        return render(request, "_confirm_remove.html", plant=ready_plant(plant_id))

    @app.post("/plants/{plant_id}/remove", response_class=HTMLResponse)
    def remove(
        request: Request, plant_id: int, background_tasks: BackgroundTasks, page: int = Form(1)
    ):
        ready_plant(plant_id)
        db.delete_plant(plant_id)
        if syncer:
            background_tasks.add_task(syncer.run)
        return grid(request, page, headers={"HX-Trigger": "closeModal"})

    return app
