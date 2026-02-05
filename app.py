import streamlit as st
import api_manager
from scipy.stats import poisson

st.title("⚽ Goal Metric Engine: 80% Win Tracker")

# 1. League Selection
leagues = {"EPL": 39, "La Liga": 140, "Brazil Serie A": 71, "Brazil Serie B": 72}
selected_league = st.sidebar.selectbox("Select League", list(leagues.keys()))
league_id = leagues[selected_league]

# 2. Prediction Math
def predict_match(home_stats, away_stats, league_avg):
    # Calculate expected goals (Simplified Poisson Logic)
    home_exp = (home_stats['all']['goals']['for'] / home_stats['all']['played'])
    away_exp = (away_stats['all']['goals']['for'] / away_stats['all']['played'])
    
    home_win_prob = 0
    for i in range(1, 10):
        for j in range(i):
            home_win_prob += poisson.pmf(i, home_exp) * poisson.pmf(j, away_exp)
    return home_win_prob

# 3. Execution
if st.button("Run Global Analysis"):
    standings = api_manager.get_league_standings(league_id)
    fixtures = api_manager.get_upcoming_fixtures(league_id)
    
    # Create a lookup for team stats
    team_stats = {team['team']['name']: team for team in standings}
    
    for game in fixtures:
        h_name = game['teams']['home']['name']
        a_name = game['teams']['away']['name']
        
        prob = predict_match(team_stats[h_name], team_stats[a_name], 1.3)
        
        st.write(f"**{h_name} vs {a_name}**")
        if prob > 0.75:
            st.success(f"🔥 HIGH CONFIDENCE BET: {h_name} Win ({prob:.1%})")
        else:
            st.info(f"Analysis: Home Win Probability at {prob:.1%}")
        st.divider()
