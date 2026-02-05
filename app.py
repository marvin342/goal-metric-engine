import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math

# --- PAGE SETUP ---
st.set_page_config(page_title="Sharp All-Sport Engine - NUKE EDITION", layout="wide", page_icon="☢️")

# --- NUKE STYLING ---
st.markdown("""
    <style>
    .nuke-box {
        background-color: #FF0000; color: white; padding: 30px; border-radius: 15px;
        border: 5px solid black; text-align: center; font-weight: bold; font-size: 28px;
        animation: pulse-red 0.8s infinite;
    }
    @keyframes pulse-red {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 20px rgba(255, 0, 0, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- API CONFIG (Using your key) ---
API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"
BASE_URL = "https://api.the-odds-api.com/v4/sports/"

# --- ADVANCED MATH ENGINE ---
def calculate_sharp_metrics(total_expected_goals):
    # Split xG for Home/Away (Standard 55/45 split for general sports)
    h_exp = total_expected_goals * 0.55
    a_exp = total_expected_goals * 0.45
    
    o15, o25, o35 = 0, 0, 0
    for i in range(15):
        for j in range(15):
            prob = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            if (i + j) > 1.5: o15 += prob
            if (i + j) > 2.5: o25 += prob
            if (i + j) > 3.5: o35 += prob
    return {"1.5": o15, "2.5": o25, "3.5": o35}

tab1, tab2 = st.tabs(["📡 🔥 Sharp Trusted Picks (ALL SPORTS)", "🎯 Manual Sharp Terminal"])

# =======================
# 📡 🔥 SHARP TRUSTED PICKS
# =======================
with tab1:
    st.header("Scanning All Global Markets for Nukes...")
    
    if st.button("🚀 SCAN GLOBAL UPCOMING GAMES"):
        # Fetching 'upcoming' with 'totals' market to see Over/Under lines
        res = requests.get(
            f"{BASE_URL}upcoming/odds",
            params={"apiKey": API_KEY, "regions": "us,uk", "markets": "totals", "oddsFormat": "decimal"}
        )
        
        if res.status_code != 200:
            st.error(f"API Error: {res.status_code}")
        else:
            matches = res.json()
            found_nuke = False
            
            for m in matches[:20]: # Check first 20 upcoming games
                try:
                    # Find the Over 2.5 line from the first bookmaker
                    market = m['bookmakers'][0]['markets'][0]
                    # Get the price for 'Over' at the '2.5' point
                    o25_price = next(o['price'] for o in market['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5)
                    
                    market_prob = 1 / o25_price
                    # Inverting Poisson to find implied goals
                    implied_goals = -math.log(1 - market_prob) * 2.0
                    
                    metrics = calculate_sharp_metrics(implied_goals)
                    
                    # --- SUPER STRONG FILTER ---
                    # Only show NUKE if Bookie probability is > 68% and Math confirms > 72%
                    is_nuke = market_prob > 0.68 and metrics["2.5"] > 0.72
                    
                    with st.expander(f"{m['sport_title']} | {m['home_team']} vs {m['away_team']}"):
                        if is_nuke:
                            st.markdown('<div class="nuke-box">☢️ SHARP TRUSTED PICK ☢️</div>', unsafe_allow_html=True)
                            st.balloons()
                            found_nuke = True
                        
                        c = st.columns(3)
                        c[0].metric("Market Confidence", f"{market_prob:.0%}")
                        c[1].metric("Over 2.5 Prob", f"{metrics['2.5']:.0%}")
                        c[2].metric("Implied Total Goals", f"{implied_goals:.2f}")
                except:
                    continue
            
            if not found_nuke:
                st.info("No high-confidence 'Nukes' found in the next 20 games. Try again in an hour!")

# =======================
# 🎯 MANUAL SHARP TERMINAL
# =======================
with tab2:
    st.header("Custom Game Analysis")
    h_xg = st.slider("Home Team Projected xG", 0.0, 5.0, 1.8)
    a_xg = st.slider("Away Team Projected xG", 0.0, 5.0, 1.4)
    
    if st.button("Run Sharp Analysis"):
        results = calculate_sharp_metrics(h_xg + a_xg)
        cols = st.columns(3)
        for i, (label, val) in enumerate(results.items()):
            delta_label = "☢️ NUKE" if val > 0.82 else "STRONG" if val > 0.75 else None
            cols[i].metric(f"Over {label}", f"{val:.1%}", delta=delta_label)
