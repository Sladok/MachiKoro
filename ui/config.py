from __future__ import annotations

import os

# Базовая папка проекта (на уровень выше папки ui)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Каталоги с картинками
CARDS_IMG_DIR = os.path.join(BASE_DIR, "assets", "images", "cards")
DICE_IMG_DIR = os.path.join(BASE_DIR, "assets", "images", "dice")

# Размеры карт у игроков
PLAYER_CARD_W, PLAYER_CARD_H = 135, 200

# Размеры карт на рынке
MARKET_CARD_W, MARKET_CARD_H = 135, 200
