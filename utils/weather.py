import aiohttp
from datetime import datetime, timezone, timedelta
import logging
import random
from config import OPENWEATHERMAP_API_KEY, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# Кэш для погодных данных
weather_cache = {}

def wind_direction(deg):
    """Определение направления ветра"""
    directions = ['С', 'СВ', 'В', 'ЮВ', 'Ю', 'ЮЗ', 'З', 'СЗ']
    return directions[round(deg / 45) % 8]

def generate_random_ip():
    """Генерация случайного публичного IP адреса"""
    first_octet = random.choice([1, 14, 23, 27, 36, 37, 39, 42, 49, 50, 58, 59, 60, 61, 101, 102, 103, 104, 105, 106, 107, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223])
    return f"{first_octet}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

async def get_location_async(ip):
    """Асинхронное получение локации по IP"""
    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"http://ip-api.com/json/{ip}") as response:
                data = await response.json()
                if data['status'] == 'success':
                    return data['city'], data['countryCode']
                return None, None
    except Exception as e:
        logger.error(f"Ошибка получения локации для IP {ip}: {e}")
        return None, None

def process_weather_data(data):
    """Обработка данных погоды"""
    if data.get('cod') != 200:
        return None

    main = data['main']
    weather = data['weather'][0]
    wind = data['wind']
    sys = data['sys']

    timezone_offset = data.get('timezone', 0)
    sunrise_utc = sys['sunrise']
    sunset_utc = sys['sunset']

    sunrise_local = sunrise_utc + timezone_offset
    sunset_local = sunset_utc + timezone_offset
    
    sunrise_str = datetime.fromtimestamp(sunrise_local).strftime('%H:%M')
    sunset_str = datetime.fromtimestamp(sunset_local).strftime('%H:%M')

    current_time_utc = datetime.now(timezone.utc)
    current_time_local = current_time_utc + timedelta(seconds=timezone_offset)
    
    result = {
        'city': data['name'],
        'country': sys['country'],
        'temp': main['temp'],
        'feels_like': main['feels_like'],
        'humidity': main['humidity'],
        'pressure': round(main['pressure'] * 0.750062),
        'wind_speed': wind['speed'],
        'wind_dir': wind_direction(wind['deg']) if 'deg' in wind else 'N/A',
        'description': weather['description'],
        'sunrise': sunrise_str,
        'sunset': sunset_str,
        'timezone_offset': timezone_offset,
        'current_time_local': current_time_local
    }
    
    logger.info(f"Погода для {data['name']}: {result['temp']}°C, {result['description']}")
    return result

async def get_current_weather_async(city, country_code=None):
    """Асинхронное получение погоды с кэшированием"""
    cache_key = f"{city}_{country_code}" if country_code else city
    
    # Проверка кэша
    if cache_key in weather_cache:
        cache_data, timestamp = weather_cache[cache_key]
        if (datetime.now().timestamp() - timestamp) < 600: 
            logger.info(f"Использован кэш для: {city}")
            return cache_data
    
    try:
        query = f"{city},{country_code}" if country_code else city
        url = "http://api.openweathermap.org/data/2.5/weather"
        
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            params = {
                'q': query,
                'units': 'metric', 
                'APPID': OPENWEATHERMAP_API_KEY,
                'lang': 'ru'
            }
            async with session.get(url, params=params) as response:
                data = await response.json()
                weather_data = process_weather_data(data)
                
                # Сохранение в кэш
                if weather_data:
                    weather_cache[cache_key] = (weather_data, datetime.now().timestamp())
                    # Очистка старого кэша
                    if len(weather_cache) > 100:
                        oldest_key = next(iter(weather_cache))
                        weather_cache.pop(oldest_key)
                
                return weather_data
                
    except Exception as e:
        logger.error(f"Ошибка получения погоды для {city}: {e}")
        return None
