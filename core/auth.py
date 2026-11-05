"""Account security: salted scrypt (stdlib), login lockout, lazy migration from the legacy users.csv.

- Passwords are never stored in plain text or as bare SHA-256.
- 5 failed logins per email within 15 minutes → temporary lock.
- Failed logins return ONE generic message (no "email not found" hint).
"""
from __future__ import annotations
import base64, csv, hashlib, hmac, os, re, time
from pathlib import Path
from core import db

EMAIL_RE = re.compile(r"^[\w.+-]{1,64}@[\w-]{1,63}(\.[\w-]{1,63})+$")
N, R, P = 2 ** 14, 8, 1
MAX_FAILS, WINDOW = 5, 15 * 60
LEGACY_CSV = Path(__file__).resolve().parent.parent / "data" / "users.csv"
GENERIC_FAIL = "Incorrect email or password."
_b64 = lambda b: base64.b64encode(b).decode()


def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    h = hashlib.scrypt(pw.encode(), salt=salt, n=N, r=R, p=P, dklen=32)
    return f"scrypt${N}${R}${P}${_b64(salt)}${_b64(h)}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, h = stored.split("$")
        if scheme != "scrypt":
            return False
        want = base64.b64decode(h)
        got = hashlib.scrypt(pw.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p), dklen=len(want))
        return hmac.compare_digest(got, want)
    except Exception:
        return False


_DUMMY = hash_password("not-a-real-password")      # equalises timing for unknown emails


def _fails(email: str) -> int:
    with db.conn() as c:
        return c.execute("SELECT COUNT(*) FROM login_attempts WHERE email=? AND ts>=?",
                         (email, time.time() - WINDOW)).fetchone()[0]


def _legacy_row(email: str) -> dict | None:
    if not LEGACY_CSV.exists():
        return None
    try:
        with open(LEGACY_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if (row.get("email") or "").strip().lower() == email:
                    return row
    except Exception:
        pass
    return None


def register(email: str, name: str, password: str) -> tuple[bool, str]:
    email, name = email.strip().lower(), " ".join(name.split())[:60]
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    if not name:
        return False, "Please enter your name."
    if not 8 <= len(password) <= 128:
        return False, "Password must be 8–128 characters."
    with db.conn() as c:
        if c.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            return False, "Email already registered."
        c.execute("INSERT INTO users(email,name,pw_hash,created) VALUES(?,?,?,?)",
                  (email, name, hash_password(password), time.time()))
    return True, "Account created!"


def authenticate(email: str, password: str) -> tuple[bool, dict | None, str]:
    email = email.strip().lower()
    if _fails(email) >= MAX_FAILS:
        return False, None, "Too many failed attempts. Please wait 15 minutes and try again."
    with db.conn() as c:
        row = c.execute("SELECT email,name,pw_hash FROM users WHERE email=?", (email,)).fetchone()
    user = None
    if row:
        if verify_password(password, row["pw_hash"]):
            user = {"email": row["email"], "name": row["name"]}
    else:
        verify_password(password, _DUMMY)
        legacy = _legacy_row(email)                       # one-time upgrade of old SHA-256 accounts
        if legacy and hmac.compare_digest(hashlib.sha256(password.encode()).hexdigest(),
                                          str(legacy.get("password_hash", ""))):
            name = (legacy.get("name") or email)[:60]
            with db.conn() as c:
                c.execute("INSERT OR IGNORE INTO users(email,name,pw_hash,created) VALUES(?,?,?,?)",
                          (email, name, hash_password(password), time.time()))
            user = {"email": email, "name": name}
    with db.conn() as c:
        if user:
            c.execute("DELETE FROM login_attempts WHERE email=?", (email,))
        else:
            c.execute("INSERT INTO login_attempts(email,ts) VALUES(?,?)", (email, time.time()))
    return (True, user, "") if user else (False, None, GENERIC_FAIL)
