# agents/itinerary_builder.py

from typing import Dict, Any
from datetime import datetime
from llms.llm_provider import get_llm
from state.travel_state import TravelState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage


def itinerary_builder(state: TravelState) -> Dict[str, Any]:
    llm = get_llm(provider="groq", temperature=0.7)

    # Extract fields
    destination = state["destination"]
    budget = state["budget_type"]
    trip_type = state["trip_type"]
    num_people = state["num_people"]
    start_date = state["start_date"]
    end_date = state["end_date"]
    interests = [trip_type] + state.get("additional_comments", "").split(",")
    origin = "user's home city"  # Optional, can be extended

    trip_nights = (end_date - start_date).days

    # Prompt setup using your template
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            content="You are a meticulous, local-savvy travel planner. "
                    "Create realistic, walkable, day-by-day itineraries that minimize backtracking by clustering nearby sights "
                    "and using public transport where sensible. Respect opening hours, include approximate durations and buffers, "
                    "and avoid overpacking days. Include at least ~1 hour of downtime daily. "
                    "If something is closed, suggest an alternative nearby."
        ),
        HumanMessage(
    content=
    f"Trip Summary:\n"
    f"- Route: {origin} → {destination}\n"
    f"- Dates: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}  •  Nights: {trip_nights}\n"
    f"- Party size: {num_people}\n"
    f"- Budget: {budget}\n"
    f"- Interests: {', '.join([i.strip() for i in interests if i.strip()]) or 'general sightseeing'}\n\n"
    "Instructions:\n"
    "- Use the following scaffold EXACTLY. Fill in the bullets under each day; do not add or remove days.\n"
    "- Each day must include:\n"
    "  (1) Morning\n"
    "  (2) Afternoon\n"
    "  (3) Evening\n"
    "  (4) Dining\n"
    "  (5) Downtime (~1 hr)\n"
    "- Try to cluster by neighborhood each day to reduce transit time. Mention brief transit hints.\n"
    "- Add specific examples (e.g., museum/gallery/park names) and a short reason why they fit.\n"
    "- Keep the tone concise and practical. Avoid flowery language.\n\n"
    f"This trip spans **{trip_nights} days**.\n"
    f"You MUST generate **exactly {trip_nights} complete days**, clearly labeled as:\n\n"
    f"**Day 1 (Weekday, Month Day, Year)**\n...\n**Day {trip_nights} (Weekday, Month Day, Year)**\n\n"
    "⚠️ If you stop before all days are complete, the output will be rejected. Do not stop early."
)
    ])


    messages = prompt.format_messages()
    result = llm.invoke(messages)

    return {
        "itinerary": result.content
    }
