import os
import requests
from google import genai
from dotenv import load_dotenv

load_dotenv()

def _get_client():
    return genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

def search_player(player_name):
    """Search for a player by name and return their ID."""
    url = "https://statsapi.mlb.com/api/v1/sports/1/players"
    response = requests.get(url)
    data = response.json()
    
    name_lower = player_name.lower()
    for player in data["people"]:
        if name_lower in player["fullName"].lower():
            return player["id"], player["fullName"]
    
    return None, None

def get_player_stats(player_id):
    """Get hitting or pitching stats for a player."""
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}?hydrate=stats(group=[hitting,pitching],type=season)"
    response = requests.get(url)
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
{concise}
"""
    
    response = _get_client().models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text