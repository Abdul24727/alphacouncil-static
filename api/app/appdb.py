"""App data (accounts, sessions, portfolios, alerts, preferences).

Postgres on staging and production (DATABASE_URL), SQLite for local development
and tests; SQLAlchemy Core keeps one schema for both. Market data never lives
here: it stays in the pipeline's files.
"""

import secrets
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Engine,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    event,
    select,
)

metadata = MetaData()


def utcnow() -> datetime:
    return datetime.now(UTC)


users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(254), nullable=False, unique=True),
    Column("password_hash", String(100), nullable=False),
    Column("display_name", String(80)),
    Column("locale", String(5), nullable=False, default="en"),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
)

sessions = Table(
    "sessions",
    metadata,
    # SHA-256 of the cookie token; the token itself is never stored.
    Column("token_hash", String(64), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)

# "Forgot password?" links (auth.forgot_password). Like sessions, only the SHA-256 of the
# token in the emailed link is stored. A link works once, within an hour.
password_resets = Table(
    "password_resets",
    metadata,
    Column("token_hash", String(64), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("used_at", DateTime(timezone=True)),
)

holdings = Table(
    "holdings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("ticker_key", String(40), nullable=False),
    Column("quantity", Float, nullable=False),
    Column("avg_cost", Float),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
    UniqueConstraint("user_id", "ticker_key", name="uq_holding_user_ticker"),
)

alerts = Table(
    "alerts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("ticker_key", String(40), nullable=False),
    Column("kind", String(10), nullable=False),  # "above" | "below"
    Column("price", Float, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
)

prefs = Table(
    "prefs",
    metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("data", JSON, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=utcnow),
)

# What a user accepted and when: the versioned acceptance text and the document versions
# it covered (app/legal.py). Removed with the account.
consents = Table(
    "consents",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("kind", String(20), nullable=False),  # "registration"
    Column("text_version", String(10), nullable=False),
    Column("documents", JSON, nullable=False),  # {"terms": "1.2", "privacy": "1.2"}
    Column("accepted_at", DateTime(timezone=True), nullable=False, default=utcnow),
)

# Rate-limit hits, shared by every API worker (auth.DbRateLimit). Rows older than a day go.
rate_hits = Table(
    "rate_hits",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("key", String(300), nullable=False, index=True),
    Column("at", DateTime(timezone=True), nullable=False, index=True),
)


# Ids the browser sees (accounts, holdings, alerts) are random, not a running count: they say
# nothing about other accounts and cannot be guessed. Ownership is still checked on every request.
ID_MAX = 2**31 - 1  # the id columns are 32-bit integers


def random_id(conn, table: Table) -> int:  # noqa: ANN001
    while True:
        candidate = secrets.randbelow(ID_MAX) + 1
        if conn.execute(select(table.c.id).where(table.c.id == candidate)).first() is None:
            return candidate


@lru_cache
def engine_for(url: str) -> Engine:
    eng = create_engine(url, pool_pre_ping=True, future=True)
    if url.startswith("sqlite"):

        @event.listens_for(eng, "connect")
        def _sqlite_fk(dbapi_conn, _):  # noqa: ANN001
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    metadata.create_all(eng)
    return eng
