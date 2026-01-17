"""
Простые "модели" (структуры данных), чтобы было удобнее работать с задачами.

Это не ORM, а обычный dataclass.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    """Одна задача из таблицы tasks."""

    id: int
    text: str
    user: str
    created_at: str  # ISO-строка времени (например, 2026-01-17T12:34:56)
    status: str      # например: todo / done
    category: str    # например: general / bug / feature


