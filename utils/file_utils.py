import os
import time
import httpx
import random
import string
import structlog
from io import BytesIO

logger = structlog.get_logger(__name__)
file_tokens: dict[str, str] = dict()


def generate_random_ip():
    """Generate a random public IP address"""

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
    """Generate a random weather card name"""
    random_string = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=16)
    )
    return f"{prefix}_{random_string}.{extension}"


async def cleanup_files(*file_paths: str):
    """Deleting files after use"""
    for file_path in file_paths:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info("File deleted", file_path=file_path)
                    break
                else:
                    logger.warn("File already deleted", file_path=file_path)
                    break
            except Exception as ex:
                logger.warning(
                    f"Attempt {attempt + 1} to delete {file_path}: {ex}",
                    attempt=attempt + 1,
                    file_path=file_path,
                    caught_exception=(repr(ex), str(ex)),
                )
                if attempt < max_attempts - 1:
                    time.sleep(0.1)
                else:
                    logger.error(
                        f"Failed to delete {file_path} after {max_attempts} attempts",
                        file_path=file_path,
                        max_attempts=max_attempts,
                        exc_info=True,
                    )


async def upload_to_website(
    local_io: BytesIO, filename: str
) -> tuple[str, str] | None:
    """Copying file. Temporarily to 0x0.st

    Args:
        local_io (BytesIO): Bytes of the file to copy

    Returns:
        tuple[str, str] | None: Returns a link to the file and a token to delete the file
    """
    try:
        async with httpx.AsyncClient() as client:
            url = "https://0x0.st/"
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
                    "Error from 0x0.st",
                    response=response,
                    status_code=response.status_code,
                    content=response.content,
                )
                return None

        logger.debug(
            "File copied to server", from_io=local_io, output_file=filename
        )
        file_tokens[result] = x_token

        return result, x_token
    except Exception as ex:
        logger.error(
            "File copy error",
            caught_exception=(repr(ex), str(ex)),
            exc_info=True,
        )
        return None


async def delete_file(file_url: str):
    """Delete file from 0x0.st

    Args:
        file_url (str): link to file of the form "https://0x0.st/AbCd.txt"
    """
    token = file_tokens.get(file_url)
    if not token:
        logger.warn("didn't find cached token", file_url=file_url)
        return
    await delete_file_(file_url=file_url, x_token=token)


async def delete_file_(file_url: str, x_token: str):
    """Delete file from 0x0.st

    Args:
        file_url (str): link to the file of the form "https://0x0.st/AbCd.txt"
        x_token (str): X-Token from the header after downloading the file
    """
    if not file_url.startswith("https://0x0.st/"):
        raise ValueError("Only files from 0x0.st are allowed!")

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
                "Error from 0x0.st",
                response=response,
                status_code=response.status_code,
                content=response.content,
            )
            return None