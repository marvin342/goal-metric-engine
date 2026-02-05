import streamlit as st
import requests
from scipy.stats import poisson

# --- CONFIG ---
st.set_page_config(page_title="Goal Metric Engine", layout="wide")
API_KEY = st.secrets["FOOTBALL_API_KEY"]
BASE_URL = "https://v3.football.api-sports.io/"

# --- DATA FETCHING ---
def get_next_games(league_id, season):
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io", 
        'x-rapidapi-key': API_KEY
    }
    # Using 'next=10' is the most bulletproof way to get data
    url = f"{BASE_URL}fixtures?league={league_id}&season={season}&next=10"
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # This part helps us debug if the API key is the problem
        if "errors" in data and data["errors"]:
            st.error(f"API Error: {data['errors']}")
            return []
            
        return data.get('response', [])
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

# --- MATH ---
def calculate_confidence(home_avg, away_avg):
    home_win_prob = 0
    for i in range(7):
        for j in range(i):
            home_win_prob += poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
    return home_win_prob

# --- UI ---
st.title("⚽ Goal Metric Engine")

# League Selection
leagues = {
    "Premier League (UK)": {"id": 39, "season": 2025},
    "Brazil Serie A": {"id": 71, "season": 2026},
    "La Liga (Spain)": {"id": 140, "season": 2025}
}

selected = st.selectbox("Choose League", list(leagues.keys()))
l_id = leagues[selected]["id"]
l_season = leagues[selected]["season"]

if st.button("Generate Predictions"):
    with st.spinner("Talking to API..."):
        fixtures = get_next_games(l_id, l_season)
        
        if not fixtures:
            st.warning("⚠️ No matches returned. Your API key might still be activating, or you hit the 100-request limit.")
        else:
            for f in fixtures:
                h_team = f['teams']['home']['name']
                a_team = f['teams']['away']['name']
                
                # Using 1.9 vs 1.1 as a standard 'Heavy Favorite' simulation
                prob = calculate_confidence(1.9, 1.1)
                
                with st.container():
                    st.subheader(f"{h_team} vs {a_team}")
                    if prob > 0.75:
                        st.success(f"🔥 HIGH CONFIDENCE: {prob:.1%}")
                    else:
                        st.info(f"Win Probability: {prob:.1%}")
                    st.divider()
