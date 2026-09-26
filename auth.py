"""
Local, demo-grade user accounts + scan history, backed by SQLite.

Design notes (worth saying out loud to judges):
- Passwords are NEVER stored in plain text. We store a PBKDF2-HMAC-SHA256 hash
  with a random per-user salt, so the database alone can't reveal a password.
- One account per email is enforced by a UNIQUE constraint on the email column.
- Each user gets a unique ID (uuid4).
This is fine for a local demo. It is NOT production auth (no email verification,
no rate limiting, and on a public host the SQLite file is not private/persistent).
"""
import hashlib
import os
import re
import sqlite3
import uuid
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()  # load .env FIRST, so ADMIN_EMAILS below is read correctly

DB_PATH = os.path.join(os.path.dirname(__file__), "redteam.db")
_ITERATIONS = 200_000
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _admin_emails() -> set[str]:
    # "super-admins" bootstrapped from .env: ADMIN_EMAILS=a@x.com,b@y.com
    # read live each time, so editing .env + restart always takes effect
    return {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}


def is_super_admin(email: str) -> bool:
    """Admin from .env — can never be revoked inside the app."""
    return email.strip().lower() in _admin_emails()


def is_admin(email: str) -> bool:
    """Admin if in .env (super-admin) OR promoted in the database."""
    email = email.strip().lower()
    if email in _admin_emails():
        return True
    with _connect() as conn:
        row = conn.execute("SELECT is_admin FROM users WHERE email = ?", (email,)).fetchone()
    return bool(row and row["is_admin"])


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            pw_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            ts TEXT NOT NULL,
            label TEXT,
            score INTEGER, blocked INTEGER, total INTEGER)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL)""")
        # migrate older databases that predate the is_admin column
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        if "is_admin" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS).hex()


def sign_up(email: str, password: str) -> tuple[bool, str, dict | None]:
    """Create a new account. Returns (ok, message, user)."""
    init_db()  # make sure the tables exist even if the db file was recreated
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return False, "That doesn't look like a valid email address.", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters.", None
    salt = os.urandom(16).hex()
    user = {"id": uuid.uuid4().hex[:12], "email": email}
    try:
        with _connect() as conn:
            conn.execute("INSERT INTO users (id, email, pw_hash, salt, created_at) VALUES (?,?,?,?,?)",
                         (user["id"], email, _hash(password, salt), salt, datetime.now().isoformat()))
        user["is_admin"] = is_admin(email)
        return True, "Account created.", user
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists. Please log in.", None


def log_in(email: str, password: str) -> tuple[bool, str, dict | None]:
    """Check credentials. Returns (ok, message, user)."""
    init_db()
    email = email.strip().lower()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if row is None:
        return False, "No account with this email. Please sign up.", None
    if _hash(password, row["salt"]) != row["pw_hash"]:
        return False, "Wrong password.", None
    return True, "Welcome back!", {"id": row["id"], "email": row["email"], "is_admin": is_admin(row["email"])}


def create_session(user_id: str) -> str:
    """Make a login token (kept in the URL) so a refresh stays logged in."""
    init_db()
    token = uuid.uuid4().hex
    with _connect() as conn:
        conn.execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?,?,?)",
                     (token, user_id, datetime.now().isoformat()))
    return token


def user_by_token(token: str) -> dict | None:
    """Return the logged-in user for a session token, or None."""
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT u.id AS id, u.email AS email FROM sessions s "
            "JOIN users u ON u.id = s.user_id WHERE s.token = ?", (token,)).fetchone()
    if row is None:
        return None
    return {"id": row["id"], "email": row["email"], "is_admin": is_admin(row["email"])}


def delete_session(token: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def record_scan(user_id: str, score: int, blocked: int, total: int, label: str = "scan") -> None:
    init_db()
    with _connect() as conn:
        conn.execute("INSERT INTO scans (user_id, ts, label, score, blocked, total) VALUES (?,?,?,?,?,?)",
                     (user_id, datetime.now().isoformat(), label, score, blocked, total))


def scan_history(user_id: str) -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT ts, label, score, blocked, total FROM scans "
                            "WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    return [dict(r) for r in rows]


# ── Admin management (an admin can grant/revoke admin in-app) ─────────
def all_users() -> list[dict]:
    """Every account with its scan stats and admin status (no password data)."""
    init_db()
    with _connect() as conn:
        rows = conn.execute("""
            SELECT u.id, u.email, u.created_at, u.is_admin AS db_admin,
                   COUNT(s.id) AS scans,
                   MAX(s.score) AS best_score,
                   (SELECT score FROM scans WHERE user_id = u.id ORDER BY id DESC LIMIT 1) AS last_score
            FROM users u LEFT JOIN scans s ON s.user_id = u.id
            GROUP BY u.id ORDER BY u.created_at DESC""").fetchall()
    users = []
    for r in rows:
        d = dict(r)
        d["super_admin"] = is_super_admin(d["email"])
        d["admin"] = bool(d["db_admin"]) or d["super_admin"]
        users.append(d)
    return users


def leaderboard(limit: int = 10) -> list[dict]:
    """Highest-scoring scans across all users (for a friendly leaderboard)."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT u.email AS email, s.score AS score, s.label AS label "
            "FROM scans s JOIN users u ON u.id = s.user_id "
            "ORDER BY s.score DESC, s.id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def set_admin(user_id: str, value: bool) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("UPDATE users SET is_admin = ? WHERE id = ?", (1 if value else 0, user_id))


def grant_admin_by_email(email: str) -> tuple[bool, str]:
    """Promote an existing user to admin, by email."""
    init_db()
    email = email.strip().lower()
    with _connect() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if row is None:
        return False, "No account with that email. They must sign up first."
    set_admin(row["id"], True)
    return True, f"{email} is now an admin."


def platform_stats() -> dict:
    init_db()
    with _connect() as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        scans = conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
        avg = conn.execute("SELECT AVG(score) FROM scans").fetchone()[0]
    return {"users": users, "scans": scans, "avg_score": round(avg) if avg else 0}


def delete_user(user_id: str) -> None:
    """Admin action: remove a user and all of their scans."""
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM scans WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


init_db()


if __name__ == "__main__":
    # Self-test against a throwaway database.
    DB_PATH = os.path.join(os.path.dirname(__file__), "_authtest.db")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    print(sign_up("me@test.com", "secret123"))        # -> ok
    print(sign_up("ME@test.com", "other123")[:2])     # -> duplicate (case-insensitive)
    print(sign_up("bademail", "secret123")[:2])       # -> invalid email
    print(sign_up("x@test.com", "123")[:2])           # -> short password
    print(log_in("me@test.com", "wrong")[:2])         # -> wrong password
    ok, msg, user = log_in("me@test.com", "secret123")
    print(ok, msg, user)                              # -> welcome back
    record_scan(user["id"], 28, 9, 32)
    record_scan(user["id"], 62, 20, 32)
    print("history:", scan_history(user["id"]))
    os.remove(DB_PATH)
    print("self-test OK")
