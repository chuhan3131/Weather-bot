import os
import time
import random
import string
import shutil
import logging
import ipaddress

logger = logging.getLogger(__name__)

def generate_random_ip():
    """Генерация случайного публичного IP адреса"""
    while True:

        first_octet = random.randint(1, 223)  

        if first_octet == 10:
            continue
        if first_octet == 172:
            second_octet = random.randint(0, 255)
            if 16 <= second_octet <= 31:
                continue
        if first_octet == 192 and random.randint(0, 255) == 168:
            continue
        if first_octet == 169 and random.randint(0, 255) == 254:
            continue
        
        second_octet = random.randint(0, 255)
        third_octet = random.randint(0, 255)
        fourth_octet = random.randint(1, 254)  
        
        ip = f"{first_octet}.{second_octet}.{third_octet}.{fourth_octet}"

        try:
            ip_obj = ipaddress.IPv4Address(ip)
            if not ip_obj.is_private and not ip_obj.is_multicast and not ip_obj.is_loopback:
                return ip
        except:
            continue

def generate_random_filename(prefix="weather", extension="png"):
    """Генерация случайного имени карточки погоды"""
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    return f"{prefix}_{random_string}.{extension}"

def cleanup_files(*file_paths):
    """Удаление файлов после использования"""
    for file_path in file_paths:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Удален файл: {file_path}")
                    break
                else:
                    logger.info(f"Файл уже удален: {file_path}")
                    break
            except Exception as e:
                logger.warning(f"Попытка {attempt + 1} удаления {file_path}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(0.1)
                else:
                    logger.error(f"Не удалось удалить {file_path} после {max_attempts} попыток")

def upload_to_website(local_path, filename):
    """Копирование файла"""
    try:
        shutil.copy2(local_path, filename)
        return True
    except Exception as e:
        logger.error(f"Ошибка копирования файла: {e}")
        return False
