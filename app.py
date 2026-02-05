import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math
from streamlit_autorefresh import st_autorefresh # pip install streamlit-autorefresh

# --- PAGE SETUP ---
st.set_page_config(page_title="SYNDICATE AI - GLOBAL AUTO-SCAN", layout="wide", page_icon="☢️")

# --- UI STYLING ---
st.markdown("""
    <style>
    .nuke-card { background: #0b0e14; border: 2px solid #00ff41; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
    .league-header { color: #ffeb3b; font-size: 1.5rem; font-weight: bold; border-bottom: 2px solid #ffeb3b; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 🕒 AUTO-REFRESH: 600,000ms = 10 Minutes
count = st_autorefresh(interval=600000, key="fizzbuzzcounter")

API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"

# --- LEAGUE REGISTRY ---
LEAGUES = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "soccer_epl",
    "🇪🇸 La Liga": "soccer_spain_la_liga",
    "🇮🇹 Serie A": "soccer_italy_serie_a",
    "🇮🇹 Serie B": "soccer_italy_serie_b",
    "🇧🇷 Brazil Serie A": "soccer_brazil_campeonato",
    "🇧🇷 Brazil Serie B": "soccer_brazil_serie_b",
    "🇩🇪 Bundesliga": "soccer_germany_bundesliga"
}

# --- THE ENGINE ---
def get_pro_probs(target_xg):
    h_xg, a_xg = target_xg * 0.525, target_xg * 0.475
    probs = {"1.5": 0, "2.5": 0, "3.5": 0}
    for i in range(11):
        for j in range(11):
            p = poisson.pmf(i, h_xg) * poisson.pmf(j, a_xg)
            if (i == 0 and j == 0) or (i == 1 and j == 1): p *= 1.15 # Dixon-Coles
            if i + j > 1.5: probs["1.5"] += p
            if i + j > 2.5: probs["2.5"] += p
            if i + j > 3.5: probs["3.5"] += p
    return probs

# =======================
# 📡 DASHBOARD
# =======================
st.title("☢️ SYNDICATE AI: GLOBAL VALUE SCANNER")
st.write(f"⏱️ **Last Refreshed:** {pd.Timestamp.now().strftime('%H:%M:%S')} (Auto-update every 10 mins)")

# Scan all targeted leagues
for league_name, league_id in LEAGUES.items():
    st.markdown(f'<div class="league-header">{league_name}</div>', unsafe_allow_html=True)
    
    url = f"https://api.the-odds-api.com/v4/sports/{league_id}/odds"
    params = {"apiKey": API_KEY, "regions": "uk,eu", "markets": "totals", "oddsFormat": "decimal"}
    
    try:
        data = requests.get(url, params=params).json()
        if not data:
            st.info("No upcoming matches found for this league.")
            continue

        for m in data[:10]: # Check next 10 matches per league
            try:
                bookie = m['bookmakers'][0]
                o25 = next(o for o in bookie['markets'][0]['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5)
                price = o25['price']
                
                # Math Engine
                target_xg = 2.48 + (1.25 / math.log(price + 0.08))
                preds = get_pro_probs(target_xg)
                edge = preds["2.5"] - (1 / price)

                if edge > 0.08: # Only show high value
                    with st.container():
                        st.markdown(f'<div class="nuke-card">✅ <b>NUKE:</b> {m["home_team"]} vs {m["away_team"]} | Edge: {edge:+.1%}</div>', unsafe_allow_html=True)
                        c = st.columns(3)
                        c[0].metric("Market Odds", f"{price}")
                        c[1].metric("Sharp Prob", f"{preds['2.5']:.1%}")
                        c[2].metric("Target xG", f"{target_xg:.2f}")
            except: continue
    except:
        st.error(f"Failed to connect to {league_name} data.")import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math
from streamlit_autorefresh import st_autorefresh # pip install streamlit-autorefresh

# --- PAGE SETUP ---
st.set_page_config(page_title="SYNDICATE AI - GLOBAL AUTO-SCAN", layout="wide", page_icon="☢️")

# --- UI STYLING ---
st.markdown("""
    <style>
    .nuke-card { background: #0b0e14; border: 2px solid #00ff41; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
    .league-header { color: #ffeb3b; font-size: 1.5rem; font-weight: bold; border-bottom: 2px solid #ffeb3b; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 🕒 AUTO-REFRESH: 600,000ms = 10 Minutes
count = st_autorefresh(interval=600000, key="fizzbuzzcounter")

API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"

# --- LEAGUE REGISTRY ---
LEAGUES = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "soccer_epl",
    "🇪🇸 La Liga": "soccer_spain_la_liga",
    "🇮🇹 Serie A": "soccer_italy_serie_a",
    "🇮🇹 Serie B": "soccer_italy_serie_b",
    "🇧🇷 Brazil Serie A": "soccer_brazil_campeonato",
    "🇧🇷 Brazil Serie B": "soccer_brazil_serie_b",
    "🇩🇪 Bundesliga": "soccer_germany_bundesliga"
}

# --- THE ENGINE ---
def get_pro_probs(target_xg):
    h_xg, a_xg = target_xg * 0.525, target_xg * 0.475
    probs = {"1.5": 0, "2.5": 0, "3.5": 0}
    for i in range(11):
        for j in range(11):
            p = poisson.pmf(i, h_xg) * poisson.pmf(j, a_xg)
            if (i == 0 and j == 0) or (i == 1 and j == 1): p *= 1.15 # Dixon-Coles
            if i + j > 1.5: probs["1.5"] += p
            if i + j > 2.5: probs["2.5"] += p
            if i + j > 3.5: probs["3.5"] += p
    return probs

# =======================
# 📡 DASHBOARD
# =======================
st.title("☢️ SYNDICATE AI: GLOBAL VALUE SCANNER")
st.write(f"⏱️ **Last Refreshed:** {pd.Timestamp.now().strftime('%H:%M:%S')} (Auto-update every 10 mins)")

# Scan all targeted leagues
for league_name, league_id in LEAGUES.items():
    st.markdown(f'<div class="league-header">{league_name}</div>', unsafe_allow_html=True)
    
    url = f"https://api.the-odds-api.com/v4/sports/{league_id}/odds"
    params = {"apiKey": API_KEY, "regions": "uk,eu", "markets": "totals", "oddsFormat": "decimal"}
    
    try:
        data = requests.get(url, params=params).json()
        if not data:
            st.info("No upcoming matches found for this league.")
            continue

        for m in data[:10]: # Check next 10 matches per league
            try:
                bookie = m['bookmakers'][0]
                o25 = next(o for o in bookie['markets'][0]['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5)
                price = o25['price']
                
                # Math Engine
                target_xg = 2.48 + (1.25 / math.log(price + 0.08))
                preds = get_pro_probs(target_xg)
                edge = preds["2.5"] - (1 / price)

                if edge > 0.08: # Only show high value
                    with st.container():
                        st.markdown(f'<div class="nuke-card">✅ <b>NUKE:</b> {m["home_team"]} vs {m["away_team"]} | Edge: {edge:+.1%}</div>', unsafe_allow_html=True)
                        c = st.columns(3)
                        c[0].metric("Market Odds", f"{price}")
                        c[1].metric("Sharp Prob", f"{preds['2.5']:.1%}")
                        c[2].metric("Target xG", f"{target_xg:.2f}")
            except: continue
    except:
        st.error(f"Failed to connect to {league_name} data.")
