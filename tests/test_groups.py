import re
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path

from app.db import Database
from tests.conftest import TODAY, add_ready


def _card_count(html: str) -> int:
    return len(re.findall(r'<article class="card', html))


def test_create_list_and_get_a_group(db):
    created = db.create_group("Living room")
    assert created.name == "Living room"
    assert db.get_group(created.id).name == "Living room"
    assert [g.name for g in db.list_groups()] == ["Living room"]


def test_init_adds_a_photo_column_to_groups_without_data_loss(tmp_path):
    db_path = tmp_path / "old.db"
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute("CREATE TABLE groups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
        conn.execute("INSERT INTO groups (name) VALUES ('Living room')")

    database = Database(db_path)
    database.init()

    group = database.get_group(1)
    assert group.name == "Living room"
    assert group.photo is None


def test_rename_a_group(db):
    group = db.create_group("Living room")
    db.rename_group(group.id, "Lounge")
    assert db.get_group(group.id).name == "Lounge"


def test_creating_a_group_with_a_cover_stores_it(db):
    group = db.create_group("Living room", photo="/static/group-presets/leaf.svg")
    assert db.get_group(group.id).photo == "/static/group-presets/leaf.svg"


def test_set_group_photo_changes_the_cover(db):
    group = db.create_group("Living room")
    db.set_group_photo(group.id, "/photos/group-1.jpg")
    assert db.get_group(group.id).photo == "/photos/group-1.jpg"


def test_deleting_a_group_with_an_uploaded_cover_removes_the_file(db, config):
    group = db.create_group("Living room")
    config.photos_dir.mkdir(parents=True, exist_ok=True)
    cover_path = config.photos_dir / f"group-{group.id}.jpg"
    cover_path.write_bytes(b"fake photo")
    db.set_group_photo(group.id, f"/photos/group-{group.id}.jpg?v=abcd1234")

    db.delete_group(group.id)

    assert not cover_path.exists()


def test_deleting_a_group_with_a_preset_cover_does_not_touch_any_file(db, config):
    group = db.create_group("Living room", photo="/static/group-presets/leaf.svg")

    db.delete_group(group.id)  # must not raise or try to delete the shared preset asset

    preset_path = (
        Path(__file__).resolve().parent.parent / "app" / "static" / "group-presets" / "leaf.svg"
    )
    assert preset_path.exists()


def test_deleting_a_group_unassigns_its_plants_instead_of_deleting_them(db):
    group = db.create_group("Living room")
    plant = db.add_plant("local:monstera", "Monstera", TODAY, group_id=group.id)
    db.delete_group(group.id)
    assert db.get_group(group.id) is None
    assert db.get_plant(plant.id) is not None
    assert db.get_plant(plant.id).group_id is None


def test_list_plants_filters_by_group(db):
    a = db.create_group("A")
    b = db.create_group("B")
    p1 = db.add_plant("local:monstera", "Monstera", TODAY, group_id=a.id)
    p2 = db.add_plant("local:pilea", "Pilea", TODAY, group_id=b.id)
    unassigned = db.add_plant("local:cactus", "Cactus", TODAY)

    assert [p.id for p in db.list_plants(group_id=a.id)] == [p1.id]
    assert [p.id for p in db.list_plants(group_id=b.id)] == [p2.id]
    assert {p.id for p in db.list_plants()} == {p1.id, p2.id, unassigned.id}


def test_set_plant_group_moves_and_unassigns(db):
    a = db.create_group("A")
    b = db.create_group("B")
    plant = db.add_plant("local:monstera", "Monstera", TODAY, group_id=a.id)

    db.set_plant_group(plant.id, b.id)
    assert db.get_plant(plant.id).group_id == b.id
    assert db.list_plants(group_id=a.id) == []

    db.set_plant_group(plant.id, None)
    assert db.get_plant(plant.id).group_id is None


# --- landing page -------------------------------------------------------------------


def test_landing_page_with_no_groups_shows_only_all(client):
    html = client.get("/").text
    assert "All" in html and "0 plants" in html
    assert _card_count(html) == 1  # just the "All" card


def test_landing_page_shows_a_stored_cover_regardless_of_the_groups_plants(client, db):
    group = db.create_group("Living room", photo="/static/group-presets/leaf.svg")
    add_ready(db, "Monstera", group_id=group.id)  # has its own photo, should be ignored

    html = client.get("/").text
    assert "/static/group-presets/leaf.svg" in html


def test_landing_page_shows_groups_with_their_own_counts(client, db):
    a = db.create_group("Living room")
    db.create_group("Bedroom")
    add_ready(db, "Monstera", group_id=a.id)
    add_ready(db, "Pilea", group_id=a.id)
    add_ready(db, "Cactus")  # unassigned

    html = client.get("/").text
    assert _card_count(html) == 3  # All + Living room + Bedroom
    assert "3 plants" in html  # All's total
    assert "2 plants" in html  # Living room
    assert "0 plants" in html  # Bedroom


def test_creating_a_group_adds_a_zero_count_card(client):
    client.post("/groups", data={"name": "Living room"})
    html = client.get("/").text
    assert "Living room" in html and _card_count(html) == 2


def test_renaming_a_group_updates_the_landing_page(client, db):
    group = db.create_group("Living room")
    add_ready(db, "Monstera", group_id=group.id)
    client.post(f"/groups/{group.id}/rename", data={"name": "Lounge"})
    html = client.get("/").text
    assert "Lounge" in html and "Living room" not in html
    assert db.get_plant(1).group_id == group.id  # plant untouched


def test_deleting_a_group_removes_its_card_but_keeps_its_plants_under_all(client, db):
    group = db.create_group("Living room")
    add_ready(db, "Monstera", group_id=group.id)
    client.post(f"/groups/{group.id}/delete")
    html = client.get("/").text
    assert "Living room" not in html
    assert _card_count(html) == 1  # just "All" now
    assert db.get_plant(1).group_id is None


# --- scoped collection view ----------------------------------------------------------


def test_opening_a_group_shows_only_its_plants(client, db):
    group = db.create_group("Living room")
    add_ready(db, "Monstera", group_id=group.id)
    add_ready(db, "Pilea")  # unassigned, should not show in the group

    html = client.get(f"/groups/{group.id}").text
    assert "Monstera" in html and "Pilea" not in html


def test_opening_all_shows_every_plant(client, db):
    group = db.create_group("Living room")
    add_ready(db, "Monstera", group_id=group.id)
    add_ready(db, "Pilea")

    html = client.get("/groups/all").text
    assert "Monstera" in html and "Pilea" in html


def test_pagination_is_scoped_per_group(client, db):
    group = db.create_group("Living room")
    for i in range(7):
        add_ready(db, f"InGroup{i}", group_id=group.id)
    for i in range(3):
        add_ready(db, f"Elsewhere{i}")  # unassigned, shouldn't affect this group's paging

    page1 = client.get(f"/groups/{group.id}").text
    assert _card_count(page1) == 6 and "Page 1 of 2" in page1
    page2 = client.get("/grid", params={"view_group_id": str(group.id), "page": 2}).text
    assert _card_count(page2) == 1 and "InGroup6" in page2 and "Page 2 of 2" in page2


# --- assigning and moving a plant's group ---------------------------------------------


def test_adding_a_plant_with_a_group_selected_puts_it_under_that_group_and_all(client, db):
    group = db.create_group("Living room")
    client.post("/plants", data={"type_id": "local:monstera", "name": "Monstera", "group_id": str(group.id)})
    assert db.get_plant(1).group_id == group.id
    assert "Monstera" in client.get(f"/groups/{group.id}").text
    assert "Monstera" in client.get("/groups/all").text


def test_adding_a_plant_without_a_group_puts_it_only_under_all(client, db):
    group = db.create_group("Living room")
    client.post("/plants", data={"type_id": "local:monstera", "name": "Monstera"})
    assert db.get_plant(1).group_id is None
    assert "Monstera" not in client.get(f"/groups/{group.id}").text
    assert "Monstera" in client.get("/groups/all").text


def test_moving_a_plant_to_a_different_group_later(client, db):
    a = db.create_group("A")
    b = db.create_group("B")
    plant = add_ready(db, "Monstera", group_id=a.id)

    response = client.post(f"/plants/{plant.id}/group", data={"group_id": str(b.id)})
    assert "refreshGrid" in response.headers["HX-Trigger"]
    assert db.get_plant(plant.id).group_id == b.id
    assert "Monstera" not in client.get(f"/groups/{a.id}").text
    assert "Monstera" in client.get(f"/groups/{b.id}").text


def test_landing_page_shows_a_due_count_badge_on_groups_with_due_plants(client, db):
    group = db.create_group("Living room")
    add_ready(db, "Fresh", 7, TODAY - timedelta(days=1), group_id=group.id)  # not due
    add_ready(db, "Thirsty", 7, TODAY - timedelta(days=7), group_id=group.id)  # due today

    html = client.get("/").text
    assert "1 due" in html


def test_landing_page_shows_no_due_badge_when_nothing_is_due(client, db):
    group = db.create_group("Living room")
    add_ready(db, "Fresh", 7, TODAY - timedelta(days=1), group_id=group.id)

    html = client.get("/").text
    assert "due" not in html.lower()


def test_all_group_can_be_renamed(client, db):
    assert "All" in client.get("/").text
    client.post("/groups/all/rename", data={"name": "Everything"})
    html = client.get("/").text
    assert "Everything" in html and ">All<" not in html


def test_all_group_rename_is_reflected_in_the_collection_view_switcher(client, db):
    db.set_setting("all_group_name", "Everything")
    html = client.get("/groups/all").text
    assert "Everything" in html


def test_unassigning_a_plant_removes_it_from_its_group(client, db):
    group = db.create_group("Living room")
    plant = add_ready(db, "Monstera", group_id=group.id)

    client.post(f"/plants/{plant.id}/group", data={"group_id": ""})
    assert db.get_plant(plant.id).group_id is None
    assert "Monstera" not in client.get(f"/groups/{group.id}").text
    assert "Monstera" in client.get("/groups/all").text


# --- cover picker --------------------------------------------------------------------


def test_new_group_form_renders_all_8_presets(client):
    html = client.get("/groups/new").text
    for preset in ["leaf", "cactus", "succulent", "potted-plant", "flower", "vine", "fern", "palm"]:
        assert f"/static/group-presets/{preset}.svg" in html


def test_creating_a_group_with_a_preset_stores_it(client, db):
    client.post("/groups", data={"name": "Living room", "preset": "cactus"})
    group = db.list_groups()[0]
    assert group.photo == "/static/group-presets/cactus.svg"


def test_creating_a_group_with_an_uploaded_cover_stores_it(client, db):
    response = client.post(
        "/groups", data={"name": "Living room"}, files={"photo": ("mine.png", b"\x89PNGfakedata", "image/png")}
    )
    group = db.list_groups()[0]
    assert group.photo is not None and group.photo.startswith("/photos/group-")
    assert "Living room" in response.text


def test_creating_a_group_with_an_invalid_upload_creates_nothing_and_shows_an_error(client, db):
    response = client.post(
        "/groups", data={"name": "Living room"}, files={"photo": ("notes.txt", b"hello", "text/plain")}
    )
    assert db.list_groups() == []
    assert "That file" in response.text
    assert 'value="Living room"' in response.text


def test_creating_a_group_with_neither_preset_nor_upload_stays_auto_derived(client, db):
    client.post("/groups", data={"name": "Living room"})
    group = db.list_groups()[0]
    assert group.photo is None


# --- combined edit flow ---------------------------------------------------------------


def test_edit_group_form_shows_edit_for_a_real_group(client, db):
    group = db.create_group("Living room")
    html = client.get(f"/groups/{group.id}/edit").text
    assert "Edit group" in html and "Rename group" not in html
    assert "cover-picker" in html


def test_all_edit_modal_is_unchanged_no_cover_rename_label(client):
    html = client.get("/groups/all/edit").text
    assert "Rename group" in html and "Edit group" not in html
    assert "cover-picker" not in html


def test_edit_group_form_preselects_the_current_preset(client, db):
    group = db.create_group("Living room", photo="/static/group-presets/fern.svg")
    html = client.get(f"/groups/{group.id}/edit").text
    assert 'value="fern" checked' in html


def test_changing_only_the_name_leaves_the_cover_unchanged(client, db):
    group = db.create_group("Living room", photo="/static/group-presets/fern.svg")
    client.post(f"/groups/{group.id}/rename", data={"name": "Lounge"})
    updated = db.get_group(group.id)
    assert updated.name == "Lounge"
    assert updated.photo == "/static/group-presets/fern.svg"


def test_changing_only_the_cover_via_preset_leaves_the_name_unchanged(client, db):
    group = db.create_group("Living room")
    client.post(f"/groups/{group.id}/rename", data={"name": "Living room", "preset": "palm"})
    updated = db.get_group(group.id)
    assert updated.name == "Living room"
    assert updated.photo == "/static/group-presets/palm.svg"


def test_changing_only_the_cover_via_upload_leaves_the_name_unchanged(client, db):
    group = db.create_group("Living room")
    client.post(
        f"/groups/{group.id}/rename", data={"name": "Living room"},
        files={"photo": ("mine.png", b"\x89PNGfakedata", "image/png")},
    )
    updated = db.get_group(group.id)
    assert updated.name == "Living room"
    assert updated.photo is not None and updated.photo.startswith("/photos/group-")


def test_changing_both_name_and_cover_together(client, db):
    group = db.create_group("Living room")
    client.post(f"/groups/{group.id}/rename", data={"name": "Lounge", "preset": "vine"})
    updated = db.get_group(group.id)
    assert updated.name == "Lounge"
    assert updated.photo == "/static/group-presets/vine.svg"


def test_an_invalid_upload_on_edit_leaves_both_name_and_cover_unchanged(client, db):
    group = db.create_group("Living room", photo="/static/group-presets/fern.svg")
    response = client.post(
        f"/groups/{group.id}/rename", data={"name": "Lounge"},
        files={"photo": ("notes.txt", b"hello", "text/plain")},
    )
    unchanged = db.get_group(group.id)
    assert unchanged.name == "Living room"
    assert unchanged.photo == "/static/group-presets/fern.svg"
    assert "That file" in response.text


def test_an_uploaded_cover_wins_over_a_preset_selected_at_the_same_time(client, db):
    group = db.create_group("Living room")
    client.post(
        f"/groups/{group.id}/rename", data={"name": "Living room", "preset": "palm"},
        files={"photo": ("mine.png", b"\x89PNGfakedata", "image/png")},
    )
    updated = db.get_group(group.id)
    assert updated.photo is not None and updated.photo.startswith("/photos/group-")
