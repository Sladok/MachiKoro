from typing import List, Any
from cards import Card
from random import randint, seed

def _roll(n):
    rolls = list()
    for _ in range(n):
        seed(randint(1, 500000000000000000))
        roll = randint(1, 6)
        rolls.append(roll)
    return rolls


class GameState:
    def __init__(self, players):
        self.players: List[PlayerState] = players
        self.now_turn: PlayerState = None
        self.current_phase: str = ""  # ?
        self.__max_players: int = 2
        self.last_roll: List[int] = []

    def process_phase(self):
        if self.current_phase == "Бросок кубика":
            rolls = _roll(1)
            self.current_phase = "Активация карт"
            self.last_roll = rolls
            
        if self.current_phase == "Активация карт":
            
            for player in self.players:
                for card in player.card_list:
                    if sum(self.last_roll) in card.roll_num:
                        if card.color_type == "blue":
                            if card.effect_type == "получить":
                                player.money += card.money
                                print(f"{player.id} получил деньги за карту {card.name}")

                        
                        elif card.color_type == "green":
                            if card.effect_type == "получить" and player.id == self.now_turn.id:
                                player.money += card.money
                                print(f"{player.id} получил деньги за карту {card.name}")
            
        print()
        self.now_turn = self.players[self.now_turn.id + 1] if self.now_turn.id < self.__max_players - 1 else self.players[0]
        self.current_phase = "Бросок кубика"

class PlayerState:
    def __init__(self, id: int, start_money: int = 3):
        self.id = id
        self.money = start_money 
        self.card_list: List[Card] = []


class MarketState:
    def __init__(self):
        self.cards: List[Card] = []

class Deck:
    def __init__(self):
        self.cards = [
            
        ]
