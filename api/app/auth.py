"""Accounts: email + password, server-side sessions in an HttpOnly cookie.

- Passwords: bcrypt over a SHA-256 pre-hash (so length past 72 bytes still counts).
- Sessions: a random token in the cookie; only its SHA-256 is stored.
- Writes with a session cookie must come from an allowed Origin (CSRF).
- Login and signup are rate limited per IP and per email.
"""

import base64
import hashlib
import json
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from .appdb import consents, engine_for, prefs, rate_hits, sessions, users, utcnow
from .legal import REGISTRATION
from .settings import Settings

COOKIE = "acp_session"
# Sign-in failures answer 403, not 401: a 401 without a WWW-Authenticate challenge (cookie
# sessions have none) makes browsers drop cached HTTP Basic credentials, which logged
# testers out of the staging gate after any signed-out API call.
AUTH_FAILED = 403
SESSION_DAYS = 30
UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}

router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(prefix="/me", tags=["auth"])


# --- primitives -------------------------------------------------------------------------------


def _prehash(password: str) -> bytes:
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prehash(password), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prehash(password), hashed.encode())
    except ValueError:
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class RateLimit:
    """Sliding window per key; enough for one API process per host."""

    def __init__(self, limit: int, window_s: int):
        self.limit, self.window = limit, window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


class DbRateLimit:
    """The same sliding window, counted in the app database so that every API worker
    (uvicorn --workers N) shares one count per key."""

    def __init__(self, url: str, name: str, limit: int, window_s: int):
        self.url, self.name, self.limit, self.window = url, name, limit, window_s

    def hit(self, key: str) -> bool:
        k, now = f"{self.name}:{key}", utcnow()
        with engine_for(self.url).begin() as conn:
            conn.execute(delete(rate_hits).where(rate_hits.c.at < now - timedelta(days=1)))
            recent = conn.execute(
                select(func.count())
                .select_from(rate_hits)
                .where(rate_hits.c.key == k, rate_hits.c.at >= now - timedelta(seconds=self.window))
            ).scalar_one()
            if recent >= self.limit:
                return False
            conn.execute(insert(rate_hits).values(key=k, at=now))
            return True


def login_limit(request: Request) -> RateLimit | DbRateLimit:
    """One limiter per app instance (created in main.create_app)."""
    return request.app.state.login_limit


# --- dependencies -------------------------------------------------------------------------------


def settings_of(request: Request) -> Settings:
    return request.app.state.settings


def db(request: Request) -> Engine:
    return engine_for(settings_of(request).database_url)


class User(BaseModel):
    id: int
    email: str
    display_name: str | None
    locale: str


def current_user(request: Request) -> User | None:
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    with db(request).connect() as conn:
        row = conn.execute(
            select(users.c.id, users.c.email, users.c.display_name, users.c.locale, sessions.c.expires_at)
            .join(sessions, sessions.c.user_id == users.c.id)
            .where(sessions.c.token_hash == _token_hash(token))
        ).first()
    if row is None:
        return None
    expires = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=UTC)
    if expires < datetime.now(UTC):
        return None
    return User(id=row.id, email=row.email, display_name=row.display_name, locale=row.locale)


def require_user(user: Annotated[User | None, Depends(current_user)]) -> User:
    if user is None:
        raise HTTPException(AUTH_FAILED, "Sign in to use this.")
    return user


def check_origin(request: Request) -> None:
    """CSRF: a cookie-authenticated write must come from one of our own origins."""
    if request.method not in UNSAFE or COOKIE not in request.cookies:
        return
    origin = request.headers.get("origin")
    allowed = {o.strip() for o in settings_of(request).allowed_origins.split(",") if o.strip()}
    if origin not in allowed:
        raise HTTPException(403, "Cross-site request refused.")


def client_ip(request: Request) -> str:
    """The visitor's address for rate limits. nginx sets X-Real-IP from the connection,
    replacing anything the client sent, and the web app's rewrite passes it on. The first
    X-Forwarded-For entry is not used: the client can write it."""
    return request.headers.get("x-real-ip", "").strip() or (request.client.host if request.client else "?")


# --- endpoints ----------------------------------------------------------------------------------


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=200)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        local, _, domain = v.partition("@")
        if not local or "." not in domain or " " in v:
            raise ValueError("enter a valid email address")
        return v


class SignupBody(Credentials):
    display_name: str | None = Field(default=None, max_length=80)
    locale: str = Field(default="en", pattern="^(en|ar)$")
    # The registration acceptance (app/legal.py); an account needs it.
    accept_terms: bool = False


class DeleteBody(BaseModel):
    password: str = Field(max_length=200)


class LoginBody(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)


class Me(BaseModel):
    user: User | None


def _start_session(request: Request, response: Response, conn, user_id: int) -> None:  # noqa: ANN001
    token = secrets.token_urlsafe(32)
    conn.execute(
        insert(sessions).values(
            token_hash=_token_hash(token),
            user_id=user_id,
            created_at=utcnow(),
            expires_at=utcnow() + timedelta(days=SESSION_DAYS),
        )
    )
    response.set_cookie(
        COOKIE,
        token,
        max_age=SESSION_DAYS * 86400,
        httponly=True,
        secure=settings_of(request).cookie_secure,
        samesite="lax",
        path="/",
    )


def _limited(request: Request, email: str) -> None:
    limit = login_limit(request)
    if not (limit.hit(f"ip:{client_ip(request)}") and limit.hit(f"email:{email.strip().lower()}")):
        raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")


@router.post("/signup", operation_id="signup", dependencies=[Depends(check_origin)])
def signup(request: Request, response: Response, body: SignupBody) -> Me:
    _limited(request, body.email)
    if not body.accept_terms:
        raise HTTPException(422, "Please accept the Terms of Service and Privacy Policy to continue.")
    try:
        with db(request).begin() as conn:
            uid = conn.execute(
                insert(users).values(
                    email=body.email,
                    password_hash=hash_password(body.password),
                    display_name=(body.display_name or "").strip() or None,
                    locale=body.locale,
                    created_at=utcnow(),
                )
            ).inserted_primary_key[0]
            conn.execute(
                insert(consents).values(
                    user_id=uid,
                    kind=REGISTRATION["kind"],
                    text_version=REGISTRATION["text_version"],
                    documents=REGISTRATION["documents"],
                    accepted_at=utcnow(),
                )
            )
            _start_session(request, response, conn, uid)
    except IntegrityError as exc:
        raise HTTPException(409, "An account with this email already exists.") from exc
    return Me(user=User(id=uid, email=body.email, display_name=body.display_name, locale=body.locale))


@router.post("/login", operation_id="login", dependencies=[Depends(check_origin)])
def login(request: Request, response: Response, body: LoginBody) -> Me:
    _limited(request, body.email)
    email = body.email.strip().lower()
    with db(request).begin() as conn:
        row = conn.execute(select(users).where(users.c.email == email)).first()
        # Same error for unknown email and wrong password.
        if row is None or not verify_password(body.password, row.password_hash):
            raise HTTPException(AUTH_FAILED, "Email or password is incorrect.")
        _start_session(request, response, conn, row.id)
    return Me(user=User(id=row.id, email=row.email, display_name=row.display_name, locale=row.locale))


@router.post("/logout", operation_id="logout", dependencies=[Depends(check_origin)])
def logout(request: Request, response: Response) -> Me:
    token = request.cookies.get(COOKIE)
    if token:
        with db(request).begin() as conn:
            conn.execute(delete(sessions).where(sessions.c.token_hash == _token_hash(token)))
    response.delete_cookie(COOKIE, path="/")
    return Me(user=None)


@me_router.post("/delete", operation_id="deleteAccount", dependencies=[Depends(check_origin)])
def delete_account(
    request: Request, response: Response, body: DeleteBody, user: Annotated[User, Depends(require_user)]
) -> Me:
    """Deletes the account and everything stored with it (sessions, holdings, alerts,
    preferences, consents cascade). The password is asked again."""
    with db(request).begin() as conn:
        row = conn.execute(select(users.c.password_hash).where(users.c.id == user.id)).first()
        if row is None or not verify_password(body.password, row.password_hash):
            raise HTTPException(AUTH_FAILED, "Password is incorrect.")
        conn.execute(delete(users).where(users.c.id == user.id))
    response.delete_cookie(COOKIE, path="/")
    return Me(user=None)


@router.get("/me", operation_id="me")
def me(user: Annotated[User | None, Depends(current_user)]) -> Me:
    return Me(user=user)


# --- preferences ---------------------------------------------------------------------------------


class Prefs(BaseModel):
    """Per-user UI settings: panes, chart, language, decimals, font size, controls on hover,
    and the Copilot results pinned to My dashboards."""

    data: dict[str, Any]


@me_router.get("/prefs", operation_id="getPrefs")
def get_prefs(request: Request, user: Annotated[User, Depends(require_user)]) -> Prefs:
    with db(request).connect() as conn:
        row = conn.execute(select(prefs.c.data).where(prefs.c.user_id == user.id)).first()
    return Prefs(data=row.data if row else {})


@me_router.put("/prefs", operation_id="putPrefs", dependencies=[Depends(check_origin)])
def put_prefs(request: Request, body: Prefs, user: Annotated[User, Depends(require_user)]) -> Prefs:
    data = {k: v for k, v in body.data.items() if k in PREF_KEYS}
    if len(json.dumps(data, default=str)) > PREFS_MAX_BYTES:
        raise HTTPException(413, "Too much saved. Unpin something from My dashboards.")
    with db(request).begin() as conn:
        updated = conn.execute(
            update(prefs).where(prefs.c.user_id == user.id).values(data=data, updated_at=utcnow())
        ).rowcount
        if not updated:
            conn.execute(insert(prefs).values(user_id=user.id, data=data, updated_at=utcnow()))
        if data.get("locale") in ("en", "ar"):
            conn.execute(update(users).where(users.c.id == user.id).values(locale=data["locale"]))
    return Prefs(data=data)


PREF_KEYS = {"layout", "chart", "locale", "decimals", "fontSize", "controlsOnHover", "dashboards"}
# Pinned tables carry their rows; a few dozen fit comfortably.
PREFS_MAX_BYTES = 512_000
