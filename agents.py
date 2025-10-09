"""
This file contains the AI agent functions for decision-making. It uses prompt templates and LLM chains to analyze
weather suitability and suggest alternative destinations. Outputs are parsed as JSON for structured responses.
UPDATED: Added generate_trip_plan from user's code, using HumanMessage for Gemini invocation.
"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import json
import streamlit as st
import pandas as pd

# Existing functions (unchanged)
def agent_weather_decision(llm, weather_data, destination, travel_date):
    """Let the agent decide if weather is suitable for travel"""
    
    prompt_template = PromptTemplate(
        input_variables=["weather_data", "destination", "travel_date"],
        template="""You are an expert travel advisor AI agent. Analyze the following weather data for a traveler's destination and make a decision.

Weather Data for {destination} on {travel_date}:
{weather_data}

Your task:
1. Carefully analyze the weather conditions (temperature, precipitation, wind, humidity, etc.)
2. Decide if this weather is SUITABLE or NOT SUITABLE for travel
3. Consider factors like:
   - Extreme temperatures (below 5°C or above 40°C are concerning)
   - Heavy rain, storms, or severe weather warnings
   - Strong winds that could disrupt activities
   - Any dangerous weather conditions
   
4. Provide your decision in the following JSON format:
{{
    "decision": "SUITABLE" or "NOT_SUITABLE",
    "reasoning": "Brief explanation of your decision",
    "concerns": ["list", "of", "specific", "concerns"] or [],
    "recommendation": "What you recommend the traveler should do"
}}

Be realistic but not overly cautious. Light rain or mild temperatures are usually acceptable. Focus on safety and comfort.

Your response (JSON only):"""
    )
    
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    try:
        response = chain.run(
            weather_data=weather_data,
            destination=destination,
            travel_date=travel_date
        )
        
        # Parse JSON response
        # Sometimes the model might add markdown, so clean it
        response = response.strip()
        if response.startswith("```json"):
            response = response.replace("```json", "").replace("```", "").strip()
        elif response.startswith("```"):
            response = response.replace("```", "").strip()
            
        decision_data = json.loads(response)
        return decision_data
    except Exception as e:
        st.error(f"Error in agent decision: {str(e)}")
        # Fallback decision
        return {
            "decision": "SUITABLE",
            "reasoning": "Unable to properly analyze weather data, but proceeding with caution.",
            "concerns": [],
            "recommendation": "Please review the weather data yourself and make an informed decision."
        }

def agent_suggest_alternatives(llm, original_destination, reason, starting_city, travel_date):
    """Agent suggests alternative destinations with better weather"""
    
    prompt_template = PromptTemplate(
        input_variables=["original_destination", "reason", "starting_city", "travel_date"],
        template="""You are an expert travel advisor AI agent. The traveler wanted to go to {original_destination} from {starting_city} on {travel_date}, but the weather is not suitable.

Reason for rejection: {reason}

Your task:
1. Suggest 3 alternative destinations that would have BETTER weather conditions during that time
2. Consider destinations that are:
   - Accessible from {starting_city}
   - Have similar attractions or experiences
   - Known for good weather during that season
   - Worth visiting

Provide your suggestions in the following JSON format:
{{
    "alternatives": [
        {{
            "city": "City Name, Country",
            "reason": "Why this is a good alternative",
            "expected_weather": "Brief description of typical weather"
        }},
        {{
            "city": "City Name, Country",
            "reason": "Why this is a good alternative",
            "expected_weather": "Brief description of typical weather"
        }},
        {{
            "city": "City Name, Country",
            "reason": "Why this is a good alternative",
            "expected_weather": "Brief description of typical weather"
        }}
    ]
}}

Your response (JSON only):"""
    )
    
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    try:
        response = chain.run(
            original_destination=original_destination,
            reason=reason,
            starting_city=starting_city,
            travel_date=travel_date
        )
        
        # Clean and parse JSON
        response = response.strip()
        if response.startswith("```json"):
            response = response.replace("```json", "").replace("```", "").strip()
        elif response.startswith("```"):
            response = response.replace("```", "").strip()
            
        alternatives_data = json.loads(response)
        return alternatives_data.get("alternatives", [])
    except Exception as e:
        st.error(f"Error getting alternatives: {str(e)}")
        return []

# User's generate_trip_plan (integrated, using session_state key)
def generate_trip_plan(flights_df, hotels_df, attractions_df, num_days, city, google_key):
    """Generate trip plan via Gemini using DataFrames."""
    flights_str = flights_df.to_string(index=False)
    hotels_str = hotels_df.to_string(index=False)
    attractions_str = attractions_df.to_string(index=False)

    prompt = f"""
You are a travel planner. Using the following information, build a day-wise itinerary for a visitor spending {num_days} days in {city}.

Flights:
{flights_str}

Hotels:
{hotels_str}

Attractions:
{attractions_str}

Requirements:
- Prioritize top-rated attractions each day.
- Consider hotel location for efficiency.
- Include breakfast/lunch/dinner suggestions if possible.
 Keep the plan realistic: if there are too many attractions for the number of days, drop the less important ones.
- Output in a clear day-wise format.
"""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_key
    )
    message = HumanMessage(content=prompt)
    result = llm.invoke([message])
    return result.content
