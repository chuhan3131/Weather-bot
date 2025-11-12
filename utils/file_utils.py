import os
import time
import random
import string
import shutil
import structlog
from io import BytesIO

logger = structlog.get_logger(__name__)


def generate_random_ip():
    """Генерация случайного публичного IP адреса"""

    first_octet = random.choice(
        [
            1,
            14,
            23,
            27,
            36,
            37,
            39,
            42,
            49,
            50,
            *range(58, 61),
            *range(101, 107),
            *range(110, 126),
            *range(133, 223),
        ]
    )
    second_octet = random.randint(0, 255)
    third_octet = random.randint(0, 255)
    fourth_octet = random.randint(1, 254)

    return f"{first_octet}.{second_octet}.{third_octet}.{fourth_octet}"


def generate_random_filename(prefix="weather", extension="png"):
    """Генерация случайного имени карточки погоды"""
    random_string = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=16)
    )
    return f"{prefix}_{random_string}.{extension}"


def cleanup_files(*file_paths: str):
    """Удаление файлов после использования"""
    for file_path in file_paths:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info("Удален файл", file_path=file_path)
                    break
                else:
                    logger.warn("Файл уже удален", file_path=file_path)
                    break
            except Exception as ex:
                logger.warning(
                    f"Попытка {attempt + 1} удаления {file_path}: {ex}",
                    attempt=attempt + 1,
                    file_path=file_path,
                    caught_exception=(repr(ex), str(ex)),
                )
                if attempt < max_attempts - 1:
                    time.sleep(0.1)
                else:
                    logger.error(
                        f"Не удалось удалить {file_path} после {max_attempts} попыток",
                        file_path=file_path,
                        max_attempts=max_attempts,
                        exc_info=True,
                    )


def upload_to_website(local_io: BytesIO, filename: str):
    """Копирование файла"""
    try:
        with open(filename, "wb") as file:
            shutil.copyfileobj(local_io, file)
        return True
    except Exception as ex:
        logger.error(
            "Ошибка копирования файла",
            caught_exception=(repr(ex), str(ex)),
            exc_info=True,
        )
        return False
