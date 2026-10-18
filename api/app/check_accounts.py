"""Made-up accounts for checks on a server (docs/account-import.md). @example.com only: it
refuses any other address, so it can never open a member's account.

    python -m app.check_accounts mint <name@example.com>    # prints a reset token (one hour)
    python -m app.check_accounts forget <prefix>            # removes <prefix>*@example.com
"""

import secrets
import sys
from datetime import timedelta

from sqlalchemy import delete, insert, select

from .appdb import engine_for, password_resets, users, utcnow
from .auth import RESET_MINUTES, _token_hash
from .settings import Settings

DOMAIN = "@example.com"


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] not in ("mint", "forget"):
        print(__doc__, file=sys.stderr)
        return 2
    what, arg = argv[0], argv[1].strip().lower()
    with engine_for(Settings().database_url).begin() as conn:
        if what == "mint":
            if not arg.endswith(DOMAIN):
                print(f"refused: only {DOMAIN} test accounts", file=sys.stderr)
                return 2
            uid = conn.execute(select(users.c.id).where(users.c.email == arg)).scalar_one()
            token, now = secrets.token_urlsafe(32), utcnow()
            conn.execute(
                insert(password_resets).values(
                    token_hash=_token_hash(token),
                    user_id=uid,
                    created_at=now,
                    expires_at=now + timedelta(minutes=RESET_MINUTES),
                )
            )
            print(token)
        else:
            if not arg or "@" in arg or "%" in arg or "_" in arg:
                print("refused: give the part before the made-up accounts' numbers, e.g. imported-check-", file=sys.stderr)
                return 2
            gone = conn.execute(delete(users).where(users.c.email.like(f"{arg}%{DOMAIN}"))).rowcount
            print(f"removed: {gone}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
