import pytest
from fastapi.testclient import TestClient

from app import main
from app.settings import Settings

from .conftest import BRIEFS


def search(client, q, **params):
    r = client.get("/v1/tickers/search", params={"q": q, **params})
    assert r.status_code == 200, r.text
    return r.json()["results"]


def test_exact_symbol_ranks_first(client):
    assert search(client, "2222")[0]["ticker_key"] == "2222_TADAWUL"


@pytest.mark.parametrize("q", ["aramco", "Saudi Aramco", "أرامكو", "ارامكو"])
def test_english_and_arabic_names(client, q):
    assert search(client, q)[0]["ticker_key"] == "2222_TADAWUL"


def test_arabic_without_definite_article(client):
    assert search(client, "راجحي")[0]["ticker_key"] == "1120_TADAWUL"


def test_eastern_arabic_digits(client):
    assert search(client, "١١٢٠")[0]["ticker_key"] == "1120_TADAWUL"


def test_tadawul_keeps_bare_symbol_when_shared(client):
    slugs = {h["ticker_key"]: h["slug"] for h in search(client, "2010")}
    assert slugs == {"2010_TADAWUL": "2010", "2010_KSE": "2010_KSE"}


def test_missing_english_name_is_null_not_invented(client):
    hit = search(client, "EMAAR")[0]
    assert hit["name_en"] is None
    assert hit["name_ar"] == "إعمار"


def test_no_match(client):
    assert search(client, "zzzz") == []


def test_limit(client):
    assert len(search(client, "a", limit=2)) <= 2


def test_empty_query_rejected(client):
    assert client.get("/v1/tickers/search", params={"q": ""}).status_code == 422


def test_unconfigured_database_is_503(monkeypatch):
    monkeypatch.setattr(main, "get_settings", lambda: Settings(_env_file=None))
    r = TestClient(main.create_app()).get("/v1/tickers/search", params={"q": "2222"})
    assert r.status_code == 503
    assert r.json()["detail"].startswith("Market data unavailable")


def test_health_reports_universe(client):
    body = client.get("/v1/health").json()
    assert body["market_data"] == "ok"
    assert body["universe_size"] == len(BRIEFS)
    assert body["universe_as_of"] == max(b[7] for b in BRIEFS)
