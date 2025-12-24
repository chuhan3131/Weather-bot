import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers.user_handlers import router as common_router
from handlers.inline import rt as inline_router
from utils.logger import logger

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():
    dp.include_router(common_router)
    dp.include_router(inline_router)
    
    logger.info("Bot started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
