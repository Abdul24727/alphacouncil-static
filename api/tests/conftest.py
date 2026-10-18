import csv
import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app import main
from app.settings import Settings

TODAY = datetime.now(UTC).date().isoformat()
LONG_AGO = "2026-01-05"

# A handful of real tickers. Values are fixtures, not market data.
BRIEFS_COLUMNS = (
    "ticker_key, ticker, exchange, currency, sector_id, sector_en, sector_ar, as_of_date, last_price,"
    " day_change_pct, volume, value_traded, market_cap_raw, pe, pb, dividend_yield_pct, roe_pct,"
    " return_1m, return_3m, return_6m, return_12m, vol_1y, max_drawdown, regime_score,"
    " has_price_history, source_run_ts"
)
BRIEFS = [
    ("2222_TADAWUL", "2222", "TADAWUL", "SAR", None, "Energy", "الطاقة", LONG_AGO, 26.5, -0.9, 9e6, 2.4e8, 6413000.0,
     None, 4.09, 5.03, 26.75, -0.01, -0.04, 0.05, 0.10, 0.155, -0.40, 85, 1, "20260105_000115"),
    ("2223_TADAWUL", "2223", "TADAWUL", "SAR", None, "Energy", "الطاقة", LONG_AGO, 126.7, -0.94, 1e5, 1.3e7, 21000.0,
     18.0, 3.0, 4.0, 15.0, 0.0, 0.0, 0.0, 0.0, 0.3, -0.2, 40, 1, "20260105_000115"),
    ("2382_TADAWUL", "2382", "TADAWUL", "SAR", None, "Energy", "الطاقة", LONG_AGO, 17.7, -3.1, 1e5, 1.7e6, 3000.0,
     None, None, None, None, None, None, None, None, None, None, None, 0, "20260105_000115"),
    ("1120_TADAWUL", "1120", "TADAWUL", "SAR", None, "Banks", "البنوك", TODAY, 64.55, -0.69, 9.7e6, 6.3e8, 387300.0,
     14.5, 3.2, 2.58, 23.5, 0.02, 0.05, 0.1, 0.2, 0.2, -0.3, 60, 1, "20260105_000115"),
    ("2010_TADAWUL", "2010", "TADAWUL", "SAR", None, "Materials", "المواد الأساسية", TODAY, 60.0, 0.0, 1e6, 6e7, 180000.0,
     None, None, None, None, None, None, None, None, None, None, None, 1, None),
    ("2010_KSE", "2010", "KSE", "KWD", None, "Industrials", "الصناعة", TODAY, 0.259, -1.1, 4e4, 1.2e4, 55.56,
     None, None, None, None, None, None, None, None, None, None, None, 1, None),
    ("FAB_ADX", "FAB", "ADX", "AED", 4, "Banks", "البنوك", TODAY, 19.9, -0.6, 2.6e6, 5.2e7, 219847.44,
     10.37, 1.66, 4.02, 16.67, 0.1, 0.1, 0.1, 0.1, 0.29, -0.3, 70, 1, None),
    ("EMAAR_DFM", "EMAAR", "DFM", "AED", 9, "Real Estate", "العقارات", TODAY, 11.6, -3.0, 1e7, 1e8, 102000.0,
     None, None, None, None, None, None, None, None, None, None, None, 1, None),
    # Like Saudi Tadawul Group: the pipeline's default bucket (sector_id 1) labelled "Energy".
    ("1111_TADAWUL", "1111", "TADAWUL", "SAR", 1, "Energy", "الطاقة", TODAY, 160.0, 0.5, 1e5, 1.6e7, 999999.0,
     None, None, None, None, None, None, None, None, None, None, None, 0, None),
]

UNIVERSE_CSV = [
    ("2222", "TADAWUL", "أرامكو السعودية", "/sa-ar/companies/tadawul/2222/overview"),
    ("2223", "TADAWUL", "لوبريف", "/sa-ar/companies/tadawul/luberef/overview"),
    ("2382", "TADAWUL", "أديس", "/sa-ar/companies/tadawul/ades/overview"),
    ("1120", "TADAWUL", "الراجحي", "/sa-ar/companies/tadawul/ribl/overview"),
    ("2010", "TADAWUL", "سابك", "/sa-ar/companies/tadawul/sabic/overview"),
    ("2010", "KSE", "شركة اختبار", "/kw-ar/companies/kse/test-industrial-co/overview"),
    ("FAB", "ADX", "أبو ظبي الأول", "/ae-ar/companies/adx/first-abu-dhabi-bank/overview"),
    ("EMAAR", "DFM", "إعمار", "/ae-ar/companies/dfm/emaar/overview"),
]


def _db(path, schema: list[str], rows: dict[str, list[tuple]]):
    conn = sqlite3.connect(path)
    for ddl in schema:
        conn.execute(ddl)
    for table, values in rows.items():
        if values:
            marks = ",".join("?" for _ in values[0])
            conn.executemany(f"INSERT INTO {table} VALUES ({marks})", values)
    conn.commit()
    conn.close()


@pytest.fixture
def data_files(tmp_path):
    briefs = tmp_path / "briefs_index.sqlite"
    _db(
        briefs,
        [
            f"CREATE TABLE briefs ({BRIEFS_COLUMNS})",
            "CREATE TABLE ticker_tech_snapshot (ticker_key TEXT, status TEXT, as_of_date TEXT, rsi_14 REAL,"
            " sma_50 REAL, sma_200 REAL, above_50d INT, above_200d INT, macd_bull INT, dist_to_52w_high REAL,"
            " dist_from_52w_low REAL, ma_cross_50_200 INT)",
        ],
        {
            "briefs": BRIEFS,
            "ticker_tech_snapshot": [("2222_TADAWUL", "ok", LONG_AGO, 50.4, 26.6, 26.0, 0, 1, 1, -4.9, 15.5, 1)],
        },
    )

    yesterday = (datetime.now(UTC) - timedelta(hours=20)).isoformat()
    screening = tmp_path / "screening.sqlite"
    _db(
        screening,
        [
            "CREATE TABLE ticker_freshness (ticker_key TEXT, category TEXT, as_of_utc TEXT, last_success_utc TEXT,"
            " max_age_days REAL, is_stale INT, item_count INT)",
            "CREATE TABLE scraped_ratios (ticker_key TEXT, pe REAL, pb REAL, div_yield REAL, roe REAL, roa REAL,"
            " ev_ebitda REAL, ev_revenue REAL, book_value REAL, eps_ttm REAL, market_cap_mn REAL, shares_out_mn REAL)",
            "CREATE TABLE stocks (ticker_key TEXT, pb REAL, roe_pct REAL, roa_pct REAL, dividend_yield_pct REAL)",
            "CREATE TABLE fundamentals_gauges (ticker_key TEXT, gauge_key TEXT, value REAL, status TEXT,"
            " inputs_json TEXT, score REAL)",
            "CREATE TABLE fundamentals_lineitems (ticker_key TEXT, ticker TEXT, exchange TEXT, fiscal_year INT,"
            " section TEXT, item_index INT, line_item_label TEXT, value REAL)",
            "CREATE TABLE dividends (ticker_key TEXT, announce_date TEXT, ex_date TEXT, pay_date TEXT,"
            " amount_mn REAL, dps REAL, note TEXT)",
            "CREATE TABLE capital_changes (ticker_key TEXT, date TEXT, change_type TEXT, capital_before_mn REAL,"
            " shares_before_mn REAL, capital_after_mn REAL, shares_after_mn REAL, change_pct REAL, note TEXT)",
            "CREATE TABLE ticker_insights (ticker_key TEXT, updated_at TEXT, data_json TEXT)",
        ],
        {
            "ticker_freshness": [
                ("2222_TADAWUL", "prices", f"{LONG_AGO}T00:00:00", f"{LONG_AGO}T01:43:12+00:00", 2, 0, 1),
                ("2222_TADAWUL", "fundamentals", yesterday, yesterday, 100, 0, 1),
                # News rows carry the fetch time as as_of, whatever the newest item's date.
                ("2222_TADAWUL", "news", yesterday, yesterday, 2, 0, 1),
                ("1120_TADAWUL", "news", yesterday, yesterday, 2, 0, 1),
                ("1120_TADAWUL", "disclosures", yesterday, yesterday, 120, 0, 1),
                ("2223_TADAWUL", "news", yesterday, yesterday, 2, 0, 0),
            ],
            "scraped_ratios": [
                ("2222_TADAWUL", 14.47, 4.1, 5.01, 26.75, 15.86, 7.4, None, 6.49, 1.84, 6413000.0, 242000.0),
                # Like METH.AD: negative earnings and negative book value.
                ("FAB_ADX", 0.0, -0.13, None, 121.24, -2.0, None, None, -4.81, -2.52, None, None),
            ],
            "stocks": [("2222_TADAWUL", None, None, None, None)],
            "fundamentals_gauges": [
                ("2222_TADAWUL", "debt_equity", 0.2, "ok", "{}", 54.0),
                ("2222_TADAWUL", "current_ratio", 2.0, "ok", "{}", 68.4),
                ("2222_TADAWUL", "ev_ebitda", None, "na_sector", "{}", None),
                ("2222_TADAWUL", "payout", 41.9, "ok", "{}", 63.5),
            ],
            "fundamentals_lineitems": [
                ("EMAAR_DFM", "EMAAR", "DFM", 2024, "Income Statement", 0, "الايرادات", 35505.0),
                ("EMAAR_DFM", "EMAAR", "DFM", 2025, "Income Statement", 0, "الايرادات", 49557.26),
                ("EMAAR_DFM", "EMAAR", "DFM", 2025, "Balance Sheet", 0, "نقد وما يعادله", 71400.0),
            ],
            "dividends": [
                ("2222_TADAWUL", "2026-08-04", "2026-08-19", "2026-08-27", 82060.0, 0.34, "Q 2 _ 2026"),
                ("2222_TADAWUL", "2030-01-01", "2030-01-10", "2030-01-20", 82060.0, 0.35, "Q 4 _ 2029"),
            ],
            "capital_changes": [("2222_TADAWUL", "2023-05-08", "Bonus Shares", 75000.0, 220000.0, 90000.0, 242000.0, 20.0, "")],
            "ticker_insights": [
                (
                    "2222_TADAWUL",
                    "2026-08-12",
                    json.dumps(
                        {
                            "performance": {"as_of": "2026-08-11", "1m": -0.67},
                            "seasonality": {
                                "years": [{"year": 2026, "monthly_pct": [1.0] * 12, "partial": True}],
                                "average": [1.0] * 12,
                                "years_back": 5,
                            },
                            "ownership": None,
                            "analysts": None,
                        }
                    ),
                )
            ],
        },
    )

    evidence = tmp_path / "evidence.sqlite"
    _db(
        evidence,
        [
            "CREATE TABLE items (id TEXT, ticker_key TEXT, section TEXT, date TEXT, title TEXT, url TEXT,"
            " local_path TEXT, snippet TEXT, main_text TEXT, extraction_status TEXT, ai_summary_ar TEXT,"
            " ai_summary_en TEXT, ai_summary_fetched_at TEXT)",
            "CREATE TABLE news_ai (url TEXT, headline_en TEXT, summary_en TEXT, summary_ar TEXT, impact TEXT)",
        ],
        {
            "items": [
                ("n1", "2222_TADAWUL", "news", TODAY, "Aramco news", "https://www.argaam.com/en/a/1", None, "s", None, None, None, None, None),
                ("d1", "2222_TADAWUL", "disclosures", "2026-03-09T21:00:00", "Buyback", "https://www.argaam.com/en/a/2", None, "", None, None, None, "Summary", None),
                ("e1", "2222_TADAWUL", "events", "2026-06-08T21:00:00", "cash dividend distribution", None, None, "", None, None, None, None, None),
                ("x1", "2222_TADAWUL", "events", "unknown_date_3", "undated", None, None, "", None, None, None, None, None),
                ("e2", "1120_TADAWUL", "events", f"{TODAY}T21:00:00", "financial results disclosure", None, None, "", None, None, None, None, None),
                ("d2", "1120_TADAWUL", "disclosures", "2026-01-05T21:00:00", "Board meeting", "https://www.argaam.com/en/a/3", None, "", None, None, None, None, None),
            ],
            "news_ai": [("https://www.argaam.com/en/a/1", "Aramco news", "Up", "صعود", "positive")],
        },
    )

    indices = tmp_path / "market_indices.sqlite"
    _db(
        indices,
        ["CREATE TABLE market_indices (id INTEGER, market TEXT, name_en TEXT, name_ar TEXT, price REAL, change_ REAL,"
         " change_pct REAL, volume REAL, source_url TEXT, fetched_at TEXT)"],
        {"market_indices": [(1, "TASI", "Tadawul All-Share", "تداول", 10138.83, -179.3, -1.7378, None, None, datetime.now(UTC).isoformat())]},
    )

    names = tmp_path / "tickers_universe_corrected.csv"
    with open(names, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "exchange", "company_name", "company_path"])
        w.writerows(UNIVERSE_CSV)

    saudi = tmp_path / "tickers_saudi_en_names.csv"
    with open(saudi, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "name_en"])
        w.writerow(["2010", "Saudi Basic Industries Corporation"])
        w.writerow(["2223", "Saudi Aramco Base Oil Company - Luberef"])

    prices = tmp_path / "universe"
    today = datetime.now(UTC).date()
    english = [
        "Date,Price,Change,Change (%),Volume,Turnover,Open,High,Low",
        "11/12/2019,29.10,0.00,0.00 %,29540607,,29.10,29.10,29.10",
        f"{(today - timedelta(days=1)):%d/%m/%Y},26.00,,,1000,26000,25.90,26.10,25.80",
        f'{today:%d/%m/%Y},26.50,0.50,1.92 %,"9,327,140","248,170,145",26.00,26.60,25.95',
    ]
    arabic = [
        "التاريخ,السعر,التغير,التغير (%),حجم التداول,قيمة التداول,الافتتاح,الأعلى,الأدنى",
        '2026/10/12,18.52,(0.02),(0.11 %),"3,829,048","71,141,029",18.54,18.74,18.46',
        '2026/10/13,18.86,0.34,1.84 %,"3,395,404","63,657,192",18.52,18.86,18.52',
        "2026/10/14,18.90,,,,,19.50,18.95,18.80",
    ]
    # Like BMEB.BH: the file stops in 2018 while briefs carries today's run date.
    stopped = [english[0], "07/08/2018,0.05,,,100,5,0.05,0.05,0.05", "08/08/2018,0.04,,,100,4,0.04,0.04,0.04"]
    # Like 4240: a current file while briefs says there is no price history.
    current = [english[0], f"{(today - timedelta(days=1)):%d/%m/%Y},14.40,,,10,144,14.40,14.40,14.40", f"{today:%d/%m/%Y},14.54,,,10,145,14.50,14.60,14.50"]
    for key, lines in (("2222_TADAWUL", english), ("FAB_ADX", arabic), ("2010_KSE", stopped), ("2382_TADAWUL", current)):
        (prices / key).mkdir(parents=True)
        (prices / key / "price_history_10y.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return Settings(
        _env_file=None,
        universe_root=prices,
        market_indices_db=indices,
        database_url=f"sqlite:///{(tmp_path / 'app.sqlite').as_posix()}",
        allowed_origins="http://testserver",
        briefs_db=briefs,
        screening_db=screening,
        evidence_db=evidence,
        market_db_immutable=False,
        ticker_names_csv=names,
        saudi_en_names_csv=saudi,
    )


@pytest.fixture
def client(data_files, monkeypatch):
    monkeypatch.setattr(main, "get_settings", lambda: data_files)
    return TestClient(main.create_app())
