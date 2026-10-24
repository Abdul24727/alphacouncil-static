"""Company names per ticker_key, ported from llm-council/backend/ticker_names.py.

name_ar comes from the universe CSV (`company_name`), except where NAME_AR_OVERRIDES
corrects it. name_en is derived: TADAWUL uses a brand override, then the curated
Saudi CSV; the other GCC exchanges use the readable URL slug. When no real English
name exists, name_en is None rather than an invented one.
"""

import csv
from pathlib import Path

SAUDI_EN_OVERRIDES: dict[str, str] = {
    "2222": "Saudi Aramco",
    "2010": "SABIC",
    "7010": "stc",
    "7020": "Mobily",
    "1120": "Al Rajhi Bank",
    "1180": "Saudi National Bank (SNB)",
    "1150": "Alinma Bank",
    "1211": "Maaden",
    "2280": "Almarai",
    "2082": "ACWA Power",
    "4280": "Kingdom Holding",
    "4190": "Jarir",
    "4002": "Mouwasat",
    "2270": "SADAFCO",
    "2380": "Petro Rabigh",
    "2310": "Sipchem",
    "4210": "SRMG",
    "2050": "Savola Group",
}

# Source URL slugs that are misspelled or mangled, keyed by ticker_key.
SLUG_NAME_OVERRIDES: dict[str, str] = {
    "ORDS_QSE": "Ooredoo",
    "QFBQ_QSE": "Qatar First Bank",
    "QIBK_QSE": "Qatar Islamic Bank",
    "GISS_QSE": "Gulf International Services",
    "MARK_QSE": "Masraf Al Rayan",
    "EAND_ADX": "e& (Etisalat)",
    "DU_DFM": "du",
    "827_KSE": "Boursa Kuwait",
    "BEYON_BSE": "Beyon",
    # Renamed after the pipeline's CSV was written (see NAME_AR_OVERRIDES for the Arabic).
    "GULFNAV_DFM": "Etihad Energy Holding",
}

# Arabic names the universe CSV has wrong or out of date. `name_ar` otherwise comes from the
# pipeline's `company_name`, which we do not edit (it belongs to the old repo), so a company renamed
# after that CSV was written keeps its old Arabic name until it is listed here.
#
# GULFNAV_DFM: Gulf Navigation Holding (الخليج للملاحة القابضة) became Etihad Energy Holding PJSC
# on completing its acquisition of Brooge, and the DFM ticker became ETIHADENERGY after the close on
# 2026-06-19. The Arabic name is a transliteration, "اتحاد إنيرجي القابضة", not a translation of
# "Energy" — Al Khaleej (2026-04-27 and 2026-06-16), Al Bayan and Zawya's Arabic release of the
# launch all give it that way. The ticker key and symbol stay GULFNAV: they are this app's primary
# key for the listing, in URLs, saved portfolios, alerts and past advisors' sessions.
NAME_AR_OVERRIDES: dict[str, str] = {
    "GULFNAV_DFM": "اتحاد إنيرجي القابضة",
}

_ACRONYMS = {
    "ADNOC", "NBD", "ENBD", "NMDC", "MBME", "ADNH", "OQ", "GFH", "RAK", "BHM", "KMEFIC",
    "PJSC", "PSC", "QSC", "KSC", "BSC", "SAOG", "WLL", "REIT", "LLC",
    "NBK", "GBK", "KIB", "ABK", "KFH", "NBB", "BBK", "BSF", "SICO", "AUB", "GIB", "CBD",
    "UAB", "ADCB", "FAB", "ADIB", "DIB", "QNB", "QIB", "QIIB", "IHC", "TAQA", "DEWA",
}

_SLUG_EXCHANGES = {"ADX", "DFM", "KSE", "QSE", "MSM", "BSE"}


def _fix_acronyms(name: str) -> str:
    return " ".join(w.upper() if w.upper() in _ACRONYMS else w for w in name.split())


def _slug_from_path(path: str) -> str:
    """"/ae-ar/companies/adx/abu-dhabi-commercial-bank/overview" -> "abu-dhabi-commercial-bank"."""
    if not path:
        return ""
    return path.split("/overview")[0].rsplit("/", 1)[-1].strip()


def _derive_name_en(ticker: str, exchange: str, company_path: str, saudi_en: dict[str, str]) -> str | None:
    if exchange == "TADAWUL":
        return SAUDI_EN_OVERRIDES.get(ticker) or saudi_en.get(ticker)
    override = SLUG_NAME_OVERRIDES.get(f"{ticker}_{exchange}")
    if override:
        return override
    slug = _slug_from_path(company_path)
    if exchange not in _SLUG_EXCHANGES or not slug:
        return None
    if "-" in slug:
        return _fix_acronyms(slug.replace("-", " ").title())
    if len(slug) <= 5 or slug.upper() in _ACRONYMS:
        return slug.upper()
    return slug.title()


def _read_csv(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.is_file():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_names(universe_csv: Path | None, saudi_en_csv: Path | None) -> dict[str, dict[str, str | None]]:
    """{ticker_key: {"name_en", "name_ar"}}. Missing files give an empty index."""
    saudi_en = {
        (row.get("ticker") or "").strip(): (row.get("name_en") or "").strip()
        for row in _read_csv(saudi_en_csv)
        if row.get("ticker") and row.get("name_en")
    }
    index: dict[str, dict[str, str | None]] = {}
    for row in _read_csv(universe_csv):
        ticker = (row.get("ticker") or "").strip()
        exchange = (row.get("exchange") or "").strip()
        if not ticker or not exchange:
            continue
        key = f"{ticker}_{exchange}"
        name_en = _derive_name_en(ticker, exchange, row.get("company_path") or "", saudi_en)
        index[key] = {
            "name_en": name_en if name_en and name_en != ticker else None,
            "name_ar": NAME_AR_OVERRIDES.get(key) or (row.get("company_name") or "").strip() or None,
        }
    return index
