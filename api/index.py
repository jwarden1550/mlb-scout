import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, jsonify
from analyzer import search_player, get_player_stats, generate_scouting_report
from database import init_db, save_report

app = Flask(__name__, template_folder="../templates")

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scout", methods=["POST"])
def scout():
    data = request.get_json()
    player_name = data.get("player_name", "").strip()

    if not player_name:
        return jsonify({"error": "Please enter a player name."}), 400

    player_id, full_name = search_player(player_name)

    if not player_id:
        return jsonify({"error": f"Player '{player_name}' not found. Try their full name."}), 404

    stats = get_player_stats(player_id)
    report = generate_scouting_report(stats)

    save_report(full_name, report)

    return jsonify({
        "player_name": full_name,
        "report": report
    })

if __name__ == "__main__":
    app.run(debug=True)
