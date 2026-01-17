"""
Хендлеры команды /start.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.common import main_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """
    /start — приветствие и краткая справка по возможностям бота.

    Пользователь должен сразу понять:
    - что это за бот
    - какие команды доступны
    - что делать дальше
    """
    # reply_markup добавляет "кнопки" под полем ввода.
    await message.answer(
        "Привет! Я бот для командной работы со списком задач.\n\n"
        "Я помогу вам быстро добавлять задачи в общий список и выгружать их в CSV.\n\n"
        "<b>Доступные команды:</b>\n"
        "• /add — добавить задачу\n"
        "• /list — показать список задач\n"
        "• /list_csv — выгрузить задачи в CSV\n\n"
        "Готовы? Начните с /add",
        reply_markup=main_keyboard(),
    )


