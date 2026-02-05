import streamlit as st
import pandas as pd
import fbrefdata as fd
from scipy.stats import poisson

st.set_page_config(page_title="Goal Metric Engine", layout="wide")

st.title("⚽ Goal Metric Engine: Global Edition")
st.markdown("### Predicting 2026 Fixtures via FBref Scraper")

# --- LEAGUE MAPPING ---
# These are the exact names the scraper uses
leagues = {
    "Premier League (UK)": "ENG-Premier League",
    "La Liga (Spain)": "ESP-La Liga",
    "Brazil Serie A": "BRA-Série A",
    "Bundesliga (GER)": "GER-Bundesliga",
    "Serie A (ITA)": "ITA-Serie A"
}

selected_label = st.sidebar.selectbox("Select League", list(leagues.keys()))
league_id = leagues[selected_label]

# Choose the right season for the league
# Europe is 2025-2026, Brazil is 2026
if "Brazil" in selected_label:
    target_season = "2026"
else:
    target_season = "2025-2026"

@st.cache_data(ttl=3600)
def get_matches(lg, sn):
    try:
        # Initialize the specialized FBref scraper
        scraper = fd.FBref(lg, sn)
        schedule = scraper.read_schedule()
        # Only keep games that haven't been played (no score yet)
        upcoming = schedule[schedule['score'].isna()]
        return upcoming
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

def run_math(h_xg=1.8, a_xg=1.1):
    h_win = 0
    for i in range(6):
        for j in range(i):
            h_win += poisson.pmf(i, h_xg) * poisson.pmf(j, a_xg)
    return h_win

if st.button(f"Analyze {selected_label} Matches"):
    with st.spinner(f"Scraping live {target_season} data..."):
        df = get_matches(league_id, target_season)
        
        if df.empty:
            st.warning("No upcoming matches found. The season might be in a break.")
        else:
            st.success(f"Found {len(df.head(10))} upcoming matches!")
            for idx, row in df.head(10).iterrows():
                # Handling different column names from the scraper
                home = row.get('home_team', 'Home')
                away = row.get('away_team', 'Away')
                date = row.get('date', 'TBD')
                
                win_prob = run_math() # We'll plug in live xG next!
                
                with st.container():
                    st.write(f"**{date}**")
                    col1, col2 = st.columns([2, 1])
                    col1.subheader(f"{home} vs {away}")
                    
                    if win_prob > 0.75:
                        col2.success(f"🔥 HIGH CONF: {win_prob:.1%}")
                    else:
                        col2.metric("Home Win Prob", f"{win_prob:.1%}")
                    st.divider()
