import streamlit as st
import api_manager
from scipy.stats import poisson

st.set_page_config(page_title="Goal Metric Engine", layout="wide")
st.title("⚽ Goal Metric Engine: 80% Confidence Tracker")

# League Mapping
LEAGUES = {
    "Premier League (UK)": 39,
    "La Liga (Spain)": 140,
    "Brazil Serie A": 71,
    "Brazil Serie B": 72,
    "Bundesliga (Germany)": 78
}

league_name = st.sidebar.selectbox("Select League", list(LEAGUES.keys()))
league_id = LEAGUES[league_name]

# The Prediction Logic
def get_probability(home_avg, away_avg):
    home_win = 0
    draw = 0
    for i in range(10): # Home goals
        for j in range(10): # Away goals
            prob = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j: home_win += prob
            elif i == j: draw += prob
    return home_win, draw, (1 - home_win - draw)

if st.button("Generate High-Confidence Predictions"):
    with st.spinner("Analyzing League Data..."):
        fixtures = api_manager.fetch_fixtures(league_id)
        
        for game in fixtures:
            home = game['teams']['home']['name']
            away = game['teams']['away']['name']
            
            # Here, the AI simulates the game
            # In a pro version, we'd use real team xG here
            h_prob, d_prob, a_prob = get_probability(1.8, 1.1) 
            
            # THE 80% FILTER: Only highlight the best bets
            if h_prob > 0.75:
                st.success(f"🔥 HIGH CONFIDENCE: {home} Win ({h_prob:.1%})")
            elif (h_prob + d_prob) > 0.85:
                st.info(f"🛡️ SAFE BET: {home} or Draw (Double Chance)")
            else:
                st.write(f"⚖️ {home} vs {away}: Probabilities: H:{h_prob:.0%} D:{d_prob:.0%} A:{a_prob:.0%}")import streamlit as st
import api_manager
from scipy.stats import poisson

st.set_page_config(page_title="Goal Metric Engine", layout="wide")
st.title("⚽ Goal Metric Engine: 80% Confidence Tracker")

# League Mapping
LEAGUES = {
    "Premier League (UK)": 39,
    "La Liga (Spain)": 140,
    "Brazil Serie A": 71,
    "Brazil Serie B": 72,
    "Bundesliga (Germany)": 78
}

league_name = st.sidebar.selectbox("Select League", list(LEAGUES.keys()))
league_id = LEAGUES[league_name]

# The Prediction Logic
def get_probability(home_avg, away_avg):
    home_win = 0
    draw = 0
    for i in range(10): # Home goals
        for j in range(10): # Away goals
            prob = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j: home_win += prob
            elif i == j: draw += prob
    return home_win, draw, (1 - home_win - draw)

if st.button("Generate High-Confidence Predictions"):
    with st.spinner("Analyzing League Data..."):
        fixtures = api_manager.fetch_fixtures(league_id)
        
        for game in fixtures:
            home = game['teams']['home']['name']
            away = game['teams']['away']['name']
            
            # Here, the AI simulates the game
            # In a pro version, we'd use real team xG here
            h_prob, d_prob, a_prob = get_probability(1.8, 1.1) 
            
            # THE 80% FILTER: Only highlight the best bets
            if h_prob > 0.75:
                st.success(f"🔥 HIGH CONFIDENCE: {home} Win ({h_prob:.1%})")
            elif (h_prob + d_prob) > 0.85:
                st.info(f"🛡️ SAFE BET: {home} or Draw (Double Chance)")
            else:
                st.write(f"⚖️ {home} vs {away}: Probabilities: H:{h_prob:.0%} D:{d_prob:.0%} A:{a_prob:.0%}")
