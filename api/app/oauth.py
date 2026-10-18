"""Sign in with Google (OpenID Connect, authorization-code flow, server side).

/v1/auth/google/start sends the browser to Google with a random state (only its SHA-256 is
stored, for 10 minutes, and the same value is kept in an HttpOnly cookie so only the browser
that started can finish). Google returns to <site>/auth/google/callback, the address registered
for the old site's Google client; nginx passes that to /v1/auth/google/callback here.

The code is exchanged for Google's ID token directly with Google over TLS, with the client
secret; per OpenID Connect Core 3.1.3.7 the TLS connection stands in for checking the token's
signature, and the audience, issuer and expiry are still checked.

Accounts: Google's stable id ("sub") finds a linked account. Otherwise a verified Google email
that matches an account links to it (Google has proved the address). Otherwise a new account
is made, but only when the terms were accepted on the sign-up page first.
"""

import base64
import json
import os
import secrets
import time
import urllib.parse
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, func, insert, select, update

from . import http
from .appdb import oauth_identities, oauth_states, random_id, users, utcnow
from .auth import _has_registration, _record_registration, _start_session, _token_hash, db, hash_password, settings_of, site_url

router = APIRouter(prefix="/auth/google", tags=["auth"])

AUTHORIZE = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
ISSUERS = {"https://accounts.google.com", "accounts.google.com"}
STATE_COOKIE = "acp_oauth"
STATE_MINUTES = 10


def _callback(request: Request) -> str:
    return f"{site_url(settings_of(request))}/auth/google/callback"


def _safe_next(path: str) -> str:
    """Only our own pages: a path, never another site ("//evil", "https://...")."""
    return path if path.startswith("/") and not path.startswith("//") and "\\" not in path else "/home"


def _page(locale: str, path: str) -> str:
    return f"{'/ar' if locale == 'ar' and not path.startswith('/ar') else ''}{path}"


@router.get("/start", operation_id="googleStart")
def google_start(
    request: Request,
    next: Annotated[str, Query(max_length=300)] = "/home",
    locale: Annotated[str, Query(pattern="^(en|ar)$")] = "en",
    accept: Annotated[bool, Query()] = False,
) -> RedirectResponse:
    s = settings_of(request)
    if not s.google_client_id or not os.environ.get("GOOGLE_CLIENT_SECRET"):
        return RedirectResponse(_page(locale, "/login?error=google_unavailable"), status_code=303)
    state = secrets.token_urlsafe(32)
    with db(request).begin() as conn:
        conn.execute(delete(oauth_states).where(oauth_states.c.expires_at < utcnow()))
        conn.execute(
            insert(oauth_states).values(
                state_hash=_token_hash(state),
                next_path=_safe_next(next),
                locale=locale,
                accepted_terms=accept,
                expires_at=utcnow() + timedelta(minutes=STATE_MINUTES),
            )
        )
    query = urllib.parse.urlencode(
        {
            "client_id": s.google_client_id,
            "redirect_uri": _callback(request),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
        }
    )
    response = RedirectResponse(f"{AUTHORIZE}?{query}", status_code=303)
    response.set_cookie(
        STATE_COOKIE, state, max_age=STATE_MINUTES * 60, httponly=True, secure=s.cookie_secure, samesite="lax", path="/"
    )
    return response


def _claims(id_token: str) -> dict:
    try:
        payload = id_token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (IndexError, ValueError):
        return {}


@router.get("/callback", operation_id="googleCallback")
def google_callback(
    request: Request,
    state: Annotated[str, Query(max_length=200)] = "",
    code: Annotated[str, Query(max_length=2000)] = "",
    error: Annotated[str, Query(max_length=200)] = "",
) -> RedirectResponse:
    s = settings_of(request)
    cookie = request.cookies.get(STATE_COOKIE, "")
    with db(request).begin() as conn:
        row = conn.execute(
            delete(oauth_states)
            .where(oauth_states.c.state_hash == _token_hash(state), oauth_states.c.expires_at > utcnow())
            .returning(oauth_states.c.next_path, oauth_states.c.locale, oauth_states.c.accepted_terms)
        ).first()
    locale = row.locale if row else "en"

    def fail(reason: str) -> RedirectResponse:
        r = RedirectResponse(_page(locale, f"/login?error={reason}"), status_code=303)
        r.delete_cookie(STATE_COOKIE, path="/")
        return r

    if row is None or not state or not secrets.compare_digest(cookie, state):
        return fail("google_expired")
    if error or not code:
        return fail("google_cancelled")
    token = http.call(
        "POST",
        TOKEN,
        form={
            "code": code,
            "client_id": s.google_client_id or "",
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
            "redirect_uri": _callback(request),
            "grant_type": "authorization_code",
        },
    )
    claims = _claims((token.body or {}).get("id_token", "")) if token.ok and isinstance(token.body, dict) else {}
    if (
        not claims.get("sub")
        or claims.get("aud") != s.google_client_id
        or claims.get("iss") not in ISSUERS
        or int(claims.get("exp", 0)) < time.time()
    ):
        return fail("google_failed")
    sub, email = str(claims["sub"]), str(claims.get("email", "")).strip().lower()
    verified = claims.get("email_verified") is True and "@" in email
    now = utcnow()
    response = RedirectResponse(_page(locale, row.next_path), status_code=303)
    response.delete_cookie(STATE_COOKIE, path="/")
    with db(request).begin() as conn:
        linked = conn.execute(
            select(oauth_identities.c.user_id).where(oauth_identities.c.provider == "google", oauth_identities.c.subject == sub)
        ).first()
        uid = linked.user_id if linked else None
        if uid is None and verified:
            match = conn.execute(select(users.c.id).where(users.c.email == email)).first()
            uid = match.id if match else None
        if uid is None:
            if not verified:
                return fail("google_unverified")
            if not row.accepted_terms:
                # A new account: the terms are accepted on the sign-up page, then Google again.
                r = RedirectResponse(_page(locale, "/signup?google=terms"), status_code=303)
                r.delete_cookie(STATE_COOKIE, path="/")
                return r
            uid = random_id(conn, users)
            conn.execute(
                insert(users).values(
                    id=uid,
                    email=email,
                    # Unusable: no password logs in until one is set with "Forgot password?".
                    password_hash=hash_password(secrets.token_urlsafe(32)),
                    has_password=False,
                    display_name=(str(claims.get("name") or "")[:80] or None),
                    locale=locale,
                    created_at=now,
                    email_verified_at=now,
                )
            )
            _record_registration(conn, uid)
        elif not _has_registration(conn, uid):
            # Brought over from the old site: the terms are accepted once here too.
            if not row.accepted_terms:
                r = RedirectResponse(_page(locale, "/signup?google=terms"), status_code=303)
                r.delete_cookie(STATE_COOKIE, path="/")
                return r
            _record_registration(conn, uid)
        if not linked:
            conn.execute(insert(oauth_identities).values(provider="google", subject=sub, user_id=uid, email=email or None, created_at=now))
        if verified:
            conn.execute(update(users).where(users.c.id == uid).values(email_verified_at=func.coalesce(users.c.email_verified_at, now)))
        _start_session(request, response, conn, uid)
    return response
