"""
Описание карт

Только данные: какие карты, свойства, на какие кубики срабатывают, и сколько дают. Нет логики игры
"""


from __future__ import annotations

from typing import List, Dict
from enum import Enum
from dataclasses import dataclass
import os
import json 

# путь к cards.json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS_JSON_PATH = os.path.join(BASE_DIR, "assets", "images", "cards", "cards.json")


class CardColor(str, Enum):
      BLUE = "blue"        # срабатывает у всех, даже не в свой ход
      GREEN = "green"      # срабатывает только в свой ход
      RED = "red"          # срабатывает в чужой ход
      PURPLE = "purple"    # особые эффектные, обычно ограничение по 1 шт.
      YELLOW = "yellow"


class CardType(str, Enum):
     ESTABLISHMENT = "establishment"      # предприятие
     LANDMARK = "landmark"                # достопримечательность


class CardVersion(str, Enum):
    NORMAL = "normal"   # обычная
    PLUS   = "plus"     # с +
    SHARP  = "sharp"    # с #

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
    image: str | None = None
    version: CardVersion = CardVersion.NORMAL  # В игре есть 3 версии, это обычные карты, плюс и шарп(#)


def _load_cards_from_json(path: str = CARDS_JSON_PATH) -> Dict[str, CardDef]:
    """
    Читает описание карт из JSON-файла и возвращает словарь card_id -> CardDef.

    Формат JSON (пример):
    {
      "wheat_field": {
        "name": "Пшеничное поле",
        "color": "blue",
        "card_type": "establishment",
        "cost": 1,
        "activation_numbers": [1],
        "income": 1,
        "image": "wheat_field.png",
        "version": "normal"
      }
    }
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    cards: Dict[str, CardDef] = {}

    for card_id, data in raw.items():
        # строковые значения → Enum’ы
        try:
            color = CardColor(data["color"])
        except ValueError:
            raise ValueError(f"Неизвестный color='{data['color']}' для карты {card_id}")

        try:
            card_type = CardType(data["card_type"])
        except ValueError:
            raise ValueError(f"Неизвестный card_type='{data['card_type']}' для карты {card_id}")

        version_str = data.get("version", "normal")
        try:
            version = CardVersion(version_str)
        except ValueError:
            raise ValueError(f"Неизвестный version='{version_str}' для карты {card_id}")

        activation_numbers = [int(x) for x in data.get("activation_numbers", [])]

        card = CardDef(
            id=card_id,
            name=data["name"],
            color=color,
            card_type=card_type,
            cost=int(data["cost"]),
            activation_numbers=activation_numbers,
            income=int(data["income"]),
            image=data.get("image"),
            version=version,
        )
        cards[card_id] = card

    return cards





CARDS: Dict[str, CardDef] = _load_cards_from_json()


def get_card_def(card_id: str) -> CardDef:
    """
    Утилита для получения описания карты по id.
    """
    return CARDS[card_id]






# # Карты
# # Стартовые
# WHEAT_FIELD = "wheat_field"        # пшеничное поле (синяя)
# BAKERY = "bakery"                  # пекарня (зелёная)

# # синие
# RANCH = "ranch"                    # ранчо
# FOREST = "forest"                  # лес
# WHEAT_FIELD_BUY = "wheat_field_buy"
# VINEYARD = "vineyard"
# MINE = "mine"
# FISHING_BOAT = "fishing_boat"

# # зелёные
# CONVENIENCE_STORE = "convenience_store"  # магазинчик
# BAKERY_BUY = "bakery_buy" 

# # красные
# CAFE = "cafe"

# # фиолетовые (упрощённая)
# STADIUM = "stadium"

# # Одна (из нескольких) достопримечательностей на MVP
# TRAIN_STATION = "train_station"


# CARDS: Dict[str, CardDef] = {
#     WHEAT_FIELD: CardDef(
#         id=WHEAT_FIELD,
#         name="Пшеничное поле",
#         color=CardColor.BLUE,
#         card_type=CardType.ESTABLISHMENT,
#         cost=1,
#         activation_numbers=[1],
#         income=1,
#         image="0.png",
#         version=CardVersion.NORMAL
#     ),
#     BAKERY: CardDef(
#         id=BAKERY,
#         name="Пекарня",
#         color=CardColor.GREEN,
#         card_type=CardType.ESTABLISHMENT,
#         cost=1,
#         activation_numbers=[2, 3],
#         income=1,
#         image="1.png",
#         version=CardVersion.NORMAL
#     ),
#     FOREST: CardDef(
#         id=FOREST,
#         name="Заповедник",
#         color=CardColor.BLUE,
#         card_type=CardType.ESTABLISHMENT,
#         cost=3,
#         activation_numbers=[5],
#         income=1,
#         image="2.png",
#         version=CardVersion.NORMAL
#     ),
#     CONVENIENCE_STORE: CardDef(
#         id=CONVENIENCE_STORE,
#         name="Цветник",
#         color=CardColor.BLUE,
#         card_type=CardType.ESTABLISHMENT,
#         cost=2,
#         activation_numbers=[4],
#         income=1,
#         image="3.png",
#         version=CardVersion.PLUS
#     ),
#     VINEYARD: CardDef(
#         id=VINEYARD,
#         name="Виноградник",
#         color=CardColor.BLUE,
#         card_type=CardType.ESTABLISHMENT,
#         cost=3,
#         activation_numbers=[7],
#         income=3,
#         image="4.png",
#         version=CardVersion.SHARP
#     ),
#     MINE: CardDef(
#         id=MINE,
#         name="Рудник",
#         color=CardColor.BLUE,
#         card_type=CardType.ESTABLISHMENT,
#         cost=6,
#         activation_numbers=[9],
#         income=5,
#         image="5.png",
#         version=CardVersion.NORMAL
#     ),
#     FISHING_BOAT: CardDef(
#         id=FISHING_BOAT,
#         name="Рыбацкий баркас",
#         color=CardColor.BLUE,
#         card_type=CardType.ESTABLISHMENT,
#         cost=2,
#         activation_numbers=[8],
#         income=3,
#         image="6.png",
#         version=CardVersion.PLUS
#     ),
#     RANCH: CardDef(
#         id=RANCH,
#         name="Ферма",
#         color=CardColor.BLUE,
#         card_type=CardType.ESTABLISHMENT,
#         cost=1,
#         activation_numbers=[2],
#         income=1,
#         image="7.png",
#         version=CardVersion.NORMAL
#     ),
#     TRAIN_STATION: CardDef(
#         id=TRAIN_STATION,
#         name="Вокзал",
#         color=CardColor.YELLOW,
#         card_type=CardType.LANDMARK,
#         cost=4,
#         activation_numbers=[],
#         income=0,
#         image="8.png",
#         version=CardVersion.NORMAL
#     ),
# }
