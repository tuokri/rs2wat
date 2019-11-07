"""
Simple, initial, database API revision.
"""

import datetime

import psycopg2

CONN = None


def init_db(database):
    global CONN
    CONN = psycopg2.connect(database, sslmode="require")


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