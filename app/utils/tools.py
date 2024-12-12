import requests
from langchain.tools import tool

@tool
def get_current_weather(latitude: float, longitude: float) -> str:
    """Get the current weather at a location
    
    :param latitude: The latitude coordinate of the location
    :type latitude: float
    :param longitude: The longitude coordinate of the location
    :type longitude: float
    """
    # Format the URL with proper parameter substitution
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m&hourly=temperature_2m&daily=sunrise,sunset&timezone=auto"

    try:
        # Make the API call
        response = requests.get(url)

        # Raise an exception for bad status codes
        response.raise_for_status()

        # Return the JSON response
        return response.json()

    except requests.RequestException as e:
        # Handle any errors that occur during the request
        print(f"Error fetching weather data: {e}")
        return None
