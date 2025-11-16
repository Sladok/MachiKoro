from state import GameState, PlayerState, MarketState
from cards import Card, CARDS, convert_card_cfg
from random import randint, choice

def _create_players(max_players: int = 2, start_money: int = 3):
    players = []
    for i in range(max_players):
        player = PlayerState(id=i, start_money=start_money)

        name, description, \
        color_type, effect_type, card_type,\
        roll_num, cost, money = convert_card_cfg(cfg=CARDS["0"])

        standart_card1 = Card(name, description, 
                             color_type, effect_type, 
                             card_type, roll_num, 
                             cost, money)

        name, description, \
        color_type, effect_type, card_type,\
        roll_num, cost, money = convert_card_cfg(cfg=CARDS["1"])

        standart_card2 = Card(name, description, 
                             color_type, effect_type, 
                             card_type, roll_num, 
                             cost, money)


        player.card_list.append(standart_card1)
        player.card_list.append(standart_card2)

        players.append(player)
    return players


def start_game(max_players: int = 2, start_money: int = 3):
    game = GameState(players=_create_players(max_players=max_players, start_money=start_money))

    game.now_turn = choice(game.players)
    game.current_phase = "Бросок кубика"
    game.__max_players = max_players

    market = MarketState()

    while True:
        print("=------------------------------------=")
        print(f"now_turn - {game.now_turn.id}")

        game.process_phase()

        print(f"Последний бросок игры - {', '.join(map(str, game.last_roll))}")

        for player in game.players:
            print(f"{player.id} = {player.money}")

        input()

start_game(2, 3)