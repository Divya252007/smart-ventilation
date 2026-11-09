
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_DIR = Path(__file__).parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "ventilation.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sensor_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                mq135 INTEGER,
                temperature REAL,
                humidity REAL,
                pir_motion INTEGER,
                mode TEXT,
                fan_on INTEGER,
                relay_on INTEGER,
                red_led INTEGER,
                green_led INTEGER,
                buzzer_on INTEGER,
                air_status TEXT,
                temperature_status TEXT,
                alert_message TEXT
            )
        """)
        conn.commit()


def save_reading(data):
    timestamp = datetime.now(timezone.utc).isoformat()

    fields = [
        "mq135", "temperature", "humidity", "pir_motion",
        "mode", "fan_on", "relay_on", "red_led",
        "green_led", "buzzer_on", "air_status",
        "temperature_status", "alert_message"
    ]

    values = [data.get(field) for field in fields]

    with get_connection() as conn:
        conn.execute(
            f"""
            INSERT INTO sensor_history
            (timestamp, {', '.join(fields)})
            VALUES (?, {', '.join(['?'] * len(fields))})
            """,
            [timestamp] + values
        )
        conn.commit()


def get_latest():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sensor_history ORDER BY id DESC LIMIT 1"
        ).fetchone()

    return dict(row) if row else None


def get_history(limit=500):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM sensor_history
            ORDER BY id DESC LIMIT ?
            """,
            (limit,)
        ).fetchall()

    return [dict(row) for row in reversed(rows)]
