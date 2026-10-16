from datetime import UTC, datetime

from app import council
from app.freshness import assess, trading_days_between


def get(client, path, status=200):
    r = client.get(path)
    assert r.status_code == status, r.text
    return r.json()


# --- detail and freshness ---------------------------------------------------------------


def test_detail_resolves_slug_and_fills_pe_from_scraped_ratios(client):
    d = get(client, "/v1/tickers/2222")
    assert d["ticker"]["ticker_key"] == "2222_TADAWUL"
    assert d["quote"]["last_price"] == 26.5
    assert d["valuation"]["pe"] == 14.47  # briefs.pe is null for Tadawul
    assert d["technicals"]["above_200d"] is True


def test_detail_unknown_ticker_is_404(client):
    get(client, "/v1/tickers/NOPE", status=404)


def test_ticker_key_and_lowercase_resolve(client):
    assert get(client, "/v1/tickers/2010_kse")["ticker"]["exchange"] == "KSE"
    assert get(client, "/v1/tickers/2010")["ticker"]["exchange"] == "TADAWUL"


def test_old_quote_is_stale_and_recent_fundamentals_are_fresh(client):
    # 2223 has no price file, so its quote comes from an old briefs row.
    old = get(client, "/v1/tickers/2223")["quote"]
    assert old["source"] == "briefs" and old["freshness"]["stale"] is True
    d = get(client, "/v1/tickers/2222")
    assert d["quote"]["freshness"]["stale"] is False  # today's price file
    by_cat = {f["category"]: f for f in d["freshness"]}
    assert by_cat["prices"]["stale"] is True
    assert by_cat["fundamentals"]["stale"] is False
    assert by_cat["prices"]["updated_at"].startswith("2026-01-05T01:43")


def test_weekend_is_not_late_for_prices():
    # Thursday close checked on Saturday: zero Tadawul trading days have passed.
    thu, sat = datetime(2026, 10, 8, tzinfo=UTC), datetime(2026, 10, 10, 12, tzinfo=UTC)
    assert trading_days_between(thu.date(), sat.date(), "TADAWUL") == 0
    f = assess(category="prices", as_of_utc="2026-10-08", last_success_utc=None, max_age_days=2, exchange="TADAWUL", now=sat)
    assert f.stale is False
    # UAE closes Saturday-Sunday instead.
    assert trading_days_between(thu.date(), sat.date(), "DFM") == 1


def test_pipeline_run_stamp_parses():
    f = assess(category="prices", as_of_utc="2026-08-07", last_success_utc="20260807_000115", max_age_days=2, exchange="TADAWUL")
    assert f.updated_at == "2026-08-07T00:01:15+00:00"


# --- peers, news, events --------------------------------------------------------------------


def test_peers_same_sector_largest_first_excluding_self(client):
    p = get(client, "/v1/tickers/2222/peers")
    keys = [r["ticker"]["ticker_key"] for r in p["peers"]]
    assert "2222_TADAWUL" not in keys
    assert keys == ["2223_TADAWUL", "2382_TADAWUL"] or p["basis"] == "sector_gcc"


def test_peers_fall_back_to_gcc_when_exchange_has_few(client):
    p = get(client, "/v1/tickers/FAB/peers")
    assert p["basis"] == "sector_gcc"
    assert [r["ticker"]["ticker_key"] for r in p["peers"]] == ["1120_TADAWUL"]


def test_news_newest_first_with_summaries(client):
    items = get(client, "/v1/tickers/2222/news")
    assert [i["id"] for i in items] == ["n1", "d1"]
    assert items[0]["summary_en"] == "Up" and items[0]["impact"] == "positive"
    assert items[1]["summary_en"] == "Summary"


def test_events_skip_undated_rows(client):
    assert [i["id"] for i in get(client, "/v1/tickers/2222/events")] == ["e1"]


# --- council -----------------------------------------------------------------------------------


def test_council_votes_from_database_values(client):
    c = get(client, "/v1/tickers/2222/council")
    votes = {s["seat"]: s["vote"] for s in c["seats"]}
    assert votes == {
        "value": "neutral",  # P/E 14.47 from scraped_ratios
        "quality": "bullish",  # ROE 26.75
        "income": "bullish",  # yield 5.03
        "momentum": "bullish",  # regime 85 with golden cross
        "risk": "neutral",  # volatility 15.5%
        "news": "bullish",  # one positive rated item today
    }
    assert sum(c["counts"].values()) == 6


def test_council_abstains_without_data(client):
    c = get(client, "/v1/tickers/2382/council")
    assert all(s["vote"] == "abstain" for s in c["seats"] if s["seat"] != "news")


def test_seat_rules():
    assert council.value_seat(9).vote == "bullish"
    assert council.value_seat(-3).vote == "abstain"
    assert council.quality_seat(-5).vote == "bearish"
    assert council.income_seat(0).vote == "abstain"
    assert council.momentum_seat(70, False).vote == "neutral"
    assert council.risk_seat(30, 6).vote == "bearish"
    assert council.news_seat(["positive", "negative"]).vote == "neutral"
    assert council.news_seat([]).vote == "abstain"


# --- fundamentals, statements, corporate, insights ------------------------------------------


def test_fundamentals_groups_and_published_fallback(client):
    f = get(client, "/v1/tickers/2222/fundamentals")
    groups = {g["group"]: g for g in f["groups"]}
    assert set(groups) == {"valuation", "profitability", "health", "income"}
    pe = next(m for m in groups["valuation"]["metrics"] if m["key"] == "pe")
    assert pe["value"] == 14.47 and pe["status"] == "published" and pe["sector_percentile"] is None
    assert groups["health"]["score"] == (54.0 + 68.4) / 2
    assert f["freshness"]["category"] == "fundamentals"


def test_statements_by_year(client):
    s = get(client, "/v1/tickers/EMAAR_DFM/statements")
    assert s["years"] == [2024, 2025] and s["unit"] == "mn" and s["currency"] == "AED"
    income = next(x for x in s["statements"] if x["section"] == "Income Statement")
    assert income["rows"][0]["values"] == {"2024": 35505.0, "2025": 49557.26}


def test_corporate(client):
    c = get(client, "/v1/tickers/2222/corporate")
    # Newest first, including an announced future payment.
    assert [d["dps"] for d in c["dividends"]] == [0.35, 0.34]
    assert c["capital_changes"][0]["change_type"] == "Bonus Shares"


def test_seasonality_blanks_months_after_the_data(client):
    i = get(client, "/v1/tickers/2222/insights")
    months = i["seasonality"]["years"][0]["monthly_pct"]
    assert months[:8] == [1.0] * 8 and months[8:] == [None] * 4
    assert i["ownership"] is None


def test_slugs_with_dots_and_spaces_resolve(client):
    from app.universe import _slug_key

    assert _slug_key("E NBD") == _slug_key("e%20nbd".replace("%20", " ")) == "ENBD"
    assert _slug_key("ADAV.AD") == "ADAVAD"


# --- QA findings (2026-10-16) -------------------------------------------------------------------


def test_quote_is_dated_by_its_price_not_the_run_date(client):
    # The price file stops in 2018; briefs carries today's run date.
    q = get(client, "/v1/tickers/2010_kse")["quote"]
    assert q["source"] == "prices_file" and q["as_of_date"] == "2018-08-08" and q["last_price"] == 0.04
    assert q["freshness"]["stale"] is True


def test_the_price_file_decides_price_history(client):
    # briefs says no history, the file has two current bars: the header and the chart agree.
    d = get(client, "/v1/tickers/2382")
    assert d["has_price_history"] is True and d["quote"]["source"] == "prices_file"
    assert d["quote"]["last_price"] == 14.54 and d["quote"]["freshness"]["stale"] is False
    assert get(client, "/v1/tickers/2382/prices")["has_history"] is True


def test_ratios_that_mean_nothing_are_null(client):
    # Negative earnings: no P/E (not 0.00x). Negative book value: no P/B, no ROE.
    v = get(client, "/v1/tickers/FAB")["valuation"]
    assert v["pe"] is None and v["pb"] is None and v["roe_pct"] is None


def test_every_screen_shows_the_same_ratios(client):
    v = get(client, "/v1/tickers/2222")["valuation"]
    f = {m["key"]: m["value"] for g in get(client, "/v1/tickers/2222/fundamentals")["groups"] for m in g["metrics"]}
    row = next(r for r in get(client, "/v1/screener") if r["ticker"]["ticker_key"] == "2222_TADAWUL")
    assert (v["pe"], v["pb"], v["dividend_yield_pct"], v["roe_pct"]) == (f["pe"], f["pb"], f["div_yield"], f["roe"])
    assert (row["pe"], row["pb"], row["dividend_yield_pct"], row["roe_pct"]) == (v["pe"], v["pb"], v["dividend_yield_pct"], v["roe_pct"])
    council = {s["seat"]: s["inputs"][0]["value"] for s in get(client, "/v1/tickers/2222/council")["seats"]}
    assert council["value"] == v["pe"] and council["income"] == v["dividend_yield_pct"]


def test_the_default_sector_bucket_is_not_a_sector(client):
    # 1111 is labelled "Energy" through sector_id 1, the pipeline's unclassified bucket.
    assert get(client, "/v1/tickers/1111")["ticker"]["sector_en"] is None
    peers = [p["ticker"]["ticker_key"] for p in get(client, "/v1/tickers/2222/peers")["peers"]]
    assert "1111_TADAWUL" not in peers and "2223_TADAWUL" in peers
