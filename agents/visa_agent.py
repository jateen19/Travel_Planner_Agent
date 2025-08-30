# agents/visa_agent.py

from typing import Dict, Any
from llms.llm_provider import get_llm
from state.travel_state import TravelState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage


def visa_agent(state: TravelState) -> Dict[str, Any]:
    llm = get_llm(provider="groq", temperature=0.3)

    # Extract fields
    origin_country = state["origin_country"]
    destination = state["destination"]

    VISA_SYSTEM_PROMPT = """
You are a helpful travel visa assistant.
Your task is to provide concise visa eligibility information for tourist travel only.

Given an origin country and a destination country, return the one or two easiest ways the traveler can be eligible to enter the destination.

If no visa is required, clearly state that and mention the allowed duration of stay.

If visa on arrival or eVisa is available, mention that, including how early to apply (if needed).

Include brief and practical tips, such as passport validity requirements, proof of return ticket, or travel insurance.

Respond in a clear and concise format (2–5 sentences max).
Focus only on tourism entry, not work, study, or immigration.
"""

    # Visa information prompt
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=VISA_SYSTEM_PROMPT),
        HumanMessage(
            content=f"I am traveling from {origin_country} to {destination} for tourism purposes. "
                   f"What are the visa requirements and entry procedures I need to know about?"
        )
    ])

    messages = prompt.format_messages()
    result = llm.invoke(messages)

    print("==== VISA AGENT RAW LLM RESPONSE ====")
    print(result.content)
    print("==== LENGTH:", len(result.content))

    return {
        "visa_info": result.content
    }