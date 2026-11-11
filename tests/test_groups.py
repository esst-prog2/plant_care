import re

from tests.conftest import TODAY, add_ready


def _card_count(html: str) -> int:
    return len(re.findall(r'<article class="card', html))


def test_create_list_and_get_a_group(db):
    created = db.create_group("Living room")
    assert created.name == "Living room"
    assert db.get_group(created.id).name == "Living room"
    assert [g.name for g in db.list_groups()] == ["Living room"]


def test_rename_a_group(db):
    group = db.create_group("Living room")
    db.rename_group(group.id, "Lounge")
    assert db.get_group(group.id).name == "Lounge"


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


def test_unassigning_a_plant_removes_it_from_its_group(client, db):
    group = db.create_group("Living room")
    plant = add_ready(db, "Monstera", group_id=group.id)

    client.post(f"/plants/{plant.id}/group", data={"group_id": ""})
    assert db.get_plant(plant.id).group_id is None
    assert "Monstera" not in client.get(f"/groups/{group.id}").text
    assert "Monstera" in client.get("/groups/all").text
