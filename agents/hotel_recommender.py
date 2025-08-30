# agents/hotel_recommender.py

from typing import Dict, Any, List
import os
import json
from amadeus import Client, ResponseError
from llms.llm_provider import get_llm
from state.travel_state import TravelState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage


def hotel_recommender(state: TravelState) -> Dict[str, Any]:
    """
    Recommends hotels based on destination, itinerary, and user preferences.
    Uses Amadeus Hotel List API for real hotel data.
    """
    
    # Initialize Amadeus client
    try:
        amadeus = Client(
            client_id=os.getenv('AMADEUS_CLIENT_ID'),
            client_secret=os.getenv('AMADEUS_CLIENT_SECRET'),
            hostname='test'  # Use 'production' for live API
        )
    except Exception as e:
        print(f"Failed to initialize Amadeus client: {e}")
        return {"suggested_hotels": "Unable to fetch hotel recommendations. Please check API credentials."}
    
    # Extract fields
    destination = state["destination"]
    budget = state["budget_type"]
    trip_type = state["trip_type"]
    num_people = state["num_people"]
    start_date = state["start_date"]
    end_date = state["end_date"]
    itinerary = state.get("itinerary", "")
    
    trip_nights = (end_date - start_date).days
    
    # Get LLM for intelligent recommendations
    llm = get_llm(provider="groq", temperature=0.5)
    
    def fetch_hotels_for_location(location: str) -> List[Dict]:
        """Fetch hotels from Amadeus API for a specific location"""
        try:
            # Search for hotels by keyword/city
            response = amadeus.reference_data.locations.hotels.by_city.get(
                cityCode=location[:4].upper(),  # Use first 4 chars as city code approximation
                radius=50,
                radiusUnit='KM',
                hotelSource='ALL'
            )
            
            hotels = []
            for hotel in response.data[:10]:  # Limit to 10 hotels
                hotels.append({
                    'name': hotel.get('name', 'Unknown Hotel'),
                    'location': hotel.get('address', {}).get('cityName', location),
                    'hotel_id': hotel.get('hotelId', ''),
                    'chain_code': hotel.get('chainCode', ''),
                    'distance': hotel.get('distance', {}).get('value', 0)
                })
            return hotels
            
        except ResponseError as error:
            print(f"Amadeus API error for {location}: {error}")
            return []
        except Exception as e:
            print(f"Error fetching hotels for {location}: {e}")
            return []
    
    # Try to fetch real hotel data
    hotel_data = fetch_hotels_for_location(destination)
    
    # Create hotel recommendation prompt
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            content="You are an expert hotel concierge and travel advisor. "
                   "Your job is to recommend the most suitable hotels based on the traveler's "
                   "destination, itinerary, budget, and preferences. Consider location convenience, "
                   "transportation links, and proximity to planned activities. "
                   "Provide practical advice about different areas to stay."
        ),
        HumanMessage(
            content=f"""
**Trip Details:**
- Destination: {destination}
- Duration: {trip_nights} nights
- Group Size: {num_people} people
- Budget Level: {budget}
- Trip Style: {trip_type}

**Itinerary Context:**
{itinerary[:500] + '...' if len(itinerary) > 500 else itinerary}

**Available Hotels (from Amadeus API):**
{json.dumps(hotel_data, indent=2) if hotel_data else "No real-time hotel data available"}

**Instructions:**
Please recommend 2-3 hotels that would be ideal for this traveler, considering:

1. **Location Strategy**: Should they stay in one central location or split between areas?
2. **Budget Alignment**: Hotels that match their {budget} budget level
3. **Convenience**: Proximity to planned activities and transportation
4. **Group Size**: Suitable room configurations for {num_people} people

**Format your response as:**

## 🏨 Hotel Recommendations

### Hotel Option 1: [Hotel Name]
- **Location**: [Area/District]
- **Why Perfect**: [2-3 sentences explaining fit]
- **Budget**: [Price range for {budget} travelers]
- **Booking Tip**: [Practical advice]

### Hotel Option 2: [Hotel Name]
- **Location**: [Area/District] 
- **Why Perfect**: [2-3 sentences explaining fit]
- **Budget**: [Price range for {budget} travelers]
- **Booking Tip**: [Practical advice]

### Hotel Option 3: [Hotel Name] (if multi-city or long stay)
- **Location**: [Area/District]
- **Why Perfect**: [2-3 sentences explaining fit] 
- **Budget**: [Price range for {budget} travelers]
- **Booking Tip**: [Practical advice]

## 🗺️ Location Strategy
[Brief explanation of recommended approach - central vs. multiple locations]

Use the real hotel data when available, but supplement with your knowledge for complete recommendations.
"""
        )
    ])
    
    try:
        messages = prompt.format_messages()
        result = llm.invoke(messages)
        
        print("==== HOTEL RECOMMENDER RAW LLM RESPONSE ====")
        print(result.content)
        print("==== AMADEUS DATA USED ====")
        print(f"Found {len(hotel_data)} hotels from API")
        print("==== LENGTH:", len(result.content))
        
        return {
            "suggested_hotels": result.content
        }
        
    except Exception as e:
        print(f"Error in hotel recommendation: {e}")
        return {
            "suggested_hotels": f"Hotel recommendations temporarily unavailable. Please try again later. (Error: {str(e)})"
        }