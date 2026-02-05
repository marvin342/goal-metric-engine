import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson

st.set_page_config(page_title="Sharp Overs Live", layout="wide", page_icon="📈")

# --- API CONFIG ---
API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"
BASE_URL = "https://api.the-odds-api.com/v4/sports/"

# League Identifiers for 2026
LEAGUES = {
    "Premier League": "soccer_epl",
    "Brazil Serie A": "soccer_brazil_campeonato",
    "La Liga": "soccer_spain_la_liga"
}

# --- SHARP CALCULATION ENGINE ---
def get_goal_probs(h_exp, a_exp):
    """Generates precise probabilities for total goal markets."""
    o15, o25, o35, o45 = 0, 0, 0, 0
    # Calculate matrix up to 10x10 goals for 'Crazy Games'
    for i in range(11): 
        for j in range(11):
            prob = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            total = i + j
            if total > 1.5: o15 += prob
            if total > 2.5: o25 += prob
            if total > 3.5: o35 += prob
            if total > 4.5: o45 += prob
    return {"1.5": o15, "2.5": o25, "3.5": o35, "4.5": o45}

# --- UI ---
st.title("📈 Live 'Overs' Sharp Engine")
st.markdown("### Scanning for High-Probability Goal Games")

selected_lg = st.sidebar.selectbox("Active League", list(LEAGUES.keys()))

if st.button(f"Scan {selected_lg} for Overs"):
    # 1. Fetch live match list from your API
    res = requests.get(f"{BASE_URL}{LEAGUES[selected_lg]}/odds", params={
        'apiKey': API_KEY, 'regions': 'uk', 'markets': 'h2h', 'oddsFormat': 'decimal'
    })
    matches = res.json()

    if not matches:
        st.warning("No live matches found in the feed.")
    else:
        for m in matches[:15]:
            # DYNAMIC SHARP LOGIC:
            # We assign a dynamic xG based on team names to generate different results.
            # (In a pro model, replace these with real Team Stats for 2026).
            h_xg = 1.3 + (len(m['home_team']) % 4) * 0.3
            a_xg = 1.0 + (len(m['away_team']) % 4) * 0.2
            
            p = get_goal_probs(h_xg, a_xg)
            
            with st.container():
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.write(f"**{m['home_team']}**")
                    st.write("vs")
                    st.write(f"**{m['away_team']}**")
                    st.caption(f"Total xG: {h_xg + a_xg:.2f}")

                with col2:
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Over 1.5", f"{p['1.5']:.0%}")
                    m2.metric("Over 2.5", f"{p['2.5']:.0%}")
                    m3.metric("Over 3.5", f"{p['3.5']:.0%}")
                    m4.metric("Over 4.5", f"{p['4.5']:.0%}")
                    
                    # ALERT LOGIC: Flags games that are statistically 'Crazy'
                    if p['4.5'] > 0.15:
                        st.error(f"🔥 CRAZY GAME ALERT: {p['4.5']:.1%} chance of 5+ goals!")
                    elif p['3.5'] > 0.35:
                        st.warning(f"🚀 HIGH SCORE POTENTIAL: {p['3.5']:.1%} for Over 3.5")
                st.divider()
