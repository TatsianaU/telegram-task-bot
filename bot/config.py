"""
Модуль конфигурации.

Здесь мы читаем переменные окружения и собираем настройки в один объект.
Так новичкам проще: всё, что связано с настройками, в одном месте.
"""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Config:
    bot_token: str
    db_path: str


def load_config() -> Config:
    """
    Читает настройки из переменных окружения.

    Ожидаемые переменные:
        BOT_TOKEN - токен Telegram-бота
        DB_PATH   - путь к SQLite базе (опционально)
    """
    bot_token = (os.getenv("BOT_TOKEN") or "").strip()
    if not bot_token:
        raise RuntimeError(
            "Не найден BOT_TOKEN. Создайте файл .env (см. env.example) "
            "или задайте переменную окружения BOT_TOKEN."
        )

    db_path = (os.getenv("DB_PATH") or "tasks.db").strip()

    return Config(bot_token=bot_token, db_path=db_path)


