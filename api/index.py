import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from analyzer import search_player, get_player_stats, generate_scouting_report
from database import init_db, save_report, get_cached_report, get_all_reports, get_report_by_id

app = Flask(__name__, template_folder="../templates")
app.secret_key = os.environ.get("SECRET_KEY", "mlb-scout-secret")

try:
    init_db()
except Exception as e:
    print(f"DB init warning: {e}")


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def login_required_api(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        admin_username = os.environ.get("ADMIN_USERNAME")
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if username == admin_username and password == admin_password:
            session["logged_in"] = True
            return redirect(url_for("index"))
        return render_template("login.html", error="Invalid username or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/reports")
@login_required
def reports():
    try:
        all_reports = get_all_reports()
    except Exception:
        all_reports = []
    return render_template("reports.html", reports=all_reports)

@app.route("/reports/<int:report_id>")
@login_required_api
def get_report(report_id):
    try:
        report_text = get_report_by_id(report_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if report_text is None:
        return jsonify({"error": "Report not found"}), 404
    return jsonify({"report": report_text})

@app.route("/scout", methods=["POST"])
@login_required_api
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
        api_key = os.environ.get("GROQ_API_KEY", "")
        if api_key:
            msg = msg.replace(api_key, "[REDACTED]")
        return jsonify({"error": f"Failed to generate report: {msg}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
