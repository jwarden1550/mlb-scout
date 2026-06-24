import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify
from database import get_connection, get_watched_players, save_report
from analyzer import get_player_stats, generate_scouting_report
from datetime import datetime

app = Flask(__name__)

@app.route("/api/cron", methods=["GET"])
def cron():
    """Daily cleanup: remove reports older than 24 hours so cache stays current.
    On Mondays, also generate fresh weekly reports for all watched players."""

    # 1. Delete reports older than 24 hours
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM reports WHERE created_at < NOW() - INTERVAL '24 hours'")
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    # 2. On Mondays, generate weekly reports for watched players
    weekly_reports = 0
    if datetime.utcnow().weekday() == 0:
        try:
            players = get_watched_players()
            for row in players:
                _db_id, player_name, player_id = row
                try:
                    stats = get_player_stats(player_id)
                    report = generate_scouting_report(stats)
                    save_report(player_name, report)
                    weekly_reports += 1
                except Exception as e:
                    print(f"Weekly report failed for {player_name}: {e}")
        except Exception as e:
            print(f"Weekly reports error: {e}")

    return jsonify({"deleted": deleted, "weekly_reports": weekly_reports})
