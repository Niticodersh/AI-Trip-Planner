"""
LangGraph-powered AI agents for weather decision-making and alternative suggestions.
Uses StateGraph for stateful, multi-step decision workflows.
"""
from typing import TypedDict, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END, START
import json
import streamlit as st
import pandas as pd

# ============ State Definitions ============
class WeatherDecisionState(TypedDict):
    """State for weather decision graph"""
    weather_data: str
    destination: str
    travel_date: str
    decision: str  # "SUITABLE" or "NOT_SUITABLE"
    reasoning: str
    concerns: list[str]
    recommendation: str

class AlternativeState(TypedDict):
    """State for alternative suggestions graph"""
    original_destination: str
    reason: str
    starting_city: str
    travel_date: str
    alternatives: list[dict]

# ============ Weather Decision Graph ============
def analyze_weather_node(state: WeatherDecisionState, llm) -> WeatherDecisionState:
    """Node: Analyze weather data using LLM"""
    prompt = f"""You are an expert travel advisor AI agent. Analyze the following weather data and make a decision.

Weather Data for {state['destination']} on {state['travel_date']}:
{state['weather_data']}

Your task:
1. Analyze temperature, precipitation, wind, humidity
2. Decide if weather is SUITABLE or NOT_SUITABLE for travel
3. Consider:
   - Extreme temperatures (below 5°C or above 40°C are concerning)
   - Heavy rain, storms, severe weather warnings
   - Strong winds disrupting activities
   - Dangerous conditions

4. Provide your decision in JSON format:
{{
    "decision": "SUITABLE" or "NOT_SUITABLE",
    "reasoning": "Brief explanation",
    "concerns": ["list", "of", "concerns"] or [],
    "recommendation": "What you recommend"
}}

Be realistic but not overly cautious. Light rain or mild temperatures are usually acceptable.

Respond with JSON only:"""

    try:
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        
        # Clean response - FIXED: Added both arguments to replace()
        response_text = response.content.strip()
        if response_text.startswith("```"):
            response_text = response_text.replace("```json", "", 1).replace("```", "")
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "")

        
        # Parse JSON
        decision_data = json.loads(response_text)
        
        # Update state with parsed data
        state["decision"] = decision_data.get("decision", "SUITABLE")
        state["reasoning"] = decision_data.get("reasoning", "Weather conditions analyzed")
        state["concerns"] = decision_data.get("concerns", [])
        state["recommendation"] = decision_data.get("recommendation", "Proceed with your trip")
        
        return state
        
    except json.JSONDecodeError as e:
        st.error(f"JSON parsing error: {str(e)}")
        st.error(f"Response was: {response_text[:200]}...")
        # Fallback
        state["decision"] = "SUITABLE"
        state["reasoning"] = "Unable to parse weather analysis, proceeding with caution"
        state["concerns"] = []
        state["recommendation"] = "Review weather data manually before traveling"
        return state
        
    except Exception as e:
        st.error(f"Weather analysis error: {str(e)}")
        # Fallback
        state["decision"] = "SUITABLE"
        state["reasoning"] = "Unable to analyze weather, proceeding with caution"
        state["concerns"] = []
        state["recommendation"] = "Review weather data manually"
        return state

def create_weather_decision_graph(llm):
    """Create and compile the weather decision graph"""
    workflow = StateGraph(WeatherDecisionState)
    
    # Add node with llm parameter closure
    workflow.add_node("analyze_weather", lambda state: analyze_weather_node(state, llm))
    
    # Define flow
    workflow.add_edge(START, "analyze_weather")
    workflow.add_edge("analyze_weather", END)
    
    return workflow.compile()

# ============ Alternative Suggestions Graph ============
def generate_alternatives_node(state: AlternativeState, llm) -> AlternativeState:
    """Node: Generate alternative destinations"""
    prompt = f"""You are an expert travel advisor. The traveler wanted to go to {state['original_destination']} from {state['starting_city']} on {state['travel_date']}, but weather is unsuitable.

Reason: {state['reason']}

Suggest 3 alternative destinations with better weather:
1. Accessible from {state['starting_city']}
2. Similar attractions
3. Good weather during that season
4. Worth visiting

Respond in JSON format:
{{
    "alternatives": [
        {{
            "city": "City Name, Country",
            "reason": "Why this is a good alternative",
            "expected_weather": "Brief weather description"
        }},
        {{
            "city": "City Name, Country",
            "reason": "Why this is a good alternative",
            "expected_weather": "Brief weather description"
        }},
        {{
            "city": "City Name, Country",
            "reason": "Why this is a good alternative",
            "expected_weather": "Brief weather description"
        }}
    ]
}}

JSON only:"""

    try:
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        
        # Clean response - FIXED: Added both arguments to replace()
        response_text = response.content.strip()
        # if response_text.startswith("```json"):
        #     response_text = response_text.replace("``````", "", 1).strip()
        # elif response_text.startswith("```"):
        #     response_text = response_text.replace("```", "", 2).strip()
        if response_text.startswith("```"):
            response_text = response_text.replace("```json", "", 1).replace("```", "")
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "")

        # Parse JSON
        alternatives_data = json.loads(response_text)
        state["alternatives"] = alternatives_data.get("alternatives", [])
        
        return state
        
    except json.JSONDecodeError as e:
        st.error(f"JSON parsing error in alternatives: {str(e)}")
        st.error(f"Response was: {response_text[:200]}...")
        state["alternatives"] = []
        return state
        
    except Exception as e:
        st.error(f"Alternatives generation error: {str(e)}")
        state["alternatives"] = []
        return state

def create_alternatives_graph(llm):
    """Create and compile the alternatives suggestion graph"""
    workflow = StateGraph(AlternativeState)
    
    workflow.add_node("generate_alternatives", lambda state: generate_alternatives_node(state, llm))
    
    workflow.add_edge(START, "generate_alternatives")
    workflow.add_edge("generate_alternatives", END)
    
    return workflow.compile()

# ============ Legacy Functions (for trip plan generation) ============
def generate_trip_plan(flights_df, hotels_df, attractions_df, num_days, city, google_key):
    """Generate trip plan via Gemini using DataFrames."""
    flights_str = flights_df.to_string(index=False)
    hotels_str = hotels_df.to_string(index=False)
    attractions_str = attractions_df.to_string(index=False)

    prompt = f"""
    You are a highly organized travel planner.

    Using the following information, build a day-wise itinerary for a visitor spending {num_days} days in {city}.

    Flights:
    {flights_str}

    Hotels:
    {hotels_str}

    Attractions:
    {attractions_str}

    Requirements:
    - Prioritize top-rated attractions each day.
    - Consider hotel location for efficient planning.
    - Include meal suggestions where possible.
    - Make the plan realistic for {num_days} days: if there are too many attractions, focus on the best.
    - Format the output in a clear, day-by-day itinerary with headings.

    **Before the itinerary, after you mention the best flight and hotel, present an Estimated Budget section like this:**

    - Best roundtrip flight ticket: $[flight_price] x 2  
    - Hotel ({num_days} nights): $[hotel_price_per_night] × {num_days}  
    - Other local expenses (meals, transit, attractions): Estimate an appropriate value for {city}  
    - **Total estimated budget for {num_days} days: $[total_amount] USD**  

    Show each of the above clearly, then write a friendly summary like:
    “This covers your roundtrip airfare, hotel stay, and typical daily expenses in {city}.”

    Do NOT show how you calculated the numbers, just display the prices as listed above.

    Then continue with the day-wise itinerary as usual.

    Example format:
    **Day 1: Arrival & Exploration**
    - Morning: Check into [Hotel Name]
    - Afternoon: Visit [Attraction]
    - Evening: Dinner at [Area]

    Continue this format for all {num_days} days.
"""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-exp",
        google_api_key=google_key
    )
    message = HumanMessage(content=prompt)
    result = llm.invoke([message])
    return result.content
