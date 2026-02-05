import streamlit as st
import requests

API_KEY = st.secrets["FOOTBALL_API_KEY"]
BASE_URL = "https://v3.football.api-sports.io/"
HEADERS = {'x-rapidapi-host': "v3.football.api-sports.io", 'x-rapidapi-key': API_KEY}

# This "caches" the data for 24 hours (86400 seconds)
@st.cache_data(ttl=86400)
def get_league_standings(league_id, season=2025):
    url = f"{BASE_URL}standings?league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS).json()
    return response['response'][0]['league']['standings'][0]

@st.cache_data(ttl=3600) # Cache fixtures for 1 hour
def get_upcoming_fixtures(league_id, season=2025):
    url = f"{BASE_URL}fixtures?league={league_id}&season={season}&next=10"
    response = requests.get(url, headers=HEADERS).json()
    return response['response']
