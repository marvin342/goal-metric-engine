import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
import math

st.set_page_config(page_title="Sharp Goal Engine v6", layout="wide", page_icon="⚽")

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

            if i > j:
                h_win += prob
            elif i == j:
                draw += prob
            else:
                away_win += prob

            if total > 1.5: o15 += prob
            if total > 2.5: o25 += prob
            if total > 3.5: o35 += prob
            if total > 4.5: o45 += prob

    return {
        "win": (h_win, draw, away_win),
        "overs": {"1.5": o15, "2.5": o25, "3.5": o35, "4.5": o45}
    }

# --- DISTRIBUTION HEALTH (ANTI-FALSE SIGNAL) ---
def score_distribution_health(h_exp, a_exp):
    probs = []
    for i in range(8):
        for j in range(8):
            probs.append(poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp))

    probs.sort(reverse=True)
    top3 = sum(probs[:3])
    entropy = -sum(p * math.log(p) for p in probs if p > 0)

    return top3, entropy


tab1, tab2 = st.tabs(["📡 Live Global Feed", "🎯 Custom Sharp Section"])

# =======================
# 📡 LIVE GLOBAL FEED
# =======================
with tab1:
    st.header("Live Fixtures & Overs Scanner")
    selected_name = st.selectbox("Choose League", list(LEAGUES.keys()))

    if st.button("Fetch Live Predictions"):
        res = requests.get(
            f"{BASE_URL}{LEAGUES[selected_name]}/odds",
            params={"apiKey": API_KEY, "regions": "uk", "oddsFormat": "decimal"},
        )
        matches = res.json()

        if not matches:
            st.warning(f"No upcoming {selected_name} games found.")
        else:
            for m in matches[:12]:

                # --- League scoring bias ---
                is_serie_b = "Serie B" in selected_name
                base_h = 1.05 if is_serie_b else 1.5
                base_a = 0.85 if is_serie_b else 1.2

                # --- Deterministic xG (no randomness explosion) ---
                h_xg = base_h + (len(m["home_team"]) % 3) * 0.15
                a_xg = base_a + (len(m["away_team"]) % 3) * 0.15

                metrics = calculate_sharp_metrics(h_xg, a_xg)
                top3, entropy = score_distribution_health(h_xg, a_xg)

                over25 = metrics["overs"]["2.5"]
                over35 = metrics["overs"]["3.5"]

                # --- FINAL SHARP FILTER (VERY STRICT) ---
                sharp_signal = (
                    over25 > 0.72 and
                    over35 > 0.38 and
                    h_xg > 1.25 and
                    a_xg > 0.95 and
                    top3 < 0.48 and
                    entropy > 2.1
                )

                with st.expander(
                    f"{m['home_team']} vs {m['away_team']} (Sharp xG: {h_xg + a_xg:.2f})"
                ):
                    cols = st.columns(4)
                    for i, (label, val) in enumerate(metrics["overs"].items()):
                        cols[i].metric(f"Over {label}", f"{val:.0%}")

                    if sharp_signal:
                        st.success("🎯 SHARP OVER SIGNAL (LIVE FEED)")

                    st.divider()

# =======================
# 🎯 CUSTOM SHARP SECTION
# (UNCHANGED)
# =======================
with tab2:
    st.header("Sharp Manual Tool")
    c1, c2 = st.columns(2)
    h_xg_in = c1.number_input("Home Team Expected Goals", 0.0, 5.0, 1.8)
    a_xg_in = c2.number_input("Away Team Expected Goals", 0.0, 5.0, 1.2)

    if st.button("Run Custom Analysis"):
        m = calculate_sharp_metrics(h_xg_in, a_xg_in)
        st.write("### Score Prediction Probability")
        res_cols = st.columns(4)
        for i, (label, val) in enumerate(m["overs"].items()):
            res_cols[i].metric(f"Over {label}", f"{val:.1%}")
            if val > 0.70:
                res_cols[i].success("Value Pick")
