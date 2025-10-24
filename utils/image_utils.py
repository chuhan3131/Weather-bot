import time
import logging
import asyncio
import aiofiles
import os
from PIL import Image, ImageDraw, ImageFont
from config import UPLOAD_TIMEOUT

logger = logging.getLogger(__name__)

# Глобальные переменные для кэша ресурсов
FONT_LARGE = None
FONT_MEDIUM = None  
FONT_TEMP = None
MAIN_IMG = None
GLOBE_IMG = None
EMOJI_CACHE = {}

def load_resources():
    """Предзагрузка ресурсов"""
    global FONT_LARGE, FONT_MEDIUM, FONT_TEMP, MAIN_IMG, GLOBE_IMG, EMOJI_CACHE
    
    try:
        FONT_LARGE = ImageFont.truetype("SF-Pro-Display-Medium.otf", 72)
        FONT_MEDIUM = ImageFont.truetype("SF-Pro-Display-Medium.otf", 46.75)
        FONT_TEMP = ImageFont.truetype("SF-Pro-Display-Medium.otf", 186.99)
        
        MAIN_IMG = Image.open("templates/main_temp.png").convert("RGBA")
        GLOBE_IMG = Image.open("templates/globe.png").convert("RGBA")

        emoji_paths = {
            'sun': "templates/weather_emoji/sun.png",
            'cloud': "templates/weather_emoji/cloud.png", 
            'rain': "templates/weather_emoji/rain.png",
            'storm': "templates/weather_emoji/storm.png",
            'snow': "templates/weather_emoji/snow.png",
            'fog': "templates/weather_emoji/fog.png",
            'sun_cloud': "templates/weather_emoji/sun_cloud.png",
            'sun_cloud_rain': "templates/weather_emoji/sun_cloud_rain.png",
            'thermometer': "templates/weather_emoji/thermometer.png"
        }
        
        for key, path in emoji_paths.items():
            EMOJI_CACHE[key] = Image.open(path).convert("RGBA")
        
        logger.info("Ресурсы предзагружены")
    except Exception as e:
        logger.error(f"Ошибка предзагрузки ресурсов: {e}")
        raise 

def get_weather_emoji(description, size=(550, 550)):
    """Получение эмодзи по краткому описанию"""
    try:
        desc_lower = description.lower()

        if any(word in desc_lower for word in ['ясно', 'clear', 'солнечно', 'sunny']):
            emoji = EMOJI_CACHE['sun']
        elif any(word in desc_lower for word in ['небольшая облачность', 'few clouds', 'малооблачно']):
            emoji = EMOJI_CACHE['sun_cloud']
        elif any(word in desc_lower for word in ['облачно', 'cloud', 'пасмурно', 'overcast', 'broken clouds', 'scattered clouds']):
            emoji = EMOJI_CACHE['cloud']
        elif any(word in desc_lower for word in ['дождь', 'rain', 'ливень', 'shower', 'drizzle', 'морось', 'изморось']):
            if any(word in desc_lower for word in ['легкий', 'light', 'небольшой', 'слабый', 'drizzle', 'морось']):
                emoji = EMOJI_CACHE['sun_cloud_rain']
            else:
                emoji = EMOJI_CACHE['rain']
        elif any(word in desc_lower for word in ['гроза', 'thunderstorm', 'storm', 'шторм']):
            emoji = EMOJI_CACHE['storm']
        elif any(word in desc_lower for word in ['снег', 'snow', 'снегопад', 'sleet', 'graupel', 'град', 'hail']):
            emoji = EMOJI_CACHE['snow']
        elif any(word in desc_lower for word in ['туман', 'fog', 'mist', 'дымка', 'haze', 'smoke', 'mgla', 'пыль', 'dust', 'песок', 'sand', 'ash', 'volcanic']):
            emoji = EMOJI_CACHE['fog']
        elif any(word in desc_lower for word in ['шквал', 'squall', 'tornado', 'торнадо', 'hurricane', 'ураган']):
            emoji = EMOJI_CACHE['storm']
        elif any(word in desc_lower for word in ['иней', 'frost', 'гололед', 'ice', 'гололедица']):
            emoji = EMOJI_CACHE['snow']
        else:
            emoji = EMOJI_CACHE['thermometer']

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
        if any(resource is None for resource in [FONT_LARGE, FONT_MEDIUM, FONT_TEMP, MAIN_IMG, GLOBE_IMG]):
            logger.error("Ресурсы не загружены!")
            return False

        # Выполняем в отдельном потоке, так как Pillow блокирующий
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            None, 
            create_weather_card_sync, 
            weather_data, 
            output_path
        )
        
        logger.info(f"Карточка создана за {time.time() - start_time:.2f}с")
        return success
        
    except Exception as e:
        logger.error(f"Ошибка создания карточки: {e}")
        return False

def create_weather_card_sync(weather_data, output_path):
    """Синхронное создание карточки (для executor)"""
    try:
        main_img = Image.new("RGB", MAIN_IMG.size, "white")
        main_img.paste(MAIN_IMG, (0, 0))

        new_size = (80, 80)
        resized_globe = GLOBE_IMG.resize(new_size, Image.Resampling.LANCZOS)
        main_img.paste(resized_globe, (227, 165), resized_globe)

        emoji_img = get_weather_emoji(weather_data['description'])
        main_img.paste(emoji_img, (985, 15), emoji_img)
        
        draw = ImageDraw.Draw(main_img)

        city_name = weather_data['city'][:15] + "..." if len(weather_data['city']) > 15 else weather_data['city']
        draw.text((325, 170), f"{city_name}, {weather_data['country']}", font=FONT_LARGE, fill="#404040")

        current_time_local = weather_data['current_time_local']
        current_time_str = current_time_local.strftime("%A, %d %b %H:%M")
        
        month_translation = {
            'Jan': 'янв', 'Feb': 'фев', 'Mar': 'мар', 'Apr': 'апр',
            'May': 'май', 'Jun': 'июн', 'Jul': 'июл', 'Aug': 'авг',
            'Sep': 'сен', 'Oct': 'окт', 'Nov': 'ноя', 'Dec': 'дек'
        }
        day_translation = {
            'Monday': 'понедельник', 'Tuesday': 'вторник', 'Wednesday': 'среда', 
            'Thursday': 'четверг', 'Friday': 'пятница', 'Saturday': 'суббота', 'Sunday': 'воскресенье'
        }
        
        for eng, rus in day_translation.items():
            current_time_str = current_time_str.replace(eng, rus)
        for eng, rus in month_translation.items():
            current_time_str = current_time_str.replace(eng, rus)
            
        draw.text((230, 265), current_time_str, font=FONT_MEDIUM, fill=(192, 192, 194))

        temp_text = f"{weather_data['temp']:+.1f}°".replace('.', ',')
        draw.text((230, 360), temp_text, font=FONT_TEMP, fill="#404040")

        right_block_x = calculate_dynamic_position(temp_text)

        color = "#7A7B81"
        draw.text((right_block_x, 390), f"{weather_data['pressure']} мм | {weather_data['humidity']}%", font=FONT_MEDIUM, fill=color)
        draw.text((right_block_x, 460), f"{weather_data['wind_speed']} м/с, {weather_data['wind_dir']}", font=FONT_MEDIUM, fill=color)
        draw.text((right_block_x, 530), f"ощущается {weather_data['feels_like']:+.1f}°".replace('.', ','), font=FONT_MEDIUM, fill=color)

        draw.text((230, 630), weather_data['description'].capitalize(), font=FONT_LARGE, fill="#404040")

        sunrise_time = weather_data['sunrise']
        sunset_time = weather_data['sunset']
        
        draw.text((230, 728), f"Восход {sunrise_time} | Закат {sunset_time}", font=FONT_LARGE, fill="#404040")
        
        main_img.save(output_path, 'PNG', optimize=True, quality=85)
        return True
        
    except Exception as e:
        logger.error(f"Ошибка создания карточки: {e}")
        return False

# Алиас для обратной совместимости
create_weather_card = create_weather_card_async
