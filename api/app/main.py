from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

from .market_db import MarketDataUnavailable
from .prices import PriceStore
from . import auth
from .routers import copilot, market, portfolio, prices, site, templates, ticker, ticker_research, tickers
from .settings import get_settings
from .universe import Universe


def create_app() -> FastAPI:
    app = FastAPI(
        title="AlphaCouncil API",
        version="0.1.0",
        description="Market data, council and accounts for the AlphaCouncil web app.",
    )
    settings = get_settings()
    app.state.settings = settings
    app.state.universe = Universe(settings)
    app.state.prices = PriceStore(settings.universe_root)
    # Counted in the app database: every uvicorn worker shares the same limits.
    app.state.login_limit = auth.DbRateLimit(settings.database_url, "login", limit=10, window_s=15 * 60)
    app.state.reset_limit = auth.DbRateLimit(settings.database_url, "reset", limit=5, window_s=15 * 60)
    app.state.copilot_limit = auth.DbRateLimit(settings.database_url, "copilot", limit=settings.copilot_hourly_limit, window_s=60 * 60)

    v1 = APIRouter(prefix="/v1")
    v1.include_router(tickers.router)
    v1.include_router(ticker.router)
    v1.include_router(ticker_research.router)
    v1.include_router(prices.router)
    v1.include_router(copilot.router)
    v1.include_router(auth.router)
    v1.include_router(auth.me_router)
    v1.include_router(portfolio.router)
    v1.include_router(market.router)
    v1.include_router(templates.router)
    v1.include_router(site.router)

    class Health(BaseModel):
        status: str
        market_data: str
        universe_size: int
        universe_as_of: str | None

    @v1.get("/health", operation_id="health", tags=["health"])
    def health() -> Health:
        universe: Universe = app.state.universe
        try:
            universe.refresh()
            market = "ok"
        except MarketDataUnavailable as exc:
            market = f"unavailable: {exc}"
        return Health(
            status="ok",
            market_data=market,
            universe_size=len(universe.tickers),
            universe_as_of=universe.as_of,
        )

    app.include_router(v1)
    return app


app = create_app()
