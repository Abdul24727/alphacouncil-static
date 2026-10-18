"""App data (accounts, sessions, portfolios, alerts, preferences, subscriptions).

Postgres on staging and production (DATABASE_URL), SQLite for local development
and tests; SQLAlchemy Core keeps one schema for both. Market data never lives
here: it stays in the pipeline's files.
"""

import secrets
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy import (
    JSON,
    Boolean,
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
    inspect,
    select,
    text,
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
    # Set when the owner of the address proves it: the emailed link, a password reset link,
    # or Google saying the address is verified.
    Column("email_verified_at", DateTime(timezone=True)),
    # False for an account made with Google that never set a password.
    Column("has_password", Boolean),
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

# "Confirm your email" links (auth.signup / resend). Same scheme as password_resets; a link
# works once, within 48 hours.
email_verifications = Table(
    "email_verifications",
    metadata,
    Column("token_hash", String(64), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("used_at", DateTime(timezone=True)),
)

# Sign-in with Google (app/oauth.py): Google's stable account id ("sub") -> our account.
oauth_identities = Table(
    "oauth_identities",
    metadata,
    Column("provider", String(20), primary_key=True),
    Column("subject", String(255), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("email", String(254)),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
)

# A sign-in with Google in progress: the random "state" sent to Google (only its SHA-256 is
# stored), where to go afterwards, and whether the terms were accepted on the sign-up page.
oauth_states = Table(
    "oauth_states",
    metadata,
    Column("state_hash", String(64), primary_key=True),
    Column("next_path", String(300), nullable=False),
    Column("locale", String(5), nullable=False),
    Column("accepted_terms", Boolean, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)

# Pro (app/billing.py): one row per account that ever paid. Paid through current_period_end;
# renewed monthly by charging the card Moyasar saved (token_id) unless cancel_at_period_end.
subscriptions = Table(
    "subscriptions",
    metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("status", String(12), nullable=False),  # active | past_due | canceled | expired
    Column("current_period_end", DateTime(timezone=True), nullable=False),
    Column("cancel_at_period_end", Boolean, nullable=False, default=False),
    Column("token_id", String(80)),  # Moyasar card token; never card data
    Column("card_brand", String(20)),
    Column("card_last4", String(4)),
    Column("renew_attempts", Integer, nullable=False, default=0),
    Column("next_attempt_at", DateTime(timezone=True)),
    Column("reminded_for", DateTime(timezone=True)),  # the period end a reminder went out for
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=utcnow),
)

# Every Moyasar payment we acted on, once (the payment id is Moyasar's).
billing_payments = Table(
    "billing_payments",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True),
    Column("kind", String(10), nullable=False),  # first | renewal
    Column("amount", Integer, nullable=False),  # halalas
    Column("currency", String(3), nullable=False),
    Column("status", String(12), nullable=False),
    Column("period_end", DateTime(timezone=True)),  # what this payment paid up to
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
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
    _add_new_columns(eng)
    return eng


def _add_new_columns(eng: Engine) -> None:
    """create_all makes missing tables, not missing columns. Columns added to an existing table
    later are nullable, so a plain ADD COLUMN brings an older database up to date."""
    insp = inspect(eng)
    with eng.begin() as conn:
        for table in metadata.sorted_tables:
            if not insp.has_table(table.name):
                continue
            have = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name not in have:
                    assert col.nullable, f"{table.name}.{col.name}: a column added later must be nullable"
                    kind = col.type.compile(dialect=eng.dialect)
                    conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN {col.name} {kind}'))
