import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
import math
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="ELITE COMMAND AI v18", layout="wide", page_icon="☢️")
st_autorefresh(interval=600000, key="refresh")

# --- IMPROVED LEAGUE LIST (More coverage = fewer empty screens) ---
LEAGUES = {
    "Premier League": "soccer_epl", 
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a", 
    "Serie B": "soccer_italy_serie_b",
    "Bundesliga": "soccer_germany_bundesliga", 
    "Brazil A": "soccer_brazil_campeonato",
    "Mexico Liga MX": "soccer_mexico_ligamx", # Added for midweek action
    "Argentina Superliga": "soccer_argentina_primera_division" # Added for variety
}

API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"

def simulate_match_pro(target_xg):
    h_exp, a_exp = target_xg * 0.525, target_xg * 0.475
    matrix = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            p = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            if i == 0 and j == 0: p *= 1.15
            matrix[i, j] = p
    h_win, drw, a_win = np.sum(np.tril(matrix, -1)), np.sum(np.diag(matrix)), np.sum(np.triu(matrix, 1))
    return h_win, drw, a_win

st.title("☢️ ELITE COMMAND: MATCH PREDICTOR")
st.sidebar.info(f"API Key Active. Last ping: {pd.Timestamp.now().strftime('%H:%M:%S')}")

# LOWER THE THRESHOLD TO SEE IF IT WORKS
min_conf = st.sidebar.slider("Confidence Threshold %", 20, 80, 30) / 100 

found_any = False

for label, league_id in LEAGUES.items():
    url = f"https://api.the-odds-api.com/v4/sports/{league_id}/odds/?apiKey={API_KEY}&regions=uk&markets=h2h,totals"
    
    try:
        res = requests.get(url).json()
        
        # DEBUG: Let's see if the API is actually sending data
        if not res:
            st.sidebar.warning(f"{label}: API returned 0 games.")
            continue
            
        for m in res:
            try:
                bookmaker = m['bookmakers'][0]
                totals = next(mk for mk in bookmaker['markets'] if mk['key'] == 'totals')
                o25_price = next(o['price'] for o in totals['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5)
                
                # ML Engine
                target_xg = 2.45 + (1.28 / math.log(o25_price + 0.08))
                h_win, drw, a_win = simulate_match_pro(target_xg)
                
                if max(h_win, drw, a_win) >= min_conf:
                    found_any = True
                    with st.expander(f"✅ {m['home_team']} vs {m['away_team']}"):
                        st.write(f"**League:** {label}")
                        st.write(f"**AI Prediction:** Home {h_win:.0%} | Draw {drw:.0%} | Away {a_win:.0%}")
            except: continue
    except: 
        st.error(f"Failed to connect to {label}")

if not found_any:
    st.info("No games currently meet your settings. Try lowering the Confidence Slider or check back on Friday/Saturday.")
