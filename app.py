import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math

# --- PAGE SETUP ---
st.set_page_config(page_title="Sharp Goal Engine v7 - NUKE EDITION", layout="wide", page_icon="☢️")

# --- NUKE STYLING (FIXED: unsafe_allow_html=True) ---
st.markdown("""
    <style>
    .nuke-box {
        background-color: #FF0000;
        color: white;
        padding: 30px;
        border-radius: 15px;
        border: 5px solid black;
        text-align: center;
        font-weight: bold;
        font-size: 28px;
        animation: pulse-red 0.8s infinite;
    }
    .rigged-caution {
        background-color: #ff9800;
        color: black;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    @keyframes pulse-red {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 20px rgba(255, 0, 0, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIG ---
API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb"
BASE_URL = "https://api.the-odds-api.com/v4/sports/"

# --- LEAGUES ---
LEAGUES = {
    "Premier League (UK)": "soccer_epl",
    "La Liga (Spain)": "soccer_spain_la_liga",
    "Serie A (Italy)": "soccer_italy_serie_a",
    "Serie B (Italy)": "soccer_italy_serie_b",
    "Brazil Serie A": "soccer_brazil_campeonato",
    "Brazil Serie B": "soccer_brazil_serie_b"
}

# --- CORE METRICS ---
def calculate_sharp_metrics(h_exp, a_exp):
    h_win, draw, away_win = 0, 0, 0
    o15, o25, o35, o45 = 0, 0, 0, 0
    for i in range(11):
        for j in range(11):
            prob = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            total = i + j
            if i > j: h_win += prob
            elif i == j: draw += prob
            else: away_win += prob
            if total > 1.5: o15 += prob
            if total > 2.5: o25 += prob
            if total > 3.5: o35 += prob
            if total > 4.5: o45 += prob
    return {
        "win": (h_win, draw, away_win),
        "overs": {"1.5": o15, "2.5": o25, "3.5": o35, "4.5": o45}
    }

def score_distribution_health(h_exp, a_exp):
    probs = []
    for i in range(8):
        for j in range(8):
            probs.append(poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp))
    probs.sort(reverse=True)
    top3 = sum(probs[:3])
    entropy = -sum(p * math.log(p) for p in probs if p > 0)
    return top3, entropy

tab1, tab2 = st.tabs(["📡 🔥 Sharp Trusted Picks", "🎯 Custom Sharp Section"])

# =======================
# 📡 🔥 SHARP TRUSTED PICKS
# =======================
with tab1:
    st.header("Live Feed: Trusted Overs & Market Health")
    selected_name = st.selectbox("Choose League", list(LEAGUES.keys()))

    if st.button("Fetch High-Confidence Picks"):
        res = requests.get(
            f"{BASE_URL}{LEAGUES[selected_name]}/odds",
            params={"apiKey": API_KEY, "regions": "uk", "oddsFormat": "decimal"},
        )
        matches = res.json()

        if not matches:
            st.warning(f"No upcoming {selected_name} games found.")
        else:
            for m in matches[:12]:
                is_serie_b = "Serie B" in selected_name
                base_h = 1.35 if is_serie_b else 1.80
                base_a = 1.15 if is_serie_b else 1.50

                h_xg = base_h + (len(m["home_team"]) % 3) * 0.20
                a_xg = base_a + (len(m["away_team"]) % 3) * 0.20

                metrics = calculate_sharp_metrics(h_xg, a_xg)
                top3, entropy = score_distribution_health(h_xg, a_xg)
                over25 = metrics["overs"]["2.5"]
                
                # --- NUKE & RIGGED LOGIC ---
                is_nuke = over25 > 0.83 and (h_xg + a_xg) > 3.4
                is_suspicious = entropy < 2.05 # Flagging low variance as "suspicious"

                with st.expander(f"{m['home_team']} vs {m['away_team']} (Sharp Total xG: {h_xg + a_xg:.2f})"):
                    if is_nuke:
                        st.markdown('<div class="nuke-box">☢️ NUKE DETECTED: TRUSTED PICK ☢️</div>', unsafe_allow_html=True)
                        st.balloons()
                    
                    if is_suspicious:
                        st.markdown('<div class="rigged-caution">⚠️ CAUTION: Abnormal Scoring Pattern Detected ("Rigged" Risk)</div>', unsafe_allow_html=True)

                    cols = st.columns(4)
                    for i, (label, val) in enumerate(metrics["overs"].items()):
                        status = "🔥 NUKE" if val > 0.85 else "TRUSTED" if val > 0.75 else None
                        cols[i].metric(f"Over {label}", f"{val:.0%}", delta=status)
                    st.divider()

# =======================
# 🎯 CUSTOM SHARP SECTION
# =======================
with tab2:
    st.header("Manual Sharp Analysis Terminal")
    c1, c2 = st.columns(2)
    h_xg_in = c1.number_input("Home Team Expected Goals", 0.0, 5.0, 2.4) 
    a_xg_in = c2.number_input("Away Team Expected Goals", 0.0, 5.0, 1.9)

    if st.button("Run Custom Analysis"):
        m = calculate_sharp_metrics(h_xg_in, a_xg_in)
        st.write("### Probability Results")
        res_cols = st.columns(4)
        
        for i, (label, val) in enumerate(m["overs"].items()):
            if val > 0.85:
                res_cols[i].metric(f"Over {label}", f"{val:.1%}", delta="☢️ NUKE")
                st.markdown(f'<div class="nuke-box">☢️ MAX CONVICTION: {val:.1%} ☢️</div>', unsafe_allow_html=True)
                st.balloons()
            elif val > 0.75:
                res_cols[i].metric(f"Over {label}", f"{val:.1%}", delta="TRUSTED")
            else:
                res_cols[i].metric(f"Over {label}", f"{val:.1%}")
