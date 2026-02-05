import streamlit as st
import requests
from scipy.stats import poisson

# --- CONFIG ---
st.set_page_config(page_title="Goal Metric Engine", page_icon="⚽", layout="wide")
API_KEY = st.secrets["FOOTBALL_API_KEY"]
BASE_URL = "https://v3.football.api-sports.io/"

# --- IMPROVED LEAGUE MAPPING ---
LEAGUES = {
    "Premier League (UK)": {"id": 39, "season": 2025},
    "La Liga (Spain)": {"id": 140, "season": 2025},
    "Brazil Serie A": {"id": 71, "season": 2026},
    "Brazil Serie B": {"id": 72, "season": 2026}
}

def get_data(endpoint, params):
    headers = {'x-rapidapi-host': "v3.football.api-sports.io", 'x-rapidapi-key': API_KEY}
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params)
        return response.json()
    except:
        return None

# --- SIDEBAR DEBUGGER ---
st.sidebar.title("System Status")
if st.sidebar.button("Check API Quota"):
    status = get_data("status", {})
    if status and 'response' in status:
        rem = status['response']['requests']['remaining']
        st.sidebar.write(f"Requests Left Today: **{rem}**")
    else:
        st.sidebar.error("Could not reach API. Check your Key.")

# --- MAIN APP ---
st.title("⚽ Goal Metric Engine")
selected_league = st.sidebar.selectbox("Choose League", list(LEAGUES.keys()))
league_id = LEAGUES[selected_league]["id"]
season = LEAGUES[selected_league]["season"]

if st.button(f"Analyze Upcoming {selected_league} Matches"):
    with st.spinner("Fetching Live Data..."):
        # We try to get the next 10 games
        res = get_data("fixtures", {"league": league_id, "season": season, "next": 10})
        
        if res and res.get('response'):
            fixtures = res['response']
            st.success(f"Found {len(fixtures)} matches!")
            for game in fixtures:
                home = game['teams']['home']['name']
                away = game['teams']['away']['name']
                st.write(f"### {home} vs {away}")
                # (Poisson Math here...)
                st.divider()
        else:
            st.warning(f"No matches found for {selected_league} in Season {season}.")
            st.info("Try switching to a Brazil league; their 2026 season is currently active!")
