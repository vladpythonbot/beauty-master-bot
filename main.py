import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from database import Database
from handlers import register_handlers
from webapp import create_web_app


async def start_web_server(app: web.Application, host: str, port: int) -> web.AppRunner:
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logging.info("Mini App server started on %s:%s", host, port)
    return runner


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    config = load_config()
    db = Database(config.db_path)
    await db.init()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(register_handlers(db, config.admin_id, config.mini_app_url))

    web_app = create_web_app(db, bot, config.bot_token, config.admin_id)
    runner = await start_web_server(web_app, config.host, config.port)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
