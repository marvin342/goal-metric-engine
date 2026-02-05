import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson

st.set_page_config(page_title="Sharp Goal Engine v7", layout="wide", page_icon="🎯")

# --- SHARP TEAM DATABASE (2026 Ratings) ---
# 1.0 = League Average. >1.0 = Stronger. <1.0 = Weaker.
TEAM_RATINGS = {
    "Real Madrid": {"att": 1.85, "def": 0.70},
    "Barcelona": {"att": 1.70, "def": 0.85},
    "Flamengo": {"att": 1.65, "def": 0.75},
    "Palmeiras": {"att": 1.55, "def": 0.80},
    "Manchester City": {"att": 1.90, "def": 0.65},
    "Inter Milan": {"att": 1.75, "def": 0.70}
}

# Average goals per game by league (2025/26 constants)
LEAGUE_AVGS = {
    "Premier League (UK)": {"h": 1.55, "a": 1.25},
    "La Liga (Spain)": {"h": 1.45, "a": 1.15},
    "Serie A (Italy)": {"h": 1.40, "a": 1.10},
    "Brazil Serie A": {"h": 1.35, "a": 1.05},
    "Serie B (Italy)": {"h": 1.15, "a": 0.95},
    "Brazil Serie B": {"h": 1.10, "a": 0.90}
}

def get_sharp_probs(h_team, a_team, league_name):
    # Get ratings or default to 1.0 (average)
    h_stats = TEAM_RATINGS.get(h_team, {"att": 1.1, "def": 1.0})
    a_stats = TEAM_RATINGS.get(a_team, {"att": 1.0, "def": 1.1})
    l_avgs = LEAGUE_AVGS.get(league_name, {"h": 1.4, "a": 1.1})
    
    # Sharp Lambda Calculation
    h_exp = h_stats['att'] * a_stats['def'] * l_avgs['h']
    a_exp = a_stats['att'] * h_stats['def'] * l_avgs['a']
    
    # Poisson Matrix
    h_win, draw, away_win, o25, o35, o45 = 0, 0, 0, 0, 0, 0
    for i in range(11):
        for j in range(11):
            prob = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            if i > j: h_win += prob
            elif i == j: draw += prob
            else: away_win += prob
            if (i + j) > 2.5: o25 += prob
            if (i + j) > 3.5: o35 += prob
            if (i + j) > 4.5: o45 += prob
            
    return {"h_win": h_win, "draw": draw, "a_win": away_win, 
            "o25": o25, "o35": o35, "o45": o45, "h_exp": h_exp, "a_exp": a_exp}

# --- UI LOGIC ---
st.title("🎯 Sharp Betting Engine (80% Confidence Scan)")
selected_league = st.sidebar.selectbox("League Feed", list(LEAGUE_AVGS.keys()))

if st.button(f"Scan {selected_league} for Value"):
    # Simulated API response for brevity (use your 'requests.get' here)
    mock_matches = [{"home": "Real Madrid", "away": "Getafe"}, {"home": "Flamengo", "away": "Vitoria"}]
    
    for m in mock_matches:
        res = get_sharp_probs(m['home'], m['away'], selected_league)
        
        with st.container():
            st.subheader(f"{m['home']} vs {m['away']}")
            c1, c2, c3, c4 = st.columns(4)
            
            # 80% CONFIDENCE LOGIC
            if res['h_win'] > 0.78:
                c1.success(f"🔥 HOME WIN: {res['h_win']:.1%}")
            else:
                c1.metric("Home Win", f"{res['h_win']:.1%}")
                
            c2.metric("Over 2.5", f"{res['o25']:.1%}")
            
            if res['o35'] > 0.45:
                c3.warning(f"🚀 O3.5 VALUE: {res['o35']:.1%}")
            else:
                c3.metric("Over 3.5", f"{res['o35']:.1%}")
                
            if res['o45'] > 0.20:
                c4.error(f"💀 CRAZY GAME: {res['o45']:.1%}")
            else:
                c4.metric("Over 4.5", f"{res['o45']:.1%}")
            st.divider()
