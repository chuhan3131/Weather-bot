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
    first_octet = random.choice([1, 14, 23, 27, 36, 37, 39, 42, 49, 50, 58, 59, 60, 61, 101, 102, 103, 104, 105, 106, 107, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223])
    second_octet = random.randint(0, 255)
    third_octet = random.randint(0, 255)
    fourth_octet = random.randint(1, 254)
    
    return f"{first_octet}.{second_octet}.{third_octet}.{fourth_octet}"

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
