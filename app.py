import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson

st.set_page_config(page_title="Goal Metric Engine v3", layout="wide", page_icon="⚽")

# --- CONFIG ---
API_KEY = st.secrets["ODDS_API_KEY"]
BASE_URL = "https://api.the-odds-api.com/v4/sports/"

# --- LEAGUE MAPPING ---
# These are the exact IDs for The-Odds-API
LEAGUES = {
    "Premier League (UK)": "soccer_epl",
    "Brazil Serie A": "soccer_brazil_campeonato",
    "La Liga (Spain)": "soccer_spain_la_liga",
    "Bundesliga (Germany)": "soccer_germany_bundesliga"
}

def get_live_odds(sport_key):
    params = {
        'apiKey': API_KEY,
        'regions': 'uk,us',
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }
    response = requests.get(f"{BASE_URL}{sport_key}/odds", params=params)
    if response.status_code != 200:
        st.error(f"API Error: {response.json().get('message', 'Failed to fetch data')}")
        return []
    return response.json()

def calculate_probs(home_xg, away_xg):
    """
    Using Poisson distribution to calculate 
    Home Win, Draw, and Away Win probabilities.
    """
    home_win_prob = 0
    draw_prob = 0
    for i in range(7): # Goals 0 to 6
        for j in range(7):
            # probability of home scoring i and away scoring j
            p = poisson.pmf(i, home_xg) * poisson.pmf(j, away_xg)
            if i > j: home_win_prob += p
            elif i == j: draw_prob += p
    return home_win_prob, draw_prob, (1 - home_win_prob - draw_prob)

# --- UI ---
st.title("⚽ Goal Metric Engine v3")
st.write("Comparing AI Poisson Math vs. Live Bookie Odds")

selected_league = st.sidebar.selectbox("Choose League", list(LEAGUES.keys()))
sport_key = LEAGUES[selected_league]

if st.button(f"Analyze {selected_league}"):
    with st.spinner("Fetching live market data..."):
        matches = get_live_odds(sport_key)
        
        if not matches:
            st.warning("No upcoming matches found for this league.")
        else:
            for match in matches[:10]:
                home = match['home_team']
                away = match['away_team']
                
                # AI Simulation: 
                # For now, we use 1.9 (Home) vs 1.2 (Away) as a baseline favorite
                # In the next step, we can pull real xG for these teams!
                h_prob, d_prob, a_prob = calculate_probs(1.9, 1.2)
                
                with st.container():
                    st.subheader(f"{home} vs {away}")
                    c1, c2, c3 = st.columns(3)
                    
                    # Highlight 80% Confidence
                    if h_prob >= 0.75: # Close to 80% threshold
                        c1.success(f"🔥 AI WIN: {h_prob:.1%}")
                    else:
                        c1.metric("AI Home Win", f"{h_prob:.1%}")
                    
                    c2.metric("AI Draw", f"{d_prob:.1%}")
                    c3.metric("AI Away Win", f"{a_prob:.1%}")
                    st.divider()
