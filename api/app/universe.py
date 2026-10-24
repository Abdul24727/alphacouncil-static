"""The tradable universe in memory, rebuilt when the pipeline rewrites its files.

The pipeline writes a `briefs` row per listing (716 on 2026-10-24); the universe is those less the
listings in data/not_listed.json that no longer trade (714 today).
"""

import json
import re
import threading
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from .market_db import connect_ro
from .names import load_names
from .settings import Settings

# Tadawul first: the product's home market.
EXCHANGE_ORDER = ["TADAWUL", "ADX", "DFM", "QSE", "KSE", "BSE", "MSM"]

_AR_MARKS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_AR_LETTERS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي"})
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_PUNCT = re.compile(r"[^\w\s&]")


# Tadawul sectors come only from the Saudi Exchange's own classification (data/tadawul_sectors.json:
# the Main Market Watch's groups in English and Arabic, with its source and date). The pipeline's
# labels are not used for Tadawul: 98 named another group and 24 sat in a catch-all bucket
# (docs/data-fixes-2026-10-18.md, P1). A company the list does not cover has no sector ("sector
# unknown"), never a guess. Refresh the file when companies list or move sector.
TADAWUL_SECTORS_FILE = Path(__file__).parent / "data" / "tadawul_sectors.json"


def tadawul_sectors_source(path: Path = TADAWUL_SECTORS_FILE) -> dict:
    """Where the Tadawul sector list comes from and when it was taken (for /methodology)."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {"source_url": doc["source_urls"]["en"], "source_url_ar": doc["source_urls"]["ar"],
            "retrieved": doc["retrieved"], "companies": doc["companies"]}


def load_tadawul_sectors(path: Path = TADAWUL_SECTORS_FILE) -> dict[str, tuple[str, str]]:
    """Symbol -> (sector name in English, in Arabic), as the exchange publishes them."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {sym: (sec["en"], sec["ar"]) for sec in doc["sectors"] for sym in sec["symbols"]}


# Currencies each exchange trades equities in (Bahrain also lists some in US dollars). The
# pipeline gives some cross-listings their company's home currency instead (KWD on DFM, ADX
# and Bahrain, OMR on ADX), and nothing in our data records the listing's own currency, so such
# a label is dropped: the price shows with "currency not confirmed", never in the wrong one.
EXCHANGE_CURRENCIES: dict[str, set[str]] = {
    "TADAWUL": {"SAR"},
    "ADX": {"AED"},
    "DFM": {"AED"},
    "QSE": {"QAR"},
    "KSE": {"KWD"},
    "BSE": {"BHD", "USD"},
    "MSM": {"OMR"},
}

# Listings that trade in another currency than the pipeline gives them: the five US-dollar lines on
# Bahrain Bourse, recorded with the owner's decision and its sources in data/listing_currencies.json.
LISTING_CURRENCIES_FILE = Path(__file__).parent / "data" / "listing_currencies.json"

# Listings that no longer trade. The pipeline still writes a `briefs` row for them, and the app's only
# way to say anything about one was an amber price, which reads as our data being late rather than as
# the company having gone. The owner chose (2026-10-24) to leave them out of the universe instead;
# data/not_listed.json carries each one's status, date and sources, and removing an entry brings it back.
NOT_LISTED_FILE = Path(__file__).parent / "data" / "not_listed.json"


def load_not_listed(path: Path = NOT_LISTED_FILE) -> dict[str, dict]:
    """Ticker keys that no longer trade and are left out of the universe (data/not_listed.json)."""
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))["listings"]


def load_listing_currencies(path: Path = LISTING_CURRENCIES_FILE) -> dict[str, str]:
    """ticker_key -> trading currency."""
    return dict(json.loads(path.read_text(encoding="utf-8"))["listings"])


def normalize(text: str) -> str:
    """Case, Arabic letter variants, diacritics and Eastern digits folded for matching."""
    t = unicodedata.normalize("NFKC", text).lower().translate(_DIGITS)
    t = _AR_MARKS.sub("", t).translate(_AR_LETTERS)
    return " ".join(_PUNCT.sub(" ", t).split())


def _slug_key(ref: str) -> str:
    """Case, punctuation and spacing folded: "e nbd" -> "ENBD", "adav.ad" -> "ADAVAD"."""
    return normalize(ref).upper().replace(" ", "")


def _words(name: str) -> list[str]:
    words = name.split()
    # "الراجحي" should match a search for "راجحي".
    return words + [w[2:] for w in words if w.startswith("ال") and len(w) > 3]


@dataclass(frozen=True)
class Ticker:
    ticker_key: str
    symbol: str
    exchange: str
    # The listing's trading currency (price, market cap, EPS, book value), or None when the pipeline's
    # is one the exchange does not trade in and no listing currency is recorded.
    currency: str | None
    # The currency statements and dividends are labelled in: the pipeline's, when the exchange trades
    # in it. Unchanged by data/listing_currencies.json, which only knows the trading currency.
    report_currency: str | None
    # The pipeline's value as written: the unit its ratios are in (ratios.eps_in_price_unit).
    data_currency: str | None
    name_en: str | None
    name_ar: str | None
    sector_id: str | None
    sector_en: str | None
    sector_ar: str | None
    slug: str
    _symbol_norm: str = field(repr=False)
    _names_norm: tuple[str, ...] = field(repr=False)

    def score(self, q: str, tokens: list[str]) -> int:
        if self._symbol_norm == q:
            return 100
        if self._symbol_norm.startswith(q):
            return 90 - min(len(self._symbol_norm) - len(q), 9)
        best = 0
        for name in self._names_norm:
            if name == q:
                return 85
            if name.startswith(q):
                best = max(best, 75)
            elif all(any(w.startswith(tok) for w in _words(name)) for tok in tokens):
                best = max(best, 65)
            elif len(q) >= 3 and q in name:
                best = max(best, 50)
        return best


class Universe:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._lock = threading.Lock()
        self._stamp: tuple[float, ...] | None = None
        self.tickers: list[Ticker] = []
        self.by_key: dict[str, Ticker] = {}
        self._by_slug: dict[str, Ticker] = {}
        self._by_key_norm: dict[str, Ticker] = {}
        self.as_of: str | None = None

    def _file_stamp(self) -> tuple[float, ...]:
        s = self._settings
        # not_listed.json too, so editing it reloads the universe without a restart.
        paths: list[Path | None] = [s.briefs_db, s.ticker_names_csv, s.saudi_en_names_csv, NOT_LISTED_FILE]
        return tuple(p.stat().st_mtime if p and p.is_file() else 0.0 for p in paths)

    def refresh(self) -> None:
        """Reload when any source file changed since the last load."""
        stamp = self._file_stamp()
        if stamp == self._stamp:
            return
        with self._lock:
            if stamp == self._stamp:
                return
            self._load()
            self._stamp = stamp

    def _load(self) -> None:
        s = self._settings
        names = load_names(s.ticker_names_csv, s.saudi_en_names_csv)
        conn = connect_ro(s.briefs_db, immutable=s.market_db_immutable)
        try:
            rows = conn.execute(
                "SELECT ticker_key, ticker, exchange, currency, sector_id, sector_en, sector_ar, as_of_date"
                " FROM briefs"
            ).fetchall()
        finally:
            conn.close()

        # Counted over every row, including the listings dropped below: a symbol's count decides
        # whether its slug is the bare symbol or the ticker key, and dropping one must not change
        # another listing's URL.
        symbol_counts: dict[str, int] = {}
        for r in rows:
            symbol_counts[r["ticker"]] = symbol_counts.get(r["ticker"], 0) + 1

        official = load_tadawul_sectors()
        listed_in = load_listing_currencies()
        # The module global, not the bound default, so the path can be pointed elsewhere in tests.
        not_listed = load_not_listed(NOT_LISTED_FILE)
        tickers = []
        for r in rows:
            if r["ticker_key"] in not_listed:
                continue
            n = names.get(r["ticker_key"], {})
            if r["exchange"] == "TADAWUL":
                sector_en, sector_ar = official.get(r["ticker"], (None, None))
                sector_id = f"tasi:{sector_en}" if sector_en else None
            else:
                sector_en, sector_ar = r["sector_en"], r["sector_ar"]
                sector_id = None if r["sector_id"] is None else str(r["sector_id"])
            name_en, name_ar = n.get("name_en"), n.get("name_ar")
            traded = EXCHANGE_CURRENCIES.get(r["exchange"], {r["currency"]})
            report_currency = r["currency"] if r["currency"] in traded else None
            tickers.append(
                Ticker(
                    ticker_key=r["ticker_key"],
                    symbol=r["ticker"],
                    exchange=r["exchange"],
                    currency=listed_in.get(r["ticker_key"], report_currency),
                    report_currency=report_currency,
                    data_currency=r["currency"],
                    name_en=name_en,
                    name_ar=name_ar,
                    sector_id=sector_id,
                    sector_en=sector_en,
                    sector_ar=sector_ar,
                    # /t/2222 for Tadawul and for symbols unique across exchanges;
                    # /t/<ticker_key> for the rest (2010 is SABIC on Tadawul, not 2010_KSE).
                    slug=(
                        r["ticker"]
                        if r["exchange"] == "TADAWUL" or symbol_counts[r["ticker"]] == 1
                        else r["ticker_key"]
                    ),
                    _symbol_norm=normalize(r["ticker"]),
                    _names_norm=tuple(normalize(x) for x in (name_en, name_ar) if x),
                )
            )
        self.tickers = tickers
        self.by_key = {t.ticker_key: t for t in tickers}
        self._by_slug = {_slug_key(t.slug): t for t in tickers}
        self._by_key_norm = {_slug_key(t.ticker_key): t for t in tickers}
        self.as_of = max((r["as_of_date"] for r in rows if r["as_of_date"]), default=None)

    def resolve(self, ref: str) -> Ticker | None:
        """A URL slug ("2222", "2010_KSE"), a ticker_key, or a symbol unique to one exchange."""
        self.refresh()
        key = _slug_key(ref)
        return self.by_key.get(ref) or self._by_slug.get(key) or self._by_key_norm.get(key)

    def search(self, query: str, limit: int) -> list[Ticker]:
        self.refresh()
        q = normalize(query)
        if not q:
            return []
        tokens = q.split()
        order = {ex: i for i, ex in enumerate(EXCHANGE_ORDER)}
        scored = [(t.score(q, tokens), t) for t in self.tickers]
        hits = [(s, t) for s, t in scored if s > 0]
        hits.sort(key=lambda st: (-st[0], order.get(st[1].exchange, 99), st[1].symbol))
        return [t for _, t in hits[:limit]]
