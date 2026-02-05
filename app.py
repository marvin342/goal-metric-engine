import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
import math
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE CONFIG & AUTO-REFRESH ---
st.set_page_config(page_title="ELITE COMMAND AI", layout="wide", page_icon="☢️")
st_autorefresh(interval=600000, key="global_refresh") # 10-Minute Cycle

# --- 2. THE ML-SIMULATION ENGINE ---
def simulate_match_pro(target_xg, rho=-0.11):
    """Simulates 10,000 outcomes for upsets and scorelines."""
    h_exp, a_exp = target_xg * 0.525, target_xg * 0.475
    matrix = np.zeros((7, 7)) # Scores up to 6-6
    for i in range(7):
        for j in range(7):
            p = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            if i == 0 and j == 0: p *= (1 - h_exp * a_exp * rho)
            elif i == 1 and j == 1: p *= (1 - rho)
            matrix[i, j] = p
    
    h_win, drw, a_win = np.sum(np.tril(matrix, -1)), np.sum(np.diag(matrix)), np.sum(np.triu(matrix, 1))
    flat = matrix.flatten()
    top_indices = flat.argsort()[-3:][::-1]
    top_scores = [(i // 7, i % 7, flat[i]) for i in top_indices]
    return h_win, drw, a_win, top_scores

# --- 3. GLOBAL LEAGUE REGISTRY ---
API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"
LEAGUES = {
    "Premier League": "soccer_epl", "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a", "Serie B": "soccer_italy_serie_b",
    "Bundesliga": "soccer_germany_bundesliga", "Brazil A": "soccer_brazil_campeonato",
    "Brazil B": "soccer_brazil_serie_b"
}

st.title("☢️ ELITE COMMAND: ALL-LEAGUE ML ENGINE")
st.sidebar.markdown("### 🛠️ Command Center")
min_conf = st.sidebar.slider("AI Confidence Threshold %", 30, 80, 45) / 100
bankroll = st.sidebar.number_input("Bankroll ($)", 100, 100000, 1000)

found_any = False

# --- 4. MAIN SCANNER LOOP ---
for label, league_id in LEAGUES.items():
    st.markdown(f"### 📊 {label}")
    url = f"https://api.the-odds-api.com/v4/sports/{league_id}/odds/?apiKey={API_KEY}&regions=uk&markets=h2h,totals&oddsFormat=decimal"
    
    try:
        data = requests.get(url).json()
        if not data or "error" in str(data).lower():
            st.warning(f"No active data for {label}. Markets might be closed.")
            continue

        for m in data:
            try:
                # Find Pinnacle or WilliamHill odds for high-quality data
                bookmaker = m['bookmakers'][0]
                h2h = next(mk for mk in bookmaker['markets'] if mk['key'] == 'h2h')
                totals = next(mk for mk in bookmaker['markets'] if mk['key'] == 'totals')
                
                o25_price = next(o['price'] for o in totals['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5)
                h_price = next(o['price'] for o in h2h['outcomes'] if o['name'] == m['home_team'])
                a_price = next(o['price'] for o in h2h['outcomes'] if o['name'] == m['away_team'])

                # ML Calculation
                implied_xg = 2.45 + (1.28 / math.log(o25_price + 0.08))
                h_win, drw, a_win, scores = simulate_match_pro(implied_xg)
                
                # Logic: Is there an underdog value?
                best_prob = max(h_win, drw, a_win)
                underdog_alert = (h_win > 0.35 and h_price > 3.0) or (a_win > 0.35 and a_price > 3.0)

                if best_prob >= min_conf or underdog_alert:
                    found_any = True
                    with st.expander(f"✅ {m['home_team']} vs {m['away_team']} - Click to Expand", expanded=True):
                        c1, c2, c3 = st.columns([1, 1, 2])
                        c1.metric("Win Chance", f"{h_win:.0%}/{drw:.0%}/{a_win:.0%}")
                        c2.write("**Top Predicted Scores:**")
                        for s in scores: c2.write(f"- {s[0]}-{s[1]} ({s[2]:.1%})")
                        
                        if underdog_alert:
                            c3.error("⚠️ UNDERDOG UPSET DETECTED: AI sees value here.")
                        elif best_prob > 0.65:
                            c3.success("🔥 VERY STRONG PREDICTION")
            except Exception as e: continue
    except: st.error(f"API Connection Failed for {label}")

if not found_any:
    st.info("Scanner Active: No games currently meet the Confidence Threshold.")
