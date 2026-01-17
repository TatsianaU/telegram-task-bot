"""
Middleware для добавления объекта БД (db) в каждый апдейт.

Так мы можем просто писать в хендлерах:
    async def handler(message: Message, db: Database): ...

И aiogram сам подставит db.
"""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.db.sqlite import Database


class DbMiddleware(BaseMiddleware):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["db"] = self._db
        return await handler(event, data)


