"""
This file contains reusable UI components for the app, such as progress indicators, decision cards, itinerary tabs,
and navigation buttons. It helps keep the main app file clean by abstracting common rendering logic.
UPDATED: Simplified tabs to Flights, Hotels, Attractions, Itinerary. Use st.dataframe for tables from SerpApi DataFrames. Itinerary shows generated plan text.
"""
import streamlit as st
from datetime import datetime
from tools import get_flights_table, get_hotels_table, get_attractions_table
from agents import generate_trip_plan

def render_header():
    """Render the main app header."""
    st.markdown("""
    <div class='main-header'>
        <h1>✈️ AI Trip Planner</h1>
        <p>Smart travel planning with AI-powered weather analysis</p>
    </div>
    """, unsafe_allow_html=True)

def render_progress(step):
    """Render the top progress indicator."""
    if step > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**{'🟢' if step >= 1 else '⚪'} Step 1: Destination**")
        with col2:
            st.markdown(f"**{'🟢' if step >= 2 else '⚪'} Step 2: AI Weather Check**")
        with col3:
            st.markdown(f"**{'🟢' if step >= 3 else '⚪'} Step 3: Trip Details**")
        st.markdown("---")

def render_api_setup_info():
    """Render the API setup info card and expander. UPDATED: Re-added Serper instructions."""
    st.markdown("""
    <div class='api-setup-card'>
        <h3>⚙️ Before you start, please provide your API keys</h3>
        <p>This app requires three API keys to function. Don't worry, they're stored only in your session!</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("ℹ️ How to get API keys", expanded=False):
        st.markdown("""
        ### 1. Google Gemini API Key (Required for AI)
        - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
        - Click "Get API Key" or "Create API Key"
        - Copy your key
        
        ### 2. OpenWeatherMap API Key (Required for Weather)
        - Go to [OpenWeatherMap](https://openweathermap.org/api)
        - Sign up for a free account
        - Go to API Keys section
        - Copy your key
        
        ### 3. Serper API Key (Required for Search)
        - Go to [Serper.dev](https://serper.dev/)
        - Sign up (free tier available)
        - Get your API key from dashboard
        """)

def render_decision_card(decision):
    """Render the AI decision card (green for suitable, orange for not)."""
    if decision['decision'] == "SUITABLE":
        st.markdown(f"""
        <div class='agent-decision good-weather'>
            <h3>✅ AI Decision: Weather is SUITABLE for Travel</h3>
            <p><strong>Analysis:</strong> {decision['reasoning']}</p>
            <p><strong>AI Recommendation:</strong> {decision['recommendation']}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='agent-decision bad-weather'>
            <h3>⚠️ AI Decision: Weather is NOT SUITABLE for Travel</h3>
            <p><strong>Reasoning:</strong> {decision['reasoning']}</p>
            <p><strong>Recommendation:</strong> {decision['recommendation']}</p>
        </div>
        """, unsafe_allow_html=True)

def render_alternative_card(alt, idx):
    """Render a single alternative destination card with select button."""
    st.markdown(f"""
    <div class='itinerary-card'>
        <h4>🌟 Alternative {idx}: {alt['city']}</h4>
        <p><strong>Why this destination:</strong> {alt['reason']}</p>
        <p><strong>Expected Weather:</strong> {alt['expected_weather']}</p>
    </div>
    """, unsafe_allow_html=True)

def render_itinerary_tabs(agent, tools, llm, google_key, serper_key, starting_city, destination_city, duration, travel_date, decision):
    """Render tabs for Step 3 using SerpApi DataFrames + Gemini plan. UPDATED: Flights/Hotels/Attractions as separate tabs with dataframes; Itinerary shows generated text."""
    # Show AI decision summary
    decision_color = "#4facfe" if decision['decision'] == "SUITABLE" else "#fa709a"
    st.markdown(f"""
    <div style='background: {decision_color}; padding: 1rem; border-radius: 8px; color: white; margin-bottom: 1rem;'>
        <strong>AI Weather Assessment:</strong> {decision['decision']} - {decision['reasoning']}
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["✈️ Flights", "🏨 Hotels", "🗺️ Attractions", "📋 Itinerary"])
    
    date_str = travel_date.strftime('%Y-%m-%d')
    
    with tab1:
        st.subheader("Flight Options")
        with st.spinner("Fetching flights..."):
            flights_df = get_flights_table(starting_city, destination_city, date_str)
            if not flights_df.empty:
                st.dataframe(flights_df, use_container_width=True, hide_index=True)
            else:
                st.warning("No flight data available. Check official sites like Google Flights.")
    
    with tab2:
        st.subheader("Hotel Recommendations")
        with st.spinner("Fetching hotels..."):
            hotels_df = get_hotels_table(destination_city)
            if not hotels_df.empty:
                st.dataframe(hotels_df, use_container_width=True, hide_index=True)
            else:
                st.warning("No hotel data available. Check sites like Booking.com.")
    
    with tab3:
        st.subheader("Top Attractions")
        with st.spinner("Fetching attractions..."):
            attractions_df = get_attractions_table(destination_city)
            if not attractions_df.empty:
                st.dataframe(attractions_df, use_container_width=True, hide_index=True)
            else:
                st.warning("No attractions data available. Try Tripadvisor.")
    
    with tab4:
        st.subheader(f"Day-by-Day {duration}-Day Itinerary")
        with st.spinner("Generating personalized plan..."):
            flights_df = get_flights_table(starting_city, destination_city, date_str)
            hotels_df = get_hotels_table(destination_city)
            attractions_df = get_attractions_table(destination_city)
            trip_plan = generate_trip_plan(flights_df, hotels_df, attractions_df, duration, destination_city, google_key)
            st.markdown(trip_plan)

def render_footer():
    """Render the app footer."""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>🌍 Smart Travel Planning • Powered by AI</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with app info and API status. UPDATED: Mention SerpApi."""
    st.header("ℹ️ About")
    st.write("""
    This **Agentic** AI Trip Planner uses:
    - **AI Agent** for intelligent weather decisions
    - **Google Gemini** for planning
    - **OpenWeatherMap** for weather forecasts
    - **SerpApi** for real-time search (flights, hotels, attractions)
    
    **Agentic Features:**
    - 🤖 AI automatically evaluates weather
    - ⚠️ Rejects unsuitable conditions
    - 🌍 Suggests better alternatives
    - ✅ Makes smart travel decisions
    """)
    
    st.markdown("---")
    
    
    if st.session_state.api_keys_configured:
        st.success("✅ API Keys Configured")
        if st.button("🔑 Update Keys", key="sidebar_update"):
            st.session_state.step = 0
            st.rerun()
    else:
        st.warning("⚠️ API Keys Not Set")
    
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit & LangChain")
