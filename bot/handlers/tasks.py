"""
Хендлеры для работы с задачами:
- /add
- /list
- /list_csv
"""

import csv
import html
import io

from aiogram import Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types.input_file import BufferedInputFile

from bot.db.sqlite import Database
from bot.keyboards.common import main_keyboard
from bot.states.tasks import AddTaskStates

router = Router()


def _format_user(message: Message) -> str:
    """
    Пытаемся красиво определить "пользователя".
    В командных чатах удобно видеть username, но он есть не у всех.
    """
    if message.from_user is None:
        return "unknown"
    return message.from_user.username or message.from_user.full_name or "unknown"

def _short_dt(iso_dt: str) -> str:
    """
    Превращаем ISO-дату в короткий вид для списка.
    Пример: 2026-01-17T12:34:56+00:00 -> 2026-01-17 12:34
    """
    return iso_dt.replace("T", " ")[:16]


@router.message(Command("add"))
async def cmd_add(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    db: Database,
) -> None:
    """
    /add — добавление задачи.

    Поддерживаем 2 сценария:
    - /add <текст>  → добавляем задачу сразу
    - /add          → просим пользователя прислать текст следующим сообщением (FSM)
    """
    # Варианты использования:
    # 1) /add <текст задачи>  — добавляем сразу
    # 2) /add                — просим пользователя прислать текст
    text = (command.args or "").strip()
    if not text:
        await state.set_state(AddTaskStates.waiting_text)
        await message.answer(
            "Ок! Напишите текст задачи следующим сообщением.\n\n"
            "Пример: Купить молоко\n\n"
            "Когда отправите текст — я сохраню задачу и подскажу, что делать дальше.",
            reply_markup=main_keyboard(),
        )
        return

    user = _format_user(message)
    task_id = await db.add_task(text=text, user=user)
    await state.clear()
    await message.answer(
        "Готово! Я сохранил задачу.\n\n"
        f"ID: <b>{task_id}</b>\n"
        f"Текст: <code>{html.escape(text)}</code>\n\n"
        "Дальше можно посмотреть общий список: /list",
        reply_markup=main_keyboard(),
    )


@router.message(StateFilter(AddTaskStates.waiting_text))
async def add_task_waiting_text(message: Message, state: FSMContext, db: Database) -> None:
    """
    Срабатывает после /add без аргументов — когда бот ждёт текст задачи.

    Если текст пустой, просим повторить.
    Если текст есть — сохраняем задачу и выходим из состояния.
    """
    # Пользователь вызвал /add без текста — значит теперь мы ждём обычное сообщение.
    text = (message.text or "").strip()
    if not text:
        await message.answer(
            "Кажется, текст задачи пустой.\n"
            "Пожалуйста, отправьте текст задачи одним сообщением.",
            reply_markup=main_keyboard(),
        )
        return

    user = _format_user(message)
    task_id = await db.add_task(text=text, user=user)
    await state.clear()

    await message.answer(
        "Отлично! Задача сохранена.\n\n"
        f"ID: <b>{task_id}</b>\n"
        f"Текст: <code>{html.escape(text)}</code>\n\n"
        "Хотите увидеть все задачи? Напишите /list",
        reply_markup=main_keyboard(),
    )


@router.message(Command("list"))
async def cmd_list(message: Message, db: Database) -> None:
    """
    /list — показывает задачи в чате.

    Если задач нет — объясняем, что список пуст, и подсказываем /add.
    Если задачи есть — выводим нумерованный список с автором и датой.
    """
    tasks = await db.list_tasks()
    if not tasks:
        await message.answer(
            "Пока задач нет — список пуст.\n\n"
            "Добавьте первую задачу командой /add (и я попрошу текст).",
            reply_markup=main_keyboard(),
        )
        return

    lines = [
        "<b>Список задач:</b>",
        "Вот что сейчас в общем списке:",
        "",
    ]
    for i, t in enumerate(tasks, start=1):
        # Экранируем текст, чтобы HTML-разметка не ломалась из-за символов <, > и т.п.
        text = html.escape(t.text)
        user = html.escape(t.user)
        dt = html.escape(_short_dt(t.created_at))
        lines.append(f"{i}. {text} — <i>{user}</i>, {dt}")

    await message.answer("\n".join(lines), reply_markup=main_keyboard())


@router.message(Command("list_csv"))
async def cmd_list_csv(message: Message, db: Database) -> None:
    """
    /list_csv — отправляет CSV-файл со списком задач.

    Важно для Excel (Windows):
    - UTF-8 с BOM (utf-8-sig), чтобы кириллица открывалась без ручного выбора кодировки
    - разделитель ';', потому что в русской локали Excel часто ожидает именно его
    """
    tasks = await db.list_tasks()
    if not tasks:
        await message.answer(
            "Список задач пуст — CSV-файл пока формировать нечего.",
            reply_markup=main_keyboard(),
        )
        return

    # Генерируем CSV в памяти (без временных файлов на диске).
    # newline="" — рекомендация из документации csv, чтобы модуль csv сам корректно
    # управлял переводами строк (особенно важно на Windows).
    buffer = io.StringIO(newline="")
    # delimiter=';' помогает Excel сразу разбить значения по колонкам при двойном клике.
    writer = csv.writer(buffer, delimiter=";")
    # Порядок колонок по заданию:
    # id, text, user, created_at, status, category
    writer.writerow(["id", "text", "user", "created_at", "status", "category"])
    for t in tasks:
        writer.writerow([t.id, t.text, t.user, t.created_at, t.status, t.category])

    # Важно для Excel (Windows):
    # - обычный UTF-8 Excel при двойном клике часто не распознаёт
    # - UTF-8 с BOM ("utf-8-sig") Excel распознаёт почти всегда корректно
    data = buffer.getvalue().encode("utf-8-sig")
    csv_file = BufferedInputFile(data, filename="tasks.csv")

    await message.answer_document(
        csv_file,
        caption=(
            "Отправляю CSV-файл со списком задач.\n"
            "Внутри колонки: id, text, user, created_at."
        ),
        reply_markup=main_keyboard(),
    )


