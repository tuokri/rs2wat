"""
Simple, initial, database API revision.
"""

import datetime
from collections import defaultdict
from typing import List

import psycopg2
import psycopg2.extras

CONN = None


def init_db(database):
    global CONN
    CONN = psycopg2.connect(database, sslmode="require")


def insert_log_cache(path: str, open_time: datetime.datetime, bookmark: int):
    cur = CONN.cursor()
    cur.execute(
        "INSERT INTO log_cache (path, open_time, bookmark) "
        "VALUES (%s, %s, %s)", (path, open_time, bookmark))
    CONN.commit()
    cur.close()


def update_log_cache(path: str, open_time: datetime.datetime, bookmark: int):
    cur = CONN.cursor()
    cur.execute(
        "UPDATE log_cache SET open_time=(%s), bookmark=(%s) "
        "WHERE path=(%s)", (open_time, bookmark, path))
    CONN.commit()
    cur.close()


def get_log_cache() -> dict:
    cur = CONN.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM log_cache")
    d = {}
    for r in cur:
        d[(str(r["path"]), r["open_time"])] = int(r["bookmark"])
    cur.close()
    return d


def insert_ip(ip: str):
    cur = CONN.cursor()
    cur.execute(
        "INSERT INTO ip (ipv4) "
        "VALUES (%s)", (ip,))
    CONN.commit()
    cur.close()


def insert_user(steamid64: int):
    cur = CONN.cursor()
    cur.execute(
        "INSERT INTO user (steamid64) "
        "VALUES (%s)", (steamid64,))
    CONN.commit()
    cur.close()


def get_users() -> List[int]:
    cur = CONN.cursor()
    cur.execute("SELECT * FROM user")
    users = []
    for user in cur:
        users.append(user)
    cur.close()
    return users


def get_ips() -> List[str]:
    cur = CONN.cursor()
    cur.execute("SELECT * FROM ip")
    ips = []
    for ip in cur:
        ips.append(ip)
    cur.close()
    return ips


def get_user_ips(steamid64: int) -> List[str]:
    cur = CONN.cursor()
    cur.execute(
        "SELECT * FROM user_ip "
        "WHERE steamid64=(%s)", (steamid64,))
    ips = []
    for ip in cur:
        ips.append(ip)
    cur.close()
    return ips


def get_all_user_ips() -> defaultdict:
    cur = CONN.cursor()
    cur.execute("SELECT * FROM user_ip")
    user_ips = defaultdict(set)
    for r in cur:
        user_ips[r["ipv4"]].add(int(r["steamid64"]))
    cur.close()
    return user_ips


def get_ip_users(ip: str) -> List[int]:
    cur = CONN.cursor()
    cur.execute(
        "SELECT * FROM user_ip "
        "WHERE ipv4=(%s)", (ip,))
    users = []
    for user in cur:
        users.append(user)
    cur.close()
    return users


def insert_user_ip(ip: str, steamid64: int):
    cur = CONN.cursor()
    cur.execute(
        "INSERT INTO user_ip (steamid64, ipv4) VALUES "
        "( steamid64, (SELECT steamid64 from user WHERE steamid64=(%s)) ),"
        "( ipv4,      (SELECT ipv4      from ip   WHERE ip=(%s)) )",
        (steamid64, ip))
    CONN.commit()
    cur.close()
