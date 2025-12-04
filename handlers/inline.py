import time
import httpx
import asyncio
import hashlib
from aiogram import types, Router, Bot
from aiogram.enums import ParseMode
from utils.weather_utils import get_current_weather_async, get_location_async
from utils.image_utils import create_weather_card_async
from utils.file_utils import (
    generate_random_filename,
    cleanup_files,
    generate_random_ip,
)
from io import BytesIO
from config import IMGBB_API_KEY
from structlog import get_logger


rt = Router(name=__name__)
logger = get_logger(__name__)


@rt.inline_query()
async def inline_weather_query(query: types.InlineQuery, bot: Bot):
    """Async handler for inline weather queries"""
    logger.debug(
        "Inline query received",
        query=repr(query.query),
        from_user_id=query.from_user.id,
        from_user_name=repr(query.from_user.full_name),
    )

    bot_me = await bot.get_me()
    bot_username = bot_me.username
    if bot_username is None:
        raise RuntimeError("Why does the bot not have a username?")  # just for IDE :(

    location = query.query.strip().lower()

    if not location:
        results = generate_article(
            id="help",
            title="How to use the bot?",
            description=f"Type @{bot_username} location",
            message_text=HELP_MESSAGE.format(bot_username=bot_username),
        )
        await query.answer(results, cache_time=3600)  # type: ignore[arg-type]
        return

    try:
        return await _inline_weather_query(query, bot)

    except Exception as ex:
        logger.error(
            "Unknown error.",
            caught_exception=(repr(ex), str(ex)),
            exc_info=True,
        )
        results = generate_article(
            id="fallback",
            title="Weather",
            description=location,
            message_text=f"<b>@{bot_username}</b>",
        )
        await query.answer(results, cache_time=1)  # type: ignore[arg-type]


async def _inline_weather_query(query: types.InlineQuery, bot: Bot):
    bot_me = await bot.get_me()
    bot_username = bot_me.username
    if bot_username is None:
        raise RuntimeError("Why does the bot not have a username?")  # just for IDE :(

    # Process random command
    start_time = time.time()
    location = query.query.strip().lower()
    is_ip = location.count(".") == 3
    city = country_code = None

    if location == "random":
        i = 0
        while i < 3:
            random_ip = generate_random_ip()
            logger.debug(
                f"{'Regenerated' if i == 0 else 'Generated'} random IP",
                random_ip=random_ip,
            )
            city, country_code = await get_location_async(random_ip)

            if city:
                break
            i += 1
        else:
            results = generate_article(
                id="random_error",
                title="Random weather",
                description="Failed to find random location, try again",
                message_text=(
                    "Failed to find random location\n\n"
                    "Try again: <code>@{bot_username} random</code></b>"
                ),
            )
            await query.answer(results, cache_time=1)  # type: ignore[arg-type]
            elapsed_time = time.time() - start_time
            logger.warn(
                "IP generation error sent", elapsed_time=elapsed_time
            )
            return

        location = random_ip
    elif is_ip:
        city, country_code = await get_location_async(location)
        if not city:
            results = generate_article(
                id="ip_error",
                title="Location detection error",
                description=f"IP {location} not found",
                message_text=(
                    "❌ IP <code>{}</code> not found\n\n"
                    "Check the IP address and try again\n\n<b>@{}</b>"
                ).format(location, bot_username),
            )
            await query.answer(results, cache_time=1)  # type: ignore[arg-type]
            elapsed_time = time.time() - start_time
            logger.warn("IP error sent", elapsed_time=elapsed_time)
            return
    else:
        city = location

    weather_data = await get_current_weather_async(city, country_code)
    if not weather_data:
        results = generate_article(
            id="city_error",
            title="Location detection error",
            description=f"City {location} not found",
            message_text=(
                "❌ City <code>{}</code> not found\n\n"
                "Check the city and try again\n\n<b>@{}</b>"
            ).format(location, bot_username),
        )
        await query.answer(results, cache_time=1)  # type: ignore[arg-type]
        elapsed_time = time.time() - start_time
        logger.warn(
            "City error sent",
            elapsed_time=elapsed_time,
            city=city,
            location=location,
        )
        return

    image_url, website_filename = await generate_image(
        weather_data=weather_data
    )

    if query.query.strip().lower() == "random":
        title = f"Random weather in {weather_data['city']}"
        description = f"Random IP | {weather_data['temp']:+.1f}°C, {weather_data['description']}"
    else:
        title = f"Weather in {weather_data['city']}"
        description = (
            f"{weather_data['temp']:+.1f}°C, {weather_data['description']}"
        )

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

    await query.answer(results, cache_time=3)  # type: ignore[arg-type]

    elapsed_time = time.time() - start_time
    if query.query.strip().lower() == "random":
        logger.info(
            "Random weather processed.",
            elapsed_time=elapsed_time,
            city=weather_data["city"],
            country=weather_data["country"],
            temperature=weather_data["temp"],
            city_type="random",
        )
    else:
        logger.info(
            "Query processed",
            elapsed_time=elapsed_time,
            city=weather_data["city"],
            country=weather_data.get("country"),
            temperature=weather_data["temp"],
            city_type="specified",
        )

    # Clean up files
    await cleanup_files(website_filename)


def generate_result_id(city: str, timestamp: float):
    """Generate ID for inline query"""
    base_string = f"{city}_{timestamp}"
    return hashlib.md5(base_string.encode()).hexdigest()[:64]


async def upload_to_imgbb(image_io: BytesIO):  # well... why not :shrug:
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
                logger.error(
                    "Error from imgbb",
                    response=response,
                    status_code=response.status_code,
                    content=response.content,
                )
                return None
    except Exception as ex:
        logger.error(
            "Error uploading to imgbb",
            caught_exception=(repr(ex), str(ex)),
            exc_info=True,
        )
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
    # Generate files
    timestamp = int(time.time())
    local_filename = generate_random_filename(prefix=f"weather_{timestamp}")
    website_filename = local_filename

    # Async card creation
    card_created, card_io = await create_weather_card_async(weather_data)

    if not card_created:
        raise RuntimeError("Didn't created card!")
    elif card_io is None:
        raise RuntimeError("Didn't created card's BytesIO!")

    imgbb_task = asyncio.create_task(upload_to_imgbb(card_io))

    image_url = await imgbb_task

    if not image_url:
        image_url = f"https://chuhan.lol/{website_filename}"
    return image_url, website_filename


HELP_MESSAGE = (
    "🌤️ <b>Weather Bot</b>\n\n"
    "To check the weather, type:\n"
    "<code>@{bot_username} location</code>\n"
    "<code>@{bot_username} IP</code>\n"
    "<code>@{bot_username} random</code>\n\n"
    "Example: <code>@{bot_username} Moscow</code>"
)