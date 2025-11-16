from typing import List

CARDS = {
    "-1": {"name": "", "description": "", 
          "color_type": "", "effect_type": "", "card_type": "",
          "roll_num": [0], "cost": 0, "money": 0},
    "0": {"name": "Пшеничное поле", "description": "Доход из банка в ход любого игрока", 
          "color_type": "blue", "effect_type": "получить", "card_type": "растение",
          "roll_num": [1], "cost": 0, "money": 1},
    "1": {"name": "Пекарня", "description": "Доход из банка в свой ход", 
          "color_type": "green", "effect_type": "получить", "card_type": "магазин",
          "roll_num": [2, 3], "cost": 0, "money": 1}
}

def convert_card_cfg(cfg):
    return cfg["name"], cfg['description'], \
        cfg["color_type"], cfg["effect_type"], cfg["card_type"],\
        cfg['roll_num'], cfg['cost'], cfg['money']


class Card:
    def __init__(self, 
                 name: str = "",
                 description: str = "",
                 color_type: str = "" ,
                 effect_type: str = "",
                 card_type: str = "",
                 roll_num: List[int] = [],
                 cost: int = 0,
                 money: int = 0,
                 img_id: str = ""):
        """
        name: Имя карты для вывода
        description: Описание
        color_type: Цвет карты определяет действия
        effect_type: Тип эффекта
        roll_num: Сколько Кубик должен кинуть
        cost: Сколько карта стоит
        money: Сколько карта дает
        img_id: Заранее какой айди у изображения, чтобы отображать
        """

        self.name = name
        self.description = description

        self.color_type = color_type  
        self.effect_type = effect_type  
        self.card_type = card_type

        self.roll_num = roll_num  
        self.cost = cost  
        self.money = money 
        self.img_id = img_id  