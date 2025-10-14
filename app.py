"""
AI Trip Planner with LangGraph-powered agent workflows.
Run with: streamlit run app.py
"""
import streamlit as st
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from langsmith.run_helpers import tracing_context

load_dotenv()

from config import *

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'agent_decision' not in st.session_state:
    st.session_state.agent_decision = None
if 'itinerary_data' not in st.session_state:
    st.session_state.itinerary_data = None
if 'alternative_suggestions' not in st.session_state:
    st.session_state.alternative_suggestions = []
if 'api_keys_configured' not in st.session_state:
    st.session_state.api_keys_configured = True

# API Keys
google_key = os.getenv('GOOGLE_API_KEY')
weather_key = os.getenv('OPENWEATHERMAP_API_KEY')
serper_key = os.getenv('SERPAPI_KEY')
langchain_key = os.getenv('LANGCHAIN_API_KEY')

from tools import initialize_tools
from agents import create_weather_decision_graph, create_alternatives_graph
from ui_components import (render_header, render_progress, render_decision_card,
                           render_alternative_card, render_itinerary_tabs, render_footer, render_sidebar)

render_header()
render_progress(st.session_state.step)

# Step 1: Input
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

# Step 2: LangGraph Weather Analysis
elif st.session_state.step == 2:
    st.header(f"🤖 AI Weather Analysis for {st.session_state.destination_city}")
    
    with st.spinner("🔍 LangGraph agent analyzing weather..."):
        try:
            weather_tool, llm = initialize_tools(google_key, weather_key, serper_key, langchain_key)
            
            if weather_tool and llm:
                # Get weather
                weather_query = f"{st.session_state.destination_city}"
                weather_result = weather_tool.run(weather_query)
                
                st.session_state.weather_data = weather_result
                
                # Create and invoke weather decision graph
                st.info("🤖 LangGraph agent evaluating weather...")
                weather_graph = create_weather_decision_graph(llm)
                
                initial_state = {
                    "weather_data": weather_result,
                    "destination": st.session_state.destination_city,
                    "travel_date": st.session_state.travel_date.strftime('%B %d, %Y'),
                    "decision": "",
                    "reasoning": "",
                    "concerns": [],
                    "recommendation": ""
                }
                
                final_state = weather_graph.invoke(initial_state)
                decision = {
                    "decision": final_state["decision"],
                    "reasoning": final_state["reasoning"],
                    "concerns": final_state["concerns"],
                    "recommendation": final_state["recommendation"]
                }
                
                st.session_state.agent_decision = decision
                
                # Display weather data
                with st.expander("📊 Raw Weather Data"):
                    st.write(weather_result)
                
                # Display AI decision
                render_decision_card(decision)
                
                if decision['decision'] == "SUITABLE":
                    st.success("✅ Weather conditions are favorable! Automatically finalizing...")
                    import time
                    time.sleep(2)
                    st.session_state.step = 3
                    st.rerun()
                
                else:  # NOT_SUITABLE
                    if decision.get('concerns'):
                        st.warning("**Specific Concerns:**")
                        for concern in decision['concerns']:
                            st.write(f"• {concern}")
                    
                    st.markdown("---")
                    st.subheader("🌍 AI Suggests Alternative Destinations")
                    
                    with st.spinner("🤖 LangGraph finding better destinations..."):
                        # Create alternatives graph
                        alternatives_graph = create_alternatives_graph(llm)
                        
                        alt_initial_state = {
                            "original_destination": st.session_state.destination_city,
                            "reason": decision['reasoning'],
                            "starting_city": st.session_state.starting_city,
                            "travel_date": st.session_state.travel_date.strftime('%B %d, %Y'),
                            "alternatives": []
                        }
                        
                        alt_final_state = alternatives_graph.invoke(alt_initial_state)
                        alternatives = alt_final_state["alternatives"]
                        
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
                            st.warning("Proceeding despite unfavorable weather. Stay safe!")
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

# Step 3: Generate itinerary
elif st.session_state.step == 3:
    st.header(f"🗺️ Your {st.session_state.duration}-Day Trip Plan")
    st.subheader(f"{st.session_state.starting_city} → {st.session_state.destination_city}")
    
    with st.spinner("🔍 Fetching flights, hotels, attractions, and generating plan..."):
        try:
            weather_tool, llm = initialize_tools(google_key, weather_key, serper_key, langchain_key)
            
            if weather_tool and llm:
                render_itinerary_tabs(
                    llm,
                    google_key,
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
                        
        except Exception as e:
            st.error(f"Error generating trip plan: {str(e)}")
            if st.button("⬅️ Go Back"):
                st.session_state.step = 1
                st.rerun()


render_sidebar()
render_footer()
