"""SQLite storage: profiles, sensor/manual readings, chat history."""
from __future__ import annotations
import json, os, sqlite3, time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (user_id TEXT PRIMARY KEY, data TEXT NOT NULL, updated REAL);
CREATE TABLE IF NOT EXISTS readings (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, kind TEXT NOT NULL,
  value1 REAL NOT NULL, value2 REAL, context TEXT, source TEXT DEFAULT 'manual', ts REAL NOT NULL);
CREATE INDEX IF NOT EXISTS idx_readings ON readings(user_id, kind, ts);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, role TEXT NOT NULL,
  content TEXT NOT NULL, ts REAL NOT NULL);
CREATE INDEX IF NOT EXISTS idx_messages ON messages(user_id, id);
CREATE TABLE IF NOT EXISTS users (
  email TEXT PRIMARY KEY, name TEXT NOT NULL, pw_hash TEXT NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS login_attempts (email TEXT NOT NULL, ts REAL NOT NULL);
CREATE INDEX IF NOT EXISTS idx_attempts ON login_attempts(email, ts);
"""


def _path() -> Path:
    return Path(os.getenv("HEART_DB") or Path(__file__).resolve().parent.parent / "data" / "app.db")


@contextmanager
def conn():
    p = _path(); p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(p); c.row_factory = sqlite3.Row
    try:
        c.executescript(SCHEMA)
        yield c
        c.commit()
    finally:
        c.close()


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")


def get_profile(user_id: str) -> dict:
    with conn() as c:
        r = c.execute("SELECT data FROM profiles WHERE user_id=?", (user_id,)).fetchone()
    return json.loads(r["data"]) if r else {}


def save_profile(user_id: str, fields: dict) -> dict:
    merged = {**get_profile(user_id), **fields}
    with conn() as c:
        c.execute("INSERT INTO profiles(user_id,data,updated) VALUES(?,?,?) "
                  "ON CONFLICT(user_id) DO UPDATE SET data=excluded.data, updated=excluded.updated",
                  (user_id, json.dumps(merged), time.time()))
    return merged


def add_reading(user_id, kind, v1, v2=None, context=None, source="manual") -> int:
    with conn() as c:
        cur = c.execute("INSERT INTO readings(user_id,kind,value1,value2,context,source,ts) VALUES(?,?,?,?,?,?,?)",
                        (user_id, kind, v1, v2, context, source, time.time()))
        return cur.lastrowid


def get_readings(user_id, kind=None, days=30) -> list[dict]:
    q, a = "SELECT * FROM readings WHERE user_id=? AND ts>=?", [user_id, time.time() - days * 86400]
    if kind:
        q += " AND kind=?"; a.append(kind)
    with conn() as c:
        rows = c.execute(q + " ORDER BY ts DESC", a).fetchall()
    return [{**dict(r), "time": _iso(r["ts"])} for r in rows]


def add_message(user_id, role, content):
    with conn() as c:
        c.execute("INSERT INTO messages(user_id,role,content,ts) VALUES(?,?,?,?)", (user_id, role, content, time.time()))


def get_history(user_id, limit=12) -> list[dict]:
    with conn() as c:
        rows = c.execute("SELECT role,content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
                         (user_id, limit)).fetchall()
    return [dict(r) for r in reversed(rows)]
