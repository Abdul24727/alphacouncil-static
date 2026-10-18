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
    # Ask OpenRouter for the model's reasoning (shown in the collapsible steps). Off by
    # default: with DeepSeek v3.2 it roughly doubles each step's time.
    copilot_reasoning: bool = False
    # How OpenRouter picks among the hosts serving the model: "latency" (fastest first token;
    # measured 0.25 s against 1.7 s on the default pick), "throughput", "price", or "" for
    # OpenRouter's default. Sent only to openrouter.ai.
    copilot_provider_sort: str = "latency"
    copilot_effort: str = "medium"  # low | medium | high | xhigh | max
    # Questions per hour per signed-in user (or per address for the stand-in).
    copilot_hourly_limit: int = 60

    # Advisors' debate room (app/debate). Same OpenRouter client, key and host sorting as the
    # Copilot; one model for every advisor and a different one for the Chair. Without
    # OPENROUTER_API_KEY the room runs the labelled stand-in (app/debate/standin.py).
    debate_advisor_model: str = "deepseek/deepseek-v4-pro"
    debate_chair_model: str = "anthropic/claude-sonnet-5.5"
    # The advisors, in seat order: app/advisors/<id>.md each (2 to 6).
    debate_advisors: str = "buffett,lynch,dalio,marks,alwaleed,alrajhi"
    # Debate rounds between the openings and the vote (1 or 2).
    debate_rounds: int = 1
    # Ask OpenRouter for the models' reasoning. Off: each seat answers in one pass (faster).
    debate_reasoning: bool = False

    # App data (accounts, portfolios, alerts, preferences). SQLite locally, Postgres on servers.
    database_url: str = "sqlite:///./dev-app.sqlite"
    # Origins allowed to make cookie-authenticated writes (comma-separated).
    allowed_origins: str = "http://localhost:3100,http://localhost:3201"
    # True wherever the site is served over HTTPS.
    cookie_secure: bool = False
    redis_url: str | None = None

    # The site's address for links in emails (password reset). Never taken from the
    # request's Host header; unset, the first ALLOWED_ORIGINS entry is used.
    site_url: str | None = None
    # Email over SMTP (app/mail.py): the variables the old site's backend used with
    # MailerSend. No SMTP_HOST = email is not configured; the password (SMTP_PASS) stays in
    # the process environment and never in settings or logs.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_from: str = "AlphaCouncil <no-reply@alphacouncil.tech>"

    # Sign in with Google (app/oauth.py), the old site's Google web client. The secret
    # (GOOGLE_CLIENT_SECRET) stays in the process environment. Google sends people back to
    # <site>/auth/google/callback, the address registered for that client.
    google_client_id: str | None = None

    # Pro billing (app/billing.py, app/plans.py). BILLING_OPEN turns on the checkout and,
    # with it, the Free plan's limits: while it is off every account has Pro (early access).
    # The publishable key is public (it is sent to the browser); MOYASAR_SECRET_KEY and
    # MOYASAR_WEBHOOK_SECRET stay in the process environment.
    billing_open: bool = False
    moyasar_publishable_key: str | None = None
    moyasar_api: str = "https://api.moyasar.com/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
