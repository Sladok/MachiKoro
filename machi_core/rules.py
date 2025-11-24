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
from random import Random, randint

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
        player = state.current_player_state()

        actions.append(Action(type=ActionType.ROLL, num_dice=1))

        if player.has_built("train_station"):
            actions.append(Action(type=ActionType.ROLL, num_dice=2))

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
            shopping_def = get_card_def("shopping_mall")
            if player.coins >= shopping_def.cost:
                actions.append(Action(type=ActionType.BUILD_LANDMARK, card_id="shopping_mall"))

        if not player.has_built("port"):
            port_def = get_card_def("port")
            if player.coins >= port_def.cost:
                actions.append(Action(type=ActionType.BUILD_LANDMARK, card_id="port"))


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
        if card_id == "credit_bureau":
            player.coins += 5
        
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

    current_idx = state.current_player          # индекс активного
    current = state.current_player_state()      # активный игрок

    num_players = len(state.players)

    # 1) Красные (рестораны других игроков)
    # начинаем с игрока слева от current и идём по кругу
    for step in range(1, num_players):
        if current.coins <= 0:
            break  # деньги у активного закончились – дальше красные не работают

        p_idx = (current_idx + step) % num_players
        player = state.players[p_idx]          # тот, кто может получать деньги

        for card_id, count in player.establishments.items():
            if count <= 0:
                continue

            card_def = get_card_def(card_id)

            if card_def.color == CardColor.RED and dice in card_def.activation_numbers:
                
                if current.coins <= 0:
                    break  # уже нечего брать

                if card_def.version == "normal":
                    cost = card_def.income * count
                    
                    transfer = min(cost, current.coins)

                    current.coins -= transfer
                    player.coins += transfer
                
                elif card_def.version == "plus":
                    if card_id == "sushi_bar":
                        if player.has_built("port"):
                            
                            cost = card_def.income * count
                            
                            transfer = min(cost, current.coins)

                            current.coins -= transfer
                            player.coins += transfer
                    else:
                        
                        cost = card_def.income * count
                        
                        transfer = min(cost, current.coins)

                        current.coins -= transfer
                        player.coins += transfer

                elif card_def.version == "sharp":
                    if card_id == "restaurant":
                        count_landmark = current.count_build_landmark()

                        if count_landmark >= 2:
                            
                            cost = card_def.income * count
                            
                            transfer = min(cost, current.coins)

                            current.coins -= transfer
                            player.coins += transfer

                    elif card_id == "elite_bar":
                        count_landmark = current.count_build_landmark()

                        if count_landmark >= 3:
                            
                            cost = card_def.income * count
                            
                            transfer = min(cost, current.coins)

                            current.coins -= transfer
                            player.coins += transfer


                    else:
                        cost = card_def.income * count
                        
                        transfer = min(cost, current.coins)

                        current.coins -= transfer
                        player.coins += transfer

    # 2) Зеленые – как у тебя было
    for card_id, count in current.establishments.items():
        if count <= 0:
            continue

        card_def = get_card_def(card_id)

        if card_def.color == CardColor.GREEN and dice in card_def.activation_numbers:
            if card_id == "department_store":
                count_landmark = current.count_build_landmark()

                if count_landmark <= 1:
                    current.coins += card_def.income * count
            
            elif card_id == "building_demolition_company":
                
                for _ in range(count):
                    lndmrk = current.random_true_landmark()
                    
                    print(lndmrk)
                    if lndmrk is None:
                        continue

                    print("yes")

                    current.rebuild_landmark(lndmrk[0])
                    current.coins += card_def.income

            elif card_id == "flower_shop":
                result_count = 0
                for _ in range(count):
                    count_convenience_store = current.count_build_establishments("convenience_store")
                    result_count += count_convenience_store
                current.coins += result_count

            elif card_id == "winery":
                result_count = 0
                for _ in range(count):
                    count_vineyard = current.count_build_establishments("vineyard")
                    result_count += count_vineyard
                current.coins += result_count * card_def.income

                # Нужно сделать закрытие на ремонт

            elif card_id == "cheese_factory":
                result_count = 0
                for _ in range(count):
                    count_ranch = current.count_build_establishments("ranch")
                    result_count += count_ranch
                current.coins += result_count * card_def.income

                # Нужно сделать закрытие на ремонт

            elif card_id == "furniture_factory":
                result_count = 0
                for _ in range(count):
                    count_mine = current.count_build_establishments("mine")
                    result_count += count_mine

                    count_forest = current.count_build_establishments("forest")
                    result_count += count_forest

                current.coins += result_count * card_def.income

                # Нужно сделать закрытие на ремонт

            else:
                cost = card_def.income * count
                
                current.coins += cost


    # 3) Синие – как у тебя было
    for player in state.players:
        for card_id, count in player.establishments.items():
            if count <= 0:
                continue

            card_def = get_card_def(card_id)

            if card_def.color == CardColor.BLUE and dice in card_def.activation_numbers:
                
                if card_id == "cornfield":
                    count_landmark = player.count_build_landmark()

                    if count_landmark <= 1:
                        player.coins += card_def.income * count

                elif card_id == "fishing_boat":
                    if player.has_built("port"):
                        player.coins += card_def.income * count
                        
                elif card_id == "trawler":
                    if player.has_built("port"):
                        count1 = randint(1, 6)
                        count2 = randint(1, 6)
                        player.coins += (count1 + count2) * count

                else:
                    player.coins += card_def.income * count

    # 4) Фиолетовые – позже
    # TODO: они тяжелее потом добавлю


def _create_starting_player() -> PlayerState:
    """
    Создает игрока с начальными ресурсами и картами.
    """
    p = PlayerState()
    p.coins = 3

    p.add_card("wheat_field_buy", 1)
    p.add_card("bakery_buy", 1)

    p.landmarks["port"] = False
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