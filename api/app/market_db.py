import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class MarketDataUnavailable(RuntimeError):
    """The pipeline's database is not configured or cannot be opened."""


def connect_ro(path: Path | None, *, immutable: bool) -> sqlite3.Connection:
    """Open a pipeline SQLite file read-only. The API never writes market data."""
    if path is None:
        raise MarketDataUnavailable("BRIEFS_DB is not set")
    if not path.is_file():
        raise MarketDataUnavailable(f"database file not found: {path.name}")

    uri = f"{path.resolve().as_uri()}?mode=ro"
    if immutable:
        uri += "&immutable=1"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def reader(path: Path | None, *, immutable: bool, name: str) -> Iterator[sqlite3.Connection]:
    """Read-only connection for one request; `name` labels the error when unconfigured."""
    if path is None:
        raise MarketDataUnavailable(f"{name} is not set")
    conn = connect_ro(path, immutable=immutable)
    try:
        yield conn
    finally:
        conn.close()
