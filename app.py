import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math

# --- PAGE SETUP ---
st.set_page_config(page_title="Sharp Goal Engine v7 - NUKE EDITION", layout="wide", page_icon="☢️")

# --- NUKE STYLING ---
st.markdown("""
    <style>
    .nuke-box {
        background-color: #FF0000;
        color: white;
        padding: 30px;
        border-radius: 15px;
        border: 5px solid black;
        text-align: center;
        font-weight: bold;
        font-size: 28px;
        animation: pulse-red 0.8s infinite;
    }
    @keyframes pulse-red {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 20px rgba(255, 0, 0, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- API CONFIG ---
API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"
BASE_URL = "https://api.the-odds-api.com/v4/sports/"

LEAGUES = {
    "Premier League (UK)": "soccer_epl",
    "La Liga (Spain)": "soccer_spain_la_liga",
    "Serie A (Italy)": "soccer_italy_serie_a",
    "Serie B (Italy)": "soccer_italy_serie_b",
    "Brazil Serie A": "soccer_brazil_campeonato",
    "Brazil Serie B": "soccer_brazil_serie_b"
}

# --- CORE MATH ---
def calculate_sharp_metrics(h_exp, a_exp):
    o15, o25, o35, o45 = 0, 0, 0, 0
    for i in range(12):
        for j in range(12):
            prob = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            total = i + j
            if total > 1.5: o15 += prob
            if total > 2.5: o25 += prob
            if total > 3.5: o35 += prob
            if total > 4.5: o45 += prob
    return {"1.5": o15, "2.5": o25, "3.5": o35, "4.5": o45}

tab1, tab2 = st.tabs(["📡 🔥 Sharp Trusted Picks", "🎯 Custom Sharp Section"])

# =======================
# 📡 🔥 SHARP TRUSTED PICKS
# =======================
with tab1:
    st.header("Live Feed: Real-Time Market Analysis")
    selected_name = st.selectbox("Choose League", list(LEAGUES.keys()))

    if st.button("Fetch High-Confidence Picks"):
        # We fetch 'totals' instead of 'odds' to get the actual Over/Under lines
        res = requests.get(
            f"{BASE_URL}{LEAGUES[selected_name]}/odds",
            params={"apiKey": API_KEY, "regions": "uk", "markets": "totals", "oddsFormat": "decimal"},
        )
        matches = res.json()

        if not matches:
            st.warning("No live data found for this league.")
        else:
            for m in matches[:15]:
                # 1. Extract the actual bookmaker probability
                # We look for the 'Over 2.5' price from the first available bookie
                market_o25_prob = 0.5 # Default fallback
                try:
                    outcomes = m['bookmakers'][0]['markets'][0]['outcomes']
                    for o in outcomes:
                        if o['name'] == 'Over' and o['point'] == 2.5:
                            market_o25_prob = 1 / o['price']
                except: continue

                # 2. Dynamic xG calculation based on Market Probability
                # This makes the % much more realistic
                total_expected_goals = -math.log(1 - market_o25_prob) * 2.1 # Reverse-engineered Poisson
                h_xg = total_expected_goals * 0.58
                a_xg = total_expected_goals * 0.42

                metrics = calculate_sharp_metrics(h_xg, a_xg)
                
                # --- SUPER STRONG FILTER ---
                # Only "Nuke" if market probability is high AND our model confirms it
                is_nuke = market_o25_prob > 0.65 and metrics["2.5"] > 0.70

                with st.expander(f"{m['home_team']} vs {m['away_team']} | Market Conf: {market_o25_prob:.0%}"):
                    if is_nuke:
                        st.markdown('<div class="nuke-box">☢️ SHARP TRUSTED PICK: OVER 2.5 ☢️</div>', unsafe_allow_html=True)
                        st.balloons()
                    
                    cols = st.columns(4)
                    for label, val in metrics.items():
                        # We use the Market-adjusted values here
                        delta_val = "🔥 NUKE" if is_nuke and label == "2.5" else None
                        cols[i if 'i' in locals() else 0].metric(f"Over {label}", f"{val:.0%}", delta=delta_val)
                st.divider()

# =======================
# 🎯 CUSTOM SHARP SECTION
# =======================
with tab2:
    st.header("Manual Sharp Analysis Terminal")
    c1, c2 = st.columns(2)
    h_xg_in = c1.number_input("Home Team Expected Goals", 0.0, 5.0, 1.8) 
    a_xg_in = c2.number_input("Away Team Expected Goals", 0.0, 5.0, 1.4)

    if st.button("Run Custom Analysis"):
        m = calculate_sharp_metrics(h_xg_in, a_xg_in)
        res_cols = st.columns(4)
        for i, (label, val) in enumerate(m.items()):
            if val > 0.80:
                res_cols[i].metric(f"Over {label}", f"{val:.1%}", delta="☢️ NUKE")
                st.markdown(f'<div class="nuke-box">☢️ MAX CONVICTION: OVER {label} ☢️</div>', unsafe_allow_html=True)
            else:
                res_cols[i].metric(f"Over {label}", f"{val:.1%}")
