"""
Пакет с роутами (обработчиками команд).

Мы экспортируем роутеры отдельно, чтобы main.py мог просто их импортировать.
"""

from bot.handlers.start import router as start_router
from bot.handlers.tasks import router as tasks_router

__all__ = ["start_router", "tasks_router"]


