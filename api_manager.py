import requests
import streamlit as st

# This uses the secret key you added to Streamlit settings
API_KEY = st.secrets["FOOTBALL_API_KEY"]
BASE_URL = "https://v3.football.api-sports.io/"

HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

def fetch_standings(league_id):
    """Fetches current league table to calculate team strength"""
    url = f"{BASE_URL}standings?league={league_id}&season=2025"
    response = requests.get(url, headers=HEADERS).json()
    return response['response'][0]['league']['standings'][0]

def fetch_fixtures(league_id):
    """Fetches the next 10 upcoming matches"""
    url = f"{BASE_URL}fixtures?league={league_id}&season=2025&next=10"
    response = requests.get(url, headers=HEADERS).json()
    return response['response']
