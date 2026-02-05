import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson

st.set_page_config(page_title="Sharp Goal Engine v5", layout="wide", page_icon="⚽")

# --- CONFIG ---
API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"
BASE_URL = "https://api.the-odds-api.com/v4/sports/"

# --- SHARP MATH ENGINE ---
def calculate_sharp_metrics(h_exp, a_exp):
    """Calculates win probs and Over/Under goal probabilities (O1.5 to O4.5)."""
    h_win, draw, away_win = 0, 0, 0
    o15, o25, o35, o45 = 0, 0, 0, 0
    
    # Calculate matrix up to 10 goals for depth
    for i in range(11):
        for j in range(11):
            prob = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            total = i + j
            # Result Probs
            if i > j: h_win += prob
            elif i == j: draw += prob
            else: away_win += prob
            # Goal Probs
            if total > 1.5: o15 += prob
            if total > 2.5: o25 += prob
            if total > 3.5: o35 += prob
            if total > 4.5: o45 += prob
            
    return {
        "win": (h_win, draw, away_win),
        "overs": {"1.5": o15, "2.5": o25, "3.5": o35, "4.5": o45}
    }

# --- UI TABS ---
tab1, tab2 = st.tabs(["📡 Live 2026 Feed", "🎯 Custom Sharp Section"])

with tab1:
    st.header("Live Fixtures & Overs Scanner")
    leagues = {"Premier League": "soccer_epl", "Brazil Serie A": "soccer_brazil_campeonato"}
    selected = st.selectbox("Choose League", list(leagues.keys()))
    
    if st.button("Fetch Live Predictions"):
        res = requests.get(f"{BASE_URL}{leagues[selected]}/odds", params={'apiKey': API_KEY, 'regions': 'uk', 'oddsFormat': 'decimal'})
        matches = res.json()
        
        for m in matches[:10]:
            # Simulated Sharp xG based on team name variance (Replace with real stats for production)
            h_xg = 1.3 + (len(m['home_team']) % 5) * 0.2
            a_xg = 1.0 + (len(m['away_team']) % 4) * 0.2
            metrics = calculate_sharp_metrics(h_xg, a_xg)
            
            with st.expander(f"{m['home_team']} vs {m['away_team']} (xG: {h_xg+a_xg:.2f})"):
                cols = st.columns(4)
                cols[0].metric("Over 1.5", f"{metrics['overs']['1.5']:.0%}")
                cols[1].metric("Over 2.5", f"{metrics['overs']['2.5']:.0%}")
                cols[2].metric("Over 3.5", f"{metrics['overs']['3.5']:.0%}")
                cols[3].metric("Over 4.5", f"{metrics['overs']['4.5']:.0%}")
                
                if metrics['overs']['4.5'] > 0.18:
                    st.error(f"🔥 CRAZY GAME ALERT: {metrics['overs']['4.5']:.1%} chance of 5+ goals!")
                elif metrics['overs']['3.5'] > 0.40:
                    st.warning("🚀 HIGH SCORE POTENTIAL")
                st.divider()

with tab2:
    st.header("Sharp Manual Tool")
    st.info("Manually input team ratings to see if a specific 'Over' is likely to hit.")
    
    c1, c2 = st.columns(2)
    h_xg_in = c1.number_input("Home Team Expected Goals", 0.0, 5.0, 1.8)
    a_xg_in = c2.number_input("Away Team Expected Goals", 0.0, 5.0, 1.2)
    
    if st.button("Run Custom Analysis"):
        m = calculate_sharp_metrics(h_xg_in, a_xg_in)
        st.write(f"### Results for {h_xg_in} - {a_xg_in} Expected Scoreline")
        
        res_cols = st.columns(4)
        for i, (label, val) in enumerate(m['overs'].items()):
            res_cols[i].metric(f"Over {label}", f"{val:.1%}")
            if val > 0.75: res_cols[i].success("Sharp Pick")
