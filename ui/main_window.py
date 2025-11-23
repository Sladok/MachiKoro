from __future__ import annotations

from ui.config import PLAYER_CARD_W, PLAYER_CARD_H
from ui import main_window_layout as layout_helpers

from ui.main_window_dialogs import DialogsMixin
from ui.main_window_bots import BotsMixin
from ui.main_window_actions import ActionsMixin
from ui.main_window_dice import DiceMixin
from ui.main_window_log import LogMixin

from typing import List

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QMainWindow,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
    QGridLayout,
)

from machi_core.rules import new_game
from machi_core.agents import Agent

from ui.widgets.player_board import PlayerBoard


class MainWindow(
    QMainWindow,
    DialogsMixin,
    BotsMixin,
    ActionsMixin,
    DiceMixin,
    LogMixin,
):
    def __init__(self, num_players: int = 2, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Machi Koro — Table")
        self.resize(1400, 900)

        # --- Состояние игры ---------------------------------------------------
        self.num_players = num_players
        self._ask_num_players()
        self.game = new_game(self.num_players)
        self._ask_player_names()

        # планшеты игроков вокруг стола
        self.player_boards: list[PlayerBoard] = [
            PlayerBoard(self) for _ in self.game.players
        ]

        # полосы карт у каждого игрока
        self.player_card_lists: list[QListWidget] = []
        for _ in self.game.players:
            lst = QListWidget()
            lst.setViewMode(QListView.IconMode)
            lst.setFlow(QListView.LeftToRight)
            lst.setWrapping(True)
            lst.setIconSize(QSize(PLAYER_CARD_W, PLAYER_CARD_H))
            lst.setResizeMode(QListView.Adjust)
            lst.setSpacing(4)
            lst.setFixedHeight(PLAYER_CARD_H * 2 + 60)
            lst.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            lst.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            lst.setSelectionMode(QAbstractItemView.NoSelection)
            self.player_card_lists.append(lst)

        # агенты (боты/люди)
        self.agents: list[Agent | None] = [None] * self.num_players
        self._setup_agents()

        # --- Центр. виджет и корневой layout (стол) ---------------------------
        central = QWidget(self)
        self.setCentralWidget(central)
        central.setStyleSheet("background-color: #0d1117;")  # тёмный стол


        root_layout = QVBoxLayout()
        root_layout.setSpacing(8)
        root_layout.setContentsMargins(8, 32, 8, 16)
        central.setLayout(root_layout)

        # === верхние игроки ===================================================
        self.top_players_layout = QHBoxLayout()
        self.top_players_layout.setSpacing(40)
        self.top_players_layout.setContentsMargins(0, 8, 0, 8)
        root_layout.addLayout(self.top_players_layout)

        # === середина: слева игроки, в центре стол, справа игроки ============
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(16)
        root_layout.addLayout(middle_layout, 1)

        # ЛЕВАЯ КОЛОНКА ИГРОКОВ (узкая)
        self.left_players_widget = QWidget()
        self.left_players_layout = QVBoxLayout(self.left_players_widget)
        self.left_players_layout.setSpacing(16)
        self.left_players_widget.setFixedWidth(220)
        middle_layout.addWidget(self.left_players_widget)

        # ЦЕНТРАЛЬНЫЙ "СТОЛ"
        self.table_layout = QVBoxLayout()
        self.table_layout.setSpacing(8)
        middle_layout.addLayout(self.table_layout, 1)

        # ПРАВАЯ КОЛОНКА ИГРОКОВ (узкая)
        self.right_players_widget = QWidget()
        self.right_players_layout = QVBoxLayout(self.right_players_widget)
        self.right_players_layout.setSpacing(16)
        self.right_players_widget.setFixedWidth(220)
        middle_layout.addWidget(self.right_players_widget)

        # === нижние игроки ====================================================
        self.bottom_players_layout = QHBoxLayout()
        self.bottom_players_layout.setSpacing(40)
        self.bottom_players_layout.setContentsMargins(0, 8, 0, 16)
        root_layout.addLayout(self.bottom_players_layout)

        # =====================================================================
        # ВНУТРИ "СТОЛА": заголовок + кубик, рынок, действия
        # =====================================================================

        # --- Полоса: заголовок рынка + кубик в правом углу -------------------
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        self.table_layout.addLayout(header_row)

        self.market_title = QLabel("Рынок")
        self.market_title.setStyleSheet("font-weight: bold;")
        header_row.addWidget(self.market_title, 0, alignment=Qt.AlignLeft)

        header_row.addStretch(1)

        self.dice_label = QLabel()
        self.dice_label.setAlignment(Qt.AlignCenter)
        self.dice_label.setFixedSize(80, 80)
        header_row.addWidget(self.dice_label, 0, alignment=Qt.AlignRight)

        header_div = QFrame()
        header_div.setFrameShape(QFrame.HLine)
        header_div.setFrameShadow(QFrame.Sunken)
        self.table_layout.addWidget(header_div)

        # --- Рынок -----------------------------------------------------------
        self.market_container = QWidget()
        self.market_layout = QGridLayout(self.market_container)
        self.market_layout.setContentsMargins(0, 0, 0, 0)
        self.market_layout.setHorizontalSpacing(6)
        self.market_layout.setVerticalSpacing(10)
        self.market_container.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum
        )

        market_row = QHBoxLayout()
        market_row.addStretch(1)
        market_row.addWidget(self.market_container)
        market_row.addStretch(1)
        self.table_layout.addLayout(market_row)

        # --- Действия --------------------------------------------------------
        self.table_layout.addSpacerItem(
            QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Minimum)
        )

        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)
        self.table_layout.addLayout(actions_row)

        actions_row.addStretch(1)

        self.actions_container = QWidget()
        self.actions_layout = QHBoxLayout(self.actions_container)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(8)

        self.actions_scroll = QScrollArea()
        self.actions_scroll.setWidgetResizable(True)
        self.actions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.actions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.actions_scroll.setFrameShape(QFrame.NoFrame)
        self.actions_scroll.setWidget(self.actions_container)

        actions_row.addWidget(self.actions_scroll, 0)
        actions_row.addStretch(1)

        # --- Таймер для анимации кубика --------------------------------------
        self._dice_timer = None
        self._dice_sequence: list[int] = []

        # Первый рендер
        self._refresh_full_ui()
        self._maybe_schedule_bot()

    # ===== обёртки для layout_helpers ========================================
    def _rebuild_player_areas(self) -> None:
        layout_helpers.rebuild_player_areas(self)

    def _update_all_player_cards(self) -> None:
        layout_helpers.update_all_player_cards(self)

    def _update_market(self) -> None:
        layout_helpers.update_market(self)

    # =====================================================================
    # Обновление UI
    # =====================================================================
    def _refresh_full_ui(self) -> None:
        self._update_all_player_cards()
        self._rebuild_player_areas()
        self._update_market()
        self._rebuild_actions()
        if self.game.last_roll is not None:
            self._set_dice_face(self.game.last_roll)
