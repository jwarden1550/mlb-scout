import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify
from database import get_connection

app = Flask(__name__)

@app.route("/api/cron", methods=["GET"])
def cron():
    """Daily cleanup: remove reports older than 24 hours so cache stays current."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM reports WHERE created_at < NOW() - INTERVAL '24 hours'")
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"deleted": deleted})
