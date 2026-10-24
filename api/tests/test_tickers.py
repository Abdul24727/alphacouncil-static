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


# --- listings that no longer trade (data/not_listed.json, owner 2026-10-24) -----------------------


def _not_listed_file(tmp_path, listings):
    import json

    path = tmp_path / "not_listed.json"
    path.write_text(json.dumps({"about": "test", "listings": listings}), encoding="utf-8")
    return path


def _client_without(tmp_path, monkeypatch, data_files, listings):
    """A client whose universe leaves `listings` out."""
    from app import universe

    monkeypatch.setattr(universe, "NOT_LISTED_FILE", _not_listed_file(tmp_path, listings))
    monkeypatch.setattr(main, "get_settings", lambda: data_files)
    return TestClient(main.create_app())


def test_a_listing_that_no_longer_trades_is_left_out(tmp_path, monkeypatch, data_files):
    c = _client_without(tmp_path, monkeypatch, data_files, {"EMAAR_DFM": {"status": "delisted"}})
    assert search(c, "EMAAR") == []
    assert c.get("/v1/tickers/EMAAR_DFM").status_code == 404
    assert "EMAAR_DFM" not in {t["ticker_key"] for t in c.get("/v1/tickers").json()}
    # The ones still trading are untouched.
    assert search(c, "2222")[0]["ticker_key"] == "2222_TADAWUL"


def test_dropping_a_listing_does_not_change_another_listings_slug(tmp_path, monkeypatch, data_files):
    """2010 is on Tadawul and Boursa Kuwait: dropping one must not give the other the bare symbol,
    which would silently change a live URL."""
    c = _client_without(tmp_path, monkeypatch, data_files, {"2010_TADAWUL": {"status": "delisted"}})
    assert {h["ticker_key"]: h["slug"] for h in search(c, "2010")} == {"2010_KSE": "2010_KSE"}
    assert c.get("/v1/tickers/2010_KSE").status_code == 200
    assert c.get("/v1/tickers/2010").status_code == 404


def test_the_shipped_not_listed_file_names_taqa_and_kppc_with_their_evidence():
    from app.universe import load_not_listed

    listings = load_not_listed()
    assert set(listings) == {"TAQA_ADX", "624_KSE"}
    assert listings["TAQA_ADX"]["status"] == "delisted" and listings["TAQA_ADX"]["since"] == "2026-09-01"
    # KPPC's reason was never confirmed, so the file must not claim it was delisted.
    assert listings["624_KSE"]["status"] == "unconfirmed"
    for entry in listings.values():
        assert entry["note"] and entry["sources"] and entry["last_bar"]


def test_a_company_renamed_after_the_pipeline_csv_shows_its_new_name_in_both_languages():
    """Gulf Navigation became Etihad Energy Holding; the Arabic is a transliteration, not a
    translation, so it is recorded rather than derived (names.NAME_AR_OVERRIDES)."""
    from app.names import NAME_AR_OVERRIDES, SLUG_NAME_OVERRIDES

    assert SLUG_NAME_OVERRIDES["GULFNAV_DFM"] == "Etihad Energy Holding"
    assert NAME_AR_OVERRIDES["GULFNAV_DFM"] == "اتحاد إنيرجي القابضة"
