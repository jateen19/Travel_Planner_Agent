# state/travel_state.py

from typing import TypedDict, Literal, Optional, List
from datetime import date

TripType = Literal["adventure", "cultural", "romantic", "family", "solo"]
BudgetType = Literal["budget", "mid-range", "luxury"]

class TravelState(TypedDict, total=False):
    # User Input
    origin_country: str
    destination: str
    budget_type: BudgetType
    trip_type: TripType
    num_people: int
    start_date: date
    end_date: date
    additional_comments: Optional[str]
    include_activities: Optional[bool]

    # System-generated intermediate states
    suggested_hotels: Optional[str]
    suggested_activities: Optional[str]
    itinerary: Optional[str]
    packing_tips: Optional[str]
    visa_info: Optional[str]
    weather_forecast: Optional[str]

    # Metadata or internal flags
    trip_duration_days: Optional[int]
    error: Optional[str]
