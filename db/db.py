"""
Simple, initial, database API revision.
"""

import datetime
import os

import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]
CONN = psycopg2.connect(DATABASE_URL, sslmode="require")


def insert_log_cache(path: str, open_time: datetime.datetime, bookmark: int):
    cur = CONN.cursor()
    cur.execute("INSERT INTO log_cache (path, open_time, bookmark) "
                "VALUES (%s, %s, %s)", path, open_time, bookmark)
    CONN.commit()
    cur.close()


def update_log_cache(path: str, open_time: datetime.datetime, bookmark: int):
    cur = CONN.cursor()
    cur.execute("UPDATE log_cache SET open_time=(%s), bookmark=(%s) "
                "WHERE path=(%s)", open_time, bookmark, path)
    CONN.commit()
    cur.close()


def get_log_cache() -> dict:
    cur = CONN.cursor(cursor_factory=psycopg2.extras.DictCursor)
    result = cur.execute("SELECT * FROM log_cache").fetchall()
    cur.close()
    d = {}
    for r in result:
        d[(r["path"], r["open_time"])] = r["bookmark"]
    return d
