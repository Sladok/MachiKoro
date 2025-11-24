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
from machi_core.cards import CardVersion  

from ui.widgets.player_board import PlayerBoard

class ClickableLabel(QLabel):
    """QLabel, по которому можно кликать как по кнопке."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._click_callback = None

    def set_click_callback(self, callback):
        self._click_callback = callback

    def mousePressEvent(self, event):
        # ЛКМ -> вызываем callback
        if event.button() == Qt.LeftButton and self._click_callback is not None:
            self._click_callback()
        return super().mousePressEvent(event)


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
        self.game = new_game(self.num_players, {CardVersion.NORMAL, CardVersion.PLUS, CardVersion.SHARP})
        self._ask_player_names()

        # планшеты игроков вокруг стола
        self.player_boards: list[PlayerBoard] = [
            PlayerBoard(self) for _ in self.game.players
        ]

        # полосы карт у каждого игрока
        self.player_card_lists: list[QListWidget] = []
        for idx, _ in enumerate(self.game.players):
            lst = QListWidget()
            lst.setViewMode(QListView.IconMode)

            # хотим ОДНУ строку, а не столбец
            lst.setFlow(QListView.LeftToRight)
            lst.setWrapping(False)

            lst.setIconSize(QSize(PLAYER_CARD_W, PLAYER_CARD_H))
            lst.setResizeMode(QListView.Adjust)
            lst.setSpacing(4)

            lst.setFixedHeight(PLAYER_CARD_H + 30)
            lst.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            lst.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            lst.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            lst.setSelectionMode(QAbstractItemView.NoSelection)

            # <<< НОВОЕ: клик по элементу в полосе игрока
            lst.itemClicked.connect(
                lambda item, pidx=idx: self._on_player_landmark_clicked(pidx, item)
            )

            self.player_card_lists.append(lst)

        # агенты (боты/люди)
        self.agents: list[Agent | None] = [None] * self.num_players
        self._setup_agents()

        # --- Центр. виджет и корневой layout (стол) ---------------------------
        central = QWidget(self)
        central.setObjectName("tableRoot")
        self.setCentralWidget(central)

        central.setStyleSheet("""
            QWidget#tableRoot {
                background: qradialgradient(
                    cx: 0.5, cy: 0.35, radius: 1.0,
                    fx: 0.5, fy: 0.35,
                    stop: 0   #243447,   /* центр посветлее */
                    stop: 0.6 #141a23,
                    stop: 1   #05070b    /* по краям темнее */
                );
            }
        """)

        root_layout = QVBoxLayout()
        root_layout.setSpacing(8)
        root_layout.setContentsMargins(8, 32, 8, 120)

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
        # self.left_players_widget.setFixedWidth(320)
        middle_layout.addWidget(self.left_players_widget, 1)

        # ЦЕНТРАЛЬНЫЙ "СТОЛ"
        self.table_layout = QVBoxLayout()
        self.table_layout.setSpacing(8)
        middle_layout.addLayout(self.table_layout, 2)

        # ПРАВАЯ КОЛОНКА ИГРОКОВ (узкая)
        self.right_players_widget = QWidget()
        self.right_players_layout = QVBoxLayout(self.right_players_widget)
        self.right_players_layout.setSpacing(16)
        # self.right_players_widget.setFixedWidth(320)
        middle_layout.addWidget(self.right_players_widget, 1)

        # === нижние игроки ====================================================
        self.bottom_players_layout = QHBoxLayout()
        self.bottom_players_layout.setSpacing(40)
        self.bottom_players_layout.setContentsMargins(0, 8, 0, 32)
        root_layout.addLayout(self.bottom_players_layout)

        # =====================================================================
        # ВНУТРИ "СТОЛА": заголовок + кубик, рынок, действия
        # =====================================================================

        # --- Полоса: заголовок рынка + кубик в правом углу -------------------
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        self.table_layout.addLayout(header_row)
        
        header_row.addStretch(1)

        self.market_title = QLabel("Рынок")
        self.market_title.setStyleSheet("font-weight: bold;")
        header_row.addWidget(self.market_title, 0, alignment=Qt.AlignLeft)

        header_row.addStretch(1)
        

        # --- Крупный кубик над маркетом -------------------------------------
        dice_row = QHBoxLayout()
        dice_row.setSpacing(8)
        self.table_layout.addLayout(dice_row)

        dice_row.addStretch(1)

        self.dice_label = ClickableLabel()
        self.dice_label.setAlignment(Qt.AlignCenter)
        self.dice_label.setFixedSize(100, 100)
        self.dice_label.set_click_callback(self._on_dice_label_clicked)

        # ► делает его визуально кнопкой
        self.dice_label.setCursor(Qt.PointingHandCursor)
        self.dice_label.setToolTip("Нажми, чтобы бросить кубик")
        self.dice_label.setStyleSheet("""
            QLabel {
                border: 2px solid #f5c518;
                border-radius: 10px;
                background-color: #161b22;
                padding: 6px;
            }
            QLabel:hover {
                border: 2px solid #ffd54f;
                background-color: #1f2630;
            }
        """)

        dice_row.addWidget(self.dice_label, 0, alignment=Qt.AlignCenter)

        dice_row.addStretch(1)
        
        # ► сразу показать какую-то грань
        if self.game.last_roll is not None:
            self._set_dice_face(self.game.last_roll)
        else:
            self._set_dice_face(1)   # например, «1»


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

        # Внутренний layout для кнопок действий (без лишних виджетов)
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(8)

        # Центруем actions_layout между двумя растяжками
        actions_row.addStretch(1)
        actions_row.addLayout(self.actions_layout)
        actions_row.addStretch(1)


        # --- Таймер для анимации кубика --------------------------------------
        self._dice_timer = None
        self._dice_sequence: list[int] = []
        self._last_dice_values: list[int] | None = None

        # Первый рендер
        self._refresh_full_ui()
        self._maybe_schedule_bot()

    def _reset_game(self) -> None:
        """
        Полный рестарт партии:
          - новое состояние игры;
          - заново спрашиваем имена;
          - заново выбираем, кто бот/человек.
        Количество игроков берём из self.num_players.
        """
        # остановить анимацию кубика
        if self._dice_timer is not None:
            self._dice_timer.stop()
        self._dice_sequence = []
        self._last_dice_values = None

        # пересоздать ядро
        self.game = new_game(
            self.num_players,
            {CardVersion.NORMAL, CardVersion.PLUS, CardVersion.SHARP},
        )

        # заново спросить имена
        self._ask_player_names()

        # заново настроить агентов
        self.agents = [None] * self.num_players
        self._setup_agents()

        # сбросить кубик и перерисовать
        self._set_dice_face(1)
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

        # --- заголовок над рынком: статус партии ---
        if self.game.done and self.game.winner is not None:
            winner_idx = self.game.winner
            if 0 <= winner_idx < len(self.game.players):
                p = self.game.players[winner_idx]
                name = getattr(p, "name", f"Игрок {winner_idx + 1}")
                self.market_title.setText(f"Победитель: {name}")
            else:
                self.market_title.setText("Игра окончена")
        elif self.game.done:
            self.market_title.setText("Игра окончена")
        else:
            self.market_title.setText("Рынок")
        
        # --- кубики ---
        if self.game.last_roll is not None:
            # если знаем реальные кубики — показываем их
            if getattr(self, "_last_dice_values", None):
                self._set_dice_face(self._last_dice_values)
            else:
                self._set_dice_face(self.game.last_roll)