import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_FOLDER = WORKSPACE_ROOT / "data"
UPLOAD_FOLDER = DATA_FOLDER / "uploads"
REPORT_FOLDER = DATA_FOLDER / "reports"
DB_FILE = DATA_FOLDER / "corebuild.db"


def ensure_data_store():
    DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    REPORT_FOLDER.mkdir(parents=True, exist_ok=True)

    if not DB_FILE.exists():
        sqlite3.connect(DB_FILE).close()

    init_db()


def reset_data_store():
    if UPLOAD_FOLDER.exists():
        shutil.rmtree(UPLOAD_FOLDER)

    if REPORT_FOLDER.exists():
        shutil.rmtree(REPORT_FOLDER)

    if DB_FILE.exists():
        DB_FILE.unlink()

    ensure_data_store()


def get_connection():
    conn = sqlite3.connect(DB_FILE)
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

    # CHAT HISTORY

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        question TEXT,
        response TEXT,
        date TEXT,
        timestamp TEXT
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


def log_chat_history(name, phone, question, response_text):
    conn = get_connection()
    cur = conn.cursor()

    today = datetime.now().strftime("%d-%m-%Y")
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    cur.execute(
        """
        INSERT INTO chat_history (
            name,
            phone,
            question,
            response,
            date,
            timestamp
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            phone,
            question,
            response_text,
            today,
            timestamp
        )
    )

    conn.commit()
    conn.close()


def get_chat_history():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            name,
            phone,
            question,
            response,
            date,
            timestamp
        FROM chat_history
        ORDER BY id DESC
        """
    )

    rows = cur.fetchall()
    conn.close()

    return rows


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
