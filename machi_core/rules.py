"""
Правила игры

Здесь:
    - создание новой игры;
    - обработка броска кубика и активации простых карт;
    - переход фаз ROLL > RESOLVE > BUY > Смеша игрока/победа

Никакого input, print, без random, бросок извне.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .cards import (
    get_card_def,
    CardColor,
    CardType,
    WHEAT_FIELD,
    BAKERY,
    TRAIN_STATION,
)

from .state import GameState, PlayerState, MarketState, Phase



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


def _create_starting_player() -> PlayerState:
    """
    Создает игрока с начальными ресурсами и картами.
    """
    p = PlayerState()
    p.coins = 3

    p.add_card(WHEAT_FIELD, 1)
    p.add_card(BAKERY, 1)

    p.landmarks[TRAIN_STATION] = False
    return p


def _create_starting_market() -> MarketState:
    """
    Формирует стартовый рынок.
    """

    m = MarketState()
    
    # TODO: Потом наполнить динамически через CARD_TYPE == Establishment
    
    m.available = {
        WHEAT_FIELD: 6,
        BAKERY: 6
    }

    return m


def new_game(num_players: int = 3) -> GameState:
    """
    Создаем новое поле игры, без циклов и ввода.
    """

    players = [_create_starting_player() for _ in range(num_players)]
    market = _create_starting_market()

    game = GameState(
        players=players,
        current_player=0,
        phase=Phase.ROLL,
        market=market,
        last_roll=None,
        done=False,
        winner=None,
    )

    return game


def legal_actions(state: GameState, player_index: int) -> List[Action]:
    """
    Возвращает список доступных действий для игрока в тек. фазе.
    """

    if state.done:
        return []
    
    if player_index != state.current_player:
        return []
    
    actions: List[Action] = []

    if state.phase == Phase.ROLL:
        actions.append(Action(type=ActionType.ROLL))

    elif state.phase == Phase.BUY:
        for card_id, count in state.market.available.items():
            if count <= 0:
                continue

            card_def = get_card_def(card_id)

            if card_def.card_type == CardType.ESTABLISHMENT:
                if state.current_player_state().coins >= card_def.cost:
                    actions.append(Action(type=ActionType.BUY_CARD, card_id=card_id))

        player = state.current_player_state()

        if not player.has_built(TRAIN_STATION):
            station_def = get_card_def(TRAIN_STATION)
            if player.coins >= station_def.cost:
                actions.append(Action(type=ActionType.BUILD_LANDMARK, card_id=TRAIN_STATION))

        actions.append(Action(type=ActionType.END_BUY))

    return actions



def apply_action(state: GameState, action: Action, dice_value: Optional[int] = None) -> GameState:
    """
    Применяет действие к состоянию и возвращает ИЗМЕНЁННОЕ состояние.

    dice_value:
      - нужен только для ActionType.ROLL;
      - бросок кубика приходит ИЗВНЕ (от UI / теста / бота),
        чтобы логика была детерминируемой и пригодной для RL.
    """
    if state.done:
        return state

    if action.type == ActionType.ROLL:
        _apply_roll(state, dice_value)
    elif action.type == ActionType.BUY_CARD:
        _apply_buy_card(state, action.card_id)
    elif action.type == ActionType.BUILD_LANDMARK:
        _apply_build_landmark(state, action.card_id)
    elif action.type == ActionType.END_BUY:
        _end_buy_phase_and_maybe_finish_turn(state)
    else:
        raise ValueError(f"Неизвестный тип действия: {action.type}")

    # После любого действия стоит проверить победу
    winner = state.check_victory()
    if winner is not None:
        state.done = True
        state.winner = winner
        state.phase = Phase.GAME_OVER

    return state


def _apply_roll(state: GameState, dice_value: Optional[int]) -> None:
    if state.phase != Phase.ROLL:
        raise ValueError("Бросить кубить можно только в фазе ROLL")
    
    if dice_value is None:
        raise ValueError("Для действия ROLL нужно передать dice_value")


    state.last_roll = dice_value

    _resolve_dice(state)

    state.phase = Phase.BUY



def _resolve_dice(state: GameState) -> None:
    """
    Распределяет доход по итогам броска
    """
    dice = state.last_roll
    if dict is None:
        return


    # 1) Красные

    
    # 2) Зеленые
    current = state.current_player_state()
    for card_id, count in current.establishments.items():
        if count <= 0:
            continue

        card_def = get_card_def(card_id)

        if card_def.color == CardColor.GREEN and dice in card_def.activation_numbers:
            current.coins += card_def.income * count

    # 3) Синие
    for player in state.players:
        for card_id, count in player.establishments.items():
            if count <= 0:
                continue

            card_def = get_card_def(card_id)

            if card_def.color == CardColor.BLUE and dice in card_def.activation_numbers:
                player.coins += card_def.income * count

    # 4) Фиолетовые


def _apply_buy_card(state: GameState, card_id: Optional[str]) -> None:
    
    if state.phase != Phase.BUY:
        raise ValueError("Покупать только в фазе BUY")
    
    if not card_id:
        raise ValueError("BUY_CARD требует card_id")
    
    if not state.market.can_buy(card_id):
        raise ValueError("Карта недоступна на рынке")

    player = state.current_player_state()
    card_def = get_card_def(card_id)

    if player.coins < card_def.cost:
        raise ValueError("Не хватает монет")
    
    player.coins -= card_def.cost
    state.market.take_one(card_id)

    if card_def.card_type == CardType.ESTABLISHMENT:
        player.add_card(card_id)
    else:
        raise ValueError("Покупка LANDMARK из рынка пока не реализована.")
    

def _apply_build_landmark(state: GameState, landmark_id: Optional[str]) -> None:
    if state.phase != Phase.BUY:
        raise ValueError("Строить достопримечательности можно только в фазе BUY")
    if not landmark_id:
        raise ValueError("BUILD_LANDMARK требует card_id достопримечательности")

    player = state.current_player_state()
    card_def = get_card_def(landmark_id)

    if card_def.card_type != CardType.LANDMARK:
        raise ValueError("BUILD_LANDMARK можно вызывать только для достопримечательности")

    if player.has_built(landmark_id):
        raise ValueError("Достопримечательность уже построена")

    if player.coins < card_def.cost:
        raise ValueError("Недостаточно монет для строительства")

    player.coins -= card_def.cost
    player.build_landmark(landmark_id)





def _end_buy_phase_and_maybe_finish_turn(state: GameState) -> None:
    if state.phase != Phase.BUY:
        raise ValueError("END_BUY можно вызывать только в фазе BUY")

    # Завершение хода: передаём ход следующему игроку, фаза снова ROLL
    state.current_player = state.next_player_index()
    state.phase = Phase.ROLL
    state.last_roll = None


# from state import GameState, PlayerState, MarketState
# from cards import Card, CARDS, convert_card_cfg
# from random import randint, choice

# def _create_players(max_players: int = 2, start_money: int = 3):
#     players = []
#     for i in range(max_players):
#         player = PlayerState(id=i, start_money=start_money)

#         name, description, \
#         color_type, effect_type, card_type,\
#         roll_num, cost, money = convert_card_cfg(cfg=CARDS["0"])

#         standart_card1 = Card(name, description, 
#                              color_type, effect_type, 
#                              card_type, roll_num, 
#                              cost, money)

#         name, description, \
#         color_type, effect_type, card_type,\
#         roll_num, cost, money = convert_card_cfg(cfg=CARDS["1"])

#         standart_card2 = Card(name, description, 
#                              color_type, effect_type, 
#                              card_type, roll_num, 
#                              cost, money)


#         player.card_list.append(standart_card1)
#         player.card_list.append(standart_card2)

#         players.append(player)
#     return players


# def start_game(max_players: int = 2, start_money: int = 3):
#     game = GameState(players=_create_players(max_players=max_players, start_money=start_money))

#     game.now_turn = choice(game.players)
#     game.current_phase = "Бросок кубика"
#     game.__max_players = max_players

#     market = MarketState()

#     while True:
#         print("=------------------------------------=")
#         print(f"now_turn - {game.now_turn.id}")

#         game.process_phase()

#         print(f"Последний бросок игры - {', '.join(map(str, game.last_roll))}")

#         for player in game.players:
#             print(f"{player.id} = {player.money}")

#         input()

# start_game(2, 3)