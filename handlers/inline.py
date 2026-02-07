import time
import httpx
import asyncio
import hashlib
from aiogram import types, Router, Bot
from aiogram.enums import ParseMode
from utils.weather import (
    fetch_weather_data, 
    get_location,
    detect_language
)
from utils.image import create_weather_card_async
from utils.settings import (
    generate_random_filename,
    cleanup_files,
    generate_random_ip,
)
from utils.logger import logger
from io import BytesIO
from config import IMGBB_API_KEY


rt = Router(name=__name__)


@rt.inline_query()
async def inline_weather_query(query: types.InlineQuery, bot: Bot):
    """Async handler for inline weather queries"""
    logger.debug("Inline query received")

    bot_me = await bot.get_me()
    bot_username = bot_me.username
    if bot_username is None:
        raise RuntimeError("Why does the bot not have a username?")

    location = query.query.strip().lower()

    if not location:
        results = generate_article(
            id="help",
            title="How to use the bot?",
            description=f"Type @{bot_username} location",
            message_text=HELP_MESSAGE.format(bot_username=bot_username),
        )
        await query.answer(results, cache_time=3600)
        return

    try:
        return await _inline_weather_query(query, bot)

    except Exception as ex:
        logger.error("Unknown error.")
        results = generate_article(
            id="fallback",
            title="Weather",
            description=location,
            message_text=f"<b>@{bot_username}</b>",
        )
        await query.answer(results, cache_time=1)


async def _inline_weather_query(query: types.InlineQuery, bot: Bot):
    bot_me = await bot.get_me()
    bot_username = bot_me.username
    if bot_username is None:
        raise RuntimeError("Why does the bot not have a username?")

    start_time = time.time()
    location = query.query.strip()

    lang = detect_language(location)
    logger.debug("Detected language")
    
    is_ip = location.count(".") == 3
    city = country_code = None

    if location.lower() == "random":
        i = 0
        while i < 3:
            random_ip = generate_random_ip()
            logger.debug(f"{'Regenerated' if i == 0 else 'Generated'} random IP")
            city, country_code = await get_location(random_ip)

            if city:
                break
            i += 1
        else:
            error_msg = (
                "Не удалось найти случайное местоположение, попробуйте снова" 
                if lang == "ru" else 
                "Failed to find random location, try again"
            )
            results = generate_article(
                id="random_error",
                title="Random weather",
                description=error_msg,
                message_text=error_msg,
            )
            await query.answer(results, cache_time=1)
            elapsed_time = time.time() - start_time
            logger.warn("IP generation error sent")
            return

        location = random_ip
    elif is_ip:
        city, country_code = await get_location(location)
        if not city:
            error_title = "Ошибка определения местоположения" if lang == "ru" else "Location detection error"
            error_desc = f"IP {location} не найден" if lang == "ru" else f"IP {location} not found"
            error_text = (
                f"❌ IP <code>{location}</code> не найден\n\n"
                f"Проверьте IP-адрес и попробуйте снова\n\n<b>@{bot_username}</b>"
                if lang == "ru" else
                f"❌ IP <code>{location}</code> not found\n\n"
                f"Check the IP address and try again\n\n<b>@{bot_username}</b>"
            )
            results = generate_article(
                id="ip_error",
                title=error_title,
                description=error_desc,
                message_text=error_text,
            )
            await query.answer(results, cache_time=1)
            elapsed_time = time.time() - start_time
            logger.warn("IP error sent")
            return
    else:
        city = location

    weather_data = await fetch_weather_data(city, country_code, lang)
    if not weather_data:
        error_title = "Ошибка определения местоположения" if lang == "ru" else "Location detection error"
        error_desc = f"Город {location} не найден" if lang == "ru" else f"City {location} not found"
        error_text = (
            f"❌ Город <code>{location}</code> не найден\n\n"
            f"Проверьте название города и попробуйте снова\n\n<b>@{bot_username}</b>"
            if lang == "ru" else
            f"❌ City <code>{location}</code> not found\n\n"
            f"Check the city and try again\n\n<b>@{bot_username}</b>"
        )
        results = generate_article(
            id="city_error",
            title=error_title,
            description=error_desc,
            message_text=error_text,
        )
        await query.answer(results, cache_time=1)
        elapsed_time = time.time() - start_time
        logger.warn("City error sent")
        return

    image_url, website_filename = await generate_image(
        weather_data=weather_data
    )

    if query.query.strip().lower() == "random":
        if lang == "ru":
            title = f"Случайная погода в {weather_data['city']}"
            description = f"Случайный IP | {weather_data['temp']:+.1f}°C, {weather_data['description']}"
        else:
            title = f"Random weather in {weather_data['city']}"
            description = f"Random IP | {weather_data['temp']:+.1f}°C, {weather_data['description']}"
    else:
        if lang == "ru":
            title = f"Погода в {weather_data['city']}"
        else:
            title = f"Weather in {weather_data['city']}"
        description = f"{weather_data['temp']:+.1f}°C, {weather_data['description']}"

    result_id = generate_result_id(weather_data["city"], int(time.time()))
    results = [
        types.InlineQueryResultPhoto(
            id=result_id,
            photo_url=image_url,
            thumbnail_url=image_url,
            title=title,
            description=description,
            caption="<code>{} - {:+.1f}°C, {}</code>".format(
                weather_data["city"],
                weather_data["temp"],
                weather_data["description"],
            ),
            parse_mode=ParseMode.HTML,
            photo_width=1600,
            photo_height=1000,
        )
    ]

    await query.answer(results, cache_time=3)

    elapsed_time = time.time() - start_time
    if query.query.strip().lower() == "random":
        logger.info("Random weather processed.")
    else:
        logger.info("Query processed")

    await cleanup_files(website_filename)


def generate_result_id(city: str, timestamp: float):
    """Generate ID for inline query"""
    base_string = f"{city}_{timestamp}"
    return hashlib.md5(base_string.encode()).hexdigest()[:64]


async def upload_to_imgbb(image_io: BytesIO):
    """Async upload to imgbb"""
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.imgbb.com/1/upload"
            response = await client.post(
                url, data=dict(key=IMGBB_API_KEY), files=dict(image=image_io)
            )
            if response.status_code == 200:
                result = response.json()
                return result["data"]["url"]
            else:
                logger.error("Error from imgbb")
                return None
    except Exception as ex:
        logger.error("Error uploading to imgbb")
        return None


def generate_article(id: str, title: str, description: str, message_text: str):
    result_id = generate_result_id(id, int(time.time()))
    return (
        types.InlineQueryResultArticle(
            id=result_id,
            title=title,
            description=description,
            input_message_content=types.InputTextMessageContent(
                message_text=message_text,
                parse_mode=ParseMode.HTML,
            ),
            thumb_url="https://chuhan.lol/icon.jpg",
            thumb_width=64,
            thumb_height=64,
        ),
    )


async def generate_image(weather_data: dict):
    timestamp = int(time.time())
    local_filename = generate_random_filename(prefix=f"weather_{timestamp}")
    website_filename = local_filename

    card_created, card_io = await create_weather_card_async(weather_data)

    if not card_created:
        raise RuntimeError("Didn't created card!")
    elif card_io is None:
        raise RuntimeError("Didn't created card's BytesIO!")

    imgbb_task = asyncio.create_task(upload_to_imgbb(card_io))

    image_url = await imgbb_task

    return image_url, website_filename


HELP_MESSAGE_EN = (
    "🌤️ <b>Weather Bot</b>\n\n"
    "To check the weather, type:\n"
    "<code>@{bot_username} location</code>\n"
    "<code>@{bot_username} IP</code>\n"
    "<code>@{bot_username} random</code>\n\n"
    "Example: <code>@{bot_username} Moscow</code>\n"
)

HELP_MESSAGE_RU = (
    "🌤️ <b>Weather Bot</b>\n\n"
    "Чтобы проверить погоду, введите:\n"
    "<code>@{bot_username} город</code>\n"
    "<code>@{bot_username} IP</code>\n"
    "<code>@{bot_username} random</code>\n\n"
    "Пример: <code>@{bot_username} Москва</code>"
)

HELP_MESSAGE = HELP_MESSAGE_EN
