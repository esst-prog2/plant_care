from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .care import DUE, OK, OVERDUE, adjust_for_feedback, paginate, plant_days_left, starting_interval, status_of
from .config import Config, build_tasks_client, load_config
from .db import ALL_GROUP_NAME_KEY, FAILED, READY, Database, Plant
from .photos import store_photo, store_uploaded_photo
from .providers.composite import CareDataService, CareDataUnavailable, resolve_source
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
    # Cache-busts /static/style.css so a browser that cached an older version (e.g. from
    # before a restart) always picks up the current one instead of a stale copy.
    templates.env.globals["asset_version"] = int((APP_DIR / "static" / "style.css").stat().st_mtime)

    def render(request: Request, template: str, headers: dict | None = None, **context):
        return templates.TemplateResponse(request, template, context, headers=headers)

    def _parse_view_group_id(view_group_id: str) -> int | None:
        return None if view_group_id == "all" else int(view_group_id)

    def grid(request: Request, page: int, view_group_id: str = "all", headers: dict | None = None):
        today = clock()
        plants = db.list_plants(group_id=_parse_view_group_id(view_group_id))
        pg = paginate(len(plants), page)
        cards = [card_view(p, today) for p in plants[pg.start : pg.end]]
        return render(
            request, "_grid.html", headers, cards=cards, page=pg, total=len(plants), view_group_id=view_group_id
        )

    def _cover_photo(group_id: int | None) -> str:
        plants = db.list_plants(group_id=group_id)
        return (plants[0].photo if plants else None) or "/static/placeholder.svg"

    def _due_count(plants: list[Plant]) -> int:
        today = clock()
        due = 0
        for p in plants:
            days = plant_days_left(p, today)
            if days is not None and status_of(days) != OK:
                due += 1
        return due

    def groups_grid(request: Request, headers: dict | None = None):
        groups = db.list_groups()
        group_cards = [
            (g, len(plants := db.list_plants(group_id=g.id)), _cover_photo(g.id), _due_count(plants))
            for g in groups
        ]
        all_plants = db.list_plants()
        return render(
            request,
            "_groups_grid.html",
            headers,
            group_cards=group_cards,
            all_count=len(all_plants),
            all_name=db.get_setting(ALL_GROUP_NAME_KEY, "All"),
            all_cover=_cover_photo(None),
            all_due=_due_count(all_plants),
        )

    def details(request: Request, plant: Plant, headers: dict | None = None, photo_error: str | None = None):
        return render(
            request,
            "_details.html",
            headers,
            card=card_view(plant, clock()),
            photo_error=photo_error,
            groups=db.list_groups(),
        )

    def watered_popup(request: Request, plant: Plant, headers: dict | None = None, feedback_done=False):
        days = card_view(plant, clock())["days"]
        return render(
            request, "_watered.html", headers, plant_id=plant.id, days=days, feedback_done=feedback_done
        )

    def ready_plant(plant_id: int) -> Plant:
        plant = db.get_plant(plant_id)
        if plant is None or plant.data_status != READY:
            raise HTTPException(status_code=404, detail="Plant not found")
        return plant

    def load_plant_data(
        plant_id: int,
        type_id: str,
        name: str,
        light_delta: int = 0,
        warmth_delta: int = 0,
        pot_delta: int = 0,
    ) -> None:
        try:
            result = service.get(type_id, name)
            photo = store_photo(result.image_url, config.photos_dir, plant_id)
            source = resolve_source(result.source, result.image_url, photo)
            interval = starting_interval(result.care.interval_days, light_delta, warmth_delta, pot_delta)
            db.complete_plant(
                plant_id,
                photo,
                result.care.light,
                interval,
                source,
                about=result.about,
                photo_credit=result.credit_url,
                toxicity=result.care.toxicity,
                humidity=result.care.humidity,
                propagation=result.care.propagation,
            )
            if syncer:
                syncer.run()
        except CareDataUnavailable:
            db.fail_plant(plant_id)
        except Exception:
            log.exception("Loading data for plant %s failed", plant_id)
            db.fail_plant(plant_id)

    @app.get("/", response_class=HTMLResponse)
    def landing(request: Request):
        groups = db.list_groups()
        group_cards = [
            (g, len(plants := db.list_plants(group_id=g.id)), _cover_photo(g.id), _due_count(plants))
            for g in groups
        ]
        all_plants = db.list_plants()
        return render(
            request,
            "index.html",
            group_cards=group_cards,
            all_count=len(all_plants),
            all_name=db.get_setting(ALL_GROUP_NAME_KEY, "All"),
            all_cover=_cover_photo(None),
            all_due=_due_count(all_plants),
        )

    def collection_view(request: Request, view_group_id: str, page: int = 1):
        today = clock()
        group_id = _parse_view_group_id(view_group_id)
        plants = db.list_plants(group_id=group_id)
        pg = paginate(len(plants), page)
        cards = [card_view(p, today) for p in plants[pg.start : pg.end]]
        return render(
            request,
            "collection.html",
            cards=cards,
            page=pg,
            total=len(plants),
            view_group_id=view_group_id,
            current_group_id=group_id,
            groups=db.list_groups(),
            all_name=db.get_setting(ALL_GROUP_NAME_KEY, "All"),
        )

    @app.get("/groups/new", response_class=HTMLResponse)
    def new_group_panel(request: Request):
        return render(request, "_new_group.html")

    @app.get("/groups/all", response_class=HTMLResponse)
    def collection_all(request: Request, page: int = 1):
        return collection_view(request, "all", page)

    @app.post("/groups", response_class=HTMLResponse)
    def create_group(request: Request, name: str = Form(...)):
        name = name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="A group name is required")
        db.create_group(name)
        return groups_grid(request, headers={"HX-Trigger": "closeModal"})

    @app.get("/groups/all/edit", response_class=HTMLResponse)
    def edit_all_group(request: Request):
        return render(
            request, "_edit_group.html", rename_url="/groups/all/rename",
            current_name=db.get_setting(ALL_GROUP_NAME_KEY, "All"),
        )

    @app.post("/groups/all/rename", response_class=HTMLResponse)
    def rename_all_group(request: Request, name: str = Form(...)):
        name = name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="A group name is required")
        db.set_setting(ALL_GROUP_NAME_KEY, name)
        return groups_grid(request, headers={"HX-Trigger": "closeModal"})

    @app.get("/groups/{group_id}", response_class=HTMLResponse)
    def collection_group(request: Request, group_id: int, page: int = 1):
        if db.get_group(group_id) is None:
            raise HTTPException(status_code=404, detail="Group not found")
        return collection_view(request, str(group_id), page)

    @app.get("/groups/{group_id}/edit", response_class=HTMLResponse)
    def edit_group(request: Request, group_id: int):
        group = db.get_group(group_id)
        if group is None:
            raise HTTPException(status_code=404, detail="Group not found")
        return render(
            request, "_edit_group.html", rename_url=f"/groups/{group_id}/rename", current_name=group.name
        )

    @app.post("/groups/{group_id}/rename", response_class=HTMLResponse)
    def rename_group(request: Request, group_id: int, name: str = Form(...)):
        name = name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="A group name is required")
        db.rename_group(group_id, name)
        return groups_grid(request, headers={"HX-Trigger": "closeModal"})

    @app.get("/groups/{group_id}/confirm-delete", response_class=HTMLResponse)
    def confirm_delete_group(request: Request, group_id: int):
        group = db.get_group(group_id)
        if group is None:
            raise HTTPException(status_code=404, detail="Group not found")
        return render(request, "_confirm_delete_group.html", group=group)

    @app.post("/groups/{group_id}/delete", response_class=HTMLResponse)
    def delete_group(request: Request, group_id: int):
        db.delete_group(group_id)
        return groups_grid(request, headers={"HX-Trigger": "closeModal"})

    @app.get("/grid", response_class=HTMLResponse)
    def grid_fragment(request: Request, page: int = 1, view_group_id: str = "all"):
        return grid(request, page, view_group_id)

    @app.get("/add", response_class=HTMLResponse)
    def add_panel(request: Request, view_group_id: str = "all"):
        return render(request, "_add_panel.html", view_group_id=view_group_id)

    @app.get("/search", response_class=HTMLResponse)
    def search(request: Request, q: str = "", view_group_id: str = "all"):
        return render(request, "_results.html", results=service.search(q), q=q.strip(), view_group_id=view_group_id)

    @app.get("/plants/confirm", response_class=HTMLResponse)
    def confirm_add(request: Request, type_id: str, name: str, view_group_id: str = "all"):
        return render(
            request,
            "_confirm_add.html",
            type_id=type_id,
            name=name,
            view_group_id=view_group_id,
            groups=db.list_groups(),
        )

    @app.post("/plants", response_class=HTMLResponse)
    def add_plant(
        request: Request,
        background_tasks: BackgroundTasks,
        type_id: str = Form(...),
        name: str = Form(...),
        light_delta: int = Form(0),
        warmth_delta: int = Form(0),
        pot_delta: int = Form(0),
        group_id: str = Form(""),
        view_group_id: str = Form("all"),
    ):
        name = name.strip()
        if not type_id.strip() or not name:
            raise HTTPException(status_code=400, detail="A plant type is required")
        plant = db.add_plant(
            type_id.strip(), name, clock(), group_id=int(group_id) if group_id else None
        )
        background_tasks.add_task(
            load_plant_data, plant.id, plant.type_id, plant.name, light_delta, warmth_delta, pot_delta
        )
        return grid(request, page=10**9, view_group_id=view_group_id, headers={"HX-Trigger": "closeModal"})

    @app.post("/plants/{plant_id}/group", response_class=HTMLResponse)
    def change_plant_group(request: Request, plant_id: int, group_id: str = Form("")):
        ready_plant(plant_id)
        db.set_plant_group(plant_id, int(group_id) if group_id else None)
        return details(request, db.get_plant(plant_id), headers={"HX-Trigger": "refreshGrid"})

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

    @app.post("/plants/{plant_id}/photo", response_class=HTMLResponse)
    async def upload_photo(request: Request, plant_id: int, photo: UploadFile = File(...)):
        plant = ready_plant(plant_id)
        content = await photo.read()
        stored = store_uploaded_photo(content, photo.content_type or "", config.photos_dir, plant_id)
        if stored is None:
            return details(
                request, plant, photo_error="That file couldn't be used as a photo (unsupported type or too large)."
            )
        # A re-upload can reuse the same filename (same extension as before), so a cache-busting
        # suffix is needed or the browser keeps showing the old image from its cache.
        db.set_custom_photo(plant_id, f"{stored}?v={secrets.token_hex(4)}")
        return details(request, db.get_plant(plant_id), headers={"HX-Trigger": "refreshGrid"})

    @app.post("/plants/{plant_id}/watered", response_class=HTMLResponse)
    def watered(request: Request, plant_id: int, background_tasks: BackgroundTasks):
        plant = ready_plant(plant_id)
        db.mark_watered(plant.id, clock())
        if syncer:
            background_tasks.add_task(syncer.run)
        return watered_popup(
            request, db.get_plant(plant_id), headers={"HX-Trigger": "refreshGrid"}
        )

    @app.post("/plants/{plant_id}/feedback", response_class=HTMLResponse)
    def feedback(
        request: Request,
        plant_id: int,
        background_tasks: BackgroundTasks,
        choice: str | None = Form(None),
    ):
        plant = ready_plant(plant_id)
        db.update_interval(plant.id, adjust_for_feedback(plant.interval_days, choice))
        if syncer:
            background_tasks.add_task(syncer.run)
        return watered_popup(
            request, db.get_plant(plant_id), headers={"HX-Trigger": "refreshGrid"}, feedback_done=True
        )

    @app.get("/plants/{plant_id}/confirm-remove", response_class=HTMLResponse)
    def confirm_remove(request: Request, plant_id: int):
        return render(request, "_confirm_remove.html", plant=ready_plant(plant_id))

    @app.post("/plants/{plant_id}/remove", response_class=HTMLResponse)
    def remove(
        request: Request,
        plant_id: int,
        background_tasks: BackgroundTasks,
        page: int = Form(1),
        view_group_id: str = Form("all"),
    ):
        ready_plant(plant_id)
        db.delete_plant(plant_id)
        if syncer:
            background_tasks.add_task(syncer.run)
        return grid(request, page, view_group_id=view_group_id, headers={"HX-Trigger": "closeModal"})

    return app
