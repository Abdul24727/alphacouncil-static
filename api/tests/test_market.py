from .conftest import BRIEFS


def test_screener_has_every_ticker_with_fallback_ratios(client):
    rows = client.get("/v1/screener").json()
    assert len(rows) == len(BRIEFS)
    aramco = next(r for r in rows if r["ticker"]["ticker_key"] == "2222_TADAWUL")
    assert aramco["pe"] == 14.47 and aramco["price"]["close"] == 26.5
    assert rows[0]["ticker"]["exchange"] == "TADAWUL"


def test_overview_indices_breadth_movers_news(client):
    o = client.get("/v1/market/overview").json()
    tad = next(e for e in o["exchanges"] if e["exchange"] == "TADAWUL")
    assert tad["index"]["key"] == "TASI" and tad["index"]["freshness"]["stale"] is False
    adx = next(e for e in o["exchanges"] if e["exchange"] == "ADX")
    assert adx["index"] is None  # no ADX index row in this fixture: never invented
    assert tad["breadth"]["advancers"] == 2  # 2222 and 2382 up on the latest day
    assert any(m["ticker"]["ticker_key"] == "2222_TADAWUL" for m in o["gainers"])
    assert o["news"][0]["title"] == "Aramco news"


def test_dividend_hunter(client):
    rows = client.get("/v1/templates/dividend-hunter").json()
    aramco = next(r for r in rows if r["ticker"]["ticker_key"] == "2222_TADAWUL")
    assert aramco["next_ex_date"] == "2030-01-10" and aramco["last_ex_date"] == "2026-08-19"
    assert aramco["payout_pct"] == 41.9
    assert rows == sorted(rows, key=lambda r: -r["dividend_yield_pct"])


def test_earnings_season_window(client):
    e = client.get("/v1/templates/earnings-season?days=30").json()
    assert [x["ticker"]["ticker_key"] for x in e["events"]] == ["1120_TADAWUL"]


def test_sector_vs_sector(client):
    names = [s["sector_en"] for s in client.get("/v1/templates/sectors").json()]
    assert "Energy" in names and "Banks" in names
    c = client.get("/v1/templates/sector-vs-sector", params={"a": "Energy", "b": "Banks"}).json()
    assert c["a"]["equities"] == 3 and c["b"]["equities"] == 2
    assert c["a"]["median_pe"] == 16.235  # median of 14.47 (scraped) and 18.0
    assert client.get("/v1/templates/sector-vs-sector", params={"a": "Nope", "b": "Banks"}).status_code == 404
