"""
Описание карт

Только данные: какие карты, свойства, на какие кубики срабатывают, и сколько дают. Нет логики игры
"""


from __future__ import annotations

from typing import List, Dict
from enum import Enum
from dataclasses import dataclass


class CardColor(str, Enum):
      BLUE = "blue"        # срабатывает у всех, даже не в свой ход
      GREEN = "green"      # срабатывает только в свой ход
      RED = "red"          # срабатывает в чужой ход
      PURPLE = "purple"    # особые эффектные, обычно ограничение по 1 шт.


class CardType(str, Enum):
     ESTABLISHMENT = "establishment"      # предприятие
     LANDMARK = "landmark"                # достопримечательность


@dataclass(frozen=True)
class CardDef:
    """
    Статическое описание типа карты.
    """
    id: str
    name: str
    color: CardColor
    card_type: CardType
    cost: int
    activation_numbers: List[int]   # на какие значения кубика карта срабатывает
    income: int                     # базовый доход в монетах (для простых карт)


# Карты
# Стартовые
WHEAT_FIELD = "wheat_field"        # пшеничное поле (синяя)
BAKERY = "bakery"                  # пекарня (зелёная)

# синие
RANCH = "ranch"                    # ранчо
FOREST = "forest"                  # лес

# зелёные
CONVENIENCE_STORE = "convenience_store"  # магазинчик

# красные
CAFE = "cafe"

# фиолетовые (упрощённая)
STADIUM = "stadium"

# Одна (из нескольких) достопримечательностей на MVP
TRAIN_STATION = "train_station"


CARDS: Dict[str, CardDef] = {
    WHEAT_FIELD: CardDef(
        id=WHEAT_FIELD,
        name="Пшеничное поле",
        color=CardColor.BLUE,
        card_type=CardType.ESTABLISHMENT,
        cost=1,
        activation_numbers=[1],
        income=1,
    ),
    BAKERY: CardDef(
        id=BAKERY,
        name="Пекарня",
        color=CardColor.GREEN,
        card_type=CardType.ESTABLISHMENT,
        cost=1,
        activation_numbers=[2, 3],
        income=1,
    ),
    RANCH: CardDef(
        id=RANCH,
        name="Ранчо",
        color=CardColor.BLUE,
        card_type=CardType.ESTABLISHMENT,
        cost=1,
        activation_numbers=[2],
        income=1,
    ),
    FOREST: CardDef(
        id=FOREST,
        name="Лес",
        color=CardColor.BLUE,
        card_type=CardType.ESTABLISHMENT,
        cost=3,
        activation_numbers=[5],
        income=1,
    ),
    CONVENIENCE_STORE: CardDef(
        id=CONVENIENCE_STORE,
        name="Магазинчик",
        color=CardColor.GREEN,
        card_type=CardType.ESTABLISHMENT,
        cost=2,
        activation_numbers=[4],
        income=3,
    ),
    CAFE: CardDef(
        id=CAFE,
        name="Кафе",
        color=CardColor.RED,
        card_type=CardType.ESTABLISHMENT,
        cost=2,
        activation_numbers=[3],
        income=1,
    ),
    STADIUM: CardDef(
        id=STADIUM,
        name="Стадион",
        color=CardColor.PURPLE,
        card_type=CardType.ESTABLISHMENT,
        cost=6,
        activation_numbers=[6],
        income=2,  # Упрощённый эффект, дальше доработаешь
    ),
    TRAIN_STATION: CardDef(
        id=TRAIN_STATION,
        name="Железнодорожный вокзал",
        color=CardColor.PURPLE,
        card_type=CardType.LANDMARK,
        cost=4,
        activation_numbers=[],
        income=0,
    ),
}


def get_card_def(card_id: str) -> CardDef:
    """
    Утилита для получения описания карты по id.
    """
    return CARDS[card_id]





# CARDS = {
#     "-1": {"name": "", "description": "", 
#           "color_type": "", "effect_type": "", "card_type": "",
#           "roll_num": [0], "cost": 0, "money": 0},
#     "0": {"name": "Пшеничное поле", "description": "Доход из банка в ход любого игрока", 
#           "color_type": "blue", "effect_type": "получить", "card_type": "растение",
#           "roll_num": [1], "cost": 0, "money": 1},
#     "1": {"name": "Пекарня", "description": "Доход из банка в свой ход", 
#           "color_type": "green", "effect_type": "получить", "card_type": "магазин",
#           "roll_num": [2, 3], "cost": 0, "money": 1}
# }

# def convert_card_cfg(cfg):
#     return cfg["name"], cfg['description'], \
#         cfg["color_type"], cfg["effect_type"], cfg["card_type"],\
#         cfg['roll_num'], cfg['cost'], cfg['money']

# class Card:
#     def __init__(self, 
#                  name: str = "",
#                  description: str = "",
#                  color_type: str = "" ,
#                  effect_type: str = "",
#                  card_type: str = "",
#                  roll_num: List[int] = [],
#                  cost: int = 0,
#                  money: int = 0,
#                  img_id: str = ""):
#         """
#         name: Имя карты для вывода
#         description: Описание
#         color_type: Цвет карты определяет действия
#         effect_type: Тип эффекта
#         roll_num: Сколько Кубик должен кинуть
#         cost: Сколько карта стоит
#         money: Сколько карта дает
#         img_id: Заранее какой айди у изображения, чтобы отображать
#         """

#         self.name = name
#         self.description = description

#         self.color_type = color_type  
#         self.effect_type = effect_type  
#         self.card_type = card_type

#         self.roll_num = roll_num  
#         self.cost = cost  
#         self.money = money 
#         self.img_id = img_id  