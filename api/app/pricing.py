"""Plan tiers and prices: the same configuration the Moyasar checkout charges.

Ported from llm-council/backend/pricing.py (the old backend's single source for
plan prices). Same environment variables and defaults, so a price change made
for the checkout reaches /pricing too. Elite is parked unless ELITE_ENABLED is set
(the live site serves Free and Pro only).
"""

import os

CURRENCY = "SAR"
INTERVAL = "monthly"
PROVIDER = "moyasar"

_RANK = {"free": 0, "pro": 1, "elite": 2}
_NAME = {"free": "Free", "pro": "Pro", "elite": "Elite"}
_NAME_AR = {"free": "مجاني", "pro": "برو", "elite": "إيليت"}
_DEFAULT_PRICE = {"free": "0", "pro": "79", "elite": "399"}


def price_sar(plan: str) -> int:
    return int(os.getenv(f"PRICE_{plan.upper()}_SAR", _DEFAULT_PRICE[plan]))


def plan_ids() -> list[str]:
    ids = ["free", "pro"]
    if os.getenv("ELITE_ENABLED", "false").lower() == "true":
        ids.append("elite")
    return ids


def public_plans() -> list[dict]:
    return [
        {
            "id": p,
            "name": _NAME[p],
            "name_ar": _NAME_AR[p],
            "price_sar": price_sar(p),
            "currency": CURRENCY,
            "interval": INTERVAL,
            "rank": _RANK[p],
            "paid": price_sar(p) > 0,
        }
        for p in plan_ids()
    ]
