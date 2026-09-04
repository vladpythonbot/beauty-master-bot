import asyncio
import logging
from contextlib import suppress
from datetime import datetime

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from database import Database
from handlers import register_handlers
from texts import format_date, support_text
from webapp import create_web_app


REMINDER_MINUTES_BEFORE = 120


async def start_web_server(app: web.Application, host: str, port: int) -> web.AppRunner:
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logging.info("Mini App server started on %s:%s", host, port)
    return runner


async def reminder_loop(db: Database, bot: Bot, support_username: str = "") -> None:
    while True:
        try:
            applications = await db.get_due_reminders(datetime.now(), REMINDER_MINUTES_BEFORE)
            for application in applications:
                await bot.send_message(
                    application["user_id"],
                    (
                        "⏰ Нагадування про запис\n\n"
                        f"Дата: {format_date(application['desired_date'])}\n"
                        f"Час: {application['desired_time']}\n"
                        f"Майстер: {application['schedule_group'] or 'майстер'}\n"
                        f"Послуга:\n{application['service']}\n\n"
                        f"{support_text(support_username)}"
                    ),
                )
                await db.mark_reminder_sent(application["id"])
        except Exception:
            logging.exception("Failed to send appointment reminders")
        await asyncio.sleep(300)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    config = load_config()
    db = Database(config.db_path)
    await db.init()
    logging.info("Database path: %s", config.db_path)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(register_handlers(db, config.admin_id, config.mini_app_url, config.support_username))

    web_app = create_web_app(db, bot, config.bot_token, config.admin_id, config.public_admin_mode, config.support_username)
    runner = await start_web_server(web_app, config.host, config.port)
    reminders_task = asyncio.create_task(reminder_loop(db, bot, config.support_username))

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        reminders_task.cancel()
        with suppress(asyncio.CancelledError):
            await reminders_task
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
