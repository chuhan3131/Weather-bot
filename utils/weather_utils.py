import httpx
import aiohttp
import structlog
from datetime import datetime, timezone, timedelta
from config import (
    CACHE_TTL,
    OPENWEATHERMAP_BASE_URL,
    OPENWEATHERMAP_API_KEY,
    REQUEST_TIMEOUT,
)


logger = structlog.getLogger(__name__)

# Cache for weather data
weather_cache = {}


def wind_direction(deg):
    """Determining wind direction"""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[round(deg / 45) % 8]


async def get_location_async(ip):
    """Asynchronous location retrieval by IP"""
    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"http://ip-api.com/json/{ip}") as response:
                data = await response.json()
                if data["status"] == "success":
                    return data["city"], data["countryCode"]
                return None, None
    except Exception as ex:
        logger.error(
            "Error getting location for IP",
            ip=ip,
            caught_exception=(repr(ex), str(ex)),
            exc_info=True,
        )
        return None, None


def translate_description(description):
    """Translate weather description to English if needed"""
    # This is a simple translation dictionary. You might want to expand it
    # or use a proper translation service
    translations = {
        "ясно": "clear",
        "малооблачно": "few clouds",
        "облачно": "cloudy",
        "пасмурно": "overcast",
        "небольшой дождь": "light rain",
        "дождь": "rain",
        "ливень": "shower",
        "гроза": "thunderstorm",
        "снег": "snow",
        "туман": "fog",
        "дымка": "haze",
    }
    
    # Check if description is in Russian (Cyrillic characters)
    has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in description)
    
    if has_cyrillic:
        # Try to translate
        lower_desc = description.lower()
        for rus, eng in translations.items():
            if rus in lower_desc:
                return eng.capitalize()
        # If no translation found, return as is or use a fallback
        return description
    
    return description


def process_weather_data(data):
    """Processing weather data"""
    if data.get("cod") != 200:
        return None

    main = data["main"]
    weather = data["weather"][0]
    wind = data["wind"]
    sys = data["sys"]

    timezone_offset = data.get("timezone", 0)
    sunrise_utc = sys["sunrise"]
    sunset_utc = sys["sunset"]

    sunrise_local = sunrise_utc + timezone_offset
    sunset_local = sunset_utc + timezone_offset

    sunrise_str = datetime.fromtimestamp(sunrise_local).strftime("%H:%M")
    sunset_str = datetime.fromtimestamp(sunset_local).strftime("%H:%M")

    current_time_utc = datetime.now(timezone.utc)
    current_time_local = current_time_utc + timedelta(seconds=timezone_offset)

    # Get weather description and translate if needed
    description = weather["description"]
    
    result = {
        "city": data["name"],  # OpenWeatherMap returns city names in English when lang=en
        "country": sys["country"],
        "temp": main["temp"],
        "feels_like": main["feels_like"],
        "humidity": main["humidity"],
        "pressure": round(main["pressure"] * 0.750062),
        "wind_speed": wind["speed"],
        "wind_dir": wind_direction(wind["deg"]) if 'deg' in wind else "N/A",
        "description": description,
        "sunrise": sunrise_str,
        "sunset": sunset_str,
        "timezone_offset": timezone_offset,
        "current_time_local": current_time_local,
    }

    logger.debug(
        "Weather received",
        city_name=data["name"],
        temperature=result["temp"],
        description=result["description"],
    )
    return result


async def get_current_weather_async(city, country_code=None):
    """Asynchronous weather retrieval with caching"""
    cache_key = f"{city}_{country_code}" if country_code else city

    # Check cache
    if cache_key in weather_cache:
        cache_data, timestamp = weather_cache[cache_key]
        if (datetime.now().timestamp() - timestamp) < CACHE_TTL:
            logger.debug("Cached value used", city=city)
            return cache_data

    try:
        query = f"{city},{country_code}" if country_code else city
        url = "/data/2.5/weather"

        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            verify=False,
            base_url=OPENWEATHERMAP_BASE_URL,
        ) as client:
            params = {
                "q": query,
                "units": "metric",
                "APPID": OPENWEATHERMAP_API_KEY,
                "lang": "en",  # Changed from "ru" to "en" for English descriptions
            }
            response = await client.get(url, params=params)
            logger.debug(
                "received response from openweathermap", content=response.content
            )
            data = response.json()
            weather_data = process_weather_data(data)

            # Saving to cache
            if weather_data:
                weather_cache[cache_key] = (
                    weather_data,
                    datetime.now().timestamp(),
                )
                # Clearing old cache
                if len(weather_cache) > 100:
                    oldest_key = next(iter(weather_cache))
                    weather_cache.pop(oldest_key)

            return weather_data

    except Exception as ex:
        logger.error(
            "Error getting weather",
            city=city,
            caught_exception=(repr(ex), str(ex)),
            exc_info=True,
        )
        return None