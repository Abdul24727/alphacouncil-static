from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API configuration, read from the environment or api/.env.

    Market data stays where the pipeline writes it: SQLite files, opened
    read-only by explicit path. App data (accounts, preferences, portfolios)
    moves to Postgres in a later phase.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Universe table `briefs` (pipeline output). Never written by this API.
    briefs_db: Path | None = None
    # Scores, fundamentals, freshness (`stocks`, `ticker_freshness`, ...).
    screening_db: Path | None = None
    # News and disclosures (`items`, `news_ai`).
    evidence_db: Path | None = None
    # Per-ticker daily OHLCV: <universe_root>/<ticker_key>/price_history_10y.csv
    universe_root: Path | None = None
    # True for a frozen snapshot copy; False for the live file the pipeline rewrites.
    market_db_immutable: bool = False

    # Company names: Arabic and URL slug per ticker, plus curated Saudi English names.
    ticker_names_csv: Path | None = None
    saudi_en_names_csv: Path | None = None

    # Declared now so every environment has the same shape; used from Phase 4/5.
    database_url: str | None = None
    redis_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
