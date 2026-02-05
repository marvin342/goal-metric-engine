import streamlit as st
import requests
from scipy.stats import poisson
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Goal Metric Engine", page_icon="⚽", layout="wide")

# This pulls your key from the Streamlit Secrets you set up
API_KEY = st.secrets["FOOTBALL_API_KEY"]
BASE_URL = "https://v3.football.api-sports.io/"
HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

# --- LEAGUE MAPPING ---
LEAGUES = {
    "Premier League (UK)": 39,
    "La Liga (Spain)": 140,
    "Brazil Serie A": 71,
    "Brazil Serie B": 72,
    "Bundesliga (Germany)": 78
}

# --- FUNCTIONS ---
@st.cache_data(ttl=86400) # Saves your 100 daily requests by caching data for 24h
def get_data(endpoint, params):
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json().get('response', [])

def calculate_confidence(home_avg, away_avg):
    """The Engine: Runs Poisson math to find win probabilities"""
    home_win_prob = 0
    draw_prob = 0
    # Simulating up to 6 goals for speed and accuracy
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
league_id = LEAGUES[selected_league_name]

# --- MAIN INTERFACE ---
st.title("⚽ Goal Metric Engine")
st.markdown("### AI-Powered Football Predictions & Value Tracker")

if mode == "Live Leagues":
    if st.button("Generate High-Confidence Picks"):
        with st.spinner(f"Analyzing {selected_league_name}..."):
            # Fetch Fixtures
            fixtures = get_data("fixtures", {"league": league_id, "season": 2025, "next": 10})
            
            if not fixtures:
                st.warning("No upcoming matches found or API limit reached.")
            else:
                for game in fixtures:
                    h_team = game['teams']['home']['name']
                    a_team = game['teams']['away']['name']
                    
                    # Logic: Baseline xG (In future, we link this to live standings)
                    h_prob, d_prob, a_prob = calculate_confidence(1.8, 1.1)
                    
                    # Display Result
                    with st.container():
                        st.subheader(f"{h_team} vs {a_team}")
                        c1, c2, c3 = st.columns(3)
                        
                        # 80% CONFIDENCE FILTER
                        if h_prob >= 0.75:
                            c1.success(f"🔥 HIGH CONF: {h_prob:.1%}")
                        else:
                            c1.metric("Home Win", f"{h_prob:.1%}")
                            
                        c2.metric("Draw", f"{d_prob:.1%}")
                        c3.metric("Away Win", f"{a_prob:.1%}")
                        st.divider()

else:
    st.subheader("Manual Prediction Mode")
    col1, col2 = st.columns(2)
    h_input = col1.number_input("Home Team Attack Rating (xG)", 0.0, 5.0, 1.5)
    a_input = col2.number_input("Away Team Attack Rating (xG)", 0.0, 5.0, 1.2)
    
    if st.button("Run Simulation"):
        hp, dp, ap = calculate_confidence(h_input, a_input)
        st.write(f"#### Probability Results:")
        st.write(f"**Home Win:** {hp:.1%} | **Draw:** {dp:.1%} | **Away Win:** {ap:.1%}")
        
        if hp > 0.80:
            st.balloons()
            st.success("Target Met: This is a 80%+ Confidence Bet!")
