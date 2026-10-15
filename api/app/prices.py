"""Daily OHLCV from the pipeline's per-ticker CSV files.

UNIVERSE_ROOT/<ticker_key>/price_history_10y.csv, written by the pipeline's
batch_compute_indicators step. Two header languages occur with the same
column order (Date, Price, Change, Change %, Volume, Turnover, Open, High,
Low), so columns are read by position. Dates are DD/MM/YYYY or YYYY/MM/DD;
numbers may carry thousands separators and accounting negatives "(0.02)".
A missing value stays None: nothing is filled in or interpolated.
"""

import csv
import threading
from collections import OrderedDict
from datetime import date
from pathlib import Path

from pydantic import BaseModel

FILE_NAME = "price_history_10y.csv"
COLUMNS = ("date", "close", "change", "change_pct", "volume", "turnover", "open", "high", "low")


class Bar(BaseModel):
    time: str  # YYYY-MM-DD
    open: float | None
    high: float | None
    low: float | None
    close: float
    volume: float | None
    turnover: float | None = None


def _num(raw: str | None) -> float | None:
    if raw is None:
        return None
    s = raw.strip().replace(",", "").replace("%", "").strip()
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").strip()
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def _date(raw: str) -> date | None:
    parts = raw.strip().replace("-", "/").split("/")
    if len(parts) != 3:
        return None
    try:
        a, b, c = (int(p) for p in parts)
        return date(a, b, c) if a > 31 else date(c, b, a)
    except ValueError:
        return None


def parse(path: Path) -> list[Bar]:
    bars: dict[str, Bar] = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # header (English or Arabic)
        for row in reader:
            if len(row) < len(COLUMNS):
                continue
            d = _date(row[0])
            close = _num(row[1])
            if d is None or close is None or close <= 0:
                continue
            o, h, low = _num(row[6]), _num(row[7]), _num(row[8])
            # A bar whose range contradicts its close is kept as a close-only point.
            if None in (o, h, low) or not (low <= min(o, close) and max(o, close) <= h):
                o = h = low = None
            bars[d.isoformat()] = Bar(
                time=d.isoformat(), open=o, high=h, low=low, close=close, volume=_num(row[4]), turnover=_num(row[5])
            )
    return [bars[k] for k in sorted(bars)]


def tail_bars(path: Path, n: int = 2) -> list[Bar]:
    """The last `n` bars from the end of a price file without parsing the whole file."""
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        chunk = min(size, 4096)
        f.seek(size - chunk)
        lines = f.read().decode("utf-8-sig", errors="replace").splitlines()
    rows = [r for r in csv.reader(lines[1:] if chunk == size else lines[1:]) if len(r) >= len(COLUMNS)]
    out: dict[str, Bar] = {}
    for row in rows:
        d, close = _date(row[0]), _num(row[1])
        if d is None or close is None or close <= 0:
            continue
        out[d.isoformat()] = Bar(time=d.isoformat(), open=None, high=None, low=None, close=close,
                                 volume=_num(row[4]), turnover=_num(row[5]))
    return [out[k] for k in sorted(out)][-n:]


class PriceStore:
    """Parsed series cached per file, refreshed when the pipeline rewrites the file."""

    def __init__(self, root: Path | None, capacity: int = 128):
        self.root = root
        self._cache: OrderedDict[str, tuple[float, list[Bar]]] = OrderedDict()
        self._capacity = capacity
        self._lock = threading.Lock()
        self._tails: dict[str, tuple[float, list[Bar]]] = {}

    def path_for(self, ticker_key: str) -> Path | None:
        if self.root is None:
            return None
        p = self.root / ticker_key / FILE_NAME
        return p if p.is_file() else None

    def latest(self, ticker_key: str) -> list[Bar]:
        """The last two bars (close and previous close), cached per file version."""
        path = self.path_for(ticker_key)
        if path is None:
            return []
        mtime = path.stat().st_mtime
        hit = self._tails.get(ticker_key)
        if hit and hit[0] == mtime:
            return hit[1]
        bars = tail_bars(path, 2)
        self._tails[ticker_key] = (mtime, bars)
        return bars

    def bars(self, ticker_key: str) -> list[Bar] | None:
        """None when the ticker has no price file; otherwise its bars, oldest first."""
        path = self.path_for(ticker_key)
        if path is None:
            return None
        mtime = path.stat().st_mtime
        with self._lock:
            hit = self._cache.get(ticker_key)
            if hit and hit[0] == mtime:
                self._cache.move_to_end(ticker_key)
                return hit[1]
        series = parse(path)
        with self._lock:
            self._cache[ticker_key] = (mtime, series)
            self._cache.move_to_end(ticker_key)
            while len(self._cache) > self._capacity:
                self._cache.popitem(last=False)
        return series
