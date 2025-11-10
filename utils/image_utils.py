import time
import logging
import asyncio
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Глобальные переменные для кэша ресурсов
FONT_LARGE = ImageFont.truetype()
FONT_MEDIUM = ImageFont.truetype()
FONT_TEMP = ImageFont.truetype()
LIGHT_IMG = Image.Image()
DARK_IMG = Image.Image()
GLOBE_IMG = Image.Image()
LIGHT_EMOJI_CACHE = {}
DARK_EMOJI_CACHE = {}


def load_resources():
    """Предзагрузка ресурсов"""
    global \
        FONT_LARGE, \
        FONT_MEDIUM, \
        FONT_TEMP, \
        LIGHT_IMG, \
        DARK_IMG, \
        GLOBE_IMG, \
        LIGHT_EMOJI_CACHE, \
        DARK_EMOJI_CACHE

    try:
        FONT_LARGE = ImageFont.truetype("SF-Pro-Display-Medium.otf", 72)
        FONT_MEDIUM = ImageFont.truetype("SF-Pro-Display-Medium.otf", 46.75)
        FONT_TEMP = ImageFont.truetype("SF-Pro-Display-Medium.otf", 186.99)

        # Загружаем оба фона: светлый для дня, темный для ночи
        LIGHT_IMG = Image.open("templates/light_temp.png").convert("RGBA")
        DARK_IMG = Image.open("templates/dark_temp.png").convert("RGBA")
        GLOBE_IMG = Image.open("templates/globe.png").convert("RGBA")

        # Загружаем светлые эмодзи
        light_emoji_paths = {
            "sun": "templates/weather_emoji/light/sun.png",
            "cloud": "templates/weather_emoji/light/cloud.png",
            "rain": "templates/weather_emoji/light/rain.png",
            "storm": "templates/weather_emoji/light/storm.png",
            "snow": "templates/weather_emoji/light/snow.png",
            "fog": "templates/weather_emoji/light/fog.png",
            "sun_cloud": "templates/weather_emoji/light/sun_cloud.png",
            "sun_cloud_rain": "templates/weather_emoji/light/sun_cloud_rain.png",
            "thermometer": "templates/weather_emoji/light/thermometer.png",
            "cyclone": "templates/weather_emoji/light/cyclone.png",
            "dust": "templates/weather_emoji/light/dust.png",
            "tornado": "templates/weather_emoji/light/tornado.png",
        }

        # Загружаем темные эмодзи
        dark_emoji_paths = {
            "moon": "templates/weather_emoji/dark/moon.png",
            "cloud": "templates/weather_emoji/dark/cloud.png",
            "rain": "templates/weather_emoji/dark/rain.png",
            "storm": "templates/weather_emoji/dark/storm.png",
            "snow": "templates/weather_emoji/dark/snow.png",
            "fog": "templates/weather_emoji/dark/fog.png",
            "moon_cloud": "templates/weather_emoji/dark/moon_cloud.png",
            "moon_cloud_rain": "templates/weather_emoji/dark/moon_cloud_rain.png",
            "thermometer": "templates/weather_emoji/dark/thermometer.png",
            "cyclone": "templates/weather_emoji/dark/cyclone.png",
            "dust": "templates/weather_emoji/dark/dust.png",
            "tornado": "templates/weather_emoji/dark/tornado.png",
        }

        for key, path in light_emoji_paths.items():
            LIGHT_EMOJI_CACHE[key] = Image.open(path).convert("RGBA")

        for key, path in dark_emoji_paths.items():
            DARK_EMOJI_CACHE[key] = Image.open(path).convert("RGBA")

        logger.info("Ресурсы предзагружены")
    except Exception as e:
        logger.error(f"Ошибка предзагрузки ресурсов: {e}")
        raise


def is_night_time(current_time_local):
    """Проверяет, ночное ли время (23:00-09:00 включительно) по местному времени города"""
    hour = current_time_local.hour
    minute = current_time_local.minute

    # 23:00-09:00 включительно - ночь
    return (hour >= 23) or (hour < 9) or (hour == 9 and minute == 0)


def get_weather_emoji(description, current_time_local, size=(550, 550)):
    """Получение эмодзи по краткому описанию с учетом времени суток в городе"""
    try:
        desc_lower = description.lower()
        is_night = is_night_time(current_time_local)

        # Выбираем кэш эмодзи в зависимости от времени суток
        emoji_cache = DARK_EMOJI_CACHE if is_night else LIGHT_EMOJI_CACHE

        if any(
            word in desc_lower
            for word in ["ясно", "clear", "солнечно", "sunny"]
        ):
            # Для светлой темы - солнце, для темной - луна
            emoji_key = "moon" if is_night else "sun"
            emoji = emoji_cache.get(emoji_key, emoji_cache["thermometer"])
        elif any(
            word in desc_lower
            for word in ["небольшая облачность", "few clouds", "малооблачно"]
        ):
            # Для светлой темы - солнце с облаками, для темной - луна с облаками
            emoji_key = "moon_cloud" if is_night else "sun_cloud"
            emoji = emoji_cache.get(emoji_key, emoji_cache["cloud"])
        elif any(
            word in desc_lower
            for word in [
                "облачно",
                "cloud",
                "пасмурно",
                "overcast",
                "broken clouds",
                "scattered clouds",
            ]
        ):
            emoji = emoji_cache["cloud"]
        elif any(
            word in desc_lower
            for word in [
                "дождь",
                "rain",
                "ливень",
                "shower",
                "drizzle",
                "морось",
                "изморось",
            ]
        ):
            if any(
                word in desc_lower
                for word in [
                    "легкий",
                    "light",
                    "небольшой",
                    "слабый",
                    "drizzle",
                    "морось",
                ]
            ):
                # Для светлой темы - солнце с облаками и дождем, для темной - луна с облаками и дождем
                emoji_key = "moon_cloud_rain" if is_night else "sun_cloud_rain"
                emoji = emoji_cache.get(emoji_key, emoji_cache["rain"])
            else:
                emoji = emoji_cache["rain"]
        elif any(
            word in desc_lower
            for word in ["гроза", "thunderstorm", "storm", "шторм"]
        ):
            emoji = emoji_cache["storm"]
        elif any(
            word in desc_lower
            for word in [
                "снег",
                "snow",
                "снегопад",
                "sleet",
                "graupel",
                "град",
                "hail",
            ]
        ):
            emoji = emoji_cache["snow"]
        elif any(
            word in desc_lower
            for word in [
                "туман",
                "fog",
                "mist",
                "дымка",
                "haze",
                "smoke",
                "mgla",
                "пыль",
                "dust",
                "песок",
                "sand",
                "ash",
                "volcanic",
            ]
        ):
            emoji = emoji_cache["fog"]
        elif any(
            word in desc_lower
            for word in [
                "шквал",
                "squall",
                "tornado",
                "торнадо",
                "hurricane",
                "ураган",
            ]
        ):
            emoji = emoji_cache.get("tornado", emoji_cache["storm"])
        elif any(word in desc_lower for word in ["циклон", "cyclone"]):
            emoji = emoji_cache.get("cyclone", emoji_cache["storm"])
        elif any(
            word in desc_lower for word in ["пыль", "dust", "песок", "sand"]
        ):
            emoji = emoji_cache.get("dust", emoji_cache["fog"])
        elif any(
            word in desc_lower
            for word in ["иней", "frost", "гололед", "ice", "гололедица"]
        ):
            emoji = emoji_cache["snow"]
        else:
            emoji = emoji_cache["thermometer"]

        return emoji.resize(size, Image.Resampling.LANCZOS)

    except Exception as e:
        logger.error(f"Ошибка загрузки эмодзи: {e}")
        return Image.new("RGBA", size, (0, 0, 0, 0))


def calculate_dynamic_position(temp_text, font_temp=None, base_x=800):
    """Рассчитывает позицию для правого блока"""
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


async def create_weather_card_async(weather_data, output_path):
    """Асинхронное создание карточки"""
    start_time = time.time()

    try:
        if any(
            resource is None
            for resource in [
                FONT_LARGE,
                FONT_MEDIUM,
                FONT_TEMP,
                LIGHT_IMG,
                DARK_IMG,
                GLOBE_IMG,
            ]
        ):
            logger.error("Ресурсы не загружены!")
            return False

        # Выполняем в отдельном потоке, так как Pillow блокирующий
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            None, create_weather_card_sync, weather_data, output_path
        )

        logger.info(f"Карточка создана за {time.time() - start_time:.2f}с")
        return success

    except Exception as e:
        logger.error(f"Ошибка создания карточки: {e}")
        return False


def create_weather_card_sync(weather_data, output_path):
    """Синхронное создание карточки (для executor)"""
    try:
        current_time_local = weather_data["current_time_local"]
        is_night = is_night_time(current_time_local)

        logger.info(
            f"Создание карточки для {weather_data['city']}, местное время: {current_time_local}, ночной режим: {is_night}"
        )

        # Выбираем фон в зависимости от времени суток в городе
        background_img = DARK_IMG if is_night else LIGHT_IMG

        main_img = Image.new("RGB", background_img.size, "white")
        main_img.paste(background_img, (0, 0))

        new_size = (80, 80)
        resized_globe = GLOBE_IMG.resize(new_size, Image.Resampling.LANCZOS)
        main_img.paste(resized_globe, (227, 165), resized_globe)

        # Передаем местное время для выбора правильного эмодзи
        emoji_img = get_weather_emoji(
            weather_data["description"], current_time_local
        )
        main_img.paste(emoji_img, (985, 15), emoji_img)

        draw = ImageDraw.Draw(main_img)

        # Определяем цвета в зависимости от времени суток в городе
        if is_night:
            # Ночные цвета
            city_color = "#e4e4e5"
            date_color = "#91939c"
            temp_color = "#e4e4e5"
            right_block_color = "#7a7b81"
            description_color = "#e4e4e5"
            sunrise_color = "#e4e4e5"
        else:
            # Дневные цвета (оригинальные)
            city_color = "#404040"
            date_color = (192, 192, 194)
            temp_color = "#404040"
            right_block_color = "#7a7b81"
            description_color = "#404040"
            sunrise_color = "#404040"

        city_name = (
            weather_data["city"][:15] + "..."
            if len(weather_data["city"]) > 15
            else weather_data["city"]
        )
        draw.text(
            (325, 170),
            f"{city_name}, {weather_data['country']}",
            font=FONT_LARGE,
            fill=city_color,
        )

        current_time_str = current_time_local.strftime("%A, %d %b %H:%M")

        month_translation = {
            "Jan": "янв",
            "Feb": "фев",
            "Mar": "мар",
            "Apr": "апр",
            "May": "май",
            "Jun": "июн",
            "Jul": "июл",
            "Aug": "авг",
            "Sep": "сен",
            "Oct": "окт",
            "Nov": "ноя",
            "Dec": "дек",
        }
        day_translation = {
            "Monday": "понедельник",
            "Tuesday": "вторник",
            "Wednesday": "среда",
            "Thursday": "четверг",
            "Friday": "пятница",
            "Saturday": "суббота",
            "Sunday": "воскресенье",
        }

        for eng, rus in day_translation.items():
            current_time_str = current_time_str.replace(eng, rus)
        for eng, rus in month_translation.items():
            current_time_str = current_time_str.replace(eng, rus)

        draw.text(
            (230, 265), current_time_str, font=FONT_MEDIUM, fill=date_color
        )

        temp_text = f"{weather_data['temp']:+.1f}°".replace(".", ",")
        draw.text((230, 360), temp_text, font=FONT_TEMP, fill=temp_color)

        right_block_x = calculate_dynamic_position(temp_text)

        # Правый блок (всегда #7a7b81 в ночном режиме, в дневном остается как было)
        right_color = right_block_color if is_night else "#7a7b81"
        draw.text(
            (right_block_x, 390),
            f"{weather_data['pressure']} мм | {weather_data['humidity']}%",
            font=FONT_MEDIUM,
            fill=right_color,
        )
        draw.text(
            (right_block_x, 460),
            f"{weather_data['wind_speed']} м/с, {weather_data['wind_dir']}",
            font=FONT_MEDIUM,
            fill=right_color,
        )
        draw.text(
            (right_block_x, 530),
            f"ощущается {weather_data['feels_like']:+.1f}°".replace(".", ","),
            font=FONT_MEDIUM,
            fill=right_color,
        )

        draw.text(
            (230, 630),
            weather_data["description"].capitalize(),
            font=FONT_LARGE,
            fill=description_color,
        )

        sunrise_time = weather_data["sunrise"]
        sunset_time = weather_data["sunset"]

        draw.text(
            (230, 728),
            f"Восход {sunrise_time} | Закат {sunset_time}",
            font=FONT_LARGE,
            fill=sunrise_color,
        )

        main_img.save(output_path, "PNG", optimize=True, quality=85)
        return True

    except Exception as e:
        logger.error(f"Ошибка создания карточки: {e}")
        return False


# Алиас для обратной совместимости
create_weather_card = create_weather_card_async
