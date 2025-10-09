"""
This file handles the initial configuration for the Streamlit app, including page settings, custom CSS styling,
and initialization of session state variables. It ensures consistent UI appearance and state management across the app.
UPDATED: Re-added 'serper_api_key' to session state for SerpApi integration.
"""
import streamlit as st

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

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'agent_decision' not in st.session_state:
    st.session_state.agent_decision = None
if 'itinerary_data' not in st.session_state:
    st.session_state.itinerary_data = None
if 'api_keys_configured' not in st.session_state:
    st.session_state.api_keys_configured = False
if 'google_api_key' not in st.session_state:
    st.session_state.google_api_key = ''
if 'weather_api_key' not in st.session_state:
    st.session_state.weather_api_key = ''
if 'serper_api_key' not in st.session_state:
    st.session_state.serper_api_key = ''
if 'alternative_suggestions' not in st.session_state:
    st.session_state.alternative_suggestions = []
