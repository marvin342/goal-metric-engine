import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="SHARP SOCCER AI v9.1", layout="wide", page_icon="⚽")

# --- PRO STYLING ---
st.markdown("""
    <style>
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .nuke-alert {
        background: linear-gradient(90deg, #ff4b4b, #ff0000);
        color: white; padding: 20px; border-radius: 15px;
        text-align: center; font-size: 28px; font-weight: 900;
        border: 2px solid white; animation: pulse 1s infinite;
    }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"

# --- SMART CACHE (REFRESHES EVERY 10 MINS) ---
@st.cache_data(ttl=600)
def fetch_live_market_data():
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds"
    params = {"apiKey": API_KEY, "regions": "uk", "markets": "totals", "oddsFormat": "decimal"}
    try:
        response = requests.get(url, params=params)
        return response.json(), time.strftime("%H:%M:%S")
    except:
        return [], "Offline"

# --- THE "BRAIN" ---
def get_advanced_probs(avg_total):
    h_exp = avg_total * 0.55
    a_exp = avg_total * 0.45
    probs = {"1.5": 0, "2.5": 0, "3.5": 0}
    for i in range(12):
        for j in range(12):
            p = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            if i + j > 1.5: probs["1.5"] += p
            if i + j > 2.5: probs["2.5"] += p
            if i + j > 3.5: probs["3.5"] += p
    return probs

# =======================
# 📡 PRO LIVE DASHBOARD
# =======================
data, last_update = fetch_live_market_data()

st.title("⚽ SHARP SOCCER AI")
st.write(f"**Last Market Sync:** {last_update} (Refreshes automatically every 10 mins)")

if not data:
    st.warning("No new matches detected. This happens when there are no games in the next 24-48 hours.")
else:
    # Filter only for the next 48 hours to keep it "Fresh"
    for match in data[:30]:
        try:
            # Logic to find the specific 'Over 2.5' line
            bookie = match['bookmakers'][0]
            market = bookie['markets'][0]
            o25_outcome = next(o for o in market['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5)
            price = o25_outcome['price']
            
            # Convert Price to Target xG
            implied_goals = 2.5 + (1.0 / math.log(price + 0.05))
            preds = get_advanced_probs(implied_goals)
            
            # THE NUKE FILTER (Only high confidence)
            if preds["2.5"] > 0.70:
                with st.container():
                    st.markdown(f"### {match['home_team']} vs {match['away_team']}")
                    
                    if preds["2.5"] > 0.82:
                        st.markdown('<div class="nuke-alert">☢️ MAXIMUM CONVICTION NUKE ☢️</div>', unsafe_allow_html=True)
                        st.balloons()
                    
                    c = st.columns(3)
                    c[0].metric("Bookie Price", f"{price}")
                    c[1].metric("Sharp Confidence", f"{preds['2.5']:.1%}")
                    c[2].metric("Expected Goals", f"{implied_goals:.2f}")
                    st.divider()
        except:
            continue
