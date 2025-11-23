# ui/widgets/player_board.py
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap

from machi_core.state import PlayerState

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UI_IMG_DIR = os.path.join(BASE_DIR, "assets", "images", "ui")
COIN_IMG_PATH = os.path.join(UI_IMG_DIR, "coin1.png")

class PlayerBoard(QWidget):
    """
    Маленький "планшет игрока" для размещения вокруг стола.
    Пока: имя + монеты. Потом добавим достопримечательности и т.д.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        
        # Имя
        self.label_name = QLabel()
        name_font = QFont()
        name_font.setBold(True)
        self.label_name.setFont(name_font)
        self.label_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_name)

        # Ряд с монеткой и числом
        coins_row = QHBoxLayout()
        coins_row.setSpacing(4)

        self.coin_label = QLabel()
        self.coin_label.setFixedSize(20, 20)

        if os.path.exists(COIN_IMG_PATH):
            pm = QPixmap(COIN_IMG_PATH)
            if not pm.isNull():
                pm = pm.scaled(
                    self.coin_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.coin_label.setPixmap(pm)

        self.label_coins = QLabel()
        self.label_coins.setAlignment(Qt.AlignLeft)

        coins_row.addWidget(self.coin_label)
        coins_row.addWidget(self.label_coins)
        coins_row.addStretch(1)

        layout.addLayout(coins_row)

        # базовый стиль (для не-текущего игрока)
        self.setStyleSheet("""
            QWidget {
                border: 1px solid #555;
                border-radius: 6px;
                background-color: rgba(0, 0, 0, 80);
            }
        """)

    def update_from_state(self, player: PlayerState, is_current: bool) -> None:
        name = getattr(player, "name", "") or "Игрок"
        if not name:
            name = "Игрок"

        self.label_name.setText(name)
        self.label_coins.setText(str(player.coins))

        # подсветка текущего игрока
        if is_current:
            # жёлтая рамка и чуть более яркий фон
            self.setStyleSheet("""
                QWidget {
                    border: 2px solid #ffd166;
                    border-radius: 6px;
                    background-color: rgba(0, 0, 0, 140);
                }
            """)
        else:
            # обычная серая рамка
            self.setStyleSheet("""
                QWidget {
                    border: 1px solid #555;
                    border-radius: 6px;
                    background-color: rgba(0, 0, 0, 80);
                }
            """)
