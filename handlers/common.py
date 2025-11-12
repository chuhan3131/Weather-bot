from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from structlog import get_logger


rt = Router(name=__name__)
logger = get_logger(__name__)


@rt.message(Command("start"))
async def process_start_command(message: Message, bot: Bot):
    if message.from_user is not None:
        sender = message.from_user
    elif message.sender_chat is not None:
        sender = message.sender_chat
    else:
        logger.error(
            "Не удалось получить отправителя",
            chat_id=message.chat.id,
            message_id=message.chat.id,
        )
        return
    username_bot = await bot.get_me()
    await message.answer(
        f"<b>Привет, {sender.full_name}!</b>\n\n"
        f"Для просмотра погоды пропиши <code>@{username_bot.username} место/IP</code>\n\n"
        f"Используй <code>@{username_bot.username} random</code> для случайной локации"
    )
