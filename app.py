import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson

st.set_page_config(page_title="Goal Metric Engine v4", layout="wide", page_icon="⚽")

# --- CONFIG ---
API_KEY = st.secrets.get("ODDS_API_KEY", "2bbe95bafab32dd8fa0be8ae23608feb")
BASE_URL = "https://api.the-odds-api.com/v4/sports/"

# --- SHARP MATH ENGINE ---
def calculate_sharp_metrics(h_exp, a_exp):
    """Calculates win probs, scorelines, and 'Crazy Game' (Over 4.5) risk."""
    h_win, draw, away_win = 0, 0, 0
    over_4_5 = 0
    
    # Calculate probabilities up to 10 goals for 'Crazy Games'
    for i in range(11):
        for j in range(11):
            prob = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            if i > j: h_win += prob
            elif i == j: draw += prob
            else: away_win += prob
            
            if (i + j) > 4: over_4_5 += prob
            
    return h_win, draw, away_win, over_4_5

# --- UI SECTIONS ---
tab1, tab2 = st.tabs(["🔥 Live Value Tracker", "🎯 Custom Sharp Section"])

with tab1:
    st.header("Live Predictions")
    # Mapping for The-Odds-API
    league_keys = {"Premier League": "soccer_epl", "Brazil Serie A": "soccer_brazil_campeonato"}
    selected = st.selectbox("League", list(league_keys.keys()))
    
    if st.button("Fetch & Analyze"):
        # Note: In a full version, we'd pull league stats (averages) here.
        # For now, we simulate different strengths to show the code works.
        res = requests.get(f"{BASE_URL}{league_keys[selected]}/odds", params={'apiKey': API_KEY, 'regions': 'uk', 'oddsFormat': 'decimal'})
        matches = res.json()
        
        for m in matches[:8]:
            # DYNAMIC SIMULATION: Assigns random xG based on team names to demonstrate variance
            h_xg = 1.4 + (len(m['home_team']) % 5) * 0.2
            a_xg = 1.0 + (len(m['away_team']) % 5) * 0.1
            
            hw, dr, aw, crazy = calculate_sharp_metrics(h_xg, a_xg)
            
            with st.expander(f"{m['home_team']} vs {m['away_team']} (xG: {h_xg:.1f} - {a_xg:.1f})"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Home Win", f"{hw:.1%}")
                c2.metric("Draw", f"{dr:.1%}")
                c3.metric("Away Win", f"{aw:.1%}")
                
                if crazy > 0.15: # High threshold for Over 4.5 goals
                    c4.warning(f"⚠️ CRAZY GAME: {crazy:.1%}")
                else:
                    c4.write(f"Goal Flow: {crazy:.1%}")

with tab2:
    st.header("Custom 'Sharp' Game Analysis")
    st.info("Manually input data for games not in the live feed.")
    
    col1, col2 = st.columns(2)
    h_name = col1.text_input("Home Team Name", "Flamengo")
    h_att = col1.slider("Home Attack Strength (xG)", 0.0, 5.0, 2.1)
    
    a_name = col2.text_input("Away Team Name", "Palmeiras")
    a_def = col2.slider("Away Defensive Weakness (xG allowed)", 0.0, 5.0, 1.3)
    
    if st.button("Run Sharp Simulation"):
        # Sharp calculation: Home Att x Away Def / League Avg (Simulated as 1.3)
        h_final = (h_att * a_def) / 1.3
        # Similarly for away team
        a_final = 1.2 # Baseline
        
        hw, dr, aw, crazy = calculate_sharp_metrics(h_final, a_final)
        
        st.write(f"### Final Prediction: {h_name} ({h_final:.2f}) vs {a_name} ({a_final:.2f})")
        res_col1, res_col2 = st.columns(2)
        res_col1.write(f"**Home Win Prob:** {hw:.1%}")
        res_col1.write(f"**Draw Prob:** {dr:.1%}")
        
        if crazy > 0.20:
            st.balloons()
            st.success(f"🔥 **HIGH SCORE ALERT:** {crazy:.1%} chance of 5+ goals!")
