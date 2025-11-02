import time
import asyncio
import aiohttp
import base64
import hashlib
from aiogram import types
from aiogram.enums import ParseMode
from utils.weather import get_current_weather_async, get_location_async
from utils.image_utils import create_weather_card_async
from utils.file_utils import generate_random_filename, cleanup_files, upload_to_website, generate_random_ip
from config import IMGBB_API_KEY
import logging

logger = logging.getLogger(__name__)

def generate_result_id(city, timestamp):
    """Генерация ID для инлайна"""
    base_string = f"{city}_{timestamp}"
    return hashlib.md5(base_string.encode()).hexdigest()[:64]

async def upload_to_imgbb(image_path):
    """Асинхронная загрузка на imgbb"""
    try:
        async with aiohttp.ClientSession() as session:
            with open(image_path, "rb") as file:
                url = "https://api.imgbb.com/1/upload"
                
                data = aiohttp.FormData()
                data.add_field('key', IMGBB_API_KEY)
                data.add_field('image', base64.b64encode(file.read()).decode())
                
                async with session.post(url, data=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["data"]["url"]
                    else:
                        logger.error(f"Ошибка от imgbb: {response.status}")
                        return None
    except Exception as e:
        logger.error(f"Ошибка загрузки на imgbb: {e}")
        return None

async def inline_weather_query(query: types.InlineQuery, bot_username):
    """Асинхронный обработчик инлайн запросов погоды"""
    start_time = time.time()
    location = query.query.strip().lower()

    if not location:
        result_id = generate_result_id("help", int(time.time()))
        results = [types.InlineQueryResultArticle(
            id=result_id,
            title="Как использовать бота?", 
            description=f"Введите @{bot_username} локация",
            input_message_content=types.InputTextMessageContent(
                message_text=f"🌤️ <b>Погодник</b>\n\n"
                           "Чтобы узнать погоду, введите:\n"
                           "<code>@{bot_username} локация</code>\n"
                           "<code>@{bot_username} IP</code>\n"
                           "<code>@{bot_username} random</code>\n\n"
                           "Пример: <code>@{bot_username} Москва</code>",
                parse_mode=ParseMode.HTML
            ),
            thumb_url="https://chuhan.lol/icon.jpg",
            thumb_width=64,
            thumb_height=64
        )]
        await query.answer(results, cache_time=3600)  
        return
    
    try:
        # Обработка команды random
        if location == 'random':
            random_ip = generate_random_ip()
            logger.info(f"Сгенерирован случайный IP: {random_ip}")
            city, country_code = await get_location_async(random_ip)
            
            if not city:
                random_ip = generate_random_ip()
                logger.info(f"Повторная генерация IP: {random_ip}")
                city, country_code = await get_location_async(random_ip)
            
            if not city:
                result_id = generate_result_id("random_error", int(time.time()))
                results = [types.InlineQueryResultArticle(
                    id=result_id,
                    title="Случайная погода", 
                    description="Не удалось найти случайную локацию, попробуйте еще раз",
                    input_message_content=types.InputTextMessageContent(
                        message_text=f"Не удалось найти случайную локацию\n\nПопробуйте еще раз: <code>@{bot_username} random</code></b>",
                        parse_mode=ParseMode.HTML
                    ),
                    thumb_url="https://chuhan.lol/icon.jpg",
                    thumb_width=64,
                    thumb_height=64
                )]
                await query.answer(results, cache_time=1)
                return
                
            location = random_ip
            is_ip = True
        else:
            is_ip = '.' in location
        
        if is_ip:
            if location != 'random':
                city, country_code = await get_location_async(location)
            
            if not city:
                result_id = generate_result_id("ip_error", int(time.time()))
                results = [types.InlineQueryResultArticle(
                    id=result_id, 
                    title="Ошибка определения местоположения", 
                    description=f"IP {location} не найден",
                    input_message_content=types.InputTextMessageContent(
                        message_text=f"❌ IP <code>{location}</code> не найден\n\nПроверьте IP адрес и повторите попытку\n\n<b>@{bot_username}</b>",
                        parse_mode=ParseMode.HTML
                    ),
                    thumb_url="https://chuhan.lol/icon.jpg",
                    thumb_width=64,
                    thumb_height=64
                )]
                await query.answer(results, cache_time=1)
                logger.info(f"Ошибка IP отправлена за {time.time() - start_time:.2f}с")
                return
        else:
            city, country_code = location, None
            
        weather_data = await get_current_weather_async(city, country_code)
        if not weather_data:
            return
        
        # Генерируем файлы
        timestamp = int(time.time())
        local_filename = generate_random_filename(prefix=f"weather_{timestamp}")
        local_filepath = f"templates/{local_filename}"
        website_filename = local_filename

        # Асинхронное создание карточки
        card_created = await create_weather_card_async(weather_data, local_filepath)
        
        if not card_created:
            return

        imgbb_task = asyncio.create_task(upload_to_imgbb(local_filepath))
        upload_to_website(local_filepath, website_filename)

        image_url = await imgbb_task
        
        if not image_url:
            image_url = f"https://chuhan.lol/{website_filename}"
        
        result_id = generate_result_id(weather_data['city'], timestamp)
        
        if query.query.strip().lower() == 'random':
            title = f"Случайная погода в {weather_data['city']}"
            description = f"Случайный IP | {weather_data['temp']:+.1f}°C, {weather_data['description']}"
        else:
            title = f"Погода в {weather_data['city']}"
            description = f"{weather_data['temp']:+.1f}°C, {weather_data['description']}"
        
        results = [
            types.InlineQueryResultPhoto(
                id=result_id,
                photo_url=image_url,
                thumbnail_url=image_url,
                title=title,
                description=description,
                caption=f"<code>{weather_data['city']} - {weather_data['temp']:+.1f}°C, {weather_data['description']}</code>\n\n<b>Посмотреть погоду:</b> <code>@{bot_username} локация</code>",
                parse_mode=ParseMode.HTML,
                photo_width=1600,
                photo_height=1000
            )
        ]
        
        await query.answer(results, cache_time=3)
        
        if query.query.strip().lower() == 'random':
            logger.info(f"Случайная погода обработана за {time.time() - start_time:.2f}с - {weather_data['city']} ({weather_data['country']}) {weather_data['temp']:+.1f}°C")
        else:
            logger.info(f"Запрос обработана за {time.time() - start_time:.2f}с - {weather_data['city']} {weather_data['temp']:+.1f}°C")
        
        # Удаляем файлы
        cleanup_files(local_filepath, website_filename)
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        result_id = generate_result_id("fallback", int(time.time()))
        results = [types.InlineQueryResultArticle(
            id=result_id,
            title="Погода", 
            description=location,
            input_message_content=types.InputTextMessageContent(
                message_text=f"<b>@{bot_username}</b>",
                parse_mode=ParseMode.HTML
            ),
            thumb_url="https://chuhan.lol/icon.jpg",
            thumb_width=64,
            thumb_height=64
        )]
        await query.answer(results, cache_time=1)
