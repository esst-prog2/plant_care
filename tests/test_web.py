import re
from datetime import timedelta
from pathlib import Path

from app.main import create_app
from tests.conftest import TODAY, add_ready


def _add(client, type_id="local:monstera", name="Monstera"):
    return client.post("/plants", data={"type_id": type_id, "name": name})


def _card_count(html: str) -> int:
    return len(re.findall(r'<article class="card', html))


def _page_value(html: str) -> int:
    return int(re.search(r'id="page-input" name="page" value="(\d+)"', html).group(1))


# --- homepage and grid -----------------------------------------------------------------


def test_empty_homepage_still_offers_add_button(client):
    html = client.get("/").text
    assert "+ Add New Plant" in html and "No plants yet" in html
    assert _card_count(html) == 0 and "Page 1 of" not in html


def test_six_plants_fill_the_grid_without_page_controls(client, db):
    for i in range(6):
        add_ready(db, f"Plant{i}")
    html = client.get("/").text
    assert _card_count(html) == 6 and 'class="pager"' not in html


def test_seven_plants_are_paged_six_and_one(client, db):
    for i in range(7):
        add_ready(db, f"Plant{i}")
    page1 = client.get("/grid?page=1").text
    page2 = client.get("/grid?page=2").text
    assert _card_count(page1) == 6 and "Page 1 of 2" in page1
    assert _card_count(page2) == 1 and "Plant6" in page2 and "Page 2 of 2" in page2


def test_page_controls_are_disabled_at_the_ends(client, db):
    for i in range(13):
        add_ready(db, f"Plant{i}")
    first = client.get("/grid?page=1").text
    middle = client.get("/grid?page=2").text
    last = client.get("/grid?page=3").text
    assert re.search(r"<button[^>]*disabled>&larr; Previous", first)
    assert not re.search(r"<button[^>]*disabled>Next", first)
    assert not re.search(r"disabled", middle.split('class="pager"')[1])
    assert re.search(r"<button[^>]*disabled>Next", last)


def test_out_of_range_page_is_clamped(client, db):
    add_ready(db, "Only")
    assert _page_value(client.get("/grid?page=9").text) == 1


# --- adding ------------------------------------------------------------------------------


def test_search_lists_matches_and_handles_no_match(client):
    assert "Monstera" in client.get("/search", params={"q": "mons"}).text
    assert "Monstera" in client.get("/search", params={"q": "MONSTERA"}).text
    assert "No plants found" in client.get("/search", params={"q": "qqqzzz"}).text


def test_adding_monstera_shows_card_with_care_data(client):
    response = _add(client)
    assert "closeModal" in response.headers["HX-Trigger"]
    grid = client.get("/grid").text
    assert "Monstera" in grid and "7 days left" in grid


def test_same_plant_type_can_be_added_twice(client):
    _add(client)
    _add(client)
    assert _card_count(client.get("/grid").text) == 2


def test_adding_a_seventh_plant_jumps_to_the_page_that_shows_it(client, db):
    for i in range(6):
        add_ready(db, f"Plant{i}")
    html = _add(client).text
    assert _page_value(html) == 2 and "Monstera" in html


def test_plant_added_while_data_is_loading_shows_loading_card(client, db):
    db.add_plant("local:monstera", "Monstera", TODAY)
    html = client.get("/").text
    assert "Loading…" in html and 'hx-trigger="every 1s"' in html


def test_plant_that_cannot_load_is_not_added_and_user_is_told(client):
    _add(client, type_id="unknown:9", name="Some Rare Orchid")
    assert "Some Rare Orchid" not in client.get("/grid").text
    # the polling card learns what happened
    plants_ids = [1]
    message = client.get(f"/plants/{plants_ids[0]}/card").text
    assert "could not be loaded" in message and "Some Rare Orchid" in message


def test_blank_add_is_rejected(client):
    assert client.post("/plants", data={"type_id": " ", "name": " "}).status_code == 400


def test_offline_fallback_plant_is_marked(make_client, config):
    from app.providers.composite import CareDataService
    from app.providers.local_json import LocalProvider
    from tests.fakes import FakeOnlineSource

    service = CareDataService(LocalProvider(config.local_data_path), FakeOnlineSource(fail=True))
    client = make_client(service)
    _add(client, type_id="local:monstera", name="Monstera")
    assert "offline data" in client.get("/grid").text
    details = client.get("/plants/1").text
    assert "Offline data was used" in details and "Every 7 days" in details


def test_online_photo_description_and_credit_are_stored_and_shown(make_client, config, db, monkeypatch):
    import app.main as main
    from app.providers.base import OnlineInfo
    from app.providers.composite import CareDataService
    from app.providers.local_json import LocalProvider
    from tests.fakes import FakeOnlineSource

    info = OnlineInfo("https://img.example/m.jpg", "Monstera deliciosa is a plant.", "https://en.wikipedia.org/wiki/Monstera_deliciosa")
    monkeypatch.setattr(main, "store_photo", lambda image, photos_dir, plant_id: "/photos/1.jpg")
    client = make_client(CareDataService(LocalProvider(config.local_data_path), FakeOnlineSource(info)))
    _add(client)
    plant = db.get_plant(1)
    assert plant.photo == "/photos/1.jpg" and plant.about == "Monstera deliciosa is a plant."
    details = client.get("/plants/1").text
    assert "Monstera deliciosa is a plant." in details
    assert 'href="https://en.wikipedia.org/wiki/Monstera_deliciosa"' in details
    assert "Offline data was used" not in details
    assert "/photos/1.jpg" in client.get("/grid").text


def test_a_photo_that_cannot_be_downloaded_counts_as_offline(make_client, config, db, monkeypatch):
    import app.main as main
    from app.providers.base import OnlineInfo
    from app.providers.composite import CareDataService
    from app.providers.local_json import LocalProvider
    from tests.fakes import FakeOnlineSource

    monkeypatch.setattr(main, "store_photo", lambda image, photos_dir, plant_id: None)
    info = OnlineInfo("https://img.example/m.jpg", "About.", "https://en.wikipedia.org/wiki/M")
    client = make_client(CareDataService(LocalProvider(config.local_data_path), FakeOnlineSource(info)))
    _add(client)
    assert "Offline data was used" in client.get("/plants/1").text


def test_plant_added_offline_has_no_description_or_credit(client, db):
    _add(client)
    details = client.get("/plants/1").text
    assert 'class="about"' not in details and "Wikipedia" not in details


def test_stored_data_survives_the_internet_going_away(client, db):
    _add(client)
    plant = db.list_plants()[0]
    assert plant.interval_days == 7 and plant.light
    assert "/static/placeholder.svg" in client.get("/grid").text
    assert client.get("/static/placeholder.svg").status_code == 200
    assert "Monstera" in client.get("/plants/1").text


# --- details ---------------------------------------------------------------------------


def test_details_show_care_instructions_and_watered_button(client, db):
    add_ready(db, "Monstera", interval=7)
    html = client.get("/plants/1").text
    assert "Bright light" in html and "Every 7 days" in html and ">Watered<" in html


def test_details_of_unknown_plant_is_404(client):
    assert client.get("/plants/999").status_code == 404


# --- watering status and action ------------------------------------------------------


def test_cards_show_green_due_and_overdue_states(client, db):
    add_ready(db, "Fresh", 7, TODAY - timedelta(days=4))
    add_ready(db, "DueToday", 7, TODAY - timedelta(days=7))
    add_ready(db, "Late", 7, TODAY - timedelta(days=9))
    html = client.get("/").text
    assert re.search(r'badge ok">3 days left', html)
    assert 'badge due">Watering: Due today!' in html
    assert 'badge overdue">Watering: 2 days overdue' in html


def test_watered_resets_countdown_turns_green_and_persists(client, db, make_client):
    plant = add_ready(db, "Pilea", 7, TODAY - timedelta(days=7))
    assert "Due today!" in client.get("/").text
    response = client.post(f"/plants/{plant.id}/watered")
    assert "refreshGrid" in response.headers["HX-Trigger"]
    assert "Watered!" in response.text and "7 days" in response.text
    html = client.get("/").text
    assert "7 days left" in html and "Due today!" not in html
    assert "7 days left" in make_client().get("/").text  # after a restart


def test_watering_early_resets_to_full_interval(client, db):
    plant = add_ready(db, "Pilea", 7, TODAY - timedelta(days=3))
    client.post(f"/plants/{plant.id}/watered")
    assert "7 days left" in client.get("/").text


def test_countdown_follows_the_clock_across_days(client, db, clock):
    add_ready(db, "Pilea", 7, TODAY)
    clock.today = TODAY + timedelta(days=1)
    assert "6 days left" in client.get("/").text


# --- removing ------------------------------------------------------------------------


def test_confirm_step_then_removal_closes_the_gap(client, db):
    for i in range(7):
        add_ready(db, f"Plant{i}")
    assert "Remove Plant0?" in client.get("/plants/1/confirm-remove").text
    assert db.count_plants() == 7  # asking for confirmation removes nothing
    response = client.post("/plants/1/remove", data={"page": 1})
    assert "closeModal" in response.headers["HX-Trigger"]
    page1 = client.get("/grid?page=1").text
    assert "Plant0" not in page1 and "Plant6" in page1 and 'class="pager"' not in page1


def test_removing_only_plant_on_last_page_shows_previous_page(client, db):
    for i in range(7):
        add_ready(db, f"Plant{i}")
    html = client.post("/plants/7/remove", data={"page": 2}).text
    assert _page_value(html) == 1 and _card_count(html) == 6


def test_removed_plant_disappears_from_the_grid(client, db):
    plant = add_ready(db, "Thirsty", 7, TODAY - timedelta(days=8))
    client.post(f"/plants/{plant.id}/remove", data={"page": 1})
    assert "Thirsty" not in client.get("/").text and db.count_plants() == 0


# --- Google reminders wired into the pages ------------------------------------------------


def test_adding_a_plant_creates_two_reminders(make_client, tasks, db):
    client = make_client(tasks_client=tasks)
    _add(client)
    assert tasks.dues_for(1) == [TODAY + timedelta(days=7), TODAY + timedelta(days=14)]


def test_watering_in_the_app_completes_and_realigns_the_reminders(make_client, tasks, db, clock):
    client = make_client(tasks_client=tasks)
    _add(client)
    clock.today = TODAY + timedelta(days=7)
    client.post("/plants/1/watered")
    assert tasks.dues_for(1) == [clock.today + timedelta(days=7), clock.today + timedelta(days=14)]
    assert any(call[0] == "complete" for call in tasks.calls)


def test_removing_a_plant_deletes_its_reminders(make_client, tasks, db):
    client = make_client(tasks_client=tasks)
    _add(client)
    client.post("/plants/1/remove", data={"page": 1})
    assert tasks.tasks == {}


def test_pages_and_actions_work_when_google_is_down(make_client, tasks, db, clock):
    tasks.fail = True
    client = make_client(tasks_client=tasks)
    _add(client)
    assert "7 days left" in client.get("/grid").text
    clock.today = TODAY + timedelta(days=7)
    assert client.post("/plants/1/watered").status_code == 200
    assert "7 days left" in client.get("/grid").text
    assert client.get("/").status_code == 200
    tasks.fail = False  # Google comes back: the next sync catches up
    from app.sync import reconcile

    reconcile(db, tasks, clock.today)
    assert tasks.dues_for(1) == [clock.today + timedelta(days=7), clock.today + timedelta(days=14)]


def test_app_works_and_says_so_when_google_is_not_configured(make_client, caplog):
    import logging

    with caplog.at_level(logging.WARNING, logger="plant_care"):
        client = make_client()
    assert "not configured" in caplog.text
    _add(client)
    assert "7 days left" in client.get("/grid").text


# --- persistence and structure ---------------------------------------------------------


def test_collection_survives_restart(client, db, config, make_client):
    _add(client)
    _add(client, "local:pilea", "Pilea")
    html = make_client().get("/").text
    assert "Monstera" in html and "Pilea" in html


def test_only_the_data_access_module_opens_the_database():
    app_dir = Path(__file__).resolve().parent.parent / "app"
    offenders = [
        p.name for p in app_dir.rglob("*.py") if p.name != "db.py" and "sqlite3" in p.read_text(encoding="utf-8")
    ]
    assert offenders == []
    root_scripts = [p for p in app_dir.parent.glob("*.py") if "sqlite3" in p.read_text(encoding="utf-8")]
    assert root_scripts == []
