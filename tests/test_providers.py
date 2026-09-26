import json
from pathlib import Path

import httpx
import pytest

from app.config import BASE_DIR
from app.providers.base import OnlineInfo, ProviderError
from app.providers.composite import (
    SOURCE_FALLBACK,
    SOURCE_LOCAL,
    SOURCE_ONLINE,
    CareDataService,
    CareDataUnavailable,
)
from app.providers.local_json import LocalProvider
from app.providers.wikipedia import USER_AGENT, WikipediaSource, shorten
from tests.fakes import FakeOnlineSource

LOCAL_PATH = BASE_DIR / "data" / "plants.json"
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def local():
    return LocalProvider(LOCAL_PATH)


# --- the bundled list ------------------------------------------------------------------


def test_bundled_list_is_complete_and_has_the_readme_plants():
    raw = json.loads(LOCAL_PATH.read_text(encoding="utf-8"))
    ids = [item["id"] for item in raw]
    assert len(raw) >= 40 and len(ids) == len(set(ids))
    assert {"monstera", "pilea"} <= set(ids)
    for item in raw:
        assert item["name"].strip() and item["light"].strip() and item["wikipedia"].strip()
        assert isinstance(item["watering_days"], int) and item["watering_days"] > 0


def test_search_is_case_insensitive_and_partial(local):
    assert [p.name for p in local.search("Monstera")] == ["Monstera"]
    assert local.search("monstera") == local.search("MONSTERA") == local.search("Monstera")
    assert "Monstera" in [p.name for p in local.search("mons")]


def test_search_unknown_or_blank_returns_nothing(local):
    assert local.search("zzzz-not-a-plant") == []
    assert local.search("   ") == []


def test_selected_plant_has_light_and_interval(local):
    monstera = local.get("local:monstera")
    assert monstera.light and monstera.interval_days > 0 and monstera.wiki_title == "Monstera_deliciosa"


# --- Wikipedia, using the recorded real responses --------------------------------------


def _wiki(handler):
    return WikipediaSource(client=httpx.Client(transport=httpx.MockTransport(handler)))


def _recorded(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_real_monstera_response_gives_photo_description_and_credit():
    seen = {}

    def handler(request):
        seen["ua"] = request.headers["user-agent"]
        seen["path"] = request.url.path
        return httpx.Response(200, json=_recorded("wikipedia_monstera_deliciosa.json"))

    info = _wiki(handler).lookup("Monstera_deliciosa")
    assert info.image_url.startswith("https://") and ".jpg" in info.image_url
    assert info.about.startswith("Monstera deliciosa") and len(info.about) <= 601
    assert info.page_url == "https://en.wikipedia.org/wiki/Monstera_deliciosa"
    assert seen["ua"] == USER_AGENT and "github.com/esst-prog2/plant_care" in seen["ua"]
    assert seen["path"].endswith("/page/summary/Monstera_deliciosa")


def test_real_pilea_response_is_understood():
    info = _wiki(lambda r: httpx.Response(200, json=_recorded("wikipedia_pilea_peperomioides.json"))).lookup(
        "Pilea_peperomioides"
    )
    assert info.image_url and info.about.startswith("Pilea peperomioides")


def test_the_title_is_url_encoded():
    seen = {}

    def handler(request):
        seen["raw"] = str(request.url)
        return httpx.Response(404)

    _wiki(handler).lookup("Some plant/with odd chars")
    assert "Some%20plant%2Fwith%20odd%20chars" in seen["raw"]


def test_article_without_a_picture_gives_no_image():
    info = _wiki(lambda r: httpx.Response(200, json={"extract": "A plant.", "content_urls": {}})).lookup("X")
    assert info.image_url is None and info.about == "A plant."


def test_missing_article_is_not_an_error():
    assert _wiki(lambda r: httpx.Response(404)).lookup("Nope") == OnlineInfo()


def _failures():
    def network(request):
        raise httpx.ConnectError("no internet", request=request)

    def timeout(request):
        raise httpx.ReadTimeout("slow", request=request)

    return {
        "network": network,
        "timeout": timeout,
        "robot policy": lambda r: httpx.Response(403, text="Please respect our robot policy"),
        "rate limit": lambda r: httpx.Response(429),
        "server error": lambda r: httpx.Response(500),
        "not json": lambda r: httpx.Response(200, text="<html>"),
        "not an object": lambda r: httpx.Response(200, json=["x"]),
    }


@pytest.mark.parametrize("name", list(_failures()))
def test_every_wikipedia_failure_is_a_provider_error(name):
    with pytest.raises(ProviderError):
        _wiki(_failures()[name]).lookup("Monstera_deliciosa")


def test_long_descriptions_are_shortened_at_a_sentence_end():
    text = "First sentence here. " * 60
    short = shorten(text, 100)
    assert len(short) <= 100 and short.endswith(".")
    assert shorten("Short.", 100) == "Short."
    assert shorten("word " * 100, 50).endswith("…")


# --- the data service ------------------------------------------------------------------


def test_service_searches_only_the_bundled_list(local):
    service = CareDataService(local, FakeOnlineSource(fail=True))
    assert [p.name for p in service.search("pilea")] == ["Pilea"]


def test_without_an_online_source_care_data_comes_from_the_list(local):
    result = CareDataService(local).get("local:pilea", "Pilea")
    assert result.source == SOURCE_LOCAL and result.care.interval_days == 7
    assert result.image_url is None and result.about is None


def test_online_success_adds_photo_description_and_credit(local):
    online = FakeOnlineSource(OnlineInfo("https://img/m.jpg", "About text.", "https://en.wikipedia.org/wiki/M"))
    result = CareDataService(local, online).get("local:monstera", "Monstera")
    assert result.source == SOURCE_ONLINE
    assert (result.image_url, result.about, result.credit_url) == (
        "https://img/m.jpg", "About text.", "https://en.wikipedia.org/wiki/M",
    )
    assert online.asked == ["Monstera_deliciosa"]
    assert result.care.light and result.care.interval_days


@pytest.mark.parametrize("name", list(_failures()))
def test_online_failure_keeps_care_data_and_marks_it_offline(name, local):
    result = CareDataService(local, _wiki(_failures()[name])).get("local:monstera", "Monstera")
    assert result.source == SOURCE_FALLBACK
    assert result.care.name == "Monstera" and result.image_url is None


def test_article_without_picture_is_not_an_offline_notice(local):
    result = CareDataService(local, FakeOnlineSource(OnlineInfo())).get("local:monstera", "Monstera")
    assert result.source == SOURCE_LOCAL


def test_unknown_plant_types_are_unavailable(local):
    service = CareDataService(local)
    for type_id in ("local:does-not-exist", "external:1", "whatever"):
        with pytest.raises(CareDataUnavailable):
            service.get(type_id, "Anything")
