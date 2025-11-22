
import sys
import os

sys.path.append(os.path.abspath(".."))

from machi_core.rules import new_game, legal_actions, apply_action
from random import randint
from machi_core.actions import ActionType
from machi_core.cards import get_card_def

def _roll():
    return randint(1, 6)

def main():
    
    num_players = int(input("Сколько хотите игроков?\n>>> "))
    print()

    game = new_game(num_players)

    for idx, pl in enumerate(game.players):
        print(F"Игрок под номером {idx+1}, введите имя:")
        name = input(f">>> ").strip()
        pl.name = name
        print()

    while not game.done:
        try:
            idx = game.current_player
            actions = legal_actions(game, game.current_player)
            print(f"{game.players[idx].name} выбери действие:")

            actions_lenght = len(actions)


            for idx, action in enumerate(actions):
                if action.type == ActionType.BUY_CARD:
                    card_def = get_card_def(action.card_id)
                    print(f"{idx}. {action.type} ({card_def.name}, стоимость - {card_def.cost}, зароботок - {card_def.income}, цвет - {card_def.color}, знач. кубика - {card_def.activation_numbers})")
                else:
                    print(F"{idx}. {action.type}")
            
            cur_action = int(input(">>> "))
            print()

            if cur_action >= actions_lenght or cur_action < 0:
                print("Такого действия нету.")
                print("-" * 20 + "\n")
                continue
            
            roll_result = None
            if actions[cur_action].type == ActionType.ROLL:
                roll_result = _roll()
            game = apply_action(game, actions[cur_action], roll_result)

            if actions[cur_action].type == ActionType.ROLL:
                print(f"{game.players[idx].name} выбивает {game.last_roll}")

            for player in game.players:
                print(f"У игрока {player.name} - {player.coins} монет.")
            print("-" * 20 + "\n")

        except ValueError:
            print("Введите число.")
        except Exception as ex:
            print(ex)
    print(f"\nВыйграл {game.players[game.winner].name}")



if __name__ == "__main__":
    main()