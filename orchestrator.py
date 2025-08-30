# orchestrator.py

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from state.travel_state import TravelState
from agents.itinerary_builder import itinerary_builder
from agents.activity_finder import activity_finder
from agents.visa_agent import visa_agent
from agents.hotel_recommender import hotel_recommender
from agents.weather_agent import weather_agent


def create_travel_workflow() -> StateGraph:
    """
    Creates and returns a LangGraph workflow for travel planning.
    
    The workflow consists of:
    - visa_agent: Provides visa requirements (always runs)
    - weather_agent: Provides weather forecast (always runs)
    - itinerary_builder: Generates day-by-day travel itinerary
    - hotel_recommender: Suggests hotels based on itinerary (always runs)
    - activity_finder: Suggests categorized activities (optional)
    """
    
    # Initialize the state graph
    workflow = StateGraph(TravelState)
    
    # Add nodes
    workflow.add_node("visa_agent", visa_agent)
    workflow.add_node("weather_agent", weather_agent)
    workflow.add_node("itinerary_builder", itinerary_builder)
    workflow.add_node("hotel_recommender", hotel_recommender)
    workflow.add_node("activity_finder", activity_finder)
    
    # Define the workflow edges
    # Start with visa information
    workflow.set_entry_point("visa_agent")
    
    # Visa agent goes to weather agent
    workflow.add_edge("visa_agent", "weather_agent")
    
    # Weather agent goes to itinerary builder
    workflow.add_edge("weather_agent", "itinerary_builder")
    
    # Itinerary builder always goes to hotel recommender
    workflow.add_edge("itinerary_builder", "hotel_recommender")
    
    # Add conditional logic for activity finder
    def should_find_activities(state: TravelState) -> str:
        """
        Determines if we should proceed to activity finding based on user preference.
        Returns next node name or END.
        """
        if state.get("include_activities", False):
            return "activity_finder"
        return END
    
    # Add conditional edge from hotel_recommender
    workflow.add_conditional_edges(
        "hotel_recommender",
        should_find_activities,
        {
            "activity_finder": "activity_finder",
            END: END
        }
    )
    
    # Activity finder always goes to END
    workflow.add_edge("activity_finder", END)
    
    return workflow


def compile_workflow() -> StateGraph:
    """
    Compiles and returns the travel planning workflow.
    """
    workflow = create_travel_workflow()
    return workflow.compile()


def run_travel_planning(state: TravelState) -> Dict[str, Any]:
    """
    Runs the complete travel planning workflow.
    
    Args:
        state: Initial travel state with user preferences
        
    Returns:
        Final state with generated itinerary and optional activities
    """
    app = compile_workflow()
    result = app.invoke(state)
    return result