import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def search_player(player_name):
    """Search for a player by name and return their ID."""
    url = "https://statsapi.mlb.com/api/v1/sports/1/players"
    response = requests.get(url, timeout=10)
    data = response.json()

    name_lower = player_name.lower()
    for player in data["people"]:
        if name_lower in player["fullName"].lower():
            return player["id"], player["fullName"]

    return None, None

def get_player_stats(player_id):
    """Get hitting or pitching stats for a player."""
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}?hydrate=stats(group=[hitting,pitching],type=season)"
    response = requests.get(url, timeout=10)
    data = response.json()
    
    player = data["people"][0]
    result = {
        "name": player.get("fullName"),
        "position": player.get("primaryPosition", {}).get("name"),
        "bat_side": player.get("batSide", {}).get("description"),
        "pitch_hand": player.get("pitchHand", {}).get("description"),
        "birth_city": player.get("birthCity"),
        "birth_country": player.get("birthCountry"),
        "height": player.get("height"),
        "weight": player.get("weight"),
        "age": player.get("currentAge"),
        "stats": []
    }
    
    for stat_group in player.get("stats", []):
        if stat_group.get("splits"):
            result["stats"].append(stat_group["splits"][0]["stat"])
    
    return result

HITTING_KEYS = {"gamesPlayed", "atBats", "avg", "obp", "slg", "ops", "homeRuns", "rbi", "stolenBases", "strikeOuts", "baseOnBalls"}
PITCHING_KEYS = {"gamesPlayed", "gamesStarted", "era", "whip", "inningsPitched", "strikeOuts", "wins", "losses", "saves", "homeRunsPer9", "strikeoutsPer9"}

def _filter_stats(player_data):
    filtered = {k: v for k, v in player_data.items() if k != "stats"}
    filtered["stats"] = []
    for stat_block in player_data.get("stats", []):
        keys = HITTING_KEYS if "avg" in stat_block else PITCHING_KEYS
        filtered["stats"].append({k: stat_block[k] for k in keys if k in stat_block})
    return filtered


def generate_scouting_report(player_data):
    """Send pre-filtered player stats to Gemini and get a scouting report back."""
    concise = _filter_stats(player_data)

    prompt = f"""You are a professional MLB scout with 20 years of experience.
Based on the following player data and statistics, write a detailed scouting report.

Structure your report with these sections:
- Player Overview
- Physical Profile
- Statistical Analysis
- Strengths
- Areas for Development
- Comparison to Similar Players
- Overall Scout Grade (20-80 scale, like real MLB scouting)
- Recommendation (Sign / Monitor / Pass)

Player Data:
{concise}"""

    api_key = os.environ["GROQ_API_KEY"]
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1500,
        "temperature": 0.7
    }
    try:
        response = requests.post(
            GROQ_URL,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30
        )
        if not response.ok:
            raise RuntimeError(f"Groq API error: {response.status_code} {response.reason} — {response.text[:200]}")
        return response.json()["choices"][0]["message"]["content"]
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Groq request failed: {type(e).__name__}")