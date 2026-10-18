"""Time and cost of the advisors' sessions, from the app database.

    python -m app.debate stats [days]      # finished sessions of the last 30 days (or [days])

Run in a release's api/ with the environment of its api.env (docs/production.md, "Advisors' room").
Prints counts, seconds and OpenRouter's cost figures only; no questions or accounts.
"""

import json
import sys

from ..settings import get_settings
from . import store


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "stats":
        print(__doc__.strip())
        return 2
    days = int(argv[1]) if len(argv) > 1 else 30
    print(json.dumps(store.stats(get_settings().database_url, days), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
