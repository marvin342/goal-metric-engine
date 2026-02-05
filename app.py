import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math
from streamlit_autorefresh import st_autorefresh

# --- 1. GLOBAL PAGE SETUP ---
st.set_page_config(page_title="SYNDICATE AI - GLOBAL SCANNER", layout="wide", page_icon="📈")

# --- 2. THE TIMER (10 MINUTES / 600,000ms) ---
st_autorefresh(interval=600000, key="data_refresh_timer")

# --- 3. UI STYLING ---
st.markdown("""
    <style>
    .nuke-card { background: #0b0e14; border: 2px solid #00ff41; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 0 15px rgba(0, 255, 65, 0.2); }
    .league-header { background: #1a1c24; color: #ffeb3b; padding: 10px; border-radius: 5px; font-weight: bold; margin-top: 20px; border-left: 5px solid #ffeb3b; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"

# --- 4. LEAGUE REGISTRY ---
LEAGUES = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "soccer_epl",
    "🇪🇸 La Liga": "soccer_spain_la_liga",
    "🇮🇹 Serie A": "soccer_italy_serie_a",
    "🇮🇹 Serie B": "soccer_italy_serie_b",
    "🇧🇷 Brazil Serie A": "soccer_brazil_campeonato",
    "🇧🇷 Brazil Serie B": "soccer_brazil_serie_b",
    "🇩🇪 Bundesliga": "soccer_germany_bundesliga"
}

# --- 5. THE ENGINE (DIXON-COLES MATH) ---
def get_pro_probs(target_xg):
    h_xg, a_xg = target_xg * 0.525, target_xg * 0.475
    probs = {"1.5": 0, "2.5": 0, "3.5": 0}
    for i in range(11):
        for j in range(11):
            p = poisson.pmf(i, h_xg) * poisson.pmf(j, a_xg)
            # Dixon-Coles "Low Score" Adjustment
            if (i == 0 and j == 0) or (i == 1 and j == 1): p *= 1.15
            if i + j > 1.5: probs["1.5"] += p
            if i + j > 2.5: probs["2.5"] += p
            if i + j > 3.5: probs["3.5"] += p
    return probs

# --- 6. MAIN DASHBOARD ---
st.title("⚽ GLOBAL SYNDICATE COMMAND")
st.write(f"⏱️ **Last Refreshed:** {pd.Timestamp.now().strftime('%H:%M:%S')} | Next auto-scan in 10 mins.")

# Sidebar Controls
nuke_val = st.sidebar.slider("Nuke Sensitivity (Min Edge)", 0.05, 0.20, 0.08)
bankroll = st.sidebar.number_input("Bankroll ($)", 100, 50000, 1000)

found_any = False

for label, league_id in LEAGUES.items():
    st.markdown(f'<div class="league-header">{label}</div>', unsafe_allow_html=True)
    
    url = f"https://api.the-odds-api.com/v4/sports/{league_id}/odds"
    params = {"apiKey": API_KEY, "regions": "uk,eu", "markets": "totals", "oddsFormat": "decimal"}
    
    try:
        response = requests.get(url, params=params)
        matches = response.json() if response.status_code == 200 else []
        
        if not matches:
            st.write("No upcoming matches found.")
            continue

        for m in matches:
            try:
                # Extract Over 2.5 Price
                bookie = m['bookmakers'][0]
                market = bookie['markets'][0]
                o25 = next(o for o in market['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5)
                price = o25['price']
                
                # Math Engine
                target_xg = 2.48 + (1.25 / math.log(price + 0.08))
                preds = get_pro_probs(target_xg)
                edge = preds["2.5"] - (1 / price)

                if edge >= nuke_val:
                    found_any = True
                    with st.container():
                        st.markdown(f'<div class="nuke-card">✅ <b>NUKE ALERT:</b> {m["home_team"]} v {m["away_team"]}</div>', unsafe_allow_html=True)
                        c = st.columns(4)
                        c[0].metric("Odds", f"{price}")
                        c[1].metric("Edge", f"{edge:+.1%}")
                        c[2].metric("Sharp Prob", f"{preds['2.5']:.1%}")
                        
                        # Kelly Stake Calculation
                        b = price - 1
                        kelly = ((b * preds["2.5"]) - (1 - preds["2.5"])) / b
                        stake = max(0, round(kelly * 0.25 * bankroll, 2))
                        c[3].metric("Stake Guide", f"${stake}")
            except: continue
    except:
        st.error(f"Error fetching {label}")

if not found_any:
    st.info("Market scan complete. No high-value opportunities detected at current sensitivity.")
