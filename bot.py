import asyncio
import structlog
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from handlers import routers
from utils.image_utils import load_resources
from utils.my_wraps import wrap_loggers


logger = structlog.getLogger(__name__)


async def main():
    wrap_loggers()
    load_resources()

    # Инициализация бота
    bot = Bot(
        token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    logger.debug("Привязываем роутеры к диспетчеру.", routers=routers)
    dp.include_routers(*routers)

    logger.info("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
