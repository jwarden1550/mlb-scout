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


def get_cached_report(player_name):
    """Return a report generated within the last 24 hours for this player, or None."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT report FROM reports
        WHERE LOWER(player_name) = LOWER(%s)
          AND created_at > NOW() - INTERVAL '24 hours'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (player_name,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


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


def get_all_reports(limit=50):
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


def get_report_by_id(report_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT report FROM reports WHERE id = %s",
        (report_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None
