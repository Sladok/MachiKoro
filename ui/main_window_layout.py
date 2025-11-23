from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSizePolicy,
    QLayout,
    QPushButton,
    QLabel,
    QListWidgetItem,
)

from machi_core.cards import get_card_def
from machi_core.state import Phase

from ui.config import CARDS_IMG_DIR, MARKET_CARD_W, MARKET_CARD_H

if TYPE_CHECKING:
    from ui.main_window import MainWindow


# === вспомогательные функции для layout ======================================

def _clear_layout(layout: QLayout) -> None:
    """Удалить все элементы layout и отвязать виджеты."""
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.setParent(None)
        elif item.layout():
            _clear_layout(item.layout())


def _clear_layout_keep_widgets(layout: QLayout) -> None:
    """
    Очищает layout, НО НЕ удаляет виджеты.
    Нужен для зон игроков, где PlayerBoard и списки карт должны жить весь матч.
    """
    while layout.count():
        item = layout.takeAt(0)
        child_layout = item.layout()
        if child_layout is not None:
            _clear_layout_keep_widgets(child_layout)


def _compute_seating(window: "MainWindow") -> dict[str, list[int]]:
    """Определение, на каких сторонах стола стоят игроки (0-based индексы)."""
    n = len(window.game.players)
    if n <= 0:
        return {"top": [], "right": [], "bottom": [], "left": []}

    if n == 2:
        return {"top": [0], "right": [], "bottom": [1], "left": []}
    if n == 3:
        return {"top": [0, 1], "right": [], "bottom": [2], "left": []}
    if n == 4:
        # 1 2 / 4 3 (1-based)
        return {"top": [0, 1], "right": [], "bottom": [3, 2], "left": []}
    if n == 5:
        # 1 2 / 3 справа / 5 4 снизу
        return {"top": [0, 1], "right": [2], "bottom": [4, 3], "left": []}
    if n >= 6:
        # максимум 6
        return {"top": [0, 1], "right": [2], "bottom": [4, 3], "left": [5]}

    return {"top": list(range(n)), "right": [], "bottom": [], "left": []}


# === публичные функции, которые зовёт MainWindow =============================

def rebuild_player_areas(window: "MainWindow") -> None:
    """Расставляет PlayerBoard + карты вокруг стола, чтобы зоны игроков были крупными."""
    for layout in (
        window.top_players_layout,
        window.bottom_players_layout,
        window.left_players_layout,
        window.right_players_layout,
    ):
        _clear_layout_keep_widgets(layout)

    seating = _compute_seating(window)
    current_idx = window.game.current_player

    def make_player_widget(idx: int, side: str) -> QWidget:
        """
        Виджет зоны игрока:
        сверху/снизу — растягивается по ширине,
        слева/справа — компактнее.
        """
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 4, 4, 4)
        v.setSpacing(4)

        board = window.player_boards[idx]
        board.update_from_state(window.game.players[idx], idx == current_idx)

        cards = window.player_card_lists[idx]

        v.addWidget(board, 0, Qt.AlignCenter)
        v.addWidget(cards, 0, Qt.AlignCenter)

        if side in ("top", "bottom"):
            # сверху/снизу зона игрока занимает доступную ширину
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        else:
            # слева/справа — компактнее
            w.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        return w

    # ---------- ВЕРХ ----------
    top_indices = seating["top"]
    if len(top_indices) == 1:
        window.top_players_layout.addStretch(1)
        window.top_players_layout.addWidget(
            make_player_widget(top_indices[0], "top"), 1
        )
        window.top_players_layout.addStretch(1)
    elif len(top_indices) == 2:
        # два игрока сверху — оба большие, между ними пространство
        window.top_players_layout.addWidget(
            make_player_widget(top_indices[0], "top"), 1
        )
        window.top_players_layout.addStretch(1)
        window.top_players_layout.addWidget(
            make_player_widget(top_indices[1], "top"), 1
        )
    else:
        window.top_players_layout.addStretch(1)
        for idx in top_indices:
            window.top_players_layout.addWidget(
                make_player_widget(idx, "top"), 1
            )
        window.top_players_layout.addStretch(1)

    # ---------- НИЗ ----------
    bottom_indices = seating["bottom"]
    if len(bottom_indices) == 1:
        window.bottom_players_layout.addStretch(1)
        window.bottom_players_layout.addWidget(
            make_player_widget(bottom_indices[0], "bottom"), 1
        )
        window.bottom_players_layout.addStretch(1)
    elif len(bottom_indices) == 2:
        window.bottom_players_layout.addWidget(
            make_player_widget(bottom_indices[0], "bottom"), 1
        )
        window.bottom_players_layout.addStretch(1)
        window.bottom_players_layout.addWidget(
            make_player_widget(bottom_indices[1], "bottom"), 1
        )
    else:
        window.bottom_players_layout.addStretch(1)
        for idx in bottom_indices:
            window.bottom_players_layout.addWidget(
                make_player_widget(idx, "bottom"), 1
            )
        window.bottom_players_layout.addStretch(1)

    # ---------- ЛЕВО / ПРАВО ----------
    def fill_vertical(layout, indices: list[int], side: str) -> None:
        if not indices:
            return
        layout.addStretch(1)
        for idx in indices:
            layout.addWidget(make_player_widget(idx, side))
            layout.addStretch(1)

    fill_vertical(window.left_players_layout, seating["left"], "left")
    fill_vertical(window.right_players_layout, seating["right"], "right")


def update_all_player_cards(window: "MainWindow") -> None:
    """Обновить полосы карт у всех игроков."""
    for idx, player in enumerate(window.game.players):
        lst = window.player_card_lists[idx]
        lst.clear()

        # предприятия
        for card_id, count in player.establishments.items():
            if count <= 0:
                continue
            card_def = get_card_def(card_id)

            item = QListWidgetItem(f"x{count}")
            if card_def.image:
                img_path = os.path.join(CARDS_IMG_DIR, card_def.image)
                if os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    item.setIcon(QIcon(pixmap))

            numbers = ", ".join(str(n) for n in card_def.activation_numbers)
            item.setToolTip(
                f"{card_def.name}\n"
                f"Цена: {card_def.cost}\n"
                f"Доход: {card_def.income}\n"
                f"Активируется на: {numbers}"
            )
            lst.addItem(item)

        # достопримечательности
        built_landmarks = [lid for lid, built in player.landmarks.items() if built]
        for lid in built_landmarks:
            ldef = get_card_def(lid)
            item = QListWidgetItem("🏛")
            if ldef.image:
                img_path = os.path.join(CARDS_IMG_DIR, ldef.image)
                if os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    item.setIcon(QIcon(pixmap))
            item.setToolTip(f"{ldef.name} (построено)")
            lst.addItem(item)


def update_market(window: "MainWindow") -> None:
    """Обновить рынок (сеткой из крупных кнопок-карт)."""
    layout = window.market_layout

    # очистить сетку
    _clear_layout(layout)

    market = window.game.market
    if not market.available:
        label = QLabel("Рынок пуст")
        layout.addWidget(label, 0, 0, Qt.AlignCenter)
        return

    current_player = window.game.current_player_state()

    # Собираем список карт (id, количество), отсортированный по цене
    cards = [(cid, qty) for cid, qty in market.available.items() if qty > 0]
    cards.sort(key=lambda pair: get_card_def(pair[0]).cost)

    cards_per_row = 5
    for idx, (card_id, qty) in enumerate(cards):
        row = idx // cards_per_row
        col = idx % cards_per_row

        card_def = get_card_def(card_id)

        btn = QPushButton(f"×{qty}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFlat(True)  # без рамки-кнопки

        # крупное изображение карты
        if card_def.image:
            img_path = os.path.join(CARDS_IMG_DIR, card_def.image)
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                btn.setIcon(QIcon(pixmap))

        # размер кнопки-карты
        btn.setIconSize(QSize(MARKET_CARD_W, MARKET_CARD_H))
        btn.setFixedSize(MARKET_CARD_W + 20, MARKET_CARD_H + 30)
        btn.setStyleSheet(
            """
            QPushButton {
                border: none;
                text-align: bottom center;
                font-size: 10pt;
                padding-bottom: 4px;
            }
            QPushButton:disabled {
                color: #777;
            }
            """
        )

        numbers = ", ".join(str(n) for n in card_def.activation_numbers)
        btn.setToolTip(
            f"{card_def.name}\n"
            f"Доступно: {qty}\n"
            f"Цена: {card_def.cost}\n"
            f"Доход: {card_def.income}\n"
            f"Активируется на: {numbers}"
        )

        # доступность по деньгам и фазе
        affordable = (
            current_player.coins >= card_def.cost
            and window.game.phase == Phase.BUY
        )
        btn.setEnabled(affordable)

        # клик по кнопке -> покупка этой карты
        btn.clicked.connect(
            lambda checked=False, cid=card_id: window._on_market_card_clicked(cid)
        )

        layout.addWidget(btn, row, col, Qt.AlignCenter)

    # === динамическая высота под фактическое число рядов ============
    rows = (len(cards) + cards_per_row - 1) // cards_per_row
    if rows == 0:
        rows = 1

    v_spacing = layout.verticalSpacing()
    row_height = MARKET_CARD_H + 30  # чуть больше высоты карты с подписью
    total_height = rows * row_height + (rows - 1) * v_spacing

    window.market_container.setFixedHeight(total_height)
