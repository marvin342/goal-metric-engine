import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math

# --- PAGE SETUP ---
st.set_page_config(page_title="SHARP SOCCER AI v11.3", layout="wide", page_icon="☢️")

# --- UI STYLING ---
st.markdown("""
    <style>
    .nuke-card { background: #0e1117; border: 2px solid #ff4b4b; padding: 20px; border-radius: 15px; margin-bottom: 20px; }
    .avoid-card { background: #1a1c24; border: 2px dashed #666; padding: 15px; border-radius: 10px; opacity: 0.6; }
    .recommendation-box { background: #2e7d32; color: white; padding: 5px 15px; border-radius: 5px; font-weight: bold; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"

def get_market_analysis(xg_total):
    h_xg, a_xg = xg_total * 0.52, xg_total * 0.48
    probs = {"1.5": 0, "2.5": 0, "3.5": 0}
    for i in range(10):
        for j in range(10):
            p = poisson.pmf(i, h_xg) * poisson.pmf(j, a_xg)
            if (i == 0 and j == 0) or (i == 1 and j == 1): p *= 1.15 # Dixon-Coles
            if i + j > 1.5: probs["1.5"] += p
            if i + j > 2.5: probs["2.5"] += p
            if i + j > 3.5: probs["3.5"] += p
    return probs

# =======================
# 📡 THE ENGINE
# =======================
st.title("⚽ SHARP AI: MARKET SELECTOR")
st.sidebar.header("Scan Filter")
min_edge = st.sidebar.slider("Minimum Value Edge", 0.05, 0.20, 0.08)

@st.cache_data(ttl=300)
def fetch_data():
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds"
    params = {"apiKey": API_KEY, "regions": "uk", "markets": "totals", "oddsFormat": "decimal"}
    return requests.get(url, params=params).json()

matches = fetch_data()

for m in matches[:35]:
    try:
        # Get Bookie Price for Over 2.5 (Our baseline)
        market = m['bookmakers'][0]['markets'][0]
        o25_price = next(o['price'] for o in market['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5)
        
        # Calculate AI Probabilities
        target_xg = 2.45 + (1.28 / math.log(o25_price + 0.08))
        preds = get_market_analysis(target_xg)
        
        # Calculate Edges
        edge_25 = preds["2.5"] - (1/o25_price)
        
        # --- LOGIC: WHICH ONE TO TAKE? ---
        best_market = "None"
        if edge_25 > min_edge:
            if preds["3.5"] > 0.45: best_market = "OVER 3.5 (Aggressive)"
            elif preds["2.5"] > 0.75: best_market = "OVER 2.5 (Strong)"
            else: best_market = "OVER 1.5 (Safe)"

        # --- LOGIC: WHICH TO AVOID? ---
        # Avoid games with low expected goals or where the bookie is offering bad value
        is_trap = target_xg < 2.1 or edge_25 < 0.02

        if not is_trap and best_market != "None":
            with st.container():
                st.markdown(f'<div class="nuke-card"><h3>✅ {m["home_team"]} vs {m["away_team"]}</h3>', unsafe_allow_html=True)
                st.markdown(f'<div class="recommendation-box">🎯 TAKE: {best_market}</div>', unsafe_allow_html=True)
                
                cols = st.columns(3)
                cols[0].metric("Sharp O2.5 Prob", f"{preds['2.5']:.1%}")
                cols[1].metric("Value Edge", f"{edge_25:+.1%}")
                cols[2].metric("Target xG", f"{target_xg:.2f}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        elif is_trap:
            with st.expander(f"❌ AVOID: {m['home_team']} vs {m['away_team']} (Low Value / Trap)"):
                st.write("Reason: Market is too efficient or projected goals are too low for a safe bet.")
                
    except: continue
