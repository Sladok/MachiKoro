"""
Стурктуры данных для состояния игры

Нет логики ходов, кубиков и т.д.
Только то, что в памяти, игроки, рынок, фаза, последний бросок
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from random import choice

class Phase(str, Enum):
    """
    Фаза ходов.
    На этапы, чтобы UI и бот потом реагировали на шаги
    """

    ROLL = "roll"
    RESOLVE = "resolve"
    BUY = "buy"
    GAME_OVER = "game_over"


@dataclass
class PlayerState:
    """
    Состояние игрока:
        - Монеты;
        - Предприятия (карта --> количество)
        - Достопримечательности (id --> построена ли)
    """
    name: str = ""
    coins: int = 0
    establishments: Dict[str, int] = field(default_factory=dict)
    landmarks: Dict[str, bool] = field(default_factory=dict)

    def count_of(self, card_id: str) -> int:
        return self.establishments.get(card_id, 0)

    def add_card(self, card_id: str, count: int = 1) -> None:
        self.establishments[card_id] = self.establishments.get(card_id, 0) + count
    
    def has_built(self, landmark_id: str) -> bool:
        return self.landmarks.get(landmark_id, False)

    def build_landmark(self, landmark_id: str) -> int:
        self.landmarks[landmark_id] = True
    
    def rebuild_landmark(self, landmark_id: str) -> int:
        self.landmarks[landmark_id] = False

    def count_build_landmark(self) -> int:
        count = 0
        for lnd in self.landmarks.values():
            if lnd:
                count += 1
        return count
    
    def count_build_establishments(self, card_id: str) -> int:
        count = 0
        for lnd, cnt in self.establishments.items():
            if lnd == card_id:
                count += cnt
        return count
    
    def random_true_landmark(self):
        true_landmark = list(filter(lambda x: x[1], self.landmarks.items()))
        if true_landmark:
            return choice(true_landmark)
        else:
            None

@dataclass
class MarketState:
    """
    Рынок:
        - что на столе лежит и сколько копий
    """

    available: Dict[str, int] = field(default_factory=dict)

    deck: List[str] = field(default_factory=list)

    max_unique: int = 10

    def can_buy(self, card_id: str) -> bool:
        return self.available.get(card_id, 0) > 0

    def take_one(self, card_id: str) -> None:
        if self.available.get(card_id, 0) <= 0:
            raise ValueError(f"Нет доступных карт {card_id} на рынке")
        self.available[card_id] -= 1


@dataclass
class GameState:
    """
    Полное состояние партии только данные.
    """

    players: List[PlayerState]
    current_player: int  # индекс в players
    phase: Phase
    market: MarketState
    last_roll: Optional[int] = None

    done: bool = True
    winner: Optional[int] = None

    def current_player_state(self) -> PlayerState:
        return self.players[self.current_player]

    def next_player_index(self) -> int:
        return (self.current_player + 1) % len(self.players)

    def check_victory(self) -> Optional[int]:
        """
        Возвращает индекс победителя или None, если никто ещё не выиграл.

        # Пока что только train_station
        """

        for idx, p in enumerate(self.players):
            if p.has_built("train_station") and p.has_built("shopping_mall") and p.has_built("port"):
                return idx
            
        return None