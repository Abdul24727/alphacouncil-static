from app.prices import _num


def test_number_formats():
    assert _num('"3,829,048"'.strip('"')) == 3829048
    assert _num("(0.02)") == -0.02
    assert _num("(0.11 %)") == -0.11
    assert _num("") is None and _num(" %") is None


def test_english_file_day_first_dates(client):
    p = client.get("/v1/tickers/2222/prices").json()
    assert p["has_history"] is True
    assert p["bars"][0]["time"] == "2019-12-11"
    last = p["bars"][-1]
    assert last["close"] == 26.5 and last["volume"] == 9327140 and last["turnover"] == 248170145
    assert p["freshness"]["category"] == "prices"


def test_arabic_file_year_first_dates_and_bad_range_is_close_only(client):
    bars = client.get("/v1/tickers/FAB/prices").json()["bars"]
    assert [b["time"] for b in bars] == ["2026-10-12", "2026-10-13", "2026-10-14"]
    assert bars[0]["volume"] == 3829048
    # 2026-10-14: open 19.50 above high 18.95 cannot be a real bar; keep the close, drop the range.
    assert bars[2]["close"] == 18.9 and bars[2]["open"] is None and bars[2]["high"] is None


def test_no_price_file_means_no_history(client):
    p = client.get("/v1/tickers/EMAAR/prices").json()
    assert p["has_history"] is False and p["bars"] == [] and p["freshness"] is None


def test_quote_uses_the_newer_price_file(client):
    q = client.get("/v1/tickers/2222").json()["quote"]
    assert q["source"] == "prices_file"
    assert q["last_price"] == 26.5
    assert q["day_change_pct"] == round((26.5 / 26.0 - 1) * 100, 2)


def test_list_marks_tickers_with_prices(client):
    rows = client.get("/v1/tickers").json()
    has = {r["ticker_key"]: r["has_prices"] for r in rows}
    assert has["2222_TADAWUL"] and has["FAB_ADX"] and not has["EMAAR_DFM"]
    assert rows[0]["exchange"] == "TADAWUL"
