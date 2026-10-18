"""One-time import of the old site's accounts (docs/account-import.md).

Reads the old backend's SQLite file read-only and adds its members to this app's database
(DATABASE_URL): email, display name, language and sign-up date, and the member's own
registration acceptance where the old site recorded one. No password comes over (the old
hashes are bcrypt or sha256_crypt of the bare password, which auth.verify_password never
accepts): an imported account signs in only after its member sets a password through
"Forgot password?", and one without an acceptance accepts on that page (auth.reset_password).

Never written: the old file. Never printed: an address, a name, an id. Accounts already here
are left as they are, so a second run imports nothing new.

    python -m app.import_old /var/lib/alphacouncil/briefs_index.sqlite            # dry run
    python -m app.import_old /var/lib/alphacouncil/briefs_index.sqlite --apply
"""

import argparse
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import insert, select

from .appdb import consents, engine_for, random_id, users
from .legal import REGISTRATION
from .settings import Settings

# Not a bcrypt hash: bcrypt.checkpw refuses it (ValueError), so verify_password is False for
# every password until reset_password replaces it.
UNUSABLE_PASSWORD = "!imported-from-old-site"

# Reserved for tests and examples (RFC 2606, RFC 6761): never a member's address.
TEST_DOMAINS = ("example.com", "example.net", "example.org")
TEST_SUFFIXES = (".test", ".example", ".invalid", ".localhost")

SKIPPED = {
    "inactive": "skipped, inactive on the old site",
    "deletion": "skipped, deletion requested on the old site",
    "test": "skipped, test address (example.com, .test, ...)",
    "invalid": "skipped, not a valid email address",
    "date": "skipped, sign-up date unreadable",
    "twice": "skipped, two old accounts with one email (owner decides)",
    "here": "skipped, already an account here",
}


@dataclass
class Member:
    email: str
    display_name: str | None
    locale: str
    created_at: datetime
    # The old registration acceptance as consents values, or None.
    consent: dict | None


def _when(text: str | None) -> datetime | None:
    """The old site wrote datetime.now(timezone.utc).isoformat(); a time without a zone is UTC."""
    try:
        dt = datetime.fromisoformat((text or "").strip())
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _is_test(email: str) -> bool:
    domain = email.rpartition("@")[2]
    return domain in TEST_DOMAINS or domain.endswith(tuple(f".{d}" for d in TEST_DOMAINS) + TEST_SUFFIXES)


def _valid(email: str) -> bool:
    """The same rule as sign-up (auth.Credentials)."""
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain and " " not in email and len(email) <= 254


def read_old(path: Path, test_addresses: bool = False) -> tuple[list[Member], Counter]:
    """The members to bring and the count of old accounts left out, by reason (SKIPPED)."""
    old = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    old.row_factory = sqlite3.Row
    try:
        accounts = old.execute(
            "SELECT id, email, first_name, last_name, preferred_language, created_at, is_active,"
            " deletion_pending_at FROM users ORDER BY id"
        ).fetchall()
        has_acceptances = old.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'registration_acceptances'"
        ).fetchone()
        # A member's latest record counts, as on the old site (acceptance.latest_registration_acceptance).
        accepted = {
            r["user_id"]: r
            for r in (
                old.execute(
                    "SELECT user_id, accepted_at, acceptance_text_version, terms_version, privacy_version"
                    " FROM registration_acceptances WHERE user_id IS NOT NULL ORDER BY id"
                ).fetchall()
                if has_acceptances
                else []
            )
        }
    finally:
        old.close()

    skipped: Counter = Counter()
    emails = Counter((a["email"] or "").strip().lower() for a in accounts)
    members = []
    for a in accounts:
        email = (a["email"] or "").strip().lower()
        created = _when(a["created_at"])
        # 0 only: the old sign-in never read is_active, and some old rows may have none.
        if a["is_active"] == 0:
            skipped["inactive"] += 1
        elif a["deletion_pending_at"]:
            skipped["deletion"] += 1
        elif not _valid(email):
            skipped["invalid"] += 1
        elif _is_test(email) and not test_addresses:
            skipped["test"] += 1
        elif emails[email] > 1:
            skipped["twice"] += 1
        elif created is None:
            skipped["date"] += 1
        else:
            name = " ".join(p.strip() for p in (a["first_name"] or "", a["last_name"] or "") if p.strip())
            acc = accepted.get(a["id"])
            accepted_at = _when(acc["accepted_at"]) if acc else None
            members.append(
                Member(
                    email=email,
                    display_name=name[:80] or None,
                    locale="ar" if (a["preferred_language"] or "").strip().lower() == "ar" else "en",
                    created_at=created,
                    consent=(
                        {
                            "kind": REGISTRATION["kind"],
                            "text_version": acc["acceptance_text_version"],
                            "documents": {"terms": acc["terms_version"], "privacy": acc["privacy_version"]},
                            "accepted_at": accepted_at,
                        }
                        if acc and accepted_at
                        else None
                    ),
                )
            )
    return members, skipped


def import_members(database_url: str, members: list[Member], apply: bool) -> tuple[list[Member], int]:
    """Adds the members not here yet, in one transaction (rolled back for a dry run).
    Returns those added (or that would be) and how many were already here."""
    added, here = [], 0
    with engine_for(database_url).connect() as conn, conn.begin() as tx:
        for m in members:
            if conn.execute(select(users.c.id).where(users.c.email == m.email)).first():
                here += 1
                continue
            uid = random_id(conn, users)
            conn.execute(
                insert(users).values(
                    id=uid,
                    email=m.email,
                    password_hash=UNUSABLE_PASSWORD,
                    display_name=m.display_name,
                    locale=m.locale,
                    created_at=m.created_at,
                )
            )
            if m.consent:
                conn.execute(insert(consents).values(user_id=uid, **m.consent))
            added.append(m)
        if apply:
            tx.commit()
        else:
            tx.rollback()
    return added, here


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("old_db", type=Path, help="the old backend's SQLite file (BRIEFS_DB)")
    p.add_argument("--apply", action="store_true", help="write; without it nothing is written")
    p.add_argument(
        "--test-addresses", action="store_true", help="bring test addresses too (only for a made-up old file)"
    )
    args = p.parse_args(argv)
    if not args.old_db.is_file():
        print(f"no such file: {args.old_db}", file=sys.stderr)
        return 2

    members, skipped = read_old(args.old_db, test_addresses=args.test_addresses)
    total = len(members) + sum(skipped.values())
    added, skipped["here"] = import_members(Settings().database_url, members, args.apply)
    with_consent = sum(1 for m in added if m.consent)

    print(f"old accounts: {total}")
    print(f"{'imported' if args.apply else 'would import'}: {len(added)}")
    print(f"  with their old registration acceptance: {with_consent}")
    print(f"  to accept when they set a password: {len(added) - with_consent}")
    print(f"  in Arabic: {sum(1 for m in added if m.locale == 'ar')}")
    print(f"  with a name: {sum(1 for m in added if m.display_name)}")
    for key, label in SKIPPED.items():
        print(f"{label}: {skipped[key]}")
    print("written" if args.apply else "dry run: nothing written (add --apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
