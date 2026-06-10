import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Iterable

from config import DATABASE_PATH, DATABASE_URL

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # local SQLite-only testing still works without psycopg2 installed
    psycopg2 = None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def using_postgres() -> bool:
    return bool(DATABASE_URL)


@contextmanager
def get_conn():
    if using_postgres():
        if psycopg2 is None:
            raise RuntimeError("DATABASE_URL is set, but psycopg2-binary is not installed.")
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _sql(sql: str) -> str:
    """Write queries with %s placeholders; convert to ? for SQLite."""
    if using_postgres():
        return sql
    return sql.replace("%s", "?")


def execute(conn, sql: str, params: Iterable[Any] = ()):  # returns cursor
    cur = conn.cursor()
    cur.execute(_sql(sql), tuple(params))
    return cur


def fetchall(conn, sql: str, params: Iterable[Any] = ()) -> List[Dict[str, Any]]:
    cur = execute(conn, sql, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(row) for row in rows]


def fetchone(conn, sql: str, params: Iterable[Any] = ()) -> Optional[Dict[str, Any]]:
    cur = execute(conn, sql, params)
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def init_db() -> None:
    with get_conn() as conn:
        if using_postgres():
            execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT
                )
                """,
            ).close()
            execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS watchlist (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, stock_code),
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
                """,
            ).close()
            execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS report_logs (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    report_text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """,
            ).close()
        else:
            execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT
                )
                """,
            ).close()
            execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, stock_code),
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
                """,
            ).close()
            execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS report_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    report_text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """,
            ).close()

        # Migration for old SQLite DBs created by the first MVP.
        # Ignore errors if the columns already exist.
        for alter in [
            "ALTER TABLE users ADD COLUMN display_name TEXT",
            "ALTER TABLE users ADD COLUMN last_seen_at TEXT",
        ]:
            try:
                execute(conn, alter).close()
            except Exception:
                pass


def add_user(user_id: str, display_name: Optional[str] = None) -> None:
    with get_conn() as conn:
        if using_postgres():
            execute(
                conn,
                """
                INSERT INTO users(user_id, display_name, created_at, last_seen_at)
                VALUES(%s, %s, %s, %s)
                ON CONFLICT(user_id) DO UPDATE SET
                    display_name = COALESCE(EXCLUDED.display_name, users.display_name),
                    last_seen_at = EXCLUDED.last_seen_at
                """,
                (user_id, display_name, now_iso(), now_iso()),
            ).close()
        else:
            # SQLite supports ON CONFLICT DO UPDATE in modern versions.
            execute(
                conn,
                """
                INSERT INTO users(user_id, display_name, created_at, last_seen_at)
                VALUES(%s, %s, %s, %s)
                ON CONFLICT(user_id) DO UPDATE SET
                    display_name = COALESCE(excluded.display_name, users.display_name),
                    last_seen_at = excluded.last_seen_at
                """,
                (user_id, display_name, now_iso(), now_iso()),
            ).close()


def add_watch_stock(user_id: str, stock_code: str, stock_name: Optional[str] = None) -> None:
    add_user(user_id)
    with get_conn() as conn:
        if using_postgres():
            execute(
                conn,
                """
                INSERT INTO watchlist(user_id, stock_code, stock_name, created_at)
                VALUES(%s, %s, %s, %s)
                ON CONFLICT(user_id, stock_code) DO UPDATE SET
                    stock_name = EXCLUDED.stock_name,
                    created_at = EXCLUDED.created_at
                """,
                (user_id, stock_code, stock_name or "", now_iso()),
            ).close()
        else:
            execute(
                conn,
                """
                INSERT OR REPLACE INTO watchlist(user_id, stock_code, stock_name, created_at)
                VALUES(%s, %s, %s, %s)
                """,
                (user_id, stock_code, stock_name or "", now_iso()),
            ).close()


def remove_watch_stock(user_id: str, stock_code: str) -> int:
    with get_conn() as conn:
        cur = execute(
            conn,
            "DELETE FROM watchlist WHERE user_id = %s AND stock_code = %s",
            (user_id, stock_code),
        )
        rowcount = cur.rowcount
        cur.close()
        return rowcount


def get_watchlist(user_id: str) -> List[Dict[str, Any]]:
    add_user(user_id)
    with get_conn() as conn:
        return fetchall(
            conn,
            "SELECT stock_code, stock_name FROM watchlist WHERE user_id = %s ORDER BY stock_code",
            (user_id,),
        )


def get_all_users() -> List[str]:
    with get_conn() as conn:
        rows = fetchall(conn, "SELECT user_id FROM users ORDER BY created_at")
    return [row["user_id"] for row in rows]


def get_user_summaries() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        users = fetchall(
            conn,
            """
            SELECT user_id, display_name, created_at, last_seen_at
            FROM users
            ORDER BY created_at
            """,
        )
        for user in users:
            stocks = fetchall(
                conn,
                "SELECT stock_code, stock_name FROM watchlist WHERE user_id = %s ORDER BY stock_code",
                (user["user_id"],),
            )
            user["watchlist"] = stocks
    return users


def save_report_log(user_id: str, report_text: str) -> None:
    with get_conn() as conn:
        execute(
            conn,
            "INSERT INTO report_logs(user_id, report_text, created_at) VALUES(%s, %s, %s)",
            (user_id, report_text, now_iso()),
        ).close()


def count_report_logs() -> int:
    with get_conn() as conn:
        row = fetchone(conn, "SELECT COUNT(*) AS count FROM report_logs")
    return int(row["count"]) if row else 0
