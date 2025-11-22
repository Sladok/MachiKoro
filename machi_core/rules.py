"""
Правила игры

Здесь:
    - создание новой игры;
    - обработка броска кубика и активации простых карт;
    - переход фаз ROLL > RESOLVE > BUY > Смеша игрока/победа

Никакого input, print, без random, бросок извне.
"""

from __future__ import annotations

from typing import List, Optional


from .cards import (
    get_card_def,
    CardColor,
    CardType,
    CARDS,
    CardVersion  )

from .state import GameState, PlayerState, MarketState, Phase
from .actions import Action, ActionType
from random import Random

# сколько копий каждой версии в колоде (упростим пока)
COPIES_PER_VERSION = {
    CardVersion.NORMAL: 6,
    CardVersion.PLUS:   6,
    CardVersion.SHARP:  6,
}

def _build_market_deck(
    allowed_versions: set[CardVersion],
) -> list[str]:
    deck: list[str] = []

    for card_id, card_def in CARDS.items():
        if card_def.card_type != CardType.ESTABLISHMENT:
            continue  # достопримечательности не идут в рынок предприятий

        if card_def.version not in allowed_versions:
            continue  # фильтр по версиям (base / plus / sharp)

        copies = COPIES_PER_VERSION[card_def.version]
        deck.extend([card_id] * copies)

    return deck


def _fill_market_unique(market: MarketState) -> None:
    """
    Добрать рынок до market.max_unique уникальных типов,
    вытягивая карты из market.deck.
    """
    while len(market.available) < market.max_unique and market.deck:
        card_id = market.deck.pop()  # берём с конца
        # если такой тип уже есть на столе — просто увеличиваем количество
        market.available[card_id] = market.available.get(card_id, 0) + 1

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

        if not player.has_built("train_station"):
            station_def = get_card_def("train_station")
            if player.coins >= station_def.cost:
                actions.append(Action(type=ActionType.BUILD_LANDMARK, card_id="train_station"))
        
        if not player.has_built("shopping_mall"):
            station_def = get_card_def("shopping_mall")
            if player.coins >= station_def.cost:
                actions.append(Action(type=ActionType.BUILD_LANDMARK, card_id="shopping_mall"))


        actions.append(Action(type=ActionType.END_BUY))

    return actions


def _apply_roll(state: GameState, dice_value: Optional[int]) -> None:
    if state.phase != Phase.ROLL:
        raise ValueError("Бросить кубить можно только в фазе ROLL")
    
    if dice_value is None:
        raise ValueError("Для действия ROLL нужно передать dice_value")


    state.last_roll = dice_value

    _resolve_dice(state)

    state.phase = Phase.BUY


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
        
        # если после покупки у этого типа стало 0 – убираем его из available
        if state.market.available.get(card_id, 0) <= 0:
            state.market.available.pop(card_id, None)

        # если уникальных типов стало меньше max_unique – добираем из колоды
        if len(state.market.available) < state.market.max_unique:
            _fill_market_unique(state.market)
        
    else:
        raise ValueError("Покупка LANDMARK из рынка пока не реализована.")
    _end_buy_phase_and_maybe_finish_turn(state=state)
    

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
    _end_buy_phase_and_maybe_finish_turn(state=state)


def _end_buy_phase_and_maybe_finish_turn(state: GameState) -> None:
    if state.phase != Phase.BUY:
        raise ValueError("END_BUY можно вызывать только в фазе BUY")

    # Завершение хода: передаём ход следующему игроку, фаза снова ROLL
    state.current_player = state.next_player_index()
    state.phase = Phase.ROLL
    state.last_roll = None


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


def _resolve_dice(state: GameState) -> None:
    """
    Распределяет доход по итогам броска
    """
    dice = state.last_roll
    if dice is None:
        return

    current = state.current_player_state()  # активный игрок

    # 1) Красные
    for player in state.players:
        if current == player:
            continue
        
        for card_id, count in player.establishments.items():
            if count <= 0:
                continue

            card_def = get_card_def(card_id)

            if card_def.color == CardColor.RED and dice in card_def.activation_numbers:
                cost = card_def.income * count
                
                transfer = min(cost, current.coins)

                current.coins -= transfer
                player.coins += transfer

    
    # 2) Зеленые
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
    # TODO: они тяжелее потом добавлю


def _create_starting_player() -> PlayerState:
    """
    Создает игрока с начальными ресурсами и картами.
    """
    p = PlayerState()
    p.coins = 3

    p.add_card("wheat_field", 1)
    p.add_card("bakery", 1)

    p.landmarks["train_station"] = False
    p.landmarks["shopping_mall"] = False
    return p


def new_game(num_players: int = 3,
             allowed_versions: set[CardVersion] | None = None,
             rng: Random | None = None,
             ) -> GameState:
    """
    Создаем новое поле игры, без циклов и ввода.
    """

    players = [_create_starting_player() for _ in range(num_players)]
    
    if allowed_versions is None:
        allowed_versions = {CardVersion.NORMAL}

    deck = _build_market_deck(allowed_versions)

    if rng is None:
        import random
        rng = random.Random()
    rng.shuffle(deck)

    market = MarketState(
        available={},
        deck=deck,
        max_unique=10,  # можешь поставить 5–7 для MVP, у тебя пока мало типов
    )
    _fill_market_unique(market)

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