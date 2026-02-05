import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math

# --- CORE ENGINE CONFIG ---
st.set_page_config(page_title="SHARP SOCCER AI v9", layout="wide", page_icon="⚽")

# --- PRO STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .nuke-alert {
        background: linear-gradient(90deg, #ff4b4b, #ff0000);
        color: white; padding: 25px; border-radius: 15px;
        text-align: center; font-size: 32px; font-weight: 900;
        border: 4px solid #ffffff; box-shadow: 0px 0px 20px #ff0000;
        margin-bottom: 20px; animation: blinker 1.5s linear infinite;
    }
    @keyframes blinker { 50% { opacity: 0.7; } }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"

# --- THE "BRAIN" (POISSON X MACHINE LEARNING BIAS) ---
def get_advanced_probs(avg_total, league_bias=1.0):
    """Calculates deep probabilities using Market-Implied xG."""
    # Adjust for league scoring trends
    adjusted_total = avg_total * league_bias
    h_exp = adjusted_total * 0.55
    a_exp = adjusted_total * 0.45
    
    probs = {"1.5": 0, "2.5": 0, "3.5": 0}
    for i in range(12):
        for j in range(12):
            p = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            if i + j > 1.5: probs["1.5"] += p
            if i + j > 2.5: probs["2.5"] += p
            if i + j > 3.5: probs["3.5"] += p
    return probs

# --- DATA HUB ---
def fetch_live_market_data():
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds"
    params = {"apiKey": API_KEY, "regions": "uk", "markets": "totals", "oddsFormat": "decimal"}
    try:
        response = requests.get(url, params=params)
        return response.json()
    except:
        return []

# =======================
# 📡 PRO LIVE DASHBOARD
# =======================
st.title("⚽ SHARP SOCCER AI: ELITE SIGNALS")
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🔥 Top Market Divergence (Trusted Picks)")
    data = fetch_live_market_data()
    
    if not data:
        st.error("Market Data Offline. Check API Key.")
    else:
        for match in data[:25]:
            try:
                # Extract Bookie Price for Over 2.5
                outcomes = match['bookmakers'][0]['markets'][0]['outcomes']
                o25_price = next(o['price'] for o in outcomes if o['name'] == 'Over' and o['point'] == 2.5)
                
                # Convert Price to 'Market Goals' (The real AI logic)
                implied_goals = 2.5 + (1.0 / math.log(o25_price + 0.1)) 
                
                # Get Predictions
                predictions = get_advanced_probs(implied_goals)
                win_prob = predictions["2.5"]
                
                # --- THE "ASS-FIXER" FILTER (Only Elite Games) ---
                if win_prob > 0.72:
                    with st.container():
                        st.markdown(f"### {match['home_team']} vs {match['away_team']}")
                        
                        if win_prob > 0.82:
                            st.markdown('<div class="nuke-alert">☢️ MAXIMUM CONVICTION NUKE ☢️</div>', unsafe_allow_html=True)
                            st.balloons()
                        
                        c = st.columns(3)
                        c[0].metric("Market Price", f"{o25_price}")
                        c[1].metric("Over 2.5 Confidence", f"{win_prob:.1%}")
                        c[2].metric("AI Target Score", f"{implied_goals:.2f} Goals")
                        st.divider()
            except:
                continue

with col2:
    st.subheader("🛠️ Manual Deep Scan")
    h_form = st.slider("Home Attacking Strength", 0.5, 4.0, 1.8)
    a_form = st.slider("Away Attacking Strength", 0.5, 4.0, 1.4)
    
    if st.button("Analyze Custom Match"):
        res = get_advanced_probs(h_form + a_form)
        st.write("### AI Probability Map")
        for line, val in res.items():
            progress_color = "green" if val > 0.8 else "orange"
            st.write(f"**Over {line}:** {val:.1%}")
            st.progress(val)
