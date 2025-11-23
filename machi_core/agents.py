# machi_core/agents.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, List
import random

from .state import GameState
from .actions import Action, ActionType
from .rules import legal_actions


class Agent(ABC):
    """Базовый интерфейс агента (человек / бот / RL и т.п.)."""

    @abstractmethod
    def select_action(self, state: GameState, player_index: int) -> Action:
        """Выбрать одно допустимое действие для игрока."""
        raise NotImplementedError


class RandomBot(Agent):
    """Простой бот: *адекватный* рандом, без мысли.

    Приоритет:
    - если можно ROLL — всегда ROLL;
    - в фазе BUY сперва строит достопримечательность, потом покупает карты;
    - если ничего купить нельзя — END_BUY.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)

    def select_action(self, state: GameState, player_index: int) -> Action:
        actions: List[Action] = legal_actions(state, player_index)
        if not actions:
            raise RuntimeError("У бота нет допустимых действий")

        # 1) ROLL (один вариант)
        roll = [a for a in actions if a.type == ActionType.ROLL]
        if roll:
            return self._rng.choice(roll)

        # 2) В фазе BUY — BUILD > BUY > END_BUY
        build = [a for a in actions if a.type == ActionType.BUILD_LANDMARK]
        buy   = [a for a in actions if a.type == ActionType.BUY_CARD]
        end   = [a for a in actions if a.type == ActionType.END_BUY]

        if build:
            return self._rng.choice(build)
        if buy:
            return self._rng.choice(buy)
        if end:
            return end[0]

        # На всякий случай fallback
        return self._rng.choice(actions)
