import time
import asyncio
import httpx
import hashlib
from aiogram import types
from aiogram.enums import ParseMode
from utils.weather import get_current_weather_async, get_location_async
from utils.image_utils import create_weather_card_async
from utils.file_utils import (
    generate_random_filename,
    cleanup_files,
    upload_to_website,
    generate_random_ip,
)
from config import IMGBB_API_KEY
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def generate_result_id(city: str, timestamp: float):
    """Генерация ID для инлайна"""
    base_string = f"{city}_{timestamp}"
    return hashlib.md5(base_string.encode()).hexdigest()[:64]


async def upload_to_imgbb(image_io: BytesIO):  # well... why not :shrug:
    """Асинхронная загрузка на imgbb"""
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
f"Ошибка от imgbb: {response.status_code, response.content}"
)
                        return None
    except Exception as e:
        logger.error(f"Ошибка загрузки на imgbb: {e}")
        return None


async def inline_weather_query(query: types.InlineQuery, bot_username: str):
    """Асинхронный обработчик инлайн запросов погоды"""
    start_time = time.time()
    location = query.query.strip().lower()

    if not location:
        result_id = generate_result_id("help", int(time.time()))
        results = [
            types.InlineQueryResultArticle(
                id=result_id,
                title="Как использовать бота?",
                description=f"Введите @{bot_username} локация",
                input_message_content=types.InputTextMessageContent(
                    message_text=f"🌤️ <b>Погодник</b>\n\n"
                    "Чтобы узнать погоду, введите:\n"
                    f"<code>@{bot_username} локация</code>\n"
                    f"<code>@{bot_username} IP</code>\n"
                    f"<code>@{bot_username} random</code>\n\n"
                    f"Пример: <code>@{bot_username} Москва</code>",
                    parse_mode=ParseMode.HTML,
                ),
                thumb_url="https://chuhan.lol/icon.jpg",
                thumb_width=64,
                thumb_height=64,
            )
        ]
        await query.answer(results, cache_time=3600)  # type: ignore[arg-type]
        return

    try:
        # Обработка команды random
        is_ip = "." in location

        if location == "random":
            random_ip = generate_random_ip()
            logger.info(f"Сгенерирован случайный IP: {random_ip}")
            city, country_code = await get_location_async(random_ip)

            if not city:
                random_ip = generate_random_ip()
                logger.info(f"Повторная генерация IP: {random_ip}")
                city, country_code = await get_location_async(random_ip)

            if not city:
                result_id = generate_result_id("random_error", int(time.time()))
                results = [
                    types.InlineQueryResultArticle(
                        id=result_id,
                        title="Случайная погода",
                        description="Не удалось найти случайную локацию, попробуйте еще раз",
                        input_message_content=types.InputTextMessageContent(
                            message_text=(
                                "Не удалось найти случайную локацию\n\n"
                                "Попробуйте еще раз: <code>@{bot_username} random</code></b>"
                            ),
                            parse_mode=ParseMode.HTML,
                        ),
                        thumb_url="https://chuhan.lol/icon.jpg",
                        thumb_width=64,
                        thumb_height=64,
                    )
                ]
                await query.answer(results, cache_time=1)  # type: ignore[arg-type]
                return

            location = random_ip
            is_ip = True

        city, country_code = location, None
        if is_ip:
            if location != "random":
                city, country_code = await get_location_async(location)

            if not city:
                result_id = generate_result_id("ip_error", int(time.time()))
                results = [
                    types.InlineQueryResultArticle(
                        id=result_id,
                        title="Ошибка определения местоположения",
                        description=f"IP {location} не найден",
                        input_message_content=types.InputTextMessageContent(
                            message_text=(
                                "❌ IP <code>{}</code> не найден\n\n"
                                "Проверьте IP адрес и повторите попытку\n\n<b>@{}</b>"
                            ).format(location, bot_username),
                            parse_mode=ParseMode.HTML,
                        ),
                        thumb_url="https://chuhan.lol/icon.jpg",
                        thumb_width=64,
                        thumb_height=64,
                    )
                ]
                await query.answer(results, cache_time=1)  # type: ignore[arg-type]
                logger.info(
                    f"Ошибка IP отправлена за {time.time() - start_time:.2f}с"
                )
                return

        weather_data = await get_current_weather_async(city, country_code)
        if not weather_data:
            return

        # Генерируем файлы
        timestamp = int(time.time())
        local_filename = generate_random_filename(prefix=f"weather_{timestamp}")
        website_filename = local_filename
        # local_filepath = f"templates/{local_filename}"

        # Асинхронное создание карточки
        card_created, card_io = await create_weather_card_async(weather_data)

        if not card_created:
            return
        if card_io is None:
            return

        imgbb_task = asyncio.create_task(upload_to_imgbb(card_io))
        upload_to_website(card_io, website_filename)

        image_url = await imgbb_task

        if not image_url:
            image_url = f"https://chuhan.lol/{website_filename}"

        result_id = generate_result_id(weather_data["city"], timestamp)

        if query.query.strip().lower() == "random":
            title = f"Случайная погода в {weather_data['city']}"
            description = f"Случайный IP | {weather_data['temp']:+.1f}°C, {weather_data['description']}"
        else:
            title = f"Погода в {weather_data['city']}"
            description = (
                f"{weather_data['temp']:+.1f}°C, {weather_data['description']}"
            )

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

        if query.query.strip().lower() == "random":
            logger.info(
                "Случайная погода обработана за {:.2f}с - {} ({}) {:+.1f}°C".format(
                    time.time() - start_time,
                    weather_data["city"],
                    weather_data["country"],
                    weather_data["temp"],
                )
            )
        else:
            logger.info(
                "Запрос обработан за {:.2f}с - {} {:+.1f}°C".format(
                    time.time() - start_time,
                    weather_data["city"],
                    weather_data["temp"],
                )
            )

        # Удаляем файлы
        cleanup_files(website_filename)

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        result_id = generate_result_id("fallback", int(time.time()))
        results = [
            types.InlineQueryResultArticle(
                id=result_id,
                title="Погода",
                description=location,
                input_message_content=types.InputTextMessageContent(
                    message_text=f"<b>@{bot_username}</b>",
                    parse_mode=ParseMode.HTML,
                ),
                thumb_url="https://chuhan.lol/icon.jpg",
                thumb_width=64,
                thumb_height=64,
            )
        ]
        await query.answer(results, cache_time=1)  # type: ignore[arg-type]
