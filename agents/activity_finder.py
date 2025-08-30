# agents/activity_finder.py

from typing import Dict, Any, List
from datetime import datetime
from llms.llm_provider import get_llm
from state.travel_state import TravelState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage


def activity_finder(state: TravelState) -> Dict[str, Any]:
    llm = get_llm(provider="groq", temperature=0.7)

    # Extract fields
    destination = state["destination"]
    budget = state["budget_type"]
    trip_type = state["trip_type"]
    num_people = state["num_people"]
    start_date = state["start_date"]
    end_date = state["end_date"]
    interests = [trip_type] + state.get("additional_comments", "").split(",")
    
    trip_nights = (end_date - start_date).days

    # Activity finder prompt
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            content="You are a local activities expert and cultural guide. "
                    "Your job is to curate authentic, diverse activities across multiple categories. "
                    "Focus on experiences that locals would recommend, not just tourist traps. "
                    "Consider the traveler's budget, group size, and interests when making suggestions. "
                    "Provide practical details like approximate costs, duration, and best times to visit."
        ),
        HumanMessage(
        content=
        f"Destination: {destination}\n"
        f"Trip Duration: {trip_nights} days\n"
        f"Group Size: {num_people} people\n"
        f"Budget Level: {budget}\n"
        f"Trip Style: {trip_type}\n"
        f"Additional Interests: {', '.join([i.strip() for i in interests if i.strip()]) or 'general exploration'}\n\n"
        "Please suggest 2–3 curated activity ideas per category, grouped under the following:\n"
        "- History & Culture\n"
        "- Food & Dining\n"
        "- Hidden Gems\n"
        "- Outdoor & Activities\n"
        "- Shopping & Local Markets\n"
        "- Nightlife & Entertainment\n\n"
        "**Important formatting rules:**\n"
        "- Do NOT use tables.\n"
        "- Present each category as a Markdown header (e.g., ## History & Culture).\n"
        "- For each activity, use a short bullet point with:\n"
        "  • A clear title\n"
        "  • Short description (~2 sentences)\n"
        "  • Estimated cost and ideal time to visit (in parentheses)\n"
        "- End each section with a single **🤖 My Recommendation** based on group size and trip goals.\n"
        "- Avoid overwhelming lists. Focus on local authenticity, budget fit, and variety.\n"
        "- No HTML. Use clean Markdown only.\n\n"
        "Ensure the tone is warm, local-savvy, and informative."
    )
    ])

    messages = prompt.format_messages()
    result = llm.invoke(messages)

    return {
        "suggested_activities": result.content
    }