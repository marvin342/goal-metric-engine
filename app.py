import streamlit as st
import pandas as pd
import soccerdata as sd
from scipy.stats import poisson

st.set_page_config(page_title="Goal Metric Engine (Unlimited Free)", layout="wide")

st.title("⚽ Goal Metric Engine (Scraper Edition)")
st.info("No API Key needed! This pulls directly from FBref live data.")

# League Selection (Supported by the scraper)
leagues = {
    "Premier League (UK)": "ENG-Premier League",
    "La Liga (Spain)": "ESP-La Liga",
    "Brazil Serie A": "BRA-Serie A"
}
selected_league = st.sidebar.selectbox("Select League", list(leagues.keys()))

@st.cache_data(ttl=3600) # Re-scrapes once per hour
def get_live_data(league_name):
    try:
        # This pulls 2025/2026 data for free
        fbref = sd.FBref(leagues=[league_name], seasons='2025')
        schedule = fbref.read_schedule()
        # Filter for upcoming games (result is NaN)
        upcoming = schedule[schedule['result'].isna()]
        return upcoming
    except Exception as e:
        st.error(f"Scraper error: {e}")
        return pd.DataFrame()

# 3. Predict Probability
def predict_score(home_team, away_team):
    # Base simulation: Standard favorite logic
    # In a full version, we'd use team['xG'] here
    home_exp = 1.8
    away_exp = 1.1
    prob = 0
    for i in range(5):
        for j in range(i):
            prob += poisson.pmf(i, home_exp) * poisson.pmf(j, away_exp)
    return prob

# 4. Display Results
if st.button(f"Scrape {selected_league} Matches"):
    data = get_live_data(leagues[selected_league])
    
    if data.empty:
        st.warning("No matches found for the next few days.")
    else:
        st.success(f"Found {len(data.head(10))} upcoming matches!")
        for idx, row in data.head(10).iterrows():
            h = row['home_team']
            a = row['away_team']
            prob = predict_score(h, a)
            
            with st.container():
                st.subheader(f"{h} vs {a}")
                if prob > 0.75:
                    st.success(f"🔥 80% CONFIDENCE PICK: {prob:.1%}")
                else:
                    st.info(f"Win Probability: {prob:.1%}")
                st.divider()
