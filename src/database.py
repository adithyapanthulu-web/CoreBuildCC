import sqlite3
from datetime import datetime

def get_connection():
    conn = sqlite3.connect("../data/corebuild.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # REPORT LEADS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        date TEXT,
        downloads INTEGER DEFAULT 0
    )
    """)

    # AI SCAN TRACKING

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        date TEXT,
        timestamp TEXT,
        issue TEXT,
        blocked INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


# ----------------------------
# USER REPORT FUNCTIONS
# ----------------------------

def get_user(phone, date):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE phone=? AND date=?",
        (phone, date)
    )

    user = cur.fetchone()
    conn.close()

    return user


def update_download(phone, name, date):

    conn = get_connection()
    cur = conn.cursor()

    existing = get_user(phone, date)

    if existing:

        cur.execute(
            """
            UPDATE users
            SET downloads = downloads + 1
            WHERE phone=? AND date=?
            """,
            (phone, date)
        )

    else:

        cur.execute(
            """
            INSERT INTO users
            (name, phone, date, downloads)
            VALUES (?, ?, ?, 1)
            """,
            (name, phone, date)
        )

    conn.commit()
    conn.close()


# ----------------------------
# AI QUOTA + ANALYTICS
# ----------------------------

def get_device_scans(device_id, date):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*) as total
        FROM ai_scans
        WHERE device_id=? AND date=? AND blocked=0
        """,
        (device_id, date)
    )

    total = cur.fetchone()["total"]

    conn.close()

    return total


def log_ai_scan(
    device_id,
    issue,
    blocked=False
):

    conn = get_connection()
    cur = conn.cursor()

    today = datetime.now().strftime(
        "%d-%m-%Y"
    )

    timestamp = datetime.now().strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    cur.execute(
        """
        INSERT INTO ai_scans
        (
            device_id,
            date,
            timestamp,
            issue,
            blocked
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            device_id,
            today,
            timestamp,
            issue,
            1 if blocked else 0
        )
    )

    conn.commit()
    conn.close()


# ----------------------------
# DASHBOARD METRICS
# ----------------------------

def get_dashboard_stats():

    conn = get_connection()
    cur = conn.cursor()

    today = datetime.now().strftime(
        "%d-%m-%Y"
    )

    cur.execute(
        "SELECT COUNT(*) as total FROM ai_scans WHERE blocked=0"
    )

    total_scans = cur.fetchone()["total"]

    cur.execute(
        """
        SELECT COUNT(*) as total
        FROM ai_scans
        WHERE date=? AND blocked=0
        """,
        (today,)
    )

    today_scans = cur.fetchone()["total"]

    cur.execute(
        """
        SELECT COUNT(DISTINCT device_id)
        as total
        FROM ai_scans
        """
    )

    unique_devices = cur.fetchone()["total"]

    cur.execute(
        """
        SELECT COUNT(*) as total
        FROM ai_scans
        WHERE blocked=1
        """
    )

    blocked = cur.fetchone()["total"]
    cur.execute(
        """
        SELECT
        name,
        phone,
        date,
        downloads
        FROM users
        ORDER BY id DESC
        """
    )
    leads = cur.fetchall()
    conn.close()

    return ({

        "total_scans": total_scans,
        "today_scans": today_scans,
        "unique_devices": unique_devices,
        "blocked_attempts": blocked

    },leads)
