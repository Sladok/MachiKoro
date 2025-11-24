
import sys
import os

# Добавляем project_root в PYTHONPATH
sys.path.append(os.path.abspath(".."))

from machi_core.rules import new_game, legal_actions, apply_action

game = new_game(2)


game.players[0].coins = 10
game.players[1].coins = 10
game.players[0].add_card("furniture_factory")
game.players[0].add_card("mine")
game.players[0].add_card("mine")
game.players[0].add_card("forest")

game.players[0].build_landmark("port")

game.players[1].add_card("cafe")
game.players[1].add_card("sushi_bar")
game.players[1].build_landmark("port")

# game.players[1].build_landmark("shopping_mall")
# game.players[1].build_landmark("town_hall")
# game.players[1].add_card("restaurant")
# game.players[1].add_card("elite_bar")

player = game.players[1]



# print(game.players[0].count_build_landmark())

# print(game.players[1].count_build_landmark())

actions = legal_actions(game, 0)
roll_action = actions[0]

game = apply_action(game, roll_action, dice_value=8)

print(game.players[0])
# print(game.players[1])