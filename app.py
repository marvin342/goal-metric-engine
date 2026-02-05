import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math
from streamlit_autorefresh import st_autorefresh

# --- 1. SETUP ---
st.set_page_config(page_title="PRO SYNDICATE v16", layout="wide", page_icon="🎯")
st_autorefresh(interval=600000, key="auto_refresh") # 10-minute refresh

# --- 2. THE ENGINE: BIVARIATE VALUE LOGIC ---
def calculate_sharp_edge(price, target_xg):
    # Professional Split: Home 53% / Away 47%
    h_xg, a_xg = target_xg * 0.53, target_xg * 0.47
    over_25_prob = 0
    
    # 10x10 Matrix Simulation
    for i in range(10):
        for j in range(10):
            p = poisson.pmf(i, h_xg) * poisson.pmf(j, a_xg)
            # Dixon-Coles Adjustment for low scores (Prevents 'Ass' Predictions)
            if (i + j) <= 2: p *= 1.12 
            if i + j > 2.5: over_25_prob += p
            
    market_prob = 1 / price
    return over_25_prob, (over_25_prob - market_prob)

# --- 3. DATA FETCHING ---
API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"
LEAGUES = {
    "ENG Premier": "soccer_epl", "ESP LaLiga": "soccer_spain_la_liga",
    "ITA Serie A": "soccer_italy_serie_a", "ITA Serie B": "soccer_italy_serie_b",
    "GER Bundesliga": "soccer_germany_bundesliga", "BRA Serie A": "soccer_brazil_campeonato",
    "BRA Serie B": "soccer_brazil_serie_b"
}

# --- 4. UI LAYOUT ---
st.title("🎯 PRO SYNDICATE v16: VALUE SCANNER")
st.sidebar.header("Settings")
min_edge = st.sidebar.slider("Minimum Edge %", 0.05, 0.20, 0.10)
bankroll = st.sidebar.number_input("Bankroll ($)", 100, 10000, 1000)

st.write(f"Last Scan: **{pd.Timestamp.now().strftime('%H:%M')}**")

for name, key in LEAGUES.items():
    with st.expander(f"📡 Scanning {name}...", expanded=True):
        url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/?apiKey={API_KEY}&regions=uk&markets=totals"
        try:
            matches = requests.get(url).json()
            if not matches: st.write("No Value Found.")
            
            for m in matches:
                # Get Over 2.5 Market
                outcomes = m['bookmakers'][0]['markets'][0]['outcomes']
                o25 = next(o for o in outcomes if o['name'] == 'Over' and o['point'] == 2.5)
                price = o25['price']
                
                # Math: Inverting the Bookmaker's Brain
                # We assume the bookie knows the xG but adds "Juice"
                implied_xg = 2.45 + (1.3 / math.log(price + 0.08))
                prob, edge = calculate_sharp_edge(price, implied_xg)
                
                if edge >= min_edge:
                    st.markdown(f"### ✅ {m['home_team']} vs {m['away_team']}")
                    c = st.columns(4)
                    c[0].metric("Odds", f"{price}")
                    c[1].metric("Value Edge", f"{edge:+.1%}")
                    c[2].metric("AI Confidence", f"{prob:.1%}")
                    
                    # Kelly Stake (1/4 Kelly for safety)
                    stake = max(0, round((((price-1)*prob)-(1-prob))/(price-1) * 0.25 * bankroll, 2))
                    c[3].metric("Stake Recommendation", f"${stake}")
                    st.divider()
        except: continue
