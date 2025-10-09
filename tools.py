"""
This file defines the initialization of LangChain tools and the AI agent. It sets up environment variables for APIs
and creates reusable tools for weather, and now SerpApi for flights/hotels/attractions (replacing DDG for Step 3).
Weather still uses OpenWeatherMap. Agent for decisions.
UPDATED: Integrated SerpApi functions (get_flights_table, get_hotels_table, get_attractions_table) from user's code.
Call these directly in Step 3; no full tool list needed for itinerary now.
UPDATED: Added "Image" to hotels DF and "Thumbnail" to attractions DF for card display.
UPDATED: Integrated LangSmith tracing with @traceable on key functions (auto-traces LLM/agent; manual for SerpApi).
"""
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities.openweathermap import OpenWeatherMapAPIWrapper
from langchain.agents import initialize_agent, Tool, AgentType
from langsmith import traceable  # NEW: For explicit LangSmith tracing
import streamlit as st
from serpapi import GoogleSearch
import pandas as pd
from datetime import datetime
import re


# LangSmith (for monitoring)
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_PROJECT="ai-trip-planner"


def parse_duration(duration_str):
    """Parse duration string like '2h 30m' to minutes."""
    if pd.isna(duration_str) or duration_str == "N/A":
        return float('inf')
    # Extract numbers: hours and minutes
    hours_match = re.search(r'(\d+)h', duration_str)
    mins_match = re.search(r'(\d+)m', duration_str)
    hours = int(hours_match.group(1)) if hours_match else 0
    mins = int(mins_match.group(1)) if mins_match else 0
    return hours * 60 + mins

def parse_price(price_str):
    """Parse price string like '$100' to integer."""
    if pd.isna(price_str) or price_str == "N/A":
        return float('inf')
    # Remove $ and commas
    clean_price = re.sub(r'[^\d]', '', str(price_str))
    return int(clean_price) if clean_price else float('inf')

@traceable  # NEW: LangSmith trace for tool init
def initialize_tools(google_key, weather_key, serper_key, langchain_key):
    """Initialize LangChain tools and agent. UPDATED: Re-added serper_key for SerpApi. Traced for monitoring."""
    try:
        # Set environment variables
        os.environ['GOOGLE_API_KEY'] = google_key
        os.environ['OPENWEATHERMAP_API_KEY'] = weather_key
        os.environ['SERPAPI_KEY'] = serper_key  # For SerpApi
        os.environ["LANGCHAIN_API_KEY"] = langchain_key
        weather_tool = OpenWeatherMapAPIWrapper()
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=google_key
        )
        
        # Tools list for agent (weather only needed for decisions)
        tools = [
            Tool(
                name="Weather",
                func=weather_tool.run,
                description="Get weather forecast for a city. Input: city,country"
            )
        ]
        
        agent = initialize_agent(
            tools,
            llm,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )
        
        return agent, tools, llm
    except Exception as e:
        st.error(f"Error initializing tools: {str(e)}")
        return None, None, None

# User's SerpApi functions (integrated with params from session state)
@traceable  # NEW: Trace SerpApi calls for monitoring
def get_flights_table(origin: str, destination: str, date: str, location: str = "Austin, Texas, United States"):
    """Get flights table using SerpApi Google Flights. Traced for LangSmith."""
    query = f"Flights from {origin} to {destination} on {date}"
    
    params = {
        "api_key": os.environ['SERPAPI_KEY'],  # Use environment variable
        "engine": "google",
        "q": query,
        "location": location,
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en"
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    flights_list = []
    answer_box = results.get("answer_box", {})
    
    if answer_box.get("type") == "google_flights":
        for f in answer_box.get("flights", []):
            flight_info = f.get("flight_info", [])
            duration = flight_info[1] if len(flight_info) > 1 else "N/A"
            price = flight_info[3] if len(flight_info) > 3 else "N/A"
            flights_list.append({
                "Airline": flight_info[0] if len(flight_info) > 0 else "N/A",
                "Duration": duration,
                "Type": flight_info[2] if len(flight_info) > 2 else "N/A",
                "Price": price,
                "Duration_min": parse_duration(duration),
                "Price_num": parse_price(price)
            })
    else:
        flights_list.append({
            "Airline": "N/A",
            "Duration": "N/A",
            "Type": "N/A",
            "Price": "N/A",
            "Duration_min": float('inf'),
            "Price_num": float('inf')
        })
    
    df = pd.DataFrame(flights_list)
    df = df.sort_values(by=['Duration_min', 'Price_num'], ascending=[True, True])
    df = df.drop(['Duration_min', 'Price_num'], axis=1)
    return df

@traceable  # NEW: Trace SerpApi calls for monitoring
def get_hotels_table(location):
    """Get hotels table using SerpApi Google. UPDATED: Added 'Image' column. Traced for LangSmith."""
    params = {
        "api_key": os.environ['SERPAPI_KEY'],
        "engine": "google",
        "q": f"Hotels in {location}"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    hotels_list = []
    if "answer_box" in results and results["answer_box"].get("hotels"):
        for hotel in results["answer_box"]["hotels"]:
            hotels_list.append({
                "Hotel": hotel.get("title"),
                "Price": hotel.get("price"),
                "Rating": hotel.get("rating"),
                "Image": hotel.get("image")  # Added: Image URL for cards
            })
    df = pd.DataFrame(hotels_list)
    if not df.empty:
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0)
        df = df.sort_values(by=['Rating', 'Price'], ascending=[False, True])
    return df

@traceable  # NEW: Trace SerpApi calls for monitoring
def get_attractions_table(location):
    """Get attractions table using SerpApi Google. UPDATED: Added 'Thumbnail' column."""
    params = {
        "api_key": os.environ['SERPAPI_KEY'],
        "engine": "google",
        "q": f"Attractions in {location}"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    attractions_list = []
    for sight in results.get("top_sights", {}).get("sights", []):
        attractions_list.append({
            "Place": sight.get("title"),
            "Description": sight.get("description"),
            "Rating": sight.get("rating"),
            "Thumbnail": sight.get("thumbnail")  # Added: Thumbnail URL for cards
        })
    df = pd.DataFrame(attractions_list)
    if not df.empty:
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0)
        df = df.sort_values(by='Rating', ascending=False)
    return df
