# app.py
"""
Main entry point for the AI Trip Planner Streamlit app, now using LangGraph for orchestration.
The graph handles backend logic and state transitions, traced in LangSmith.
Streamlit renders UI based on current graph state.
On user interactions (buttons), update the graph state and resume execution.
"""
import streamlit as st
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
import pandas as pd

# Load .env
load_dotenv()

from config import *  # Page config, CSS
from graph import workflow, TripPlannerState
from ui_components import render_header, render_progress, render_decision_card, render_alternative_card, render_itinerary_tabs, render_footer, render_sidebar

# Checkpointer for persistence
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()

# Compile the graph
graph_app = workflow.compile(checkpointer=checkpointer)

# Initialize session state
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = str(hash(time.time()))  # Unique per session

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Initialize default state
default_state = {
    "step": 1,
    "starting_city": None,
    "destination_city": None,
    "travel_date": datetime.now().date() + timedelta(days=7),
    "duration": 5,
    "weather_data": None,
    "agent_decision": None,
    "alternative_suggestions": None,
    "itinerary_data": None,
    "user_choice": None,
    "selected_alternative": None,
    "google_key": os.getenv('GOOGLE_API_KEY'),
    "weather_key": os.getenv('OPENWEATHERMAP_API_KEY'),
    "serper_key": os.getenv('SERPAPI_KEY'),
    "langchain_key": os.getenv('LANGCHAIN_API_KEY')
}

# Get current state, handle missing or empty state
current_state = graph_app.get_state(config).values or default_state
if not current_state or 'step' not in current_state:
    # Initialize state if empty or missing step
    graph_app.invoke(default_state, config)
    current_state = default_state
    st.session_state.step = 1
else:
    # Ensure step is in session state
    st.session_state.step = current_state.get('step', 1)

# Header and progress
render_header()
render_progress(current_state["step"])

# Render UI based on current step
step = current_state["step"]

if step == 1:
    st.header("📍 Where would you like to go?")
    st.write(f"Google Key: {os.getenv('GOOGLE_API_KEY')[:10]}...")

    col1, col2 = st.columns(2)

    with col1:
        starting_city = st.text_input("🏠 Starting City", value=current_state.get("starting_city", ""), placeholder="e.g., Mumbai, India", key="start_city")
        destination_city = st.text_input("🎯 Destination City", value=current_state.get("destination_city", ""), placeholder="e.g., Paris, France", key="dest_city")

    with col2:
        travel_date = st.date_input(
            "📅 Travel Date",
            min_value=datetime.now().date(),
            value=current_state.get("travel_date", datetime.now().date() + timedelta(days=7)),
            key="travel_date_input"
        )
        duration = st.number_input("📆 Trip Duration (days)", min_value=1, max_value=30, value=current_state.get("duration", 5), key="duration_input")

    if st.button("🤖 Let AI Analyze Weather"):
        # Validate inputs before updating
        if not (starting_city and destination_city):
            st.error("Please fill in both Starting City and Destination City!")
        else:
            # Update state with inputs
            updates = {
                "starting_city": starting_city,
                "destination_city": destination_city,
                "travel_date": travel_date,
                "duration": duration
            }
            graph_app.update_state(config, updates, as_node="input_destination")

            # Resume graph execution
            with st.spinner("Processing..."):
                for output in graph_app.stream(None, config):
                    pass
            st.rerun()

elif step == 2:
    st.header(f"🤖 AI Weather Analysis for {current_state['destination_city']}")

    if current_state["weather_data"]:
        with st.expander("📊 Raw Weather Data"):
            st.write(current_state["weather_data"])

    if current_state["agent_decision"]:
        render_decision_card(current_state["agent_decision"])

        if current_state["agent_decision"]["decision"] == "SUITABLE":
            st.success("✅ Weather conditions are favorable! Automatically finalizing your trip...")
            time.sleep(2)

            # Auto-proceed
            graph_app.update_state(config, {"user_choice": "continue"}, as_node="user_choice")
            with st.spinner("Processing..."):
                for output in graph_app.stream(None, config):
                    pass
            st.rerun()
        else:
            if current_state["agent_decision"].get('concerns'):
                st.warning("**Specific Concerns:**")
                for concern in current_state["agent_decision"]['concerns']:
                    st.write(f"• {concern}")

            st.markdown("---")
            st.subheader("🌍 AI Suggests Alternative Destinations")

            alternatives = current_state.get("alternative_suggestions", [])
            if alternatives:
                for idx, alt in enumerate(alternatives, 1):
                    render_alternative_card(alt, idx)

                    if st.button(f"✈️ Choose {alt['city']}", key=f"alt_{idx}"):
                        updates = {
                            "user_choice": "alternative",
                            "selected_alternative": alt
                        }
                        graph_app.update_state(config, updates, as_node="user_choice")
                        with st.spinner("Processing..."):
                            for output in graph_app.stream(None, config):
                                pass
                        st.rerun()

            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📅 Try Different Date"):
                    graph_app.update_state(config, {"user_choice": "different"}, as_node="user_choice")
                    with st.spinner("Processing..."):
                        for output in graph_app.stream(None, config):
                            pass
                    st.rerun()

            with col2:
                if st.button("🗺️ Choose Different City"):
                    graph_app.update_state(config, {"user_choice": "different"}, as_node="user_choice")
                    with st.spinner("Processing..."):
                        for output in graph_app.stream(None, config):
                            pass
                    st.rerun()

            with col3:
                if st.button("⚠️ Continue Anyway"):
                    st.warning("You've chosen to proceed despite unfavorable weather. Stay safe!")
                    graph_app.update_state(config, {"user_choice": "continue"}, as_node="user_choice")
                    with st.spinner("Processing..."):
                        for output in graph_app.stream(None, config):
                            pass
                    st.rerun()

elif step == 3:
    st.header(f"🗺️ Your {current_state['duration']}-Day Trip Plan")
    st.subheader(f"{current_state['starting_city']} → {current_state['destination_city']}")

    itinerary_data = current_state.get("itinerary_data", {})
    if itinerary_data:
        # Convert dictionary back to DataFrames for rendering
        flights_df = pd.DataFrame(itinerary_data.get("flights_df", []))
        hotels_df = pd.DataFrame(itinerary_data.get("hotels_df", []))
        attractions_df = pd.DataFrame(itinerary_data.get("attractions_df", []))
        trip_plan = itinerary_data.get("trip_plan")

        render_itinerary_tabs(
            None, None, None,
            current_state["google_key"],
            current_state["serper_key"],
            current_state["starting_city"],
            current_state["destination_city"],
            current_state["duration"],
            current_state["travel_date"],
            current_state["agent_decision"],
            pre_fetched=True,
            flights_df=flights_df,
            hotels_df=hotels_df,
            attractions_df=attractions_df,
            trip_plan=trip_plan
        )

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Plan Another Trip"):
                graph_app.update_state(config, {"step": 1, "user_choice": "different"}, as_node="user_choice")
                with st.spinner("Processing..."):
                    for output in graph_app.stream(None, config):
                        pass
                st.session_state.clear()
                st.rerun()

# Sidebar and Footer
render_sidebar()
render_footer()
