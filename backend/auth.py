"""Accounts, password hashing, and sessions (Problem 4).

Passwords: PBKDF2-HMAC-SHA256 with a per-user random salt (stdlib only).
  New format:    pbkdf2_sha256$<iterations>$<salt>$<hex digest>
  Legacy (seed): pbkdf2_sha256$<salt>$<hex digest>   (120,000 iterations)
Legacy hashes are verified, then upgraded to the new format on a successful login.

Sessions: a random token in an HttpOnly cookie. Only its SHA-256 is stored
(in the `sessions` table), so a leaked database can't be replayed as logins.
"""

import hashlib
import hmac
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

PBKDF2_ITERATIONS = 600_000  # OWASP 2023+ recommendation for PBKDF2-SHA256
LEGACY_ITERATIONS = 120_000  # what the seed database used
MIN_PASSWORD_LENGTH = 8
SESSION_COOKIE = "cc_session"
SESSION_TTL = timedelta(days=7)
COOKIE_SECURE = False  # set True when served over HTTPS

# Brute-force throttle: at most MAX_FAILURES failed logins per email+IP per window.
MAX_FAILURES = 5
FAILURE_WINDOW_SECONDS = 15 * 60
_failures: dict[str, deque[float]] = defaultdict(deque)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- password hashing ----------

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4:
        algo, iterations, salt, expected = parts
        iterations = int(iterations)
    elif len(parts) == 3:
        algo, salt, expected = parts
        iterations = LEGACY_ITERATIONS
    else:
        return False
    if algo != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return hmac.compare_digest(digest.hex(), expected)


def needs_rehash(stored: str) -> bool:
    parts = stored.split("$")
    return len(parts) != 4 or int(parts[1]) < PBKDF2_ITERATIONS


# Verified against when the email doesn't exist, so response time doesn't reveal
# which emails have accounts.
_DUMMY_HASH = hash_password(secrets.token_hex(16))


# ---------- database ----------

def init_auth_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def public_user(row: sqlite3.Row) -> dict:
    """The only user fields that ever leave the backend (never password_hash)."""
    return {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "name": row["name"],
        "email": row["email"],
    }


# ---------- router ----------

def build_router(get_db) -> APIRouter:
    router = APIRouter(prefix="/api/auth", tags=["auth"])

    def start_session(conn: sqlite3.Connection, response: Response, user_id: int) -> None:
        token = secrets.token_urlsafe(32)
        now = _now()
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (_fmt(now),))
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_token_hash(token), user_id, _fmt(now), _fmt(now + SESSION_TTL)),
        )
        response.set_cookie(
            SESSION_COOKIE,
            token,
            max_age=int(SESSION_TTL.total_seconds()),
            httponly=True,  # not readable by page JavaScript
            samesite="lax",  # not sent on cross-site POSTs
            secure=COOKIE_SECURE,
            path="/",
        )

    def current_user(request: Request) -> dict | None:
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            return None
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = ? AND s.expires_at > ?
                """,
                (_token_hash(token), _fmt(_now())),
            ).fetchone()
        return public_user(row) if row else None

    def require_user(user: dict | None = Depends(current_user)) -> dict:
        if user is None:
            raise HTTPException(status_code=401, detail="Not logged in")
        return user

    router.current_user = current_user  # type: ignore[attr-defined]
    router.require_user = require_user  # type: ignore[attr-defined]

    class SignupRequest(BaseModel):
        first_name: str = Field(min_length=1, max_length=50)
        last_name: str = Field(min_length=1, max_length=50)
        email: str = Field(max_length=254)
        password: str = Field(max_length=128)

    class LoginRequest(BaseModel):
        email: str = Field(max_length=254)
        password: str = Field(max_length=128)

    @router.post("/signup", status_code=201)
    def signup(req: SignupRequest, response: Response) -> dict:
        first, last = req.first_name.strip(), req.last_name.strip()
        email = req.email.strip().lower()
        if not first or not last:
            raise HTTPException(status_code=400, detail="First and last name are required.")
        if not EMAIL_RE.match(email):
            raise HTTPException(status_code=400, detail="Please enter a valid email address.")
        if len(req.password) < MIN_PASSWORD_LENGTH:
            raise HTTPException(
                status_code=400, detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        with get_db() as conn:
            try:
                cur = conn.execute(
                    """
                    INSERT INTO users (name, email, password_hash, first_name, last_name)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (f"{first} {last}", email, hash_password(req.password), first, last),
                )
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=409, detail="An account with that email already exists.")
            start_session(conn, response, cur.lastrowid)
            row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        return {"user": public_user(row)}

    @router.post("/login")
    def login(req: LoginRequest, request: Request, response: Response) -> dict:
        email = req.email.strip().lower()
        key = f"{email}|{request.client.host if request.client else ''}"
        attempts = _failures[key]
        cutoff = time.time() - FAILURE_WINDOW_SECONDS
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        if len(attempts) >= MAX_FAILURES:
            raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")

        with get_db() as conn:
            row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
            ok = verify_password(req.password, row["password_hash"] if row else _DUMMY_HASH)
            if not row or not ok:
                attempts.append(time.time())
                # Same message either way, so attackers can't probe which emails exist.
                raise HTTPException(status_code=401, detail="Invalid email or password.")
            attempts.clear()
            if needs_rehash(row["password_hash"]):
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (hash_password(req.password), row["id"]),
                )
            start_session(conn, response, row["id"])
        return {"user": public_user(row)}

    @router.post("/logout")
    def logout(request: Request, response: Response) -> dict:
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            with get_db() as conn:
                conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
        response.delete_cookie(SESSION_COOKIE, path="/")
        return {"ok": True}

    @router.get("/me")
    def me(user: dict | None = Depends(current_user)) -> dict:
        return {"user": user}

    return router
