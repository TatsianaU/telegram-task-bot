"""
FSM-состояния для команд, связанных с задачами.
"""

from aiogram.fsm.state import State, StatesGroup


class AddTaskStates(StatesGroup):
    # Состояние: бот ждёт, что пользователь отправит текст задачи.
    waiting_text = State()


