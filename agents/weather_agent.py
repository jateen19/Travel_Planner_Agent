# agents/weather_agent.py

from typing import Dict, Any, List, Tuple
import requests
import json
from datetime import datetime, timedelta
from llms.llm_provider import get_llm
from state.travel_state import TravelState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage


def weather_agent(state: TravelState) -> Dict[str, Any]:
    """
    Provides weather forecast based on destination and travel dates.
    Uses OpenMeteo API for real-time and historical data.
    """
    
    # Extract fields
    destination = state["destination"]
    start_date = state["start_date"]
    end_date = state["end_date"]
    trip_type = state["trip_type"]
    
    # Get LLM for intelligent weather analysis
    llm = get_llm(provider="groq", temperature=0.4)
    
    def get_coordinates(location: str) -> Tuple[float, float]:
        """Get coordinates for a location using OpenMeteo geocoding"""
        try:
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            response = requests.get(geocoding_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                result = data["results"][0]
                return float(result["latitude"]), float(result["longitude"])
            else:
                print(f"No coordinates found for {location}")
                return None, None
                
        except Exception as e:
            print(f"Error getting coordinates for {location}: {e}")
            return None, None
    
    def get_weather_data(lat: float, lon: float, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch weather data from OpenMeteo API"""
        try:
            # Determine if we need forecast or historical data
            today = datetime.now().date()
            is_future = start_date > today
            
            if is_future:
                # Use forecast API
                url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": lat,
                    "longitude": lon,
                    "daily": [
                        "temperature_2m_max", 
                        "temperature_2m_min", 
                        "precipitation_sum", 
                        "rain_sum",
                        "wind_speed_10m_max",
                        "weather_code"
                    ],
                    "timezone": "auto",
                    "forecast_days": min(16, (end_date - today).days + 1)
                }
            else:
                # Use historical API
                url = "https://archive-api.open-meteo.com/v1/archive"
                params = {
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "daily": [
                        "temperature_2m_max", 
                        "temperature_2m_min", 
                        "precipitation_sum", 
                        "rain_sum",
                        "wind_speed_10m_max",
                        "weather_code"
                    ],
                    "timezone": "auto"
                }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return {}
    
    def interpret_weather_code(code: int) -> str:
        """Convert weather codes to descriptions"""
        codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
            55: "Dense drizzle", 56: "Light freezing drizzle", 57: "Dense freezing drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 66: "Light freezing rain",
            67: "Heavy freezing rain", 71: "Slight snow fall", 73: "Moderate snow fall",
            75: "Heavy snow fall", 77: "Snow grains", 80: "Slight rain showers",
            81: "Moderate rain showers", 82: "Violent rain showers", 85: "Slight snow showers",
            86: "Heavy snow showers", 95: "Thunderstorm", 96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return codes.get(code, "Unknown weather")
    
    # Get coordinates for destination
    lat, lon = get_coordinates(destination)
    
    if not lat or not lon:
        return {
            "weather_forecast": f"Unable to get weather data for {destination}. Please check the destination name."
        }
    
    # Get weather data
    weather_data = get_weather_data(lat, lon, start_date, end_date)
    
    if not weather_data:
        return {
            "weather_forecast": f"Weather data temporarily unavailable for {destination}. Please try again later."
        }
    
    # Process weather data for LLM analysis
    daily_data = weather_data.get("daily", {})
    if not daily_data:
        return {
            "weather_forecast": f"No weather data available for the selected dates in {destination}."
        }
    
    # Format weather summary for LLM
    weather_summary = []
    dates = daily_data.get("time", [])
    max_temps = daily_data.get("temperature_2m_max", [])
    min_temps = daily_data.get("temperature_2m_min", [])
    precipitation = daily_data.get("precipitation_sum", [])
    wind_speeds = daily_data.get("wind_speed_10m_max", [])
    weather_codes = daily_data.get("weather_code", [])
    
    for i, date in enumerate(dates):
        if i < len(max_temps) and i < len(min_temps):
            day_info = {
                "date": date,
                "high": f"{max_temps[i]:.1f}°C" if max_temps[i] else "N/A",
                "low": f"{min_temps[i]:.1f}°C" if min_temps[i] else "N/A",
                "precipitation": f"{precipitation[i]:.1f}mm" if i < len(precipitation) and precipitation[i] else "0mm",
                "wind": f"{wind_speeds[i]:.1f}km/h" if i < len(wind_speeds) and wind_speeds[i] else "N/A",
                "condition": interpret_weather_code(weather_codes[i]) if i < len(weather_codes) else "Unknown"
            }
            weather_summary.append(day_info)
    
    # Create weather analysis prompt
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            content="You are a knowledgeable meteorologist and travel advisor. "
                   "Analyze weather data and provide practical travel advice. "
                   "Focus on what travelers should expect, pack, and plan for. "
                   "Consider the trip type and provide activity recommendations based on weather conditions."
        ),
        HumanMessage(
            content=f"""
**Trip Details:**
- Destination: {destination}
- Travel Dates: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}
- Trip Type: {trip_type}

**Weather Data:**
{json.dumps(weather_summary, indent=2)}

**Instructions:**
Analyze this weather data and provide a comprehensive weather briefing formatted as:

## 🌤️ Weather Forecast for {destination}

### Overall Conditions
[2-3 sentence summary of general weather pattern during the trip]

### Daily Breakdown
[Highlight 2-3 key days with specific weather details]

### 🎒 Packing Recommendations
- **Essential Items**: [Based on weather conditions]
- **Optional Items**: [Weather-dependent gear]

### 📅 Activity Planning
- **Best Days For**: [Outdoor activities, sightseeing, etc.]
- **Indoor Backup Plans**: [For poor weather days]

### 🌡️ Temperature Guide
[Brief explanation of temperature range and clothing suggestions]

### ⚠️ Weather Alerts
[Any notable weather concerns or exceptional conditions]

Keep the tone helpful and practical. Focus on actionable advice for travelers.
"""
        )
    ])
    
    try:
        messages = prompt.format_messages()
        result = llm.invoke(messages)
        
        print("==== WEATHER AGENT RAW LLM RESPONSE ====")
        print(result.content)
        print("==== WEATHER DATA POINTS ====")
        print(f"Location: {destination} ({lat}, {lon})")
        print(f"Data points: {len(weather_summary)} days")
        print("==== LENGTH:", len(result.content))
        
        return {
            "weather_forecast": result.content
        }
        
    except Exception as e:
        print(f"Error in weather analysis: {e}")
        return {
            "weather_forecast": f"Weather analysis temporarily unavailable. Raw data available for {destination} from {start_date} to {end_date}."
        }