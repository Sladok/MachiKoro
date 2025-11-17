
import sys
import os

# Добавляем project_root в PYTHONPATH
sys.path.append(os.path.abspath(".."))

from machi_core.rules import new_game, legal_actions, apply_action, Action, ActionType

game = new_game(2)

# ход игрока 0: бросок
actions = legal_actions(game, 0)
# там будет один Action(ROLL)
roll_action = actions[0]
game = apply_action(game, roll_action, dice_value=2)

# теперь фаза BUY, можно смотреть legal_actions и дальше играть
