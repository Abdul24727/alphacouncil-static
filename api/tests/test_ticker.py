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


def test_ownership_keeps_one_point_per_day_and_named_holders():
    from app.routers.ticker_research import _ownership

    o = _ownership(
        {
            "foreign_series": [{"date": "2026-10-11", "pct": 0.71}, {"date": "2026-10-08", "pct": 0.72}, {"date": "2026-10-11", "pct": 0.72}],
            "major_holders": [{"name": "Kingdom of Saudi Arabia", "pct": 81.48}, {"name": "0.00 %", "pct": 0.0}],
            "recent_changes": [{"name": "", "change": 1.0}],
        }
    )
    assert o["foreign_series"] == [{"date": "2026-10-08", "pct": 0.72}, {"date": "2026-10-11", "pct": 0.72}]
    assert [h["name"] for h in o["major_holders"]] == ["Kingdom of Saudi Arabia"]
    assert o["recent_changes"] == []


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


def test_news_prefers_the_page_language_and_keeps_date_order():
    from types import SimpleNamespace as N

    from app.routers.ticker import prefer_language

    items = [N(id=1, lang="ar"), N(id=2, lang="en"), N(id=3, lang="ar"), N(id=4, lang="en"), N(id=5, lang="ar")]
    assert [i.id for i in prefer_language(items, "en", 3)] == [1, 2, 4]  # both English, topped up by the newest
    assert [i.id for i in prefer_language(items, "ar", 3)] == [1, 3, 5]
    assert [i.id for i in prefer_language(items, None, 2)] == [1, 2]


def test_an_item_with_a_summary_in_the_page_language_counts_as_readable():
    from types import SimpleNamespace as N

    from app.routers.ticker import readable_first

    def item(id, lang, title_en=None, summary_en=None, summary_ar=None):
        return N(id=id, lang=lang, title_en=title_en, summary_en=summary_en, summary_ar=summary_ar)

    items = [item(1, "ar"), item(2, "en"), item(3, "ar", summary_en="Up"), item(4, "ar", title_en="Headline"), item(5, "en", summary_ar="صعود")]
    assert [i.id for i in readable_first(items, "en", 3)] == [2, 3, 4]
    assert [i.id for i in readable_first(items, "ar", 3)] == [1, 3, 4]  # the Arabic items lead; no others needed
    assert [i.id for i in readable_first(items, "ar", 4)] == [1, 3, 4, 5]


# --- data fixes (audit 2026-10-18) ----------------------------------------------------------------


def test_news_light_follows_the_newest_item_not_the_fetch(client):
    # All three were fetched yesterday. 2222 has a news item today: fresh. 1120's newest
    # disclosure is from January (its event today is not news): stale. 2223 has none: unknown.
    def news(ref):
        return next(f for f in get(client, f"/v1/tickers/{ref}")["freshness"] if f["category"] == "news")

    fresh, old, none = news("2222"), news("1120"), news("2223")
    assert fresh["stale"] is False and fresh["max_age_days"] == 30
    assert old["stale"] is True and old["as_of"].startswith("2026-01-05")
    assert old["updated_at"] is not None  # the fetch time stays visible as "updated"
    assert none["stale"] is None and none["as_of"] is None
    disclosures = next(f for f in get(client, "/v1/tickers/1120")["freshness"] if f["category"] == "disclosures")
    assert disclosures["stale"] is True and disclosures["max_age_days"] == 120


def test_a_late_news_fetch_is_stale_even_with_a_recent_item():
    from app.freshness import assess_items

    now = datetime(2026, 10, 18, 9, tzinfo=UTC)
    late = assess_items(category="news", newest_item="2026-10-15T21:00:00", last_success_utc="2026-07-25T00:06:15+00:00",
                        max_age_days=2, exchange="TADAWUL", now=now)
    assert late.stale is True
    ok = assess_items(category="news", newest_item="2026-10-15T21:00:00", last_success_utc="2026-10-18T00:07:00+00:00",
                      max_age_days=2, exchange="TADAWUL", now=now)
    assert ok.stale is False and ok.as_of.startswith("2026-10-15")
    gone = assess_items(category="news", newest_item=None, last_success_utc="2026-07-25T00:06:15+00:00",
                        max_age_days=2, exchange="TADAWUL", now=now)
    assert gone.stale is True


def test_methodology_states_the_news_window(client):
    rules = {r["category"]: r for r in get(client, "/v1/methodology")["freshness"]}
    assert rules["news"]["max_age_days"] == 30 and rules["news"]["trading_days"] is False
    assert rules["prices"]["trading_days"] is True


def test_value_traded_says_when_the_price_file_never_records_it(client, data_files):
    # Like every Tadawul file: a turnover column that is empty on every bar.
    path = data_files.universe_root / "1111_TADAWUL" / "price_history_10y.csv"
    path.parent.mkdir(parents=True)
    path.write_text("Date,Price,Change,Change (%),Volume,Turnover,Open,High,Low\n"
                    "2026/10/14,160.00,,,1000,,159.0,161.0,158.0\n2026/10/15,161.00,,,1200,,160.0,162.0,159.5\n",
                    encoding="utf-8")
    q = get(client, "/v1/tickers/1111")["quote"]
    assert q["value_traded"] is None and q["value_traded_reason"] == "not_in_price_file"
    # FAB's last bar lacks turnover but earlier bars have it: plainly unavailable, no reason.
    q = get(client, "/v1/tickers/FAB")["quote"]
    assert q["value_traded"] is None and q["value_traded_reason"] is None
    assert get(client, "/v1/tickers/2222")["quote"]["value_traded_reason"] is None


def test_eps_shows_only_in_a_confirmed_unit():
    from app.ratios import eps_in_price_unit

    # Values as the pipeline stores them (2026-10-18): EPS, P/E, price.
    assert eps_in_price_unit(1.84, 14.47, 26.5, ["SAR"]) == 1.84  # Aramco: the price's unit
    assert eps_in_price_unit(63.74, 12.79, 0.815, ["KWD"]) == 0.06374  # NBK: fils
    assert eps_in_price_unit(27.73, 17.85, 0.495, ["BHD"]) == 0.02773  # BMMI: fils
    assert eps_in_price_unit(28.51, 13.33, 3.8, ["AED"]) == 0.2851  # ADNOCDIST: fils (1/100 AED)
    assert eps_in_price_unit(0.03, 33.24, 0.94, ["BHD"]) == 0.03  # ARIG: already in the price's unit
    assert eps_in_price_unit(3349.32, 16.43, 5.5, ["AED"]) is None  # ADNOCDRILL: 10,000x, no unit
    assert eps_in_price_unit(2901.85, 6.89, 0.2, ["KWD"]) is None  # 811: 100,000x
    assert eps_in_price_unit(32.18, 23.54, 2.47, ["KWD"]) is None  # KFH Bahrain: fils of KWD, price in USD
    assert eps_in_price_unit(75.78, 11.42, 0.87, ["AED"]) is None  # Mazaya on DFM: 1000x is not an AED unit
    assert eps_in_price_unit(-6.23, None, 0.39, ["KWD"]) is None  # a loss: no P/E to check against
    assert eps_in_price_unit(-1.06, 98.73, 80.05, ["SAR"]) is None  # 4144: EPS contradicts its P/E


def test_detail_gives_eps_in_the_price_unit_or_says_why_not(client):
    v = get(client, "/v1/tickers/2222")["valuation"]
    assert v["eps_ttm"] == 1.84 and v["eps_ttm_reason"] is None
    v = get(client, "/v1/tickers/FAB")["valuation"]  # negative earnings: no P/E to confirm the unit
    assert v["eps_ttm"] is None and v["eps_ttm_reason"] == "unit_unconfirmed"
    v = get(client, "/v1/tickers/1120")["valuation"]  # no EPS in the database: nothing to explain
    assert v["eps_ttm"] is None and v["eps_ttm_reason"] is None


def test_a_currency_the_exchange_does_not_trade_in_is_not_shown(client, data_files):
    import sqlite3

    # Like National Industries on DFM: the pipeline gives it KWD, DFM trades in AED.
    row = ("NIND_DFM", "NIND", "DFM", "KWD", 3, "Industrials", "الصناعة", datetime.now(UTC).date().isoformat(), 3.37, 0.0, 1e4, None, 8527.58,
           14.26, None, None, None, None, None, None, None, None, None, None, 0, None)
    with sqlite3.connect(data_files.briefs_db) as conn:
        conn.execute(f"INSERT INTO briefs VALUES ({','.join('?' * len(row))})", row)
    with sqlite3.connect(data_files.screening_db) as conn:
        conn.execute("INSERT INTO scraped_ratios VALUES ('NIND_DFM', 14.26, 1.24, NULL, NULL, NULL, NULL, NULL, 2.75, 236.21, NULL, 2530.44)")
    d = get(client, "/v1/tickers/NIND")
    assert d["ticker"]["currency"] is None
    # Its EPS is in fils of the pipeline's currency: confirmed by the P/E, so shown in the price's unit.
    assert d["valuation"]["eps_ttm"] == 0.23621
    assert get(client, "/v1/tickers/FAB")["ticker"]["currency"] == "AED"


def test_a_mislabelled_tadawul_sector_is_not_shown(client, data_files):
    import sqlite3

    # Like 2280 Almarai: sector_id 8, which the pipeline names "Transportation" (food producers).
    row = ("2280_TADAWUL", "2280", "TADAWUL", "SAR", 8, "Transportation", "النقل", datetime.now(UTC).date().isoformat(),
           50.0, 0.0, 1e5, None, 50000.0, None, None, None, None, None, None, None, None, None, None, None, 0, None)
    with sqlite3.connect(data_files.briefs_db) as conn:
        conn.execute(f"INSERT INTO briefs VALUES ({','.join('?' * len(row))})", row)
    assert get(client, "/v1/tickers/2280")["ticker"]["sector_en"] is None
    p = get(client, "/v1/tickers/2280/peers")
    assert p["sector_en"] is None and p["peers"] == []
    assert "Transportation" not in {s["sector_en"] for s in get(client, "/v1/templates/sectors")}
    # A right label on another id stays (fixture rows without an id keep theirs).
    assert get(client, "/v1/tickers/1120")["ticker"]["sector_en"] == "Banks"
