import streamlit as st
import requests
from scipy.stats import poisson
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="Goal Metric Engine", layout="wide")
API_KEY = st.secrets["FOOTBALL_API_KEY"]
BASE_URL = "https://v3.football.api-sports.io/"

# --- LEAGUE SETTINGS ---
LEAGUES = {
    "Premier League (UK)": {"id": 39, "season": 2025},
    "La Liga (Spain)": {"id": 140, "season": 2025},
    "Brazil Serie A": {"id": 71, "season": 2026}, # Brazil 2026 season started Jan 28!
    "Brazil Serie B": {"id": 72, "season": 2026}
}

def get_fixtures(league_id, season):
    headers = {'x-rapidapi-host': "v3.football.api-sports.io", 'x-rapidapi-key': API_KEY}
    # Using 'from' and 'to' to find games for the next 7 days
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"{BASE_URL}fixtures?league={league_id}&season={season}&from={today}&to=2026-02-15"
    
    res = requests.get(url, headers=headers).json()
    return res.get('response', [])

# --- INTERFACE ---
st.title("⚽ Goal Metric Engine")
selected_name = st.sidebar.selectbox("Select League", list(LEAGUES.keys()))
league_id = LEAGUES[selected_name]["id"]
season = LEAGUES[selected_name]["season"]

if st.button("Check Live Fixtures"):
    fixtures = get_fixtures(league_id, season)
    
    if not fixtures:
        st.error(f"No games found for {selected_name} in the next 10 days.")
        st.info("💡 Tip: If you just created your API key, it can take 1-2 hours to activate.")
    else:
        st.success(f"Found {len(fixtures)} upcoming matches!")
        for f in fixtures:
            home = f['teams']['home']['name']
            away = f['teams']['away']['name']
            date = f['fixture']['date'][:10]
            st.write(f"**{date}** | {home} vs {away}")
