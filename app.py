import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="SHARP SOCCER AI v11.2 - GLOBAL ELITE", layout="wide", page_icon="⚽")

# --- PRO UI DESIGN ---
st.markdown("""
    <style>
    .metric-card { background: #111; border: 1px solid #444; padding: 20px; border-radius: 10px; }
    .nuke-header {
        background: linear-gradient(90deg, #1a1a1a 0%, #d40000 100%);
        color: white; padding: 15px; border-radius: 8px; text-align: center;
        font-weight: 800; font-size: 22px; text-transform: uppercase;
        border: 1px solid #ff4b4b; box-shadow: 0 0 20px rgba(212, 0, 0, 0.4);
    }
    .edge-box { color: #00ff00; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"

# --- LEAGUE REGISTRY ---
LEAGUES = {
    "Spain LaLiga": "soccer_spain_la_liga",
    "Italy Serie A": "soccer_italy_serie_a",
    "Italy Serie B": "soccer_italy_serie_b",
    "Brazil Serie A": "soccer_brazil_campeonato",
    "Germany Bundesliga": "soccer_germany_bundesliga"
}

# --- THE GOD-TIER ENGINE ---
def get_god_mode_probs(xg_total, league_key):
    # Adjust Home/Away bias based on league profile
    # Brazil and Italy B tend to have stronger home-field advantages
    h_bias = 0.54 if league_key in ["soccer_brazil_campeonato", "soccer_italy_serie_b"] else 0.52
    h_xg, a_xg = xg_total * h_bias, xg_total * (1 - h_bias)
    
    probs = {"1.5": 0, "2.5": 0, "3.5": 0}
    for i in range(12):
        for j in range(12):
            p = poisson.pmf(i, h_xg) * poisson.pmf(j, a_xg)
            # Dixon-Coles Adjustment
            if (i == 0 and j == 0) or (i == 1 and j == 1): p *= 1.12
            if i + j > 1.5: probs["1.5"] += p
            if i + j > 2.5: probs["2.5"] += p
            if i + j > 3.5: probs["3.5"] += p
    return probs

# =======================
# 📡 SIDEBAR CONTROLS
# =======================
st.sidebar.title("☢️ CONTROL CENTER")
selected_labels = st.sidebar.multiselect("Select Leagues to Scan", list(LEAGUES.keys()), default=["Spain LaLiga", "Germany Bundesliga"])
nuke_val = st.sidebar.slider("Nuke Sensitivity (Edge %)", 0.05, 0.20, 0.09)
st.sidebar.info("App refreshes every 5 mins to catch market moves.")

# =======================
# 📡 DATA FETCHING
# =======================
@st.cache_data(ttl=300)
def fetch_league_data(league_id):
    url = f"https://api.the-odds-api.com/v4/sports/{league_id}/odds"
    params = {"apiKey": API_KEY, "regions": "uk,eu", "markets": "totals", "oddsFormat": "decimal"}
    res = requests.get(url, params=params)
    return res.json() if res.status_code == 200 else []

# =======================
# 🚀 MAIN DASHBOARD
# =======================
st.title("⚽ SHARP AI: GLOBAL VALUE SCANNER")
found_any = False

if not selected_labels:
    st.warning("Please select at least one league in the sidebar.")
else:
    for label in selected_labels:
        st.subheader(f"📡 Scanning {label}...")
        matches = fetch_league_data(LEAGUES[label])
        
        if not matches:
            st.write("No upcoming matches found for this league today.")
            continue

        for m in matches:
            try:
                # Find Over 2.5 Market
                bookie = m['bookmakers'][0]
                market = bookie['markets'][0]
                o25 = next(o for o in market['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5)
                price = o25['price']
                
                # Math Engine
                target_xg = 2.48 + (1.28 / math.log(price + 0.08))
                ai_preds = get_god_mode_probs(target_xg, LEAGUES[label])
                edge = ai_preds["2.5"] - (1 / price)

                if edge >= nuke_val:
                    found_any = True
                    with st.container():
                        st.markdown(f'<div class="nuke-header">☢️ {label} NUKE: {m["home_team"]} v {m["away_team"]} ☢️</div>', unsafe_allow_html=True)
                        st.balloons()
                        
                        c = st.columns(4)
                        c[0].metric("Market Odds", f"{price}")
                        c[1].markdown(f"<div class='edge-box'>EDGE: {edge:+.1%}</div>", unsafe_allow_html=True)
                        c[2].metric("Sharp Prob", f"{ai_preds['2.5']:.1%}")
                        
                        # Kelly Stake
                        b = price - 1
                        kelly = ((b * ai_preds["2.5"]) - (1 - ai_preds["2.5"])) / b
                        c[3].metric("Stake Guide", f"{max(0, round(kelly * 0.25 * 100, 1))}%")
                        st.divider()
            except: continue

if not found_any and selected_labels:
    st.info("No 'Nuke' opportunities found in these leagues right now. The market is currently efficient.")
