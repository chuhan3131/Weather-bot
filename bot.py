from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import asyncio
import logging

from config import BOT_TOKEN
from utils.image_utils import load_resources
from handlers.inline import inline_weather_query

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command('start'))
async def process_start_command(message: types.Message):
    username_bot = await bot.get_me()
    await message.answer(
        f"<b>Привет, {message.from_user.full_name}!</b>\n\n"
        f"Для просмотра погоды пропиши <code>@{username_bot.username} место/IP</code>\n\n"
        f"Используй <code>@{username_bot.username} random</code> для случайной локации"
    )

@dp.inline_query()
async def inline_query_handler(query: types.InlineQuery):
    username_bot = await bot.get_me()
    await inline_weather_query(query, username_bot.username)

async def main():
    load_resources()
    
    logger.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
