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
    # Index levels (TASI, ADX, DFM) and their history.
    market_indices_db: Path | None = None
    # Per-ticker daily OHLCV: <universe_root>/<ticker_key>/price_history_10y.csv
    universe_root: Path | None = None
    # True for a frozen snapshot copy; False for the live file the pipeline rewrites.
    market_db_immutable: bool = False

    # Company names: Arabic and URL slug per ticker, plus curated Saudi English names.
    ticker_names_csv: Path | None = None
    saudi_en_names_csv: Path | None = None

    # Copilot. Chosen by the environment only:
    #   "auto": OpenRouter when OPENROUTER_API_KEY is set, else Claude when ANTHROPIC_API_KEY
    #           (or ANTHROPIC_AUTH_TOKEN) is set, else the labelled rule-based stand-in;
    #   "openrouter" | "anthropic": that provider (the stand-in if its key is missing);
    #   "standin": always the stand-in.
    # Keys stay in the process environment and never in settings or logs.
    copilot_provider: str = "auto"
    # The model id for the chosen provider, e.g. "claude-opus-5-5" or "deepseek/deepseek-v3.2".
    copilot_model: str = "claude-opus-5-5"
    # Any OpenAI-compatible endpoint can stand in for OpenRouter.
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Ask OpenRouter for the model's reasoning (shown as the collapsible steps).
    copilot_reasoning: bool = True
    copilot_effort: str = "medium"  # low | medium | high | xhigh | max
    # Questions per hour per signed-in user (or per address for the stand-in).
    copilot_hourly_limit: int = 60

    # App data (accounts, portfolios, alerts, preferences). SQLite locally, Postgres on servers.
    database_url: str = "sqlite:///./dev-app.sqlite"
    # Origins allowed to make cookie-authenticated writes (comma-separated).
    allowed_origins: str = "http://localhost:3100,http://localhost:3201"
    # True wherever the site is served over HTTPS.
    cookie_secure: bool = False
    redis_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
