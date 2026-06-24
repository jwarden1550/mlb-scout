import os
import psycopg2


def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            player_name TEXT NOT NULL,
            report TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def save_report(player_name, report):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reports (player_name, report) VALUES (%s, %s) RETURNING id",
        (player_name, report)
    )
    report_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return report_id


def get_recent_reports(limit=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, player_name, created_at FROM reports ORDER BY created_at DESC LIMIT %s",
        (limit,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
