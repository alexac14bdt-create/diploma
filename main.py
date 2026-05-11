import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from dotenv import load_dotenv
import os

from bot.handlers import router

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="search",   description="🔍 Новый поиск"),
        BotCommand(command="nosology", description="♿ Сменить нозологию"),
        BotCommand(command="start",    description="🏠 Главное меню"),
        BotCommand(command="help",     description="ℹ️ Справка"),
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Команды меню установлены")


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в .env файле!")

    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp  = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await set_bot_commands(bot)

    logger.info("🔨 Строим граф доступности...")
    try:
        from db.base import AsyncSessionLocal
        from services.graph_recommender import build_graph_from_db
        async with AsyncSessionLocal() as session:
            await build_graph_from_db(session)
        logger.info("✅ Граф доступности построен")
    except Exception as e:
        logger.warning(f"⚠️  Граф не построен: {e} — бот работает без графа")

    logger.info("🤖 Бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
