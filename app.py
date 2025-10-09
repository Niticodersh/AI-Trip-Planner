"""
This is the main entry point for the AI Trip Planner Streamlit app. It orchestrates the multi-step workflow,
handles user inputs, calls tools/agents, and renders UI based on session state. Import other modules for modularity.
Run with: streamlit run app.py
UPDATED: Session state init at top for reload safety. Set api_keys_configured=True after env validation.
"""
import streamlit as st
from datetime import datetime, timedelta
import json
import time
import os
from dotenv import load_dotenv

# Load .env (moved to config, but ensure here too)
load_dotenv()

# Import from other modules (after load_dotenv)
from config import *  # Page config, CSS (runs validation)

# Initialize session state AT TOP (safe defaults for reload)
if 'step' not in st.session_state:
    st.session_state.step = 1  # Start at Step 1
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'agent_decision' not in st.session_state:
    st.session_state.agent_decision = None
if 'itinerary_data' not in st.session_state:
    st.session_state.itinerary_data = None
if 'alternative_suggestions' not in st.session_state:
    st.session_state.alternative_suggestions = []
if 'api_keys_configured' not in st.session_state:
    st.session_state.api_keys_configured = True  # Set True after config validation

# Keys from env (loaded in config)
google_key = os.getenv('GOOGLE_API_KEY')
weather_key = os.getenv('OPENWEATHERMAP_API_KEY')
serper_key = os.getenv('SERPAPI_KEY')
langchain_key = os.getenv('LANGCHAIN_API_KEY')

from tools import initialize_tools
from agents import agent_weather_decision, agent_suggest_alternatives
from ui_components import (render_header, render_progress, render_decision_card,
                           render_alternative_card, render_itinerary_tabs, render_footer, render_sidebar)

# Header (runs after config)
render_header()

# Progress indicator
render_progress(st.session_state.step)

# Step 1: Input destination details (now default start)
if st.session_state.step == 1:
    st.header("📍 Where would you like to go?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        starting_city = st.text_input("🏠 Starting City", placeholder="e.g., Mumbai, India", key="start_city")
        destination_city = st.text_input("🎯 Destination City", placeholder="e.g., Paris, France", key="dest_city")
    
    with col2:
        travel_date = st.date_input(
            "📅 Travel Date",
            min_value=datetime.now().date(),
            value=datetime.now().date() + timedelta(days=7),
            key="travel_date_input"
        )
        duration = st.number_input("📆 Trip Duration (days)", min_value=1, max_value=30, value=5, key="duration_input")
    
    col_x, col_y = st.columns([3, 1])
    
    with col_x:
        if st.button("🤖 Let AI Analyze Weather"):
            if not starting_city or not destination_city:
                st.error("Please fill in all fields!")
            else:
                st.session_state.starting_city = starting_city
                st.session_state.destination_city = destination_city
                st.session_state.travel_date = travel_date
                st.session_state.duration = duration
                st.session_state.step = 2
                st.rerun()

# Step 2: AI Weather Analysis
elif st.session_state.step == 2:
    st.header(f"🤖 AI Weather Analysis for {st.session_state.destination_city}")
    
    with st.spinner("🔍 AI Agent is analyzing weather conditions..."):
        try:
            agent, tools, llm = initialize_tools(google_key, weather_key, serper_key, langchain_key)
            
            if agent and tools and llm:
                # Get weather
                weather_query = f"{st.session_state.destination_city}"
                weather_result = tools[0].func(weather_query)
                
                st.session_state.weather_data = weather_result
                
                # Let AI agent decide
                st.info("🤖 AI Agent is evaluating weather conditions...")
                decision = agent_weather_decision(
                    llm,
                    weather_result,
                    st.session_state.destination_city,
                    st.session_state.travel_date.strftime('%B %d, %Y')
                )
                
                st.session_state.agent_decision = decision
                
                # Display weather data
                with st.expander("📊 Raw Weather Data"):
                    st.write(weather_result)
                
                # Display AI decision
                render_decision_card(decision)
                
                if decision['decision'] == "SUITABLE":
                    st.success("✅ Weather conditions are favorable! Automatically finalizing your trip...")
                    
                    import time
                    time.sleep(2)  # Brief pause to show the message
                    
                    # Automatically move to step 3
                    st.session_state.step = 3
                    st.rerun()
                
                else:  # NOT_SUITABLE
                    if decision.get('concerns'):
                        st.warning("**Specific Concerns:**")
                        for concern in decision['concerns']:
                            st.write(f"• {concern}")
                    
                    st.markdown("---")
                    st.subheader("🌍 AI Suggests Alternative Destinations")
                    
                    with st.spinner("🤖 Finding better destinations with good weather..."):
                        alternatives = agent_suggest_alternatives(
                            llm,
                            st.session_state.destination_city,
                            decision['reasoning'],
                            st.session_state.starting_city,
                            st.session_state.travel_date.strftime('%B %d, %Y')
                        )
                        
                        st.session_state.alternative_suggestions = alternatives
                        
                        if alternatives:
                            for idx, alt in enumerate(alternatives, 1):
                                render_alternative_card(alt, idx)
                                
                                if st.button(f"✈️ Choose {alt['city']}", key=f"alt_{idx}"):
                                    st.session_state.destination_city = alt['city']
                                    st.session_state.step = 2
                                    st.rerun()
                    
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📅 Try Different Date"):
                            st.session_state.step = 1
                            st.rerun()
                    
                    with col2:
                        if st.button("🗺️ Choose Different City"):
                            st.session_state.step = 1
                            st.rerun()
                    
                    with col3:
                        if st.button("⚠️ Continue Anyway"):
                            st.warning("You've chosen to proceed despite unfavorable weather. Stay safe!")
                            st.session_state.step = 3
                            st.rerun()
            else:
                st.error("Failed to initialize tools. Check .env keys.")
                if st.button("🔄 Restart App"):
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Error in weather analysis: {str(e)}")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("⬅️ Go Back"):
                    st.session_state.step = 1
                    st.rerun()

# Step 3: Generate full itinerary
elif st.session_state.step == 3:
    st.header(f"🗺️ Your {st.session_state.duration}-Day Trip Plan")
    st.subheader(f"{st.session_state.starting_city} → {st.session_state.destination_city}")
    
    with st.spinner("🔍 Fetching flights, hotels, attractions, and generating plan..."):
        try:
            agent, tools, llm = initialize_tools(google_key, weather_key, serper_key, langchain_key)
            
            if agent and tools:
                render_itinerary_tabs(
                    agent, tools, llm,
                    google_key,
                    serper_key,
                    st.session_state.starting_city,
                    st.session_state.destination_city,
                    st.session_state.duration,
                    st.session_state.travel_date,
                    st.session_state.agent_decision
                )
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Plan Another Trip"):
                        st.session_state.step = 1
                        st.session_state.weather_data = None
                        st.session_state.agent_decision = None
                        st.session_state.itinerary_data = None
                        st.rerun()
                        
                with col2:
                    if st.button("📥 Download Itinerary"):
                        st.success("Feature coming soon! You can copy the information above for now.")
                        
        except Exception as e:
            st.error(f"Error generating trip plan: {str(e)}")
            if st.button("⬅️ Go Back"):
                st.session_state.step = 1
                st.rerun()

# Sidebar and Footer
render_sidebar()
render_footer()
