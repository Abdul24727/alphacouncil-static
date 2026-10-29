"""The financial evidence a council seat reads: reported figures, derived figures, stated gaps.

Every test here asserts a property the Council depends on rather than a value a fixture happens
to hold: that a reconstructed annual figure is the sum of standalone quarters and not of
cumulative ones, that a derivation with no supported denominator yields nothing, that a ratio
names the denominator it divided by, that a bank is not handed a price-to-sales ratio, that a
gauge computed from statements since refreshed is withheld, and that the dataset stays inside
its budget.
"""

import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import main
from app.evidence import (
    DATASET_BUDGET,
    bounded_statements,
    calculations,
    dataset_of,
    encoded_length,
    load_items,
    period_aware,
    sector_of,
    stale_reason,
    window_of,
)

REPAIRED_SCHEMA = [
    "CREATE TABLE fundamentals_lineitems (ticker_key TEXT, ticker TEXT, exchange TEXT,"
    " fiscal_year INT, section TEXT, item_index INT, line_item_label TEXT, value REAL,"
    " period TEXT, period_end TEXT, source_json TEXT)",
    "CREATE TABLE fundamentals_lineitems_quarterly (ticker_key TEXT, ticker TEXT, exchange TEXT,"
    " fiscal_year INT, period TEXT, period_end TEXT, section TEXT, item_index INT,"
    " line_item_label TEXT, value REAL, source_json TEXT)",
    "CREATE TABLE fundamentals_gauges (ticker_key TEXT, gauge_key TEXT, value REAL, status TEXT,"
    " inputs_json TEXT, score REAL)",
    "CREATE TABLE dividends (ticker_key TEXT, announce_date TEXT, ex_date TEXT, pay_date TEXT,"
    " amount_mn REAL, dps REAL, note TEXT)",
    "CREATE TABLE stocks (ticker_key TEXT, pb REAL, roe_pct REAL, roa_pct REAL,"
    " dividend_yield_pct REAL)",
    "CREATE TABLE scraped_ratios (ticker_key TEXT, pe REAL, pb REAL, div_yield REAL, roe REAL,"
    " roa REAL, ev_ebitda REAL, ev_revenue REAL, book_value REAL, eps_ttm REAL,"
    " market_cap_mn REAL, shares_out_mn REAL)",
    "CREATE TABLE ticker_freshness (ticker_key TEXT, category TEXT, as_of_utc TEXT,"
    " last_success_utc TEXT, max_age_days REAL, is_stale INT, item_count INT)",
    "CREATE TABLE capital_changes (ticker_key TEXT, date TEXT, change_type TEXT,"
    " capital_before_mn REAL, shares_before_mn REAL, capital_after_mn REAL, shares_after_mn REAL,"
    " change_pct REAL, note REAL)",
    "CREATE TABLE ticker_insights (ticker_key TEXT, updated_at TEXT, data_json TEXT)",
]

# The four standalone quarters an industrial company reported, and the trailing-twelve-month
# figures that summing them gives. Shaped like Aramco's: a share count that does not move, an
# extraordinary charge inside the window, and no cash-flow statement at all.
QUARTERS = ["2025-09", "2025-12", "2026-03", "2026-06"]
SUM_SRC = json.dumps({"rule": "sum_quarters", "window": QUARTERS, "mode": "quarterly_reconstructed"})
END_SRC = json.dumps({"rule": "end_quarter_position", "quarter": "2026-06",
                      "window": QUARTERS, "mode": "quarterly_reconstructed"})
SNAP_SRC = json.dumps({"rule": "quarter_end_snapshot", "quarter": "2026-06"})
ANNUAL_SRC = json.dumps({"rule": "year_end_snapshot", "quarter": "2025-12"})

INDUSTRIAL_QUARTERLY = [
    ("Sales", [400.0, 420.0, 430.0, 450.0]),
    ("Gross Income", [100.0, 110.0, 108.0, 120.0]),
    ("Operating Income", [80.0, 88.0, 86.0, 96.0]),
    ("Net Profit Before Unusual Items", [60.0, 66.0, 64.0, 70.0]),
    ("Extraordinary income/expense", [0.0, -20.0, 0.0, 0.0]),
    ("Net Income", [60.0, 46.0, 64.0, 70.0]),
    ("Earning Per Share (Riyal)", [0.6, 0.46, 0.64, 0.7]),
    ("Shares Outstanding (Million)", [100.0, 100.0, 100.0, 100.0]),
]
BANK_QUARTERLY = [
    ("Operating Income", [50.0, 52.0, 54.0, 56.0]),
    ("Operating Expenses", [-12.0, -12.5, -13.0, -13.5]),
    ("Net income from investments and financing activities", [40.0, 41.0, 42.0, 43.0]),
    ("Debt Provisions", [-3.0, -3.0, -3.5, -3.5]),
    ("Net Income", [30.0, 31.0, 32.0, 33.0]),
    ("Shares Outstanding (Million)", [20.0, 20.0, 20.0, 20.0]),
]


def _write(path, rows):
    conn = sqlite3.connect(path)
    for ddl in REPAIRED_SCHEMA:
        conn.execute(ddl)
    for table, values in rows.items():
        if values:
            marks = ",".join("?" for _ in values[0])
            conn.executemany(f"INSERT INTO {table} VALUES ({marks})", values)
    conn.commit()
    conn.close()


def _flows(tk, quarterly, *, shares_moved=False, average_shares=None):
    """One income statement reconstructed from four quarters, plus the quarters themselves."""
    main_rows, quarter_rows = [], []
    for index, (label, values) in enumerate(quarterly):
        position = "Shares" in label
        if position and shares_moved:
            values = [values[0], values[1], values[2] * 1.2, values[3] * 1.2]
        total = values[-1] if position else sum(values)
        main_rows.append((tk, tk.split("_")[0], "TADAWUL", 2026, "Income Statement", index, label,
                          total, "TTM", "2026-06", END_SRC if position else SUM_SRC))
        for end, value in zip(QUARTERS, values, strict=True):
            quarter_rows.append((tk, tk.split("_")[0], "TADAWUL", int(end[:4]), "Q", end,
                                 "Income Statement", index, label, value,
                                 json.dumps({"rule": "single_quarter", "quarter": end})))
    if average_shares is not None:
        main_rows.append((tk, tk.split("_")[0], "TADAWUL", 2026, "Income Statement",
                          len(quarterly), "Average number of shares (Million)", average_shares,
                          "TTM", "2026-06",
                          json.dumps({"rule": "mean_of_quarters", "window": QUARTERS})))
    return main_rows, quarter_rows


def _balance(tk, labels, *, year=2026, period="Q", end="2026-06", src=SNAP_SRC):
    return [
        (tk, tk.split("_")[0], "TADAWUL", year, "Balance Sheet", index, label, value, period, end, src)
        for index, (label, value) in enumerate(labels)
    ]


INDUSTRIAL_BALANCE = [
    ("Cash & Cash Equivalents", 150.0), ("Total Current Assets", 600.0),
    ("Total Assets", 2000.0), ("Total Current liabilities", 300.0),
    ("Total Liabilities", 800.0), ("Gross Income", None),
    ("Total Shareholders' Equity", 1000.0), ("Minority Interest", 200.0),
    ("Total Owners Equity", 1200.0), ("Shares Outstanding (Million)", 100.0),
    ("Book Value Per Share (Riyal)", 10.0),
]
BANK_BALANCE = [
    ("Cash & Balances with Central Bank", 60.0), ("Due from Banks", 30.0),
    ("Investments", 200.0), ("Net Financing Investments", 800.0),
    ("Performing Financing Investments", 804.0),
    ("Non-performing Financing Investments", 6.0),
    ("Financing Investments Loss Provision", -10.0), ("Total Assets", 1100.0),
    ("Customer Deposits", 700.0), ("Due to Banks", 100.0), ("Term Sukuk", 70.0),
    ("Total Liabilities", 940.0), ("Total Shareholders' Equity", 130.0),
    ("Equity Sukuk", 30.0), ("Total Owners' Equity", 160.0),
    ("Shares Outstanding (Million)", 20.0),
]

DIVIDENDS = [
    # inside the window 2025-07-01 .. 2026-06-30
    ("2222_TADAWUL", "2025-08-05", "2025-08-19", "2025-08-28", 20.0, 0.20, "Q 2 _ 2025"),
    ("2222_TADAWUL", "2025-11-04", "2025-11-17", "2025-11-26", 20.0, 0.20, "Q 3 _ 2025"),
    ("2222_TADAWUL", "2026-03-10", "2026-03-16", "2026-03-31", 21.0, 0.21, "Q 4 _ 2025"),
    ("2222_TADAWUL", "2026-05-10", "2026-06-01", "2026-06-09", 21.0, 0.21, "Q 1 _ 2026"),
    # declared and paid AFTER the window: counting it is the mistake this guards against
    ("2222_TADAWUL", "2026-08-04", "2026-08-19", "2026-08-27", 80.0, 0.80, "Q 2 _ 2026"),
    # a company paying dividends through a loss year: the payout is not computable, the
    # dividends per share still are, and a seat should see both
    ("2010_TADAWUL", "2025-08-03", "2025-08-19", "2025-09-09", 45.0, 1.50, "H 1 _ 2025"),
    ("2010_TADAWUL", "2026-03-04", "2026-03-08", "2026-03-31", 45.0, 1.50, "H 2 _ 2025"),
]


def vintage(**kw):
    return json.dumps({"fiscal_year": 2026, "period": "TTM", "period_end": "2026-06",
                       "position_at": "2026-06", "sector": "non_bank", **kw})


@pytest.fixture
def repaired(tmp_path):
    """A screening database as the repaired pipeline leaves it: three companies, with periods."""
    path = tmp_path / "repaired.sqlite"
    ind_main, ind_q = _flows("2222_TADAWUL", INDUSTRIAL_QUARTERLY)
    bank_main, bank_q = _flows("1120_TADAWUL", BANK_QUARTERLY)
    loss_main, loss_q = _flows(
        "2010_TADAWUL",
        [("Sales", [300.0, 280.0, 260.0, 250.0]),
         ("Gross Income", [60.0, 40.0, 50.0, 44.0]),
         ("Net Profit Before Unusual Items", [5.0, -50.0, 2.0, -3.0]),
         ("Extraordinary income/expense", [-1.0, -160.0, -2.0, -6.0]),
         ("Net Income", [4.0, -210.0, 0.0, -9.0]),
         ("Earning Per Share (Riyal)", [0.04, -2.1, 0.0, -0.09]),
         ("Shares Outstanding (Million)", [100.0, 100.0, 100.0, 100.0])],
    )
    _write(path, {
        "fundamentals_lineitems": [
            *ind_main, *_balance("2222_TADAWUL", INDUSTRIAL_BALANCE),
            *_balance("2222_TADAWUL", INDUSTRIAL_BALANCE, year=2025, period="FY", end="2025-12",
                      src=ANNUAL_SRC),
            *bank_main, *_balance("1120_TADAWUL", BANK_BALANCE),
            *loss_main, *_balance("2010_TADAWUL", INDUSTRIAL_BALANCE),
        ],
        "fundamentals_lineitems_quarterly": [*ind_q, *bank_q, *loss_q],
        "fundamentals_gauges": [
            ("2222_TADAWUL", "net_margin", 14.0, "ok", vintage(), 61.0),
            ("2222_TADAWUL", "ps", 3.0, "ok", vintage(), 44.0),
            ("1120_TADAWUL", "ps", None, "missing_inputs",
             vintage(sector="bank", missing="Revenue/Sales line",
                     searched=["Sales", "Total Revenue"], expected_section="Income Statement",
                     available_in_section=["Operating Income", "Net Income"]), None),
            ("1120_TADAWUL", "net_margin", None, "missing_inputs", vintage(sector="bank"), None),
            ("2010_TADAWUL", "net_margin", -70.0, "ok", vintage(), 4.0),
        ],
        "dividends": DIVIDENDS,
        "stocks": [("2222_TADAWUL", None, None, None, None)],
        "scraped_ratios": [("2222_TADAWUL", 14.0, 4.0, 5.0, 26.0, 15.0, None, None, 10.0, 1.8,
                            None, 100.0)],
        "ticker_freshness": [],
        "capital_changes": [],
        "ticker_insights": [],
    })
    return path


@pytest.fixture
def conn(repaired):
    c = sqlite3.connect(repaired)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


@pytest.fixture
def repaired_client(data_files, repaired, monkeypatch):
    settings = data_files.model_copy(update={"screening_db": repaired})
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    return TestClient(main.create_app())


def get(client, path, status=200):
    r = client.get(path)
    assert r.status_code == status, r.text
    return r.json()


def dataset(conn, tk, **kw):
    items = load_items(conn, tk, years=2)
    divs = [dict(d) for d in conn.execute(
        "SELECT announce_date, ex_date, pay_date, dps, amount_mn, note FROM dividends"
        " WHERE ticker_key = ?", (tk,))]
    return dataset_of(items, ticker_key=tk, sector=sector_of(items, {}), currency="SAR",
                      dividends=divs, **kw)


def metric(ds, name):
    return next(c for c in ds.calculations if c.metric == name)


# --- reported figures -------------------------------------------------------------------------


def test_an_annual_figure_is_the_sum_of_standalone_quarters(conn):
    """The repair rests on this reading. Four columns of 400, 420, 430 and 450 are four quarters
    that add to 1,700; read as year-to-date they would mean a fiscal year of 450 and a quarter of
    10. Both the annual row and the quarters are in the dataset, so the reading is checkable
    rather than asserted."""
    ds = dataset(conn, "2222_TADAWUL")
    income = next(s for s in ds.statements if s.section == "Income Statement")
    sales = next(r for r in income.rows if r[0] == "Sales")
    assert sales[1] == pytest.approx(1700.0)
    assert income.period == "TTM" and income.period_end == "2026-06"
    assert income.aggregation == "sum_quarters"
    assert income.source_columns == QUARTERS
    quarters = next(r for r in ds.quarters.rows if r[0] == "Sales")
    assert quarters[1:] == [400.0, 420.0, 430.0, 450.0]
    assert sum(quarters[1:]) == pytest.approx(sales[1])
    assert "standalone and not cumulative" in ds.quarters.note


def test_a_share_count_is_a_position_and_says_so(conn):
    ds = dataset(conn, "2222_TADAWUL")
    income = next(s for s in ds.statements if s.section == "Income Statement")
    shares = next(r for r in income.rows if r[0] == "Shares Outstanding (Million)")
    assert shares[1] == 100.0, "a position must not be summed over the window"
    assert income.row_rules["Shares Outstanding (Million)"] == "end_quarter_position"


def test_the_statements_keep_the_rows_the_calculations_divide_by(conn):
    """The row cap must never drop a line a calculation uses. On a Tadawul balance sheet the
    share count is the last row, so taking the first N would drop it."""
    items = load_items(conn, "2222_TADAWUL", years=2)
    for statement in bounded_statements(items):
        labels = {r[0] for r in statement.rows}
        if statement.section == "Balance Sheet":
            assert "Shares Outstanding (Million)" in labels
            assert "Total Shareholders' Equity" in labels


def test_no_cash_flow_statement_is_stated_rather_than_left_to_be_noticed(conn):
    ds = dataset(conn, "2222_TADAWUL")
    assert any("NO CASH FLOW STATEMENT" in lim for lim in ds.limitations)
    assert any("never against cash" in lim for lim in ds.limitations)


# --- derived figures, and the ones that are withheld -------------------------------------------


def test_derived_eps_is_withheld_when_the_share_count_moved_inside_the_window(tmp_path):
    """An end-of-period position is not a supported denominator for a flow when the count moved.
    The wrong answer here is plausible: 240 / 120 = 2.00 against a true 2.22, and nothing on the
    face of it says which."""
    path = tmp_path / "moved.sqlite"
    main_rows, quarter_rows = _flows("2222_TADAWUL", INDUSTRIAL_QUARTERLY, shares_moved=True)
    _write(path, {"fundamentals_lineitems": [*main_rows, *_balance("2222_TADAWUL", INDUSTRIAL_BALANCE)],
                  "fundamentals_lineitems_quarterly": quarter_rows})
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    eps = metric(dataset(c, "2222_TADAWUL"), "eps_derived")
    assert eps.value is None
    assert "moved inside the window" in eps.missing[0]
    assert "120" in eps.missing[0], "the reason must show the counts it saw"
    c.close()


def test_derived_eps_is_given_when_the_count_held_still(conn):
    eps = metric(dataset(conn, "2222_TADAWUL"), "eps_derived")
    assert eps.value == pytest.approx(240.0 / 100.0, abs=1e-4)
    assert "unchanged through every quarter" in eps.denominator
    assert eps.checks and "within 2%" in eps.checks[0]


def test_an_average_share_row_is_preferred_to_a_closing_position(tmp_path):
    """"Average number of shares" contains "number of shares", so the test order matters: an
    average row must be recognised before any position marker."""
    path = tmp_path / "average.sqlite"
    main_rows, quarter_rows = _flows("2222_TADAWUL", INDUSTRIAL_QUARTERLY, shares_moved=True,
                                     average_shares=110.0)
    _write(path, {"fundamentals_lineitems": [*main_rows, *_balance("2222_TADAWUL", INDUSTRIAL_BALANCE)],
                  "fundamentals_lineitems_quarterly": quarter_rows})
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    eps = metric(dataset(c, "2222_TADAWUL"), "eps_derived")
    assert eps.value == pytest.approx(240.0 / 110.0, abs=1e-4)
    assert "mean share count over the window" in eps.denominator
    c.close()


def test_the_roe_denominator_is_named_and_is_not_the_one_including_minority_interest(conn):
    roe = metric(dataset(conn, "2222_TADAWUL"), "roe_on_period_end_common_equity")
    assert roe.value == pytest.approx(24.0)  # 240 / 1000
    assert "Total Shareholders' Equity" in roe.denominator
    assert "NOT an average" in roe.denominator
    assert "Total Owners Equity" in roe.denominator and "minority interest" in roe.denominator
    assert any("average equity" in c for c in roe.checks), "the alternative must be visible"


def test_a_return_on_negative_equity_is_withheld(tmp_path):
    """A loss over negative equity comes back positive and large. Found in the live data: a loss
    of 125.17 over equity of -18.99 reads as +659%, which is not a return at all."""
    path = tmp_path / "insolvent.sqlite"
    main_rows, quarter_rows = _flows("2222_TADAWUL", INDUSTRIAL_QUARTERLY)
    balance = [(label, -1000.0 if label == "Total Shareholders' Equity" else value)
               for label, value in INDUSTRIAL_BALANCE]
    _write(path, {"fundamentals_lineitems": [*main_rows, *_balance("2222_TADAWUL", balance)],
                  "fundamentals_lineitems_quarterly": quarter_rows})
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    roe = metric(dataset(c, "2222_TADAWUL"), "roe_on_period_end_common_equity")
    assert roe.value is None
    assert "negative equity" in roe.missing[0] and "-1,000.00" in roe.missing[0]
    assert roe.operands, "the operands it would have divided are still named"
    c.close()


def test_the_unit_check_confirms_eps_without_needing_a_price_earnings_ratio(conn):
    """A loss-making company has no meaningful P/E, so the pipeline cannot confirm its EPS unit
    that way and publishes none. The statements can confirm it against each other."""
    check = metric(dataset(conn, "2010_TADAWUL"), "eps_unit_confirmation")
    assert check.value == pytest.approx(-215.0)  # -2.15 x 100
    assert "statement's own unit" in check.checks[0]


def test_an_extraordinary_charge_is_separated_from_the_underlying_result(conn):
    ds = dataset(conn, "2010_TADAWUL")
    share = metric(ds, "extraordinary_share_of_earnings")
    assert share.value == pytest.approx(-78.6047, abs=1e-3)  # (-215 - -46) / 215
    assert any("they agree" in c for c in share.checks)
    assert "absolute value" in share.denominator


def test_a_payout_is_not_computed_on_a_loss_but_the_dividends_are_still_shown(conn):
    """The tension a seat should see: dividends of 3.00 a share against a loss of 2.15 a share.
    A payout ratio over a negative denominator would be a number with no meaning."""
    ds = dataset(conn, "2010_TADAWUL")
    payout = metric(ds, "payout_cash")
    assert payout.value is None and "not positive" in payout.missing[0]
    assert payout.operands, "the dividends it matched are still named"
    assert metric(ds, "dps_window").value == pytest.approx(3.0, abs=1e-4)


# --- the dividend window ----------------------------------------------------------------------


def test_the_dividend_window_is_the_earnings_window_and_nothing_wider(conn):
    """Matching dividends by their fiscal-year label counts a dividend declared after the window
    and reports a payout close to 100%. Matched by date, the four inside the window give 34%."""
    ds = dataset(conn, "2222_TADAWUL")
    cash = metric(ds, "payout_cash")
    assert cash.value == pytest.approx(82.0 / 240.0 * 100.0, abs=1e-4)
    assert len([o for o in cash.operands if o[2] == "dividend history"]) == 4
    assert not any("2026-08" in str(o[0]) for o in cash.operands), \
        "the dividend paid after the window must not be counted"
    naive = (82.0 + 80.0) / 240.0 * 100.0
    assert naive > 65.0 and cash.value < naive, "the guarded error is a materially higher payout"
    assert "company totals" in cash.checks[1]


def test_a_window_is_derived_from_the_reporting_mode_not_the_fiscal_year_label():
    assert window_of("TTM", "2026-06") == ("2025-07-01", "2026-06-30")
    assert window_of("FY", "2025-12") == ("2025-01-01", "2025-12-31")
    assert window_of("Q", "2026-06") == ("2026-04-01", "2026-06-30")
    assert window_of(None, None, 2025) == ("2025-01-01", "2025-12-31")
    assert window_of(None, None) is None


def test_without_an_income_statement_there_is_no_window_and_so_no_payout(tmp_path):
    path = tmp_path / "balance-only.sqlite"
    _write(path, {"fundamentals_lineitems": _balance("2222_TADAWUL", INDUSTRIAL_BALANCE,
                                                     year=2025, period="FY", end="2025-12"),
                  "dividends": DIVIDENDS})
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    payout = metric(dataset(c, "2222_TADAWUL"), "payout_cash")
    assert payout.value is None and "no earnings window" in payout.missing[0]
    c.close()


# --- banks ------------------------------------------------------------------------------------


def test_a_bank_gets_the_measures_a_bank_is_read_on(conn):
    ds = dataset(conn, "1120_TADAWUL")
    assert ds.sector == "bank"
    got = {c.metric: c for c in ds.calculations}
    assert got["cost_to_income"].value == pytest.approx(51.0 / 212.0 * 100.0, abs=1e-4)
    assert got["npl_ratio"].value == pytest.approx(6.0 / 810.0 * 100.0, abs=1e-4)
    assert got["npl_coverage"].value == pytest.approx(10.0 / 6.0 * 100.0, abs=1e-4)
    assert got["financing_to_deposits"].value == pytest.approx(800.0 / 700.0 * 100.0, abs=1e-4)
    assert got["net_financing_margin"].value == pytest.approx(166.0 / 1000.0 * 100.0)
    assert "Due from banks" in got["net_financing_margin"].denominator
    assert "NOT a regulatory capital ratio" in got["equity_to_assets"].denominator
    assert "equity sukuk" in got["roe_on_period_end_common_equity"].denominator


def test_a_bank_is_told_which_generic_ratios_do_not_apply_rather_than_shown_a_gap(repaired_client):
    f = get(repaired_client, "/v1/tickers/1120/fundamentals")
    assert f["sector"] == "bank"
    by_key = {m["key"]: m for g in f["groups"] for m in g["metrics"]}
    assert by_key["ps"]["status"] == "not_meaningful"
    assert by_key["ps"]["value"] is None
    assert "no sales line" in by_key["ps"]["note"]
    assert by_key["net_margin"]["status"] == "not_meaningful"
    assert by_key["current_ratio"]["status"] == "not_meaningful"
    # and nothing forced the bank's operating income into the revenue slot
    assert all(m["sector_percentile"] is None for m in (by_key["ps"], by_key["net_margin"]))


def test_a_company_with_no_line_items_is_not_called_a_bank(conn):
    """The bank test is the absence of two labels, so with nothing to go on every company would
    pass it and the ratios they are read on would be withheld."""
    items = load_items(conn, "NOTHING_HERE", years=2)
    assert sector_of(items, {}) == "unknown"


def test_a_bank_claim_must_be_corroborated_by_the_balance_sheet(conn):
    """Measured on the live database: the pipeline calls 204 tickers banks and only 53 are banks.
    The test behind it is an absence, and the Arabic templates carry neither line for ordinary
    companies either, so a bank claim is only honoured where a bank's own balance sheet lines are
    there to honour it."""
    bank = load_items(conn, "1120_TADAWUL", years=2)
    assert sector_of(bank, {}) == "bank", "it lends and takes deposits"
    assert sector_of(bank, {"ps": {"sector": "bank"}}) == "bank"

    # the industrial company has a current-asset split, so it was never a bank candidate
    industrial = load_items(conn, "2222_TADAWUL", years=2)
    assert sector_of(industrial, {}) == "non_bank"
    # ... and the pipeline calling it one does not make it one
    assert sector_of(industrial, {"ps": {"sector": "bank"}}) == "unknown"
    assert sector_of(industrial, {"ps": {"sector": "insurance"}}) == "insurance", "only bank is checked"


# --- staleness and rankings -------------------------------------------------------------------


def test_a_gauge_from_an_older_fiscal_year_is_withheld(conn):
    items = load_items(conn, "2222_TADAWUL", years=2)
    assert stale_reason(json.loads(vintage()), items) is None
    older = stale_reason(json.loads(vintage(fiscal_year=2025)), items)
    assert older and "has not run since the statements were refreshed" in older
    moved = stale_reason(json.loads(vintage(period_end="2026-03")), items)
    assert moved and "2026-03" in moved
    assert stale_reason({}, items) is None, "a gauge with no stamp cannot be dated"


def test_a_stale_gauge_shows_no_value_and_no_ranking(repaired_client, repaired):
    before = get(repaired_client, "/v1/tickers/2222/fundamentals")
    net_margin = next(m for g in before["groups"] for m in g["metrics"] if m["key"] == "net_margin")
    assert net_margin["status"] == "ok" and net_margin["sector_percentile"] == 61.0
    assert before["stale"] is False

    conn = sqlite3.connect(repaired)
    conn.execute("UPDATE fundamentals_gauges SET inputs_json = ? WHERE ticker_key = '2222_TADAWUL'"
                 " AND gauge_key = 'net_margin'", (vintage(fiscal_year=2025),))
    conn.commit()
    conn.close()

    after = get(repaired_client, "/v1/tickers/2222/fundamentals")
    net_margin = next(m for g in after["groups"] for m in g["metrics"] if m["key"] == "net_margin")
    assert net_margin["status"] == "stale"
    assert net_margin["value"] is None and net_margin["sector_percentile"] is None
    assert after["stale"] is True
    assert next(g for g in after["groups"] if g["group"] == "profitability")["score"] is None


def test_a_gauge_carries_its_definition_and_the_operands_it_divided(repaired_client):
    f = get(repaired_client, "/v1/tickers/2222/fundamentals")
    by_key = {m["key"]: m for g in f["groups"] for m in g["metrics"]}
    assert by_key["net_margin"]["formula"] == "net income / revenue x 100"
    assert by_key["net_margin"]["as_of"]["period"] == "TTM"
    assert by_key["net_margin"]["as_of"]["period_end"] == "2026-06"
    # the published ROE cannot say what it divided by, and says so
    assert "NOT DISCLOSED" in by_key["roe"]["denominator"]
    assert by_key["roe"]["source"] == "published by the data source"


def test_a_missing_gauge_says_what_was_searched_and_what_the_section_holds(repaired_client):
    f = get(repaired_client, "/v1/tickers/1120/fundamentals")
    by_key = {m["key"]: m for g in f["groups"] for m in g["metrics"]}
    payout = by_key["payout"]
    assert payout["value"] is None
    assert payout["note"] is None or "financial-evidence dataset" in payout["note"]


# --- the API's two schemas --------------------------------------------------------------------


def test_statements_carry_the_period_of_every_year_and_the_rule_that_differs(repaired_client):
    s = get(repaired_client, "/v1/tickers/2222/statements")
    assert s["period_aware"] is True
    income = next(x for x in s["statements"] if x["section"] == "Income Statement")
    assert income["periods"]["2026"]["period"] == "TTM"
    assert income["periods"]["2026"]["period_end"] == "2026-06"
    assert income["periods"]["2026"]["source_columns"] == QUARTERS
    balance = next(x for x in s["statements"] if x["section"] == "Balance Sheet")
    # the point of the field: one section, two years, two different windows
    assert balance["periods"]["2026"]["period"] == "Q"
    assert balance["periods"]["2025"]["period"] == "FY"
    assert balance["periods"]["2026"]["period_end"] != balance["periods"]["2025"]["period_end"]
    shares = next(r for r in income["rows"] if r["label"] == "Shares Outstanding (Million)")
    assert shares["rules"]["2026"] == "end_quarter_position"


def test_the_api_still_answers_on_a_database_parsed_before_the_repair(client):
    """The conftest database has no period columns and no quarterly table: the period-aware
    fields come back empty and nothing raises. This is what lets the API and the pipeline be
    deployed in either order."""
    s = get(client, "/v1/tickers/EMAAR_DFM/statements")
    assert s["period_aware"] is False
    income = next(x for x in s["statements"] if x["section"] == "Income Statement")
    assert income["periods"]["2025"]["period"] is None
    assert income["rows"][0]["rules"] == {}
    e = get(client, "/v1/tickers/EMAAR_DFM/evidence")
    assert e["quarters"] is None
    assert any(c["missing"] for c in e["calculations"])


def test_period_awareness_is_read_off_the_schema(conn, repaired, tmp_path):
    assert period_aware(conn) is True
    legacy = tmp_path / "legacy.sqlite"
    c = sqlite3.connect(legacy)
    c.execute("CREATE TABLE fundamentals_lineitems (ticker_key TEXT, fiscal_year INT,"
              " section TEXT, item_index INT, line_item_label TEXT, value REAL)")
    assert period_aware(c) is False
    c.close()


# --- the budget -------------------------------------------------------------------------------


def test_every_company_fits_the_budget_with_its_statements_intact(conn):
    for tk in ("2222_TADAWUL", "1120_TADAWUL", "2010_TADAWUL"):
        ds = dataset(conn, tk)
        assert encoded_length(ds) <= DATASET_BUDGET, tk
        assert ds.statements and ds.calculations


def test_a_tight_budget_drops_rows_and_records_how_many(conn):
    """The trim is a backstop, not the normal path: it drops whole rows and counts them, where a
    truncated prompt would cut one in half and change a figure without saying so."""
    items = load_items(conn, "2222_TADAWUL", years=2)
    full = dataset_of(items, ticker_key="2222_TADAWUL", sector="non_bank", currency="SAR",
                      dividends=[])
    assert sum(s.rows_omitted for s in full.statements) == 0

    tight = dataset_of(items, ticker_key="2222_TADAWUL", sector="non_bank", currency="SAR",
                       dividends=[], budget=encoded_length(full) - 200)
    assert encoded_length(tight) <= encoded_length(full) - 200
    assert sum(s.rows_omitted for s in tight.statements) > 0


def test_a_budget_smaller_than_the_protected_rows_keeps_them_anyway(conn):
    """A budget the evidence cannot meet leaves the figures the calculations divide by, the
    calculations and the limitations in place, and comes back larger than asked. Returning a
    statement that omits its own operands would be worse than returning a long one."""
    items = load_items(conn, "2222_TADAWUL", years=2)
    floor = dataset_of(items, ticker_key="2222_TADAWUL", sector="non_bank", currency="SAR",
                       dividends=[], budget=1_000)
    assert encoded_length(floor) > 1_000
    assert floor.calculations, "calculations are never traded for rows"
    assert floor.limitations, "nor are the limitations"
    balance = next(s for s in floor.statements if s.section == "Balance Sheet")
    labels = {r[0] for r in balance.rows}
    assert "Total Shareholders' Equity" in labels and "Shares Outstanding (Million)" in labels


def test_the_pack_gives_p9_its_own_budget():
    from app.debate.pack import DATASET_CHARS, DATASET_CHARS_BY_TAG

    assert DATASET_CHARS_BY_TAG["P9"] == DATASET_BUDGET
    assert DATASET_CHARS_BY_TAG["P9"] > DATASET_CHARS


# --- reported, derived and opinion stay apart --------------------------------------------------


def test_every_calculation_carries_a_formula_and_either_a_value_or_a_reason(conn):
    for tk in ("2222_TADAWUL", "1120_TADAWUL", "2010_TADAWUL"):
        for c in dataset(conn, tk).calculations:
            assert c.formula, c.metric
            assert (c.value is None) == bool(c.missing), f"{tk}/{c.metric}"
            if c.value is not None:
                assert c.unit and c.operands, c.metric


def test_the_pack_header_separates_reported_derived_and_rule_based(conn):
    from app.debate.pack import DATASETS, header_of
    from app.universe import Ticker

    t = Ticker(ticker_key="2222_TADAWUL", symbol="2222", exchange="TADAWUL", currency="SAR",
               report_currency="SAR", data_currency="SAR", name_en="Test", name_ar=None,
               sector_id=None, sector_en="Energy", sector_ar=None, slug="test",
               _symbol_norm="2222", _names_norm=("test",))
    header = header_of(t, "2026-10-29 00:00 UTC")
    assert "[P9]" in header and "[P4]" in header
    assert "Reported:" in header and "Derived:" in header and "Opinion:" in header
    assert "quote the formula" in header
    assert ("P9", "get_financial_statements") == DATASETS[-1][:2]


def test_the_dataset_says_what_is_reported_and_what_is_derived(conn):
    ds = dataset(conn, "2222_TADAWUL")
    assert "reported" in ds.basis and "derived here" in ds.basis
    assert "Rule-based votes" in ds.basis and "not evidence" in ds.basis
    assert "millions" in ds.unit and "per share" in ds.unit
    assert "source_columns" in ds.source


def test_the_evidence_endpoint_is_the_dataset_the_tool_returns(repaired_client):
    from app.copilot.tools import ALL_TOOLS, PRO_TOOLS

    spec = next(t for t in ALL_TOOLS if t["name"] == "get_financial_statements")
    assert "reporting period" in spec["description"] or "period each figure covers" in spec["description"]
    assert "get_financial_statements" in PRO_TOOLS
    e = get(repaired_client, "/v1/tickers/2222/evidence")
    assert e["ticker"] == "2222_TADAWUL" and e["currency"] == "SAR"
    assert {s["section"] for s in e["statements"]} == {"Income Statement", "Balance Sheet"}
