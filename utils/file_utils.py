import os
import time
import httpx
import random
import string
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


async def upload_to_website(
    local_io: BytesIO, filename: str
) -> tuple[str, str] | None:
    """Копирование файла. Временно на 0x0.st

    Args:
        local_io (BytesIO): Байты файла для копирования
        filename (str): Название будущего файла

    Returns:
        tuple[str, str] | None: Возвращает ссылку на файл и токен для удаления файла
    """
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://0x0.st/{filename}"
            response = await client.post(
                url,
                files=dict(file=local_io),
                headers={"User-Agent": "AlekzumWeatherBot/1.0"},
            )
            if response.status_code == 200:
                result = response.text
                x_token = response.headers["X-Token"]
            else:
                logger.error(
                    "Ошибка от 0x0.st",
                    response=response,
                    status_code=response.status_code,
                    content=response.content,
                )
                return None

        # with open(filename, "wb") as file:
        #     shutil.copyfileobj(local_io, file)
        logger.debug(
            "Файл скопирован на сервер", from_io=local_io, output_file=filename
        )
        return result, x_token
    except Exception as ex:
        logger.error(
            "Ошибка копирования файла",
            caught_exception=(repr(ex), str(ex)),
            exc_info=True,
        )
        return None


async def delete_file(file_url: str, x_token: str):
    """Удаление файла с 0x0.st

    Args:
        file_url (str): ссылка на файл вида "https://0x0.st/AbCd.txt"
        x_token (str): X-Token из заголовка после загрузки файла
    """
    if not file_url.startswith("https://0x0.st/"):
        raise ValueError("Требуется файл только из 0x0.st!")

    async with httpx.AsyncClient() as client:
        file_url = file_url.removeprefix("https://0x0.st/")
        url = f"https://0x0.st/{file_url}"
        response = await client.post(
            url,
            headers={"User-Agent": "AlekzumWeatherBot/1.0"},
            data=dict(token=x_token),
        )
        if response.status_code == 200:
            return True
        else:
            logger.error(
                "Ошибка от 0x0.st",
                response=response,
                status_code=response.status_code,
                content=response.content,
            )
            return None
