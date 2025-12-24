import os
import time
import httpx
import random
import string
from io import BytesIO

from utils.logger import logger

file_tokens: dict[str, str] = dict()


def generate_random_ip():
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
    random_string = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=16)
    )
    return f"{prefix}_{random_string}.{extension}"


async def cleanup_files(*file_paths: str):
    for file_path in file_paths:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info("File deleted")
                    break
                else:
                    logger.warn("File already deleted")
                    break
            except Exception as ex:
                logger.warning(f"Attempt {attempt + 1} to delete {file_path}: {ex}")
                if attempt < max_attempts - 1:
                    time.sleep(0.1)
                else:
                    logger.error(f"Failed to delete {file_path} after {max_attempts} attempts")