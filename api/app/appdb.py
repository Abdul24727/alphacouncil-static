"""App data (accounts, sessions, portfolios, alerts, preferences).

Postgres on staging and production (DATABASE_URL), SQLite for local development
and tests; SQLAlchemy Core keeps one schema for both. Market data never lives
here: it stays in the pipeline's files.
"""

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


@lru_cache
def engine_for(url: str) -> Engine:
    eng = create_engine(url, pool_pre_ping=True, future=True)
    if url.startswith("sqlite"):

        @event.listens_for(eng, "connect")
        def _sqlite_fk(dbapi_conn, _):  # noqa: ANN001
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    metadata.create_all(eng)
    return eng
