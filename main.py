"""
Точка входа в приложение.

Запуск:
    python main.py

Перед запуском:
    - установите зависимости из requirements.txt
    - задайте BOT_TOKEN (например, через файл .env)
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from bot.config import load_config
from bot.db.sqlite import Database
from bot.handlers import start_router, tasks_router
from bot.middlewares.db import DbMiddleware


async def main() -> None:
    # Загружаем переменные окружения из .env (если файл существует).
    load_dotenv()

    # Читаем настройки (токен бота и путь к БД).
    config = load_config()

    # Логи в консоль — полезно при обучении и отладке.
    logging.basicConfig(level=logging.INFO)

    # Создаём экземпляры Bot и Dispatcher.
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    # Включаем простое хранилище FSM в памяти — нужно, чтобы /add мог "ждать" текст задачи.
    dp = Dispatcher(storage=MemoryStorage())

    # Инициализируем БД и создаём таблицы, если их ещё нет.
    db = Database(db_path=config.db_path)
    await db.init()

    # Middleware добавит db в data каждого апдейта, а aiogram сможет передать db в хендлеры.
    dp.update.middleware(DbMiddleware(db))

    # Подключаем роутеры (обработчики команд).
    dp.include_router(start_router)
    dp.include_router(tasks_router)

    # Запускаем long-polling (бот будет получать апдейты от Telegram).
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


