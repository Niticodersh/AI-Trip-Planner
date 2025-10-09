"""
This file handles the initial configuration for the Streamlit app, including page settings, custom CSS styling.
It ensures consistent UI appearance. Session state init moved to app.py for reliability.
UPDATED: Removed session init to avoid import-order issues on reload.
"""
import streamlit as st
from dotenv import load_dotenv
import os

# Load .env at startup
load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Trip Planner",
    page_icon="✈️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .weather-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .good-weather {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    .bad-weather {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }
    .agent-decision {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .itinerary-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        font-size: 1.1rem;
        border-radius: 8px;
    }
    .api-setup-card {
        background: #fff3cd;
        border: 2px solid #ffc107;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Validate keys once at startup (early error if missing)
google_key = os.getenv('GOOGLE_API_KEY')
weather_key = os.getenv('OPENWEATHERMAP_API_KEY')
serper_key = os.getenv('SERPAPI_KEY')  # Note: Use SERPAPI_KEY as per user's code

if not all([google_key, weather_key, serper_key]):
    st.error("❌ Missing API keys in .env! Add GOOGLE_API_KEY, OPENWEATHERMAP_API_KEY, SERPAPI_KEY.")
    st.stop()
else:
    # Set configured flag after validation (now in app.py for session)
    pass
