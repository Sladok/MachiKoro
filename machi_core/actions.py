"""
Логика действий в игре.

Здесь:
    - типы действий;
    - поля у действий;

"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional



class ActionType(str, Enum):
    ROLL = "roll"
    BUY_CARD = "buy_card"
    BUILD_LANDMARK = "build_landmark"
    END_BUY = "end_buy"  # Завершить фазу покупки


@dataclass
class Action:
    """
    Действие игрока.
    Для разных типов действий разные поля
    """
    type: ActionType
    card_id: Optional[str] = None  # для BUY_CARD / BUILD_LANDMARK
