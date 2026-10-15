"""The 716-equity universe in memory, rebuilt when the pipeline rewrites its files."""

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


def normalize(text: str) -> str:
    """Case, Arabic letter variants, diacritics and Eastern digits folded for matching."""
    t = unicodedata.normalize("NFKC", text).lower().translate(_DIGITS)
    t = _AR_MARKS.sub("", t).translate(_AR_LETTERS)
    return " ".join(_PUNCT.sub(" ", t).split())


def _words(name: str) -> list[str]:
    words = name.split()
    # "الراجحي" should match a search for "راجحي".
    return words + [w[2:] for w in words if w.startswith("ال") and len(w) > 3]


@dataclass(frozen=True)
class Ticker:
    ticker_key: str
    symbol: str
    exchange: str
    currency: str | None
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
        self.as_of: str | None = None

    def _file_stamp(self) -> tuple[float, ...]:
        s = self._settings
        paths: list[Path | None] = [s.briefs_db, s.ticker_names_csv, s.saudi_en_names_csv]
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

        symbol_counts: dict[str, int] = {}
        for r in rows:
            symbol_counts[r["ticker"]] = symbol_counts.get(r["ticker"], 0) + 1

        tickers = []
        for r in rows:
            n = names.get(r["ticker_key"], {})
            name_en, name_ar = n.get("name_en"), n.get("name_ar")
            tickers.append(
                Ticker(
                    ticker_key=r["ticker_key"],
                    symbol=r["ticker"],
                    exchange=r["exchange"],
                    currency=r["currency"],
                    name_en=name_en,
                    name_ar=name_ar,
                    sector_id=str(r["sector_id"]) if r["sector_id"] is not None else None,
                    sector_en=r["sector_en"],
                    sector_ar=r["sector_ar"],
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
        self._by_slug = {t.slug.upper(): t for t in tickers}
        self.as_of = max((r["as_of_date"] for r in rows if r["as_of_date"]), default=None)

    def resolve(self, ref: str) -> Ticker | None:
        """A URL slug ("2222", "2010_KSE"), a ticker_key, or a symbol unique to one exchange."""
        self.refresh()
        ref = normalize(ref).upper().replace(" ", "")
        return self._by_slug.get(ref) or self.by_key.get(ref)

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
