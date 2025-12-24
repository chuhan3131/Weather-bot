from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from structlog import get_logger
import asyncio
from datetime import datetime
from aiogram.filters import Command
from aiogram import types, Router


router = Router(name=__name__)
logger = get_logger(__name__)


@router.message(Command("start"))
async def start_cmd(message: types.Message, bot: Bot):
    name = message.from_user.first_name or ""
    username_bot = await bot.get_me()
    bot_name = username_bot.username
    lang_code = message.from_user.language_code

    await message.answer("hi", parse_mode="HTML")
