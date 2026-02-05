import streamlit as st
import requests

# Dictionary of League IDs from API-Football
LEAGUES = {
    "Premier League (UK)": 39,
    "La Liga (Spain)": 140,
    "Serie A (Brazil)": 71,
    "Serie B (Brazil)": 72,
    "Bundesliga (Germany)": 78
}

st.title("🌍 Global Goal Metric Engine")

# 1. Select League
league_name = st.selectbox("Choose a League", list(LEAGUES.keys()))
league_id = LEAGUES[league_name]

# 2. Fetch Live Data (Simplified Example)
def get_league_stats(id):
    # This would call the API to get current goals scored/conceded for all teams
    # For now, we return a placeholder
    return {"Arsenal": 2.1, "Man City": 2.5, "Flamengo": 1.8} 

stats = get_league_stats(league_id)

# 3. Select Teams
col1, col2 = st.columns(2)
home_team = col1.selectbox("Home Team", list(stats.keys()))
away_team = col2.selectbox("Away Team", list(stats.keys()))

# 4. The Prediction
if st.button("Analyze Match"):
    # Real Poisson Math would happen here based on the stats we fetched
    st.write(f"Analyzing {home_team} vs {away_team} in {league_name}...")
