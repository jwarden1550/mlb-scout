import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, jsonify
from analyzer import search_player, get_player_stats, generate_scouting_report
from database import init_db, save_report, get_cached_report

app = Flask(__name__, template_folder="../templates")

try:
    init_db()
except Exception as e:
    print(f"DB init warning: {e}")

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scout", methods=["POST"])
def scout():
    try:
        data = request.get_json()
        player_name = data.get("player_name", "").strip()

        if not player_name:
            return jsonify({"error": "Please enter a player name."}), 400

        player_id, full_name = search_player(player_name)

        if not player_id:
            return jsonify({"error": f"Player '{player_name}' not found. Try their full name."}), 404

        try:
            cached = get_cached_report(full_name)
        except Exception:
            cached = None

        if cached:
            return jsonify({"player_name": full_name, "report": cached, "cached": True})

        stats = get_player_stats(player_id)
        report = generate_scouting_report(stats)

        try:
            save_report(full_name, report)
        except Exception as e:
            print(f"DB save warning: {e}")

        return jsonify({"player_name": full_name, "report": report})

    except Exception as e:
        msg = str(e)
        # Strip any API keys that may appear in URLs within error messages
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        if api_key:
            msg = msg.replace(api_key, "[REDACTED]")
        return jsonify({"error": f"Failed to generate report: {msg}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
