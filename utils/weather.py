import httpx
from datetime import datetime, timezone, timedelta
import re
from typing import Any, Dict, Tuple, Optional

from config import (
    CACHE_TTL,
    OPENWEATHERMAP_BASE_URL,
    OPENWEATHERMAP_API_KEY,
    REQUEST_TIMEOUT,
)
from utils.logger import logger


weather_cache = {}


def detect_language(text: str) -> str:
    has_cyrillic = bool(re.search(r'[а-яА-ЯёЁ]', text))
    
    if has_cyrillic:
        return "ru"
    has_latin = bool(re.search(r'[a-zA-Z]', text))

    return "en"


def wind_direction(deg: float) -> str:
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[round(deg / 45) % 8]


async def get_location(ip: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        timeout = httpx.Timeout(REQUEST_TIMEOUT)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"http://ip-api.com/json/{ip}")
            data = response.json()

            if data["status"] == "success":
                return data["city"], data["countryCode"]
            return None, None

    except httpx.HTTPError as ex:
        logger.error("HTTP error getting location for IP")
        return None, None

    except Exception as ex:
        logger.error("Error getting location for IP")
        return None, None


def get_description(description: str, target_lang: str = "en") -> str:
    translations_ru_to_en = {
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
        "легкий дождь": "light rain",
        "умеренный дождь": "moderate rain",
        "сильный дождь": "heavy rain",
        "легкий снег": "light snow",
        "снегопад": "snowfall",
    }
    
    translations_en_to_ru = {v: k for k, v in translations_ru_to_en.items()}
    
    if target_lang == "en":
        has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in description)
        if has_cyrillic:
            lower_desc = description.lower()
            for rus, eng in translations_ru_to_en.items():
                if rus in lower_desc:
                    return eng.capitalize()
    
    elif target_lang == "ru":
        lower_desc = description.lower()
        for eng, rus in translations_en_to_ru.items():
            if eng in lower_desc:
                return rus.capitalize()
    
    return description.capitalize()


def parse_weather_response(data: Dict[str, Any], lang: str = "en") -> Optional[Dict[str, Any]]:
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

    description = weather["description"]

    if lang != "en": 
        description = get_description(description, target_lang=lang)
    elif lang == "en": 
        description = get_description(description, target_lang="en")

    wind_dir_translations = {
        "N": "С", "NE": "СВ", "E": "В", "SE": "ЮВ",
        "S": "Ю", "SW": "ЮЗ", "W": "З", "NW": "СЗ"
    }
    
    wind_dir = wind_direction(wind["deg"]) if 'deg' in wind else "N/A"
    if lang == "ru" and wind_dir in wind_dir_translations:
        wind_dir = wind_dir_translations[wind_dir]

    result = {
        "city": data["name"],
        "country": sys["country"],
        "temp": main["temp"],
        "feels_like": main["feels_like"],
        "humidity": main["humidity"],
        "pressure": round(main["pressure"] * 0.750062),
        "wind_speed": wind["speed"],
        "wind_dir": wind_dir,
        "description": description,
        "sunrise": sunrise_str,
        "sunset": sunset_str,
        "timezone_offset": timezone_offset,
        "current_time_local": current_time_local,
        "lang": lang,
    }

    logger.debug("Weather received")
    return result


async def fetch_weather_data(
    city: str, 
    country_code: Optional[str] = None, 
    lang: str = "en"
) -> Optional[Dict[str, Any]]:
    cache_key = f"{city}_{country_code}_{lang}" if country_code else f"{city}_{lang}"

    if cache_key in weather_cache:
        cache_data, timestamp = weather_cache[cache_key]
        if (datetime.now().timestamp() - timestamp) < CACHE_TTL:
            logger.debug("Cached value used")
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
                "lang": lang, 
            }
            response = await client.get(url, params=params)
            logger.debug("Received response from openweathermap")
            data = response.json()
            weather_data = parse_weather_response(data, lang)

            if weather_data:
                weather_cache[cache_key] = (
                    weather_data,
                    datetime.now().timestamp(),
                )
                if len(weather_cache) > 100:
                    oldest_key = next(iter(weather_cache))
                    weather_cache.pop(oldest_key)

            return weather_data

    except Exception as ex:
        logger.error("Error getting weather")
        return None