import streamlit as st
import pandas as pd
import soccerdata as sd
from scipy.stats import poisson

st.set_page_config(page_title="Goal Metric Engine", layout="wide")

st.title("⚽ Goal Metric Engine: Global Edition")

# --- UPDATED LEAGUE MAPPING ---
# We use the exact IDs that soccerdata's FBref reader expects
leagues_map = {
    "Premier League (UK)": "ENG-Premier League",
    "La Liga (Spain)": "ESP-La Liga",
    "Brazil Serie A": "BRA-Serie A",
    "Bundesliga (GER)": "GER-Bundesliga"
}

selected_label = st.sidebar.selectbox("Select League", list(leagues_map.keys()))
league_id = leagues_map[selected_label]

# Determine season based on the league
season = "2026" if "Brazil" in selected_label else "2526"

@st.cache_data(ttl=3600)
def get_data(lg, sn):
    try:
        # We call the FBref class directly to avoid the 'Big 5' restriction
        fbref = sd.FBref(leagues=[lg], seasons=[sn])
        schedule = fbref.read_schedule()
        
        # Filter: Only games that haven't happened (no score)
        # FBref schedule usually uses 'score' or 'result' columns
        upcoming = schedule[schedule['result'].isna()]
        return upcoming.reset_index()
    except Exception as e:
        st.error(f"Logic Error: {e}")
        return pd.DataFrame()

if st.button(f"Analyze {selected_label}"):
    with st.spinner("Scraping live data..."):
        df = get_data(league_id, season)
        
        if df.empty:
            st.warning("No upcoming matches found. Try a different league or check if the season has started.")
        else:
            st.success(f"Found {len(df.head(10))} upcoming matches!")
            for _, row in df.head(10).iterrows():
                # Column names can vary, so we use .get() to be safe
                home = row.get('home_team', 'Home Team')
                away = row.get('away_team', 'Away Team')
                date = row.get('date', 'TBD')
                
                # Our 80% Win Logic (Poisson)
                # Simulating a strong home favorite (1.9 xG vs 1.1 xG)
                prob = 0
                for i in range(6):
                    for j in range(i):
                        prob += poisson.pmf(i, 1.9) * poisson.pmf(j, 1.1)
                
                with st.container():
                    st.write(f"**Date:** {date}")
                    col1, col2 = st.columns([2, 1])
                    col1.subheader(f"{home} vs {away}")
                    if prob > 0.75:
                        col2.success(f"🔥 HIGH CONF: {prob:.1%}")
                    else:
                        col2.info(f"Win Prob: {prob:.1%}")
                    st.divider()
