# Add a get_visa_requirements(country) tool, ask about an intl. trip.
# MEDIUM  Replace the mock weather with a real API call using `requests`
#         (same pattern as shivank2/01_function_to_tool.py).
# MEDIUM  Regroup the three tools into a TravelTools class with shared state
#         (see shivank2/08_class_based_tools.py).
# HARDER  Make the weather + cost lookups async so a multi-city comparison
#         runs in parallel (see shivank2/09_async_tools.py).
# HARDER  Add file_write from strands_tools and have the agent save an
#         itinerary to disk.
# ----------------------------------------------------------------------------------------------------

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from dotenv import load_dotenv
from strands_tools import calculator
from config import MODEL_ID
import requests

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
@tool
def get_weather_forecast(city: str, days: int) -> dict:
    """Get the weather forecast for a city over a number of days.

    Args:
        city: Destination city name (e.g., "Goa", "Bangalore")
        days: Number of days in the trip
    """
    # OpenWeatherMap 5-day / 3-hour forecast endpoint
    url = "https://api.openweathermap.org/data/2.5/forecast"
    
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"  # Ensures temperature returns in Celsius 
    }
    
    try:
        # Make the live HTTP GET request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Crashes safely if city name doesn't exist or API key fails
        weather_data = response.json()
        
        # Parse out the required metrics from the API JSON response
        # Since this returns a 5-day timeline, we check the first available slot
        forecast_list = weather_data.get("list", [])
        
        # If the API returned an empty list, fail gracefully to default data
        if not forecast_list:
            raise ValueError("No forecast data returned in the list.")
            
        # We calculate the total number of 3-hour slots to evaluate based on the trip length
        # (Each day has 8 slots of 3 hours. We cap it at the length of the list)
        slots_to_check = min(days * 8, len(forecast_list))
        
        # Initialize tracking variables with the very first slot's metrics
        absolute_high = forecast_list[0]["main"]["temp_max"]
        absolute_low = forecast_list[0]["main"]["temp_min"]
        
        # Collect descriptive conditions strings into a list
        all_conditions = []
        
        # Loop through the timeframe to pinpoint the true mathematical high/low values
        for i in range(slots_to_check):
            slot = forecast_list[i]
            
            if slot["main"]["temp_max"] > absolute_high:
                absolute_high = slot["main"]["temp_max"]
                
            if slot["main"]["temp_min"] < absolute_low:
                absolute_low = slot["main"]["temp_min"]
                
            desc = slot["weather"][0]["description"]
            if desc not in all_conditions:
                all_conditions.append(desc)
        
        # Combine the distinct weather descriptions into a readable sentence
        summary_conditions = ", ".join(all_conditions[:3])
        
        return {
            "city": city,
            "days": days,
            "high_c": round(absolute_high),
            "low_c": round(absolute_low),
            "conditions": summary_conditions
        }
        
    except Exception as e:
        # Fallback graceful default if the network goes down or the API fails
        print(f"⚠️ API Error ({e}). Falling back to default weather metrics.")
        return {
            "city": city,
            "days": days,
            "high_c": 28,
            "low_c": 20,
            "conditions": "moderate cloud cover"
        }
    

@tool
def suggest_packing_list(high_c: int, low_c: int, days: int, conditions: str) -> list:
    """Suggest what to pack based on temperatures, trip length and conditions.

    Args:
        high_c: Daytime high in Celsius
        low_c: Night-time low in Celsius
        days: Number of days in the trip
        conditions: Short description of expected weather
    """
    items = [f"{days + 1} sets of clothes", "toiletries", "phone charger"]

    if high_c >= 30:
        items += ["light cotton clothing", "sunscreen", "sunglasses", "reusable water bottle"]
    if low_c <= 15:
        items += ["warm jacket", "thermal layer"]
    elif low_c <= 22:
        items += ["light jacket for evenings"]
    if "rain" in conditions.lower() or "shower" in conditions.lower():
        items += ["compact umbrella", "quick-dry footwear"]
    if "snow" in conditions.lower():
        items += ["gloves", "woollen cap", "waterproof boots"]

    return items


@tool
def estimate_trip_cost(city: str, days: int, travellers: int = 1) -> dict:
    """Estimate the cost of a trip in Indian rupees.

    Args:
        city: Destination city
        days: Number of days
        travellers: Number of people travelling (default: 1)
    """
    per_night = {"goa": 3500, "bangalore": 3000, "jaipur": 2500, "manali": 2800}
    stay = per_night.get(city.lower(), 3000) * days
    food = 1200 * days * travellers
    local_travel = 800 * days
    total = stay + food + local_travel

    return {
        "city": city,
        "days": days,
        "travellers": travellers,
        "stay_inr": stay,
        "food_inr": food,
        "local_travel_inr": local_travel,
        "total_inr": total,
    }


agent = Agent(
    model=BedrockModel(model_id=MODEL_ID),
    tools=[get_weather_forecast, suggest_packing_list, estimate_trip_cost, calculator],
    system_prompt=(
        "You are a practical travel assistant. "
        "When asked about a trip: Answer precisely for the question. "
        "Do not call tools which are not required for the task"
    ),
)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = (
            "I'm going to Goa on 10th of this month for one week. "
            "what is the weather on that day?"
        )

    print(f"\nQuestion: {question}\n" + "-" * 130)
    response = agent(question)