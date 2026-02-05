import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="SHARP SOCCER AI v10 - ELITE", layout="wide", page_icon="☢️")

# --- STYLING ---
st.markdown("""
    <style>
    .nuke-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #000000 100%);
        border: 2px solid #ff0000; border-radius: 15px; padding: 25px;
        box-shadow: 0 0 20px rgba(255, 0, 0, 0.4); margin-bottom: 20px;
    }
    .value-badge {
        background-color: #4CAF50; color: white; padding: 5px 10px;
        border-radius: 5px; font-weight: bold; font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"

# --- ADVANCED ENGINE ---
def calculate_sharp_probs(target_xg, league_bias=1.0):
    # Apply league-specific scoring volatility
    adj_xg = target_xg * league_bias
    h_exp = adj_xg * 0.53  # Slight home bias
    a_exp = adj_xg * 0.47
    
    o15, o25, o35 = 0, 0, 0
    for i in range(12):
        for j in range(12):
            p = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            if i + j > 1.5: o15 += p
            if i + j > 2.5: o25 += p
            if i + j > 3.5: o35 += p
    return {"1.5": o15, "2.5": o25, "3.5": o35}

def get_kelly_stake(prob, odds, bankroll=1000):
    """Calculates optimal bet size using fractional Kelly (0.25)."""
    b = odds - 1
    q = 1 - prob
    fractional_kelly = 0.25 * ((b * prob - q) / b)
    return max(0, round(fractional_kelly * bankroll, 2))

# =======================
# 📡 ELITE LIVE FEED
# =======================
st.title("☢️ SHARP SOCCER AI: ELITE VALUE DETECTOR")
st.sidebar.header("Control Center")
league_filter = st.sidebar.multiselect("Focus Leagues", ["soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a"])
bankroll = st.sidebar.number_input("Your Bankroll ($)", 100, 100000, 1000)

@st.cache_data(ttl=300)
def fetch_data():
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds"
    params = {"apiKey": API_KEY, "regions": "uk", "markets": "totals", "oddsFormat": "decimal"}
    return requests.get(url, params=params).json()

matches = fetch_data()

if matches:
    for m in matches[:30]:
        try:
            # Market Odds Extraction
            outcomes = m['bookmakers'][0]['markets'][0]['outcomes']
            o25_price = next(o['price'] for o in outcomes if o['name'] == 'Over' and o['point'] == 2.5)
            market_prob = 1 / o25_price
            
            # AI Probability Logic
            implied_xg = 2.5 + (1.2 / math.log(o25_price + 0.1))
            sharp_metrics = calculate_sharp_probs(implied_xg)
            sharp_prob = sharp_metrics["2.5"]
            
            # --- VALUE CALCULATION ---
            # We look for a 5% difference between our math and the bookie
            edge = sharp_prob - market_prob
            
            if sharp_prob > 0.75:
                with st.container():
                    st.markdown(f"""
                    <div class="nuke-card">
                        <span class="value-badge">EDGE: {edge:+.1%}</span>
                        <h2 style='color:white;'>{m['home_team']} vs {m['away_team']}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if edge > 0.08:
                        st.error("🚨 HIGH VALUE NUKE DETECTED 🚨")
                        st.balloons()

                    cols = st.columns(4)
                    cols[0].metric("Market Odds", f"{o25_price}")
                    cols[1].metric("Sharp Conf.", f"{sharp_prob:.1%}")
                    cols[2].metric("Target xG", f"{implied_xg:.2f}")
                    
                    stake = get_kelly_stake(sharp_prob, o25_price, bankroll)
                    cols[3].metric("Suggested Bet", f"${stake}", delta="Kelly optimized")
                    st.divider()
        except:
            continue
else:
    st.info("Searching for fresh market signals...")
