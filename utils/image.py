import time
import structlog
import asyncio
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Any, Dict
from datetime import datetime
import os
from utils.logger import logger


FONT_LARGE: Any = None
FONT_MEDIUM: Any = None
FONT_TEMP: Any = None
LIGHT_IMG: Any = None
DARK_IMG: Any = None
GLOBE_IMG: Any = None
LIGHT_EMOJI_CACHE: Dict[str, Image.Image] = {}
DARK_EMOJI_CACHE: Dict[str, Image.Image] = {}


def load_resources():
    global FONT_LARGE, FONT_MEDIUM, FONT_TEMP, LIGHT_IMG, DARK_IMG, GLOBE_IMG
    global LIGHT_EMOJI_CACHE, DARK_EMOJI_CACHE

    try:
        # Load fonts
        FONT_LARGE = ImageFont.truetype("assets/fonts/SF-Pro-Display-Medium.otf", 72)
        FONT_MEDIUM = ImageFont.truetype("assets/fonts/SF-Pro-Display-Medium.otf", 46.75)
        FONT_TEMP = ImageFont.truetype("assets/fonts/SF-Pro-Display-Medium.otf", 186.99)

        # Load both backgrounds: light for day, dark for night
        LIGHT_IMG = Image.open("assets/templates/light_temp.png").convert("RGBA")
        DARK_IMG = Image.open("assets/templates/dark_temp.png").convert("RGBA")
        GLOBE_IMG = Image.open("assets/templates/globe.png").convert("RGBA")

        # Load light emojis
        light_emoji_paths = {
            "sun": "assets/templates/weather_emoji/light/sun.png",
            "cloud": "assets/templates/weather_emoji/light/cloud.png",
            "rain": "assets/templates/weather_emoji/light/rain.png",
            "storm": "assets/templates/weather_emoji/light/storm.png",
            "snow": "assets/templates/weather_emoji/light/snow.png",
            "fog": "assets/templates/weather_emoji/light/fog.png",
            "sun_cloud": "assets/templates/weather_emoji/light/sun_cloud.png",
            "sun_cloud_rain": "assets/templates/weather_emoji/light/sun_cloud_rain.png",
            "thermometer": "assets/templates/weather_emoji/light/thermometer.png",
            "cyclone": "assets/templates/weather_emoji/light/cyclone.png",
            "dust": "assets/templates/weather_emoji/light/dust.png",
            "tornado": "assets/templates/weather_emoji/light/tornado.png",
        }

        # Load dark emojis
        dark_emoji_paths = {
            "moon": "assets/templates/weather_emoji/dark/moon.png",
            "cloud": "assets/templates/weather_emoji/dark/cloud.png",
            "rain": "assets/templates/weather_emoji/dark/rain.png",
            "storm": "assets/templates/weather_emoji/dark/storm.png",
            "snow": "assets/templates/weather_emoji/dark/snow.png",
            "fog": "assets/templates/weather_emoji/dark/fog.png",
            "moon_cloud": "assets/templates/weather_emoji/dark/moon_cloud.png",
            "moon_cloud_rain": "assets/templates/weather_emoji/dark/moon_cloud_rain.png",
            "thermometer": "assets/templates/weather_emoji/dark/thermometer.png",
            "cyclone": "assets/templates/weather_emoji/dark/cyclone.png",
            "dust": "assets/templates/weather_emoji/dark/dust.png",
            "tornado": "assets/templates/weather_emoji/dark/tornado.png",
        }

        # Load light emojis into cache
        for key, path in light_emoji_paths.items():
            if os.path.exists(path):
                LIGHT_EMOJI_CACHE[key] = Image.open(path).convert("RGBA")
            else:
                logger.warning(f"Light emoji file not found: {path}")

        # Load dark emojis into cache
        for key, path in dark_emoji_paths.items():
            if os.path.exists(path):
                DARK_EMOJI_CACHE[key] = Image.open(path).convert("RGBA")
            else:
                logger.warning(f"Dark emoji file not found: {path}")

        # Create default fallback emoji if thermometer is missing
        if "thermometer" not in LIGHT_EMOJI_CACHE:
            LIGHT_EMOJI_CACHE["thermometer"] = Image.new("RGBA", (550, 550), (0, 0, 0, 0))
        if "thermometer" not in DARK_EMOJI_CACHE:
            DARK_EMOJI_CACHE["thermometer"] = Image.new("RGBA", (550, 550), (0, 0, 0, 0))

        logger.info("Resources preloaded successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Resource file not found: {e}")
        raise
    except Exception as e:
        logger.error("Error preloading resources")
        raise

load_resources()

def is_night_time(current_time_local: datetime) -> bool:
    hour = current_time_local.hour
    minute = current_time_local.minute

    return (hour >= 23) or (hour < 9) or (hour == 9 and minute == 0)


def get_weather_emoji(description: str, current_time_local: datetime, size: tuple = (550, 550)) -> Image.Image:
    try:
        desc_lower = description.lower()
        is_night = is_night_time(current_time_local)

        emoji_cache = DARK_EMOJI_CACHE if is_night else LIGHT_EMOJI_CACHE

        if any(word in desc_lower for word in ["ясно", "clear", "солнечно", "sunny"]):
            emoji_key = "moon" if is_night else "sun"
            emoji = emoji_cache.get(emoji_key, emoji_cache["thermometer"])
        elif any(word in desc_lower for word in ["небольшая облачность", "few clouds", "малооблачно"]):
            emoji_key = "moon_cloud" if is_night else "sun_cloud"
            emoji = emoji_cache.get(emoji_key, emoji_cache["cloud"])
        elif any(word in desc_lower for word in [
            "облачно", "cloud", "пасмурно", "overcast", 
            "broken clouds", "scattered clouds"
        ]):
            emoji = emoji_cache.get("cloud", emoji_cache["thermometer"])
        elif any(word in desc_lower for word in [
            "дождь", "rain", "ливень", "shower", 
            "drizzle", "морось", "изморось"
        ]):
            if any(word in desc_lower for word in [
                "легкий", "light", "небольшой", "слабый", 
                "drizzle", "морось"
            ]):
                emoji_key = "moon_cloud_rain" if is_night else "sun_cloud_rain"
                emoji = emoji_cache.get(emoji_key, emoji_cache["rain"])
            else:
                emoji = emoji_cache.get("rain", emoji_cache["thermometer"])
        elif any(word in desc_lower for word in ["гроза", "thunderstorm", "storm", "шторм"]):
            emoji = emoji_cache.get("storm", emoji_cache["thermometer"])
        elif any(word in desc_lower for word in [
            "снег", "snow", "снегопад", "sleet", 
            "graupel", "град", "hail"
        ]):
            emoji = emoji_cache.get("snow", emoji_cache["thermometer"])
        elif any(word in desc_lower for word in [
            "туман", "fog", "mist", "дымка", "haze", 
            "smoke", "mgla", "пыль", "dust", "песок", 
            "sand", "ash", "volcanic"
        ]):
            emoji = emoji_cache.get("fog", emoji_cache["thermometer"])
        elif any(word in desc_lower for word in [
            "шквал", "squall", "tornado", "торнадо", 
            "hurricane", "ураган"
        ]):
            emoji = emoji_cache.get("tornado", emoji_cache.get("storm", emoji_cache["thermometer"]))
        elif any(word in desc_lower for word in ["циклон", "cyclone"]):
            emoji = emoji_cache.get("cyclone", emoji_cache.get("storm", emoji_cache["thermometer"]))
        elif any(word in desc_lower for word in ["пыль", "dust", "песок", "sand"]):
            emoji = emoji_cache.get("dust", emoji_cache.get("fog", emoji_cache["thermometer"]))
        elif any(word in desc_lower for word in ["иней", "frost", "гололед", "ice", "гололедица"]):
            emoji = emoji_cache.get("snow", emoji_cache["thermometer"])
        else:
            emoji = emoji_cache["thermometer"]

        return emoji.resize(size, Image.Resampling.LANCZOS)

    except Exception as e:
        logger.error("Error loading emoji")
        return Image.new("RGBA", size, (0, 0, 0, 0))


def calculate_dynamic_position(temp_text: str, font_temp: ImageFont.FreeTypeFont = None, base_x: int = 800) -> int:
    if font_temp is None:
        font_temp = FONT_TEMP

    if font_temp is None:
        return base_x

    temp_bbox = font_temp.getbbox(temp_text)
    temp_width = temp_bbox[2] - temp_bbox[0] if temp_bbox else 0

    temp_start_x = 230
    fixed_offset = 70

    dynamic_x = temp_start_x + temp_width + fixed_offset
    min_x = 650

    return max(dynamic_x, min_x)


async def create_weather_card_async(
    weather_data: dict
) -> tuple[bool, BytesIO | None]:
    start_time = time.time()

    try:
        if any(resource is None for resource in [
            FONT_LARGE, FONT_MEDIUM, FONT_TEMP, 
            LIGHT_IMG, DARK_IMG, GLOBE_IMG
        ]):
            logger.error("Resources not loaded!")
            return False, None

        loop = asyncio.get_event_loop()
        success, card = await loop.run_in_executor(
            None, create_weather_card_sync, weather_data
        )

        elapsed_time = time.time() - start_time
        logger.info("Weather card created")
        return success, card

    except Exception as e:
        logger.error("Error creating weather card")
        return False, None


def create_weather_card_sync(
    weather_data: dict[str, Any]
) -> tuple[bool, BytesIO | None]:
    
    try:
        current_time_local = weather_data.get("current_time_local")
        lang = weather_data.get("lang", "en") 
        
        if not isinstance(current_time_local, datetime):
            logger.error("Invalid current_time_local in weather_data")
            return False, None
            
        is_night = is_night_time(current_time_local)

        logger.debug("Creating weather card")

        background_img = DARK_IMG if is_night else LIGHT_IMG

        main_img = Image.new("RGB", background_img.size, "white")
        main_img.paste(background_img, (0, 0))

        new_size = (80, 80)
        resized_globe = GLOBE_IMG.resize(new_size, Image.Resampling.LANCZOS)
        main_img.paste(resized_globe, (227, 165), resized_globe)

        emoji_img = get_weather_emoji(
            weather_data.get("description", ""), 
            current_time_local
        )
        main_img.paste(emoji_img, (985, 15), emoji_img)

        draw = ImageDraw.Draw(main_img)

        if is_night:
            # Night colors
            city_color = "#e4e4e5"
            date_color = "#91939c"
            temp_color = "#e4e4e5"
            right_block_color = "#91939c"
            description_color = "#e4e4e5"
            sunrise_color = "#e4e4e5"
        else:
            city_color = "#404040"
            date_color = (140, 140, 146)
            temp_color = "#404040"
            right_block_color = (140, 140, 146)
            description_color = "#404040"
            sunrise_color = "#404040"

        city = weather_data.get("city", "Unknown City")
        country = weather_data.get("country", "")
        city_name = f"{city[:15]}..." if len(city) > 15 else city
        draw.text(
            (325, 170),
            f"{city_name}, {country}",
            font=FONT_LARGE,
            fill=city_color
        )

        current_time_str = current_time_local.strftime("%A, %d %b %H:%M")

        if lang == "ru":
            day_translation = {
                "Monday": "понедельник",
                "Tuesday": "вторник",
                "Wednesday": "среда",
                "Thursday": "четверг",
                "Friday": "пятница",
                "Saturday": "суббота",
                "Sunday": "воскресенье",
            }
            month_translation = {
                "Jan": "янв",
                "Feb": "фев",
                "Mar": "мар",
                "Apr": "апр",
                "May": "мая",
                "Jun": "июн",
                "Jul": "июл",
                "Aug": "авг",
                "Sep": "сен",
                "Oct": "окт",
                "Nov": "ноя",
                "Dec": "дек",
            }
        else:
            day_translation = {
                "Monday": "monday",
                "Tuesday": "tuesday",
                "Wednesday": "wednesday",
                "Thursday": "thursday",
                "Friday": "friday",
                "Saturday": "saturday",
                "Sunday": "sunday",
            }
            month_translation = {
                "Jan": "jan",
                "Feb": "feb",
                "Mar": "mar",
                "Apr": "apr",
                "May": "may",
                "Jun": "jun",
                "Jul": "jul",
                "Aug": "aug",
                "Sep": "sep",
                "Oct": "oct",
                "Nov": "nov",
                "Dec": "dec",
            }

        for eng, translated in day_translation.items():
            current_time_str = current_time_str.replace(eng, translated)
        for eng, translated in month_translation.items():
            current_time_str = current_time_str.replace(eng, translated)

        draw.text(
            (230, 265), 
            current_time_str, 
            font=FONT_MEDIUM, 
            fill=date_color
        )

        temp = weather_data.get("temp", 0)
        temp_text = f"{temp:+.1f}°".replace(".", ",")
        draw.text((230, 360), temp_text, font=FONT_TEMP, fill=temp_color)

        right_block_x = calculate_dynamic_position(temp_text)

        pressure = weather_data.get("pressure", 0)
        humidity = weather_data.get("humidity", 0)
        wind_speed = weather_data.get("wind_speed", 0)
        wind_dir = weather_data.get("wind_dir", "")
        feels_like = weather_data.get("feels_like", 0)

        if lang == "ru":
            pressure_label = " мм"
            humidity_label = "%"
            wind_label = " м/с"
            feels_like_label = "ощущается как"
        else:
            pressure_label = " mm"
            humidity_label = "%"
            wind_label = " m/s"
            feels_like_label = "feels like"
        
        right_color = right_block_color if is_night else "#7a7b81"

        draw.text(
            (right_block_x, 390),
            f"{pressure}{pressure_label} | {humidity}{humidity_label}",
            font=FONT_MEDIUM,
            fill=right_color,
        )

        draw.text(
            (right_block_x, 460),
            f"{wind_speed}{wind_label}, {wind_dir}",
            font=FONT_MEDIUM,
            fill=right_color,
        )

        feels_like_text = f"{feels_like_label} {feels_like:+.1f}°".replace(".", ",")
        draw.text(
            (right_block_x, 530),
            feels_like_text,
            font=FONT_MEDIUM,
            fill=right_color,
        )

        description = weather_data.get("description", "").capitalize()
        draw.text(
            (230, 630),
            description,
            font=FONT_LARGE,
            fill=description_color,
        )

        sunrise_time = weather_data.get("sunrise", "")
        sunset_time = weather_data.get("sunset", "")
        
        if lang == "ru":
            sunrise_label = "Восход"
            sunset_label = "Закат"
            separator = " | "
        else:
            sunrise_label = "Sunrise"
            sunset_label = "Sunset"
            separator = " | "
        
        sunrise_text = f"{sunrise_label} {sunrise_time}{separator}{sunset_label} {sunset_time}"
        
        draw.text(
            (230, 728),
            sunrise_text,
            font=FONT_LARGE,
            fill=sunrise_color,
        )

        out = BytesIO()
        main_img.save(out, "PNG", optimize=True, quality=85)
        out.seek(0)
        return True, out

    except Exception as e:
        logger.error("Error creating weather card synchronously")
        return False, None


create_weather_card = create_weather_card_async