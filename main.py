from fastapi import FastAPI, HTTPException
import httpx
import math
import logging

# Configure logging
logging.basicConfig(
    filename="app.log",  # Log file
    level=logging.INFO,  # Log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
)

app = FastAPI()

# API key and base URL
GOMAPS_API_KEY = "AlzaSyvEif8PdUawsmvO1LdYw5QhxmqIildPweW"
GOMAPS_BASE_URL = "https://maps.gomaps.pro/maps/api/place/"

# Weatherstack API Key and Base URL
WEATHERSTACK_API_KEY = "bb678e9df166890112ea56d745435a98"
WEATHERSTACK_BASE_URL = "http://api.weatherstack.com/current"

#Get_weather func will return weather details in dictionary
async def get_weather(lat: float, lon: float) -> dict:
    # Constructing the query for Weatherstack API
    query = f"{lat},{lon}"
    url = f"{WEATHERSTACK_BASE_URL}?access_key={WEATHERSTACK_API_KEY}&query={query}"

    async with httpx.AsyncClient() as client:
        try:
            # Sending the GET request
            response = await client.get(url)
            response.raise_for_status()
            weather_data = response.json()

            # Check if the response contains the expected data
            if "current" in weather_data:
                return {
                    "temperature": weather_data["current"]["temperature"],
                    "description": weather_data["current"]["weather_descriptions"][0],
                    "humidity": weather_data["current"]["humidity"],
                    "wind_speed": weather_data["current"]["wind_speed"],
                    "city": weather_data.get("location", {}).get("name", "Unknown location"),
                }
            else:
                logging.error(f"Unexpected API response: {weather_data}")
                return {"error": "Unable to fetch weather details. Please check the API response."}

        except httpx.RequestError as e:
            logging.error(f"Error connecting to Weatherstack API: {e}")
            return {"error": "Unable to fetch weather details due to a connection issue."}
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error from Weatherstack API: {e.response.status_code}")
            return {"error": f"Error from weather service: {e.response.status_code}"}


# Function to calculate distance between two lat/lon points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in km
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.post("/webhook")
async def handle_webhook(request: dict):
    # Extracting intent name and parameters from the request
    intent_name = request["queryResult"]["intent"]["displayName"]
    lat = request["queryResult"]["parameters"].get("lat")
    lon = request["queryResult"]["parameters"].get("lon")
    location_type = request["queryResult"]["parameters"].get("place_type", "").lower()

    # Log the intent and input parameters
    logging.info(f"Intent: {intent_name}, Latitude: {lat}, Longitude: {lon}, Location Type: {location_type}")

    try:
        if lat and lon:
            lat = float(lat)
            lon = float(lon)
        else:
            logging.warning("Missing or invalid latitude/longitude parameters.")
            return {"fulfillmentText": "Please provide valid latitude and longitude coordinates."}
    except ValueError:
        logging.error(f"Invalid latitude or longitude values: lat={lat}, lon={lon}")
        return {"fulfillmentText": "Invalid latitude or longitude values."}

    # Handle intent: Yes_coordinates_know
    if intent_name == "Yes_coordinates_know":
        #won't be excuted
        if not location_type:
            logging.warning("Missing location type parameter.")
            return {"fulfillmentText": "Please provide a location type to search for nearby places."}

        url = f"{GOMAPS_BASE_URL}nearbysearch/json?location={lat},{lon}&radius=5000&key={GOMAPS_API_KEY}&limit=10"

        # Log the API request
        logging.info(f"Sending request to GoMaps API: {url.replace(GOMAPS_API_KEY, '[API_KEY]')}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                locations = response.json().get("results", [])
                logging.info(f"API response received: {response.status_code}")
            except httpx.RequestError as e:
                logging.error(f"Request error: {e}")
                return {"fulfillmentText": "Sorry, there was an issue connecting to the location service. Please try again later."}
            except httpx.HTTPStatusError as e:
                logging.error(f"HTTP status error: {e.response.status_code}")
                return {"fulfillmentText": f"Error from location service: {e.response.status_code}. Please try again later."}

        # Process and format the locations
        nearby_locations = []
        matched_nearby_locations = []
        for loc in locations:
            loc_lat = loc.get("geometry", {}).get("location", {}).get("lat")
            loc_lon = loc.get("geometry", {}).get("location", {}).get("lng")
            loc_type = loc.get("types", [])

            if loc_lat and loc_lon:
                distance = haversine(lat, lon, loc_lat, loc_lon)
                location_name = loc.get("name", "Unnamed location")
                address = loc.get("vicinity", "No address available")
                maps_link = f"https://www.google.com/maps?q={loc_lat},{loc_lon}"

                nearby_locations.append(
                    f"Name: {location_name}\n"
                    f"Address: {address}\n"
                    f"Distance: {distance:.2f} km\n"
                    f"Google Maps: {maps_link}\n"
                )

                for type_of_loc in loc_type:
                    if location_type == type_of_loc:
                        matched_nearby_locations.append(
                            f"Name: {location_name}\n"
                            f"Address: {address}\n"
                            f"Distance: {distance:.2f} km\n"
                            f"Google Maps: {maps_link}\n"
                            )

        if not matched_nearby_locations:
            matched_nearby_locations.append("No places matched your preferred type. Please try again with a different type.")
        else:
            preferred_loc_list = "\n\n".join(matched_nearby_locations)
            return {"fulfillmentText": f"Places that matched your Preferred type:\n\n{preferred_loc_list}\n\n"}

        location_list = "\n\n".join(nearby_locations)
        preferred_loc_list = "\n\n".join(matched_nearby_locations)
        return {"fulfillmentText": f"Nearby places within 5 km:\n\n{location_list}\n\nPlaces that Matched your Preferred type:\n\n{preferred_loc_list}\n\n"}

    # Handle intent: proceed_intent_for_weather
    elif intent_name == "proceed_intent_for_weather":
        weather_details = await get_weather(lat, lon)

        if "error" in weather_details:
            return {"fulfillmentText": weather_details["error"]}

        weather_info = (
            f"Weather Details for Your Location:\n"
            f"Temperature: {weather_details['temperature']}°C\n"
            f"Weather: {weather_details['description']}\n"
            f"Humidity: {weather_details['humidity']}%\n"
            f"Wind Speed: {weather_details['wind_speed']} m/s\n"
            f"City: {weather_details['city']}\n"
        )
        return {"fulfillmentText": weather_info}

    # Default response for unknown intents
    logging.warning(f"Unhandled intent: {intent_name}")
    return {"fulfillmentText": "Sorry, I couldn't understand your request. Please try again."}

