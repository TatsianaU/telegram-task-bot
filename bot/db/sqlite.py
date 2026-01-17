"""
Минимальный слой работы с SQLite.

Важно для новичков:
- aiogram (v3) работает асинхронно
- sqlite3 из стандартной библиотеки синхронный (может "блокировать" цикл событий)

Поэтому мы выполняем операции с БД в отдельном потоке через asyncio.to_thread.
"""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime, timezone
from threading import Lock
from typing import List, Sequence

from bot.db.models import Task


class Database:
    def __init__(self, db_path: str) -> None:
        """
        Создаёт подключение к SQLite.

        Args:
            db_path: путь к файлу базы данных (например, tasks.db)
        """
        self._db_path = db_path
        self._lock = Lock()
        # check_same_thread=False позволяет использовать соединение из разных потоков.
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    async def init(self) -> None:
        """
        Инициализирует базу данных:
        - создаёт таблицу tasks, если её нет
        - выполняет простую миграцию, если таблица устарела (добавляет новые колонки)
        """
        await asyncio.to_thread(self._init_sync)

    def _init_sync(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    user TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'todo',
                    category TEXT NOT NULL DEFAULT 'general'
                )
                """
            )
            self._migrate_sync()
            self._conn.commit()

    def _get_columns_sync(self) -> Sequence[str]:
        """
        Возвращает список колонок таблицы tasks.

        Это нужно, чтобы понимать — устарела схема или нет.
        """
        rows = self._conn.execute("PRAGMA table_info(tasks)").fetchall()
        return [str(r["name"]) for r in rows]

    def _migrate_sync(self) -> None:
        """
        Простейшая миграция схемы:
        если в старой базе нет новых колонок, добавляем их через ALTER TABLE.

        Почему так:
        - SQLite не умеет легко менять схему как Postgres
        - но ADD COLUMN — простая и безопасная операция
        """
        cols = set(self._get_columns_sync())

        # В старой версии проекта таблица была: id, text, user, created_at
        # Добавляем недостающие поля, чтобы соответствовать новой схеме.
        if "status" not in cols:
            self._conn.execute(
                "ALTER TABLE tasks ADD COLUMN status TEXT NOT NULL DEFAULT 'todo'"
            )
        if "category" not in cols:
            self._conn.execute(
                "ALTER TABLE tasks ADD COLUMN category TEXT NOT NULL DEFAULT 'general'"
            )

    async def add_task(
        self,
        text: str,
        user: str,
        status: str = "todo",
        category: str = "general",
    ) -> int:
        """
        Добавляет задачу и возвращает её id.

        Args:
            text: текст задачи
            user: автор (username или имя)
            status: статус задачи (по умолчанию todo)
            category: категория задачи (по умолчанию general)
        """
        created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        return await asyncio.to_thread(
            self._add_task_sync,
            text,
            user,
            created_at,
            status,
            category,
        )

    def _add_task_sync(
        self,
        text: str,
        user: str,
        created_at: str,
        status: str,
        category: str,
    ) -> int:
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT INTO tasks(text, user, created_at, status, category)
                VALUES (?, ?, ?, ?, ?)
                """,
                (text, user, created_at, status, category),
            )
            self._conn.commit()
            return int(cur.lastrowid)

    async def list_tasks(self) -> List[Task]:
        """
        Возвращает все задачи (от старых к новым).

        Returns:
            Список Task
        """
        return await asyncio.to_thread(self._list_tasks_sync)

    def _list_tasks_sync(self) -> List[Task]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT id, text, user, created_at, status, category
                FROM tasks
                ORDER BY id ASC
                """
            ).fetchall()
        return [
            Task(
                id=int(row["id"]),
                text=str(row["text"]),
                user=str(row["user"]),
                created_at=str(row["created_at"]),
                status=str(row["status"]),
                category=str(row["category"]),
            )
            for row in rows
        ]


