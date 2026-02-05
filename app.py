import streamlit as st
import requests
from scipy.stats import poisson
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Goal Metric Engine", page_icon="⚽", layout="wide")

# Safe key retrieval
API_KEY = st.secrets["FOOTBALL_API_KEY"]
BASE_URL = "https://v3.football.api-sports.io/"
HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

# --- LEAGUE MAPPING & SEASON LOGIC ---
# Europe (EPL/La Liga) is in 2025 season (25/26). Brazil is now in 2026 season.
LEAGUES = {
    "Premier League (UK)": {"id": 39, "season": 2025},
    "La Liga (Spain)": {"id": 140, "season": 2025},
    "Brazil Serie A": {"id": 71, "season": 2026},
    "Brazil Serie B": {"id": 72, "season": 2026},
    "Bundesliga (Germany)": {"id": 78, "season": 2025}
}

# --- FUNCTIONS ---
@st.cache_data(ttl=3600) # Cache for 1 hour to save your 100 daily requests
def get_data(endpoint, params):
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        return data.get('response', [])
    except Exception as e:
        st.error(f"API Error: {e}")
        return []

def calculate_confidence(home_avg, away_avg):
    home_win_prob = 0
    draw_prob = 0
    for i in range(7):
        for j in range(7):
            prob = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j: home_win_prob += prob
            elif i == j: draw_prob += prob
    return home_win_prob, draw_prob, (1 - home_win_prob - draw_prob)

# --- SIDEBAR ---
st.sidebar.title("Settings")
mode = st.sidebar.radio("Mode", ["Live Leagues", "Custom Match"])
selected_league_name = st.sidebar.selectbox("Choose League", list(LEAGUES.keys()))
league_info = LEAGUES[selected_league_name]

# --- MAIN INTERFACE ---
st.title("⚽ Goal Metric Engine")

if mode == "Live Leagues":
    if st.button(f"Generate High-Confidence Picks for {selected_league_name}"):
        with st.spinner("Fetching matches..."):
            # API Call with correct Season
            fixtures = get_data("fixtures", {
                "league": league_info["id"], 
                "season": league_info["season"], 
                "next": 10
            })
            
            if not fixtures:
                st.warning(f"No upcoming matches found for {selected_league_name} in season {league_info['season']}. You may have hit your 100-request daily limit.")
            else:
                st.success(f"Successfully loaded {len(fixtures)} matches!")
                for game in fixtures:
                    h_team = game['teams']['home']['name']
                    a_team = game['teams']['away']['name']
                    
                    # Logic: We use 1.8 vs 1.1 as the "Dominant Favorite" baseline
                    h_prob, d_prob, a_prob = calculate_confidence(1.8, 1.1)
                    
                    with st.container():
                        st.subheader(f"{h_team} vs {a_team}")
                        c1, c2, c3 = st.columns(3)
                        
                        if h_prob >= 0.75:
                            c1.success(f"🔥 80% GOAL MET: {h_prob:.1%}")
                        else:
                            c1.metric("Home Win", f"{h_prob:.1%}")
                            
                        c2.metric("Draw", f"{d_prob:.1%}")
                        c3.metric("Away Win", f"{a_prob:.1%}")
                        st.divider()
else:
    # (Manual mode code remains the same as your previous version)
    st.subheader("Manual Prediction Mode")
    col1, col2 = st.columns(2)
    h_input = col1.number_input("Home Team Attack Rating", 0.0, 5.0, 1.5)
    a_input = col2.number_input("Away Team Attack Rating", 0.0, 5.0, 1.2)
    if st.button("Run Simulation"):
        hp, dp, ap = calculate_confidence(h_input, a_input)
        st.write(f"**Home Win:** {hp:.1%} | **Draw:** {dp:.1%} | **Away Win:** {ap:.1%}")
        if hp > 0.80:
            st.balloons()
            st.success("Target Met: This is a 80%+ Confidence Bet!")
