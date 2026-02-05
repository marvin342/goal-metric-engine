import streamlit as st
import pandas as pd
from scipy.stats import poisson

st.set_page_config(page_title="Sharp Goal Engine", layout="wide")

# --- LEAGUE AVERAGES (2025/26 Season Data) ---
# These 'sharpen' the prediction by providing the baseline for the specific league
LEAGUE_STATS = {
    "Premier League": {"h_avg": 1.58, "a_avg": 1.26},
    "Brazil Serie A": {"h_avg": 1.35, "a_avg": 1.10},
    "La Liga": {"h_avg": 1.45, "a_avg": 1.15}
}

def calculate_market_probs(h_exp, a_exp):
    """Calculates all goal markets using a 10x10 score matrix."""
    matrix = {}
    over_1_5, over_2_5, over_3_5, over_4_5 = 0, 0, 0, 0
    
    for i in range(10): # Home goals
        for j in range(10): # Away goals
            prob = poisson.pmf(i, h_exp) * poisson.pmf(j, a_exp)
            total_goals = i + j
            
            if total_goals > 1.5: over_1_5 += prob
            if total_goals > 2.5: over_2_5 += prob
            if total_goals > 3.5: over_3_5 += prob
            if total_goals > 4.5: over_4_5 += prob
            
    return {
        "O1.5": over_1_5,
        "O2.5": over_2_5,
        "O3.5": over_3_5,
        "O4.5": over_4_5
    }

st.title("🎯 Sharp Goal Metric Engine")

# --- SIDEBAR: LEAGUE STATS ---
st.sidebar.header("Sharp Settings")
selected_lg = st.sidebar.selectbox("Select League", list(LEAGUE_STATS.keys()))
lg_h_avg = LEAGUE_STATS[selected_lg]["h_avg"]
lg_a_avg = LEAGUE_STATS[selected_lg]["a_avg"]

# --- MAIN: MANUAL INPUT ---
st.subheader(f"Custom Match Analysis: {selected_lg}")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🏠 Home Team")
    h_att = st.slider("Attack Strength (vs League Avg)", 0.5, 2.5, 1.2, help="1.0 is average. 1.5 means they score 50% more than average.")
    h_def = st.slider("Defense Strength (Goals Allowed)", 0.5, 2.5, 0.9, help="Lower is better defense.")

with col2:
    st.markdown("### ✈️ Away Team")
    a_att = st.slider("Away Attack Strength", 0.5, 2.5, 1.0)
    a_def = st.slider("Away Defense Strength", 0.5, 2.5, 1.3)

# --- THE SHARP CALCULATION ---
# Formula: Home xG = (Home Att * Away Def) * League Home Avg
h_final_xg = (h_att * a_def) * lg_h_avg
a_final_xg = (a_att * h_def) * lg_a_avg

if st.button("Calculate Sharp Probabilities"):
    probs = calculate_market_probs(h_final_xg, a_final_xg)
    
    st.divider()
    st.write(f"### Predicted Scoreline: {h_final_xg:.2f} - {a_final_xg:.2f}")
    
    # --- GOAL MARKET DISPLAY ---
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        st.metric("Over 1.5", f"{probs['O1.5']:.1%}")
        if probs['O1.5'] > 0.85: st.success("SHARP PICK")
        
    with m2:
        st.metric("Over 2.5", f"{probs['O2.5']:.1%}")
        if probs['O2.5'] > 0.70: st.success("SHARP PICK")
        
    with m3:
        st.metric("Over 3.5", f"{probs['O3.5']:.1%}")
        if probs['O3.5'] > 0.50: st.warning("VALUE FOUND")
        
    with m4:
        st.metric("Over 4.5", f"{probs['O4.5']:.1%}")
        if probs['O4.5'] > 0.25: 
            st.error("🔥 CRAZY GAME")
            st.toast("High probability of a blowout!")

    # --- ADVANCED INSIGHT ---
    st.info(f"**Insight:** Based on {selected_lg} averages, this match is expected to produce **{h_final_xg + a_final_xg:.2f}** total goals.")
