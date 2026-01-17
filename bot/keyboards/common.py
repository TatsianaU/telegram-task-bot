"""
Клавиатуры (ReplyKeyboardMarkup) — это кнопки под полем ввода.

Важно:
- команды всё равно можно вводить руками (/add, /list, ...)
- кнопки просто помогают новичкам и ускоряют работу
"""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            # Важно для UX: кнопка вставляет текст в поле ввода.
            # Поэтому делаем коротко "/add", чтобы не подставлялся шаблон "Текст задачи".
            [KeyboardButton(text="/add")],
            [KeyboardButton(text="/list"), KeyboardButton(text="/list_csv")],
        ],
        # Делаем клавиатуру "постоянной" — Telegram будет держать её в поле видимости
        # (пользователь меньше "теряет" кнопки во время диалога).
        is_persistent=True,
        resize_keyboard=True,
        input_field_placeholder="Введите команду…",
    )


