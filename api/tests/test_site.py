from app import council

from .conftest import BRIEFS


def test_plans_match_the_checkout_configuration(client, monkeypatch):
    p = client.get("/v1/plans").json()
    assert [x["id"] for x in p["plans"]] == ["free", "pro"]  # Elite parked, as on the live site
    assert p["plans"][1]["price_sar"] == 79 and p["currency"] == "SAR" and p["interval"] == "monthly"
    assert p["provider"] == "moyasar" and p["checkout_open"] is False

    # The checkout's environment overrides reach /pricing too.
    monkeypatch.setenv("PRICE_PRO_SAR", "99")
    monkeypatch.setenv("ELITE_ENABLED", "true")
    p = client.get("/v1/plans").json()
    assert [x["price_sar"] for x in p["plans"]] == [0, 99, 399]


def test_methodology_comes_from_the_rules_and_the_database(client):
    m = client.get("/v1/methodology").json()
    assert [s["seat"] for s in m["seats"]] == list(council.SEATS)
    value = next(s for s in m["seats"] if s["seat"] == "value")
    assert value["thresholds"] == {"pe_bullish_below": 10, "pe_neutral_below": 16}
    assert value["inputs"] == ["pe"]

    cats = {(f["category"], f["max_age_days"]): f for f in m["freshness"]}
    assert cats[("prices", 2)]["trading_days"] is True and cats[("prices", 2)]["tickers"] == 1
    assert cats[("fundamentals", 100)]["trading_days"] is False

    assert m["equities"] == len(BRIEFS)
    assert sum(e["equities"] for e in m["exchanges"]) == len(BRIEFS)
    adx = next(e for e in m["exchanges"] if e["exchange"] == "ADX")
    assert adx["weekend"] == [5, 6]
    assert m["pipeline_run_utc"] == "00:00"


def test_seat_rules_follow_the_thresholds(monkeypatch):
    monkeypatch.setitem(council.THRESHOLDS, "value", {"pe_bullish_below": 12, "pe_neutral_below": 20})
    s = council.value_seat(11)
    assert s.vote == "bullish" and "below 12" in s.rule and "below 20" in s.rule
