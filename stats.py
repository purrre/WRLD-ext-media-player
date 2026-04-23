import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats.db")

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value REAL NOT NULL DEFAULT 0
        )
    """)
    for key, default in [
        ("total_tracks_played", 0),
        ("total_play_time", 0.0),
        ("total_vc_time", 0.0),
        ("radio_songs_played", 0),
    ]:
        conn.execute(
            "INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)",
            (key, default),
        )
    conn.commit()
    conn.close()


def get_stats():
    conn = _get_conn()
    rows = conn.execute("SELECT key, value FROM stats").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}


def increment(key, amount=1):
    conn = _get_conn()
    conn.execute("UPDATE stats SET value = value + ? WHERE key = ?", (amount, key))
    conn.commit()
    conn.close()


def add_time(key, seconds):
    increment(key, seconds)
