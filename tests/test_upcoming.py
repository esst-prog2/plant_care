from datetime import timedelta

from tests.conftest import TODAY, add_ready


def test_upcoming_lists_plants_sorted_by_urgency(client, db):
    add_ready(db, "Overdue", 7, TODAY - timedelta(days=10))  # 3 days overdue
    add_ready(db, "DueToday", 7, TODAY - timedelta(days=7))  # due today
    add_ready(db, "Future", 7, TODAY)  # 7 days left

    html = client.get("/upcoming").text
    assert html.index("Overdue") < html.index("DueToday") < html.index("Future")


def test_upcoming_row_links_to_the_plant_details(client, db):
    plant = add_ready(db, "Monstera", 7, TODAY)

    html = client.get("/upcoming").text
    assert f'hx-get="/plants/{plant.id}"' in html
    assert 'hx-target="#modal"' in html


def test_upcoming_page_listens_for_the_refresh_signal(client, db):
    html = client.get("/upcoming").text
    assert 'hx-get="/upcoming-rows"' in html
    assert 'hx-trigger="refreshGrid from:body"' in html
    assert 'hx-target="#upcoming-wrap"' in html


def test_watering_a_plant_sends_the_refresh_signal(client, db):
    plant = add_ready(db, "Monstera", 7, TODAY - timedelta(days=8))

    response = client.post(f"/plants/{plant.id}/watered")
    assert response.headers["HX-Trigger"] == "refreshGrid"


def test_upcoming_rows_fragment_reflects_a_plant_just_watered(client, db):
    plant = add_ready(db, "Monstera", 7, TODAY - timedelta(days=8))
    assert "overdue" in client.get("/upcoming-rows").text

    client.post(f"/plants/{plant.id}/watered")

    html = client.get("/upcoming-rows").text
    assert "overdue" not in html
    assert "Monstera" in html


def test_upcoming_does_not_hide_a_long_interval_plant(client, db):
    add_ready(db, "FarOut", 30, TODAY)  # 30 days left, nothing else due sooner

    html = client.get("/upcoming").text
    assert "FarOut" in html
    assert "30 days left" in html


def test_upcoming_excludes_a_still_loading_plant(client, db):
    db.add_plant("local:monstera", "StillLoading", TODAY)  # never completed

    html = client.get("/upcoming").text
    assert "StillLoading" not in html


def test_upcoming_row_shows_group_name_or_all(client, db):
    group = db.create_group("Living room")
    add_ready(db, "Grouped", 7, TODAY, group_id=group.id)
    add_ready(db, "Unassigned", 7, TODAY)

    html = client.get("/upcoming").text
    assert "Living room" in html
    assert ">All<" in html


def test_upcoming_filters_by_group(client, db):
    a = db.create_group("Living room")
    b = db.create_group("Kitchen")
    add_ready(db, "InLivingRoom", 7, TODAY, group_id=a.id)
    add_ready(db, "InKitchen", 7, TODAY, group_id=b.id)

    html = client.get("/upcoming", params={"view_group_id": str(a.id)}).text
    assert "InLivingRoom" in html
    assert "InKitchen" not in html


def test_upcoming_default_shows_every_plant_regardless_of_group(client, db):
    group = db.create_group("Living room")
    add_ready(db, "Grouped", 7, TODAY, group_id=group.id)
    add_ready(db, "Unassigned", 7, TODAY)

    html = client.get("/upcoming").text
    assert "Grouped" in html and "Unassigned" in html


def test_upcoming_empty_state(client):
    html = client.get("/upcoming").text
    assert "All caught up" in html


def test_upcoming_empty_state_for_a_group_with_no_ready_plants(client, db):
    kitchen = db.create_group("Kitchen")
    add_ready(db, "InLivingRoom", 7, TODAY)

    html = client.get("/upcoming", params={"view_group_id": str(kitchen.id)}).text
    assert "All caught up" in html
    assert "InLivingRoom" not in html


def test_upcoming_reachable_from_landing_page(client):
    assert 'href="/upcoming"' in client.get("/").text


def test_upcoming_reachable_from_a_collection_view(client, db):
    group = db.create_group("Living room")
    assert f'href="/upcoming?view_group_id={group.id}"' in client.get(f"/groups/{group.id}").text


def test_upcoming_link_from_a_collection_view_carries_its_group_filter(client, db):
    group = db.create_group("Living room")
    add_ready(db, "InLivingRoom", 7, TODAY, group_id=group.id)

    html = client.get(f"/groups/{group.id}").text
    assert f'href="/upcoming?view_group_id={group.id}"' in html

    upcoming_html = client.get(f"/upcoming?view_group_id={group.id}").text
    assert "InLivingRoom" in upcoming_html
