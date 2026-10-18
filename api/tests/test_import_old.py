"""The one-time import of the old site's accounts (app/import_old.py), against a made-up
old database with the old backend's columns."""

import hashlib
import sqlite3

import pytest
from sqlalchemy import select

from app import import_old
from app.appdb import consents, engine_for, users
from app.legal import REGISTRATION

from .test_accounts import (  # noqa: F401
    NEW_PASSWORD,
    ORIGIN,
    forgot,
    login,
    outbox,
    signup,
    token_of,
)

# The server's users table (PRAGMA table_info, 2026-10-18) and registration_acceptances.
OLD_USERS = (
    "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT, hashed_pw TEXT,"
    " is_active INTEGER, preferred_language TEXT, created_at TEXT, email_verified_at TEXT, plan TEXT,"
    " risk_style TEXT, max_position_pct REAL, hedge_appetite TEXT, profile_picture TEXT, first_name TEXT,"
    " last_name TEXT, market TEXT, investment_goal TEXT, time_horizon TEXT, risk_tolerance TEXT,"
    " deletion_pending_at TEXT)"
)
OLD_ACCEPTANCES = (
    "CREATE TABLE registration_acceptances (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,"
    " subject_ref TEXT NOT NULL, hmac_key_id TEXT NOT NULL DEFAULT 'acc-k1', accepted_at TEXT NOT NULL,"
    " locale TEXT NOT NULL, acceptance_text_version TEXT NOT NULL, acceptance_text_hash TEXT NOT NULL,"
    " registration_flow_version TEXT NOT NULL, terms_version TEXT NOT NULL, privacy_version TEXT NOT NULL,"
    " cookie_version TEXT, document_routes TEXT NOT NULL, document_hashes TEXT NOT NULL,"
    " hash_build_id TEXT NOT NULL, corrects_id INTEGER, ip TEXT, user_agent TEXT)"
)
# bcrypt of the bare password, as passlib wrote it: never accepted by auth.verify_password.
OLD_HASH = "$2b$12$KIXQJ5q0b1gU6nJq3x1o4eY9m3b8m1u3x1o4eY9m3b8m1u3x1o4eY"

ACCOUNTS = [
    # id, email, is_active, language, created_at, first, last, deletion_pending_at
    (1, "Accepted@Example.com ", 1, "ar", "2026-03-01T10:00:00+00:00", "Sara", " Ali", None),
    (2, "noaccept@example.com", None, "en", "2026-04-02T08:30:00", "", "", None),
    (3, "inactive@example.com", 0, "en", "2026-04-03T00:00:00+00:00", "", "", None),
    (4, "leaving@example.com", 1, "en", "2026-04-04T00:00:00+00:00", "", "", "2026-09-01T00:00:00+00:00"),
    (5, "Twice@example.com", 1, "en", "2026-04-05T00:00:00+00:00", "", "", None),
    (6, "twice@example.com", 1, "en", "2026-04-06T00:00:00+00:00", "", "", None),
    (7, "not-an-address", 1, "en", "2026-04-07T00:00:00+00:00", "", "", None),
    (8, "nodate@example.com", 1, "en", "last spring", "", "", None),
    (9, "tester@example.com", 1, "en", "2026-04-09T00:00:00+00:00", "", "", None),
]


def accepted(uid, at, text="1.0", terms="1.2", privacy="1.2"):
    return (uid, "ref", "acc-k1", at, "en", text, "h", "1", terms, privacy, None, "{}", "{}", "b", None, None, None)


@pytest.fixture
def old_db(tmp_path):
    path = tmp_path / "old_briefs_index.sqlite"
    conn = sqlite3.connect(path)
    conn.execute(OLD_USERS)
    conn.execute(OLD_ACCEPTANCES)
    for uid, email, active, lang, created, first, last, deleting in ACCOUNTS:
        conn.execute(
            "INSERT INTO users (id, username, email, hashed_pw, is_active, preferred_language, created_at,"
            " plan, first_name, last_name, deletion_pending_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'pro', ?, ?, ?)",
            (uid, "u", email, OLD_HASH, active, lang, created, first, last, deleting),
        )
    # Two records for account 1: the later one counts. One left by a deleted account.
    for row in (
        accepted(1, "2026-03-01T10:00:01+00:00", terms="1.1"),
        accepted(1, "2026-03-02T09:00:00+00:00"),
        accepted(None, "2026-03-03T00:00:00+00:00"),
    ):
        conn.execute(f"INSERT INTO registration_acceptances VALUES (NULL, {', '.join('?' * len(row))})", row)
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def run(client, old_db, monkeypatch):
    """The command line as on the server, against the test app's database."""
    monkeypatch.setattr(import_old, "Settings", lambda: client.app.state.settings)
    return lambda *args: import_old.main([str(old_db), "--test-addresses", *args])


def accounts(client):
    with engine_for(client.app.state.settings.database_url).connect() as conn:
        return {r.email: r for r in conn.execute(select(users)).all()}


def consents_of(client, email):
    with engine_for(client.app.state.settings.database_url).connect() as conn:
        return conn.execute(select(consents).join(users).where(users.c.email == email)).all()


def test_brings_only_the_listed_fields_and_the_old_acceptance(client, run, old_db, capsys):
    signup(client)  # tester@example.com is already here
    client.cookies.clear()
    assert run("--apply") == 0
    out = capsys.readouterr().out
    assert "imported: 2\n" in out and "with their old registration acceptance: 1" in out
    for reason in ("inactive on the old site: 1", "deletion requested on the old site: 1", "one email (owner decides): 2",
                   "not a valid email address: 1", "sign-up date unreadable: 1", "already an account here: 1"):
        assert reason in out
    assert "@" not in out and "Sara" not in out  # counts only

    got = accounts(client)
    a, b = got["accepted@example.com"], got["noaccept@example.com"]
    assert (a.display_name, a.locale, a.created_at.isoformat()[:19]) == ("Sara Ali", "ar", "2026-03-01T10:00:00")
    assert (b.display_name, b.locale, b.created_at.isoformat()[:19]) == (None, "en", "2026-04-02T08:30:00")
    assert a.password_hash == b.password_hash == import_old.UNUSABLE_PASSWORD
    assert a.id != 1 and b.id != 2  # new random ids, as sign-up gives
    (c,) = consents_of(client, "accepted@example.com")
    assert (c.kind, c.text_version, c.documents) == ("registration", "1.0", {"terms": "1.2", "privacy": "1.2"})
    assert c.accepted_at.isoformat()[:19] == "2026-03-02T09:00:00"
    assert consents_of(client, "noaccept@example.com") == []


def test_dry_run_writes_nothing_a_second_run_adds_nothing_and_the_old_file_is_untouched(client, run, old_db, capsys):
    before = hashlib.sha256(old_db.read_bytes()).hexdigest()
    run()
    assert "would import: 3" in capsys.readouterr().out and accounts(client) == {}
    run("--apply")
    run("--apply")
    assert "imported: 0\n" in capsys.readouterr().out.split("old accounts: ")[-1]
    assert len(accounts(client)) == 3
    assert hashlib.sha256(old_db.read_bytes()).hexdigest() == before


def test_test_addresses_stay_out_unless_asked(client, old_db):
    members, skipped = import_old.read_old(old_db)
    assert members == [] and skipped["test"] == 6
    assert import_old._is_test("a@mail.example.com") and import_old._is_test("a@box.test")
    assert not import_old._is_test("a@gmail.com") and not import_old._is_test("a@example.com.sa")


def test_an_imported_member_cannot_sign_in_until_a_new_password_is_set(client, run, outbox):  # noqa: F811
    run("--apply")
    email = "accepted@example.com"
    for password in ("", "a guessed password", import_old.UNUSABLE_PASSWORD, OLD_HASH):
        assert login(client, password, email).status_code == 403
    forgot(client, email)
    token = token_of(outbox[-1])
    assert client.post("/v1/auth/reset-password/check", json={"token": token}, headers=ORIGIN).json() == {"needs_terms": False}
    r = client.post("/v1/auth/reset-password", json={"token": token, "password": NEW_PASSWORD}, headers=ORIGIN)
    assert r.status_code == 200 and r.json()["user"]["display_name"] == "Sara Ali"
    client.cookies.clear()
    assert login(client, NEW_PASSWORD, email).status_code == 200
    assert len(consents_of(client, email)) == 1  # the old acceptance, not a second one


def test_a_member_without_an_acceptance_accepts_when_setting_the_password(client, run, outbox):  # noqa: F811
    run("--apply")
    email = "noaccept@example.com"
    forgot(client, email)
    token = token_of(outbox[-1])
    check = client.post("/v1/auth/reset-password/check", json={"token": token}, headers=ORIGIN)
    assert check.json() == {"needs_terms": True}
    refused = client.post("/v1/auth/reset-password", json={"token": token, "password": NEW_PASSWORD}, headers=ORIGIN)
    assert refused.status_code == 409 and "Terms of Service" in refused.json()["detail"]
    assert consents_of(client, email) == [] and login(client, NEW_PASSWORD, email).status_code == 403
    # The refusal used nothing up: the same link works with the acceptance.
    body = {"token": token, "password": NEW_PASSWORD, "accept_terms": True}
    assert client.post("/v1/auth/reset-password", json=body, headers=ORIGIN).status_code == 200
    (c,) = consents_of(client, email)
    assert (c.text_version, c.documents) == (REGISTRATION["text_version"], REGISTRATION["documents"])
    client.cookies.clear()
    assert login(client, NEW_PASSWORD, email).status_code == 200


def test_the_link_check_answers_like_the_reset_for_a_dead_link(client, outbox):  # noqa: F811
    signup(client)
    r = client.post("/v1/auth/reset-password/check", json={"token": "not-a-real-token"}, headers=ORIGIN)
    assert r.status_code == 403 and "expired" in r.json()["detail"]
    forgot(client)
    token = token_of(outbox[-1])
    # A signed-up account has its acceptance; checking twice uses nothing up.
    for _ in range(2):
        assert client.post("/v1/auth/reset-password/check", json={"token": token}, headers=ORIGIN).json() == {"needs_terms": False}
    assert client.post("/v1/auth/reset-password", json={"token": token, "password": NEW_PASSWORD}, headers=ORIGIN).status_code == 200
    assert client.post("/v1/auth/reset-password/check", json={"token": token}, headers=ORIGIN).status_code == 403


def test_check_accounts_touch_made_up_addresses_only(client, monkeypatch, capsys):
    from app import check_accounts

    monkeypatch.setattr(check_accounts, "Settings", lambda: client.app.state.settings)
    signup(client)
    signup(client, email="member@mail.com")
    assert check_accounts.main(["mint", "member@mail.com"]) == 2
    assert check_accounts.main(["forget", "%"]) == 2 and check_accounts.main(["forget", "m_"]) == 2
    assert check_accounts.main(["mint", "Tester@Example.com"]) == 0
    token = capsys.readouterr().out.strip()
    assert client.post("/v1/auth/reset-password", json={"token": token, "password": NEW_PASSWORD}, headers=ORIGIN).status_code == 200
    assert check_accounts.main(["forget", "test"]) == 0 and "removed: 1" in capsys.readouterr().out
    assert set(accounts(client)) == {"member@mail.com"}
