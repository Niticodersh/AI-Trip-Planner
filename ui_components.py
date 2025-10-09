"""
This file contains reusable UI components for the app, such as progress indicators, decision cards, itinerary tabs,
and navigation buttons. It helps keep the main app file clean by abstracting common rendering logic.
UPDATED: Added render_stars helper to display ratings as ★ stars (e.g., ★★★★☆ for 4/5). Used in hotel/attraction cards.
UPDATED: For hotels/attractions: If any image missing, fallback to table + "Explore more..." message. If all images present, use cards only (no table).
"""
import streamlit as st
from datetime import datetime
from tools import get_flights_table, get_hotels_table, get_attractions_table
from agents import generate_trip_plan
import pandas as pd

# Detect small screen width (works for mobile/tablet)
if "screen_mode" not in st.session_state:
    try:
        width = st.runtime.scriptrunner.script_run_context.get_script_run_ctx().session.client.width
        st.session_state['screen_mode'] = 'small' if width < 800 else 'large'
    except:
        st.session_state['screen_mode'] = 'auto'

def render_stars(rating: float, max_stars: int = 5) -> str:
    """Helper to render rating as Unicode stars (e.g., ★★★★☆ for 4.0)."""
    if pd.isna(rating) or rating <= 0:
        return "☆" * max_stars
    full_stars = int(rating)
    empty_stars = max_stars - full_stars
    return "★" * full_stars + "☆" * empty_stars

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
    """Render tabs for Step 3 using SerpApi DataFrames + Gemini plan. UPDATED: Used render_stars in cards. For hotels/attractions: Pre-check images with requests (status+size); if any fail, fallback to full table + message; else cards only with per-image fallback/placeholder."""
    import requests  # For image validation/fallback
    
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
                # NEW: Strict pre-check with requests for each image
                failed_images = 0
                total_images = 0
                for _, row in hotels_df.iterrows():
                    if row.get('Image') and pd.notna(row['Image']) and row['Image'] != '':
                        total_images += 1
                        try:
                            response = requests.head(row['Image'], timeout=3, allow_redirects=True)
                            if response.status_code != 200 or 'content-length' not in response.headers or int(response.headers['content-length']) == 0:
                                failed_images += 1
                        except:
                            failed_images += 1
                
                has_issues = failed_images > 0 or total_images == 0
                if has_issues:
                    st.info(f"Image issues detected ({failed_images}/{total_images})—showing as table. More hotels you can explore on Booking.com!")
                    display_df = hotels_df[['Hotel', 'Price', 'Rating']].copy()
                    display_df['Rating'] = display_df['Rating'].apply(lambda r: f"{render_stars(r)} ({r})" if pd.notna(r) else "N/A")
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    # All good: Cards only
                    # Responsive layout: show 1 card per row on small screens
                    if st.session_state.get('screen_mode', 'auto') == 'small':
                        num_cols = 1
                    else:
                        num_cols = 3  # default for larger screens

                    cols = st.columns(num_cols)

                    for idx, row in hotels_df.iterrows():
                        col_idx = idx % 3
                        with cols[col_idx]:
                            st.markdown(f"### {row['Hotel']}")
                            st.write(f"**Price:** {row['Price']}")
                            st.write(f"**Rating:** {render_stars(row['Rating'])} ({row['Rating']})")
                            # Runtime fallback with placeholder
                            image_url = row['Image']
                            try:
                                st.image(image_url, caption=row['Hotel'])
                            except Exception:
                                try:
                                    response = requests.get(image_url, timeout=5)
                                    response.raise_for_status()
                                    st.image(response.content, caption=row['Hotel'])
                                except:
                                    st.image("https://via.placeholder.com/300x200?text=No+Image", caption=row['Hotel'])  # Placeholder
                    if len(hotels_df) > 9:
                        pass
            else:
                st.warning("No hotel data available. Check sites like Booking.com.")
    
    with tab3:
        st.subheader("Top Attractions")
        with st.spinner("Fetching attractions..."):
            attractions_df = get_attractions_table(destination_city)
            if not attractions_df.empty:
                # NEW: Pre-check thumbnails
                failed_thumbnails = 0
                for _, row in attractions_df.iterrows():
                    if row.get('Thumbnail') and pd.notna(row['Thumbnail']):
                        try:
                            response = requests.get(row['Thumbnail'], timeout=3)
                            if response.status_code != 200 or len(response.content) == 0:
                                failed_thumbnails += 1
                        except:
                            failed_thumbnails += 1
                
                if failed_thumbnails > 0:
                    st.info(f"More attractions you can explore on Tripadvisor!")
                    st.dataframe(attractions_df[['Place', 'Description', 'Rating']], use_container_width=True, hide_index=True)
                else:
                    # All good: Cards only
                    # Responsive layout: show 1 card per row on small screens
                    if st.session_state.get('screen_mode', 'auto') == 'small':
                        num_cols = 1
                    else:
                        num_cols = 3  # default for larger screens

                    cols = st.columns(num_cols)

                    for idx, row in attractions_df.iterrows():
                        col_idx = idx % 3
                        with cols[col_idx]:
                            st.markdown(f"### {row['Place']}")
                            st.write(row['Description'])
                            st.write(f"**Rating:** {render_stars(row['Rating'])} ({row['Rating']})")
                            # Per-image fallback
                            image_url = row['Thumbnail']
                            try:
                                st.image(image_url, caption=row['Place'])
                            except:
                                try:
                                    response = requests.get(image_url, timeout=5)
                                    response.raise_for_status()
                                    st.image(response.content, caption=row['Place'])
                                except:
                                    st.warning("Thumbnail unavailable.")
                    if len(attractions_df) > 9:
                        pass
            else:
                st.warning("No attractions data available. Try Tripadvisor.")
    with tab4:
        st.subheader(f"Day-by-Day {duration}-Day Itinerary")
        with st.spinner("Generating personalized plan..."):
            flights_df = get_flights_table(starting_city, destination_city, date_str)
            hotels_df = get_hotels_table(destination_city)
            attractions_df = get_attractions_table(destination_city)
            trip_plan = generate_trip_plan(flights_df, hotels_df, attractions_df, duration, destination_city, google_key)

            # Normalize excessive spacing (remove >2 consecutive newlines)
            import re
            trip_plan_clean = re.sub(r'\n{3,}', '\n\n', trip_plan.strip())

            st.session_state.itinerary_data = trip_plan_clean

            # Uniform, clean font styling
            st.markdown(
                f"""
                <div style="
                    font-family: 'Inter', sans-serif;
                    font-size: 16px;
                    line-height: 1.6;
                    color: #1c1c1c;
                    background-color: #f9f9f9;
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                    white-space: pre-wrap;">
                    {trip_plan_clean}
                </div>
                """,
                unsafe_allow_html=True
            )

            


def render_footer():
    """Render the app footer."""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>🌍 Smart Travel Planning • Powered by AI</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with app info. UPDATED: Removed API status/update button."""
    st.header("ℹ️ About")
    st.write("""
    This **Agentic** AI Trip Planner :
    
    - 🤖 Automatically evaluates weather
    - ⚠️ Rejects unsuitable conditions
    - 🌍 Suggests better alternatives
    - ✅ Makes smart travel decisions
    """)
    
    st.markdown("---")
    st.caption("Send your feedback on nitishbhardwaj471@gmail.com")
