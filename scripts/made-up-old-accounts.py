"""A made-up old-site database for checking the import on a server (docs/account-import.md).

    python -I scripts/made-up-old-accounts.py <prefix> <out.sqlite>

Writes, with the old backend's columns that app/import_old.py reads, @example.com accounts
<prefix>-{en,ar}-{1440,390}@example.com without a registration acceptance (what most old
members are) and <prefix>-accepted@example.com with one. web/scripts/check-imported.mjs then
sets their passwords through the real pages.
"""

import sqlite3
import sys
from pathlib import Path

prefix, out = sys.argv[1], Path(sys.argv[2])
if out.exists():
    sys.exit(f"{out} exists")
conn = sqlite3.connect(out)
conn.execute(
    "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT, hashed_pw TEXT,"
    " is_active INTEGER, preferred_language TEXT, created_at TEXT, first_name TEXT, last_name TEXT,"
    " deletion_pending_at TEXT)"
)
conn.execute(
    "CREATE TABLE registration_acceptances (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,"
    " accepted_at TEXT NOT NULL, acceptance_text_version TEXT NOT NULL, terms_version TEXT NOT NULL,"
    " privacy_version TEXT NOT NULL)"
)
rows = [(f"{prefix}-{loc}-{w}@example.com", loc) for loc in ("en", "ar") for w in ("1440", "390")]
rows.append((f"{prefix}-accepted@example.com", "en"))
for email, loc in rows:
    # A bcrypt hash of the bare password, as the old site stored: the import never brings it.
    conn.execute(
        "INSERT INTO users (username, email, hashed_pw, is_active, preferred_language, created_at, first_name,"
        " last_name) VALUES ('check', ?, '$2b$12$madeupmadeupmadeupmadeuOq3W6ZQb2qQx9vV1m2b3n4m5b6v7c8x', 1, ?,"
        " '2026-05-01T09:00:00+00:00', 'Check', 'Account')",
        (email, loc),
    )
conn.execute(
    "INSERT INTO registration_acceptances (user_id, accepted_at, acceptance_text_version, terms_version,"
    " privacy_version) SELECT id, '2026-05-01T09:00:01+00:00', '1.0', '1.2', '1.2' FROM users"
    " WHERE email LIKE '%-accepted@example.com'"
)
conn.commit()
conn.close()
print(f"{out}: {len(rows)} made-up accounts")
