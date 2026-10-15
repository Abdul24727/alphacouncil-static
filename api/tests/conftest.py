import csv
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import main
from app.settings import Settings

# A handful of real tickers; names and sectors only, no market numbers.
BRIEFS = [
    ("2222_TADAWUL", "2222", "TADAWUL", "SAR", "Energy", "الطاقة", "2026-08-12"),
    ("1120_TADAWUL", "1120", "TADAWUL", "SAR", "Banks", "البنوك", "2026-08-12"),
    ("2010_TADAWUL", "2010", "TADAWUL", "SAR", "Materials", "المواد الأساسية", "2026-08-12"),
    ("2010_KSE", "2010", "KSE", "KWD", "Industrials", "الصناعة", "2026-08-07"),
    ("FAB_ADX", "FAB", "ADX", "AED", "Banks", "البنوك", "2026-08-07"),
    ("EMAAR_DFM", "EMAAR", "DFM", "AED", "Real Estate", "العقارات", "2026-08-07"),
]

UNIVERSE_CSV = [
    ("2222", "TADAWUL", "أرامكو السعودية", "/sa-ar/companies/tadawul/2222/overview"),
    ("1120", "TADAWUL", "الراجحي", "/sa-ar/companies/tadawul/ribl/overview"),
    ("2010", "TADAWUL", "سابك", "/sa-ar/companies/tadawul/sabic/overview"),
    ("2010", "KSE", "شركة اختبار", "/kw-ar/companies/kse/test-industrial-co/overview"),
    ("FAB", "ADX", "أبو ظبي الأول", "/ae-ar/companies/adx/first-abu-dhabi-bank/overview"),
    ("EMAAR", "DFM", "إعمار", "/ae-ar/companies/dfm/emaar/overview"),
]


@pytest.fixture
def data_files(tmp_path):
    db = tmp_path / "briefs_index.sqlite"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE briefs (ticker_key TEXT PRIMARY KEY, ticker TEXT, exchange TEXT,"
        " currency TEXT, sector_en TEXT, sector_ar TEXT, as_of_date TEXT)"
    )
    conn.executemany("INSERT INTO briefs VALUES (?,?,?,?,?,?,?)", BRIEFS)
    conn.commit()
    conn.close()

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

    return Settings(
        _env_file=None,
        briefs_db=db,
        market_db_immutable=False,
        ticker_names_csv=names,
        saudi_en_names_csv=saudi,
    )


@pytest.fixture
def client(data_files, monkeypatch):
    monkeypatch.setattr(main, "get_settings", lambda: data_files)
    return TestClient(main.create_app())
