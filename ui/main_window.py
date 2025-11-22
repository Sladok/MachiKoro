# ui/main_window.py

from __future__ import annotations

from random import randint
from typing import List
import os
from PySide6.QtGui import QPixmap, QIcon, QFont
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QListView,
    QMessageBox,
    QInputDialog,
    QSpacerItem,
    QSizePolicy,
    QScrollArea,
    QFrame
)

from machi_core.rules import new_game, apply_action, legal_actions
from machi_core.actions import ActionType, Action
from machi_core.cards import get_card_def

# Папка с картинками карт
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS_IMG_DIR = os.path.join(BASE_DIR, "assets", "images", "cards")

CARD_W, CARD_H = 174, 271

COIN_IMG_PATH = os.path.join(BASE_DIR, "assets", "images", "ui", "coin1.png")

DICE_IMG_DIR = os.path.join(BASE_DIR, "assets", "images", "dice")

def _roll_dice() -> int:
    """UI-обёртка для броска кубика."""
    return randint(1, 6)


class MainWindow(QMainWindow):
    def __init__(self, num_players: int = 2, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Machi Koro (Desktop MVP)")
        self.resize(1100, 650)

        # --- Состояние игры ---
        self.num_players = num_players
        self._ask_num_players()
        
        self.game = new_game(self.num_players)
        self._ask_player_names()

        # --- Виджеты ---
        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QHBoxLayout()
        central.setLayout(root_layout)

        # Левая колонка: общая информация
        left_layout = QVBoxLayout()
        root_layout.addLayout(left_layout, 1)

        self.label_current = QLabel()
        self.label_phase = QLabel()
        self.label_last_roll = QLabel()
        
        # ---- КУБИК ----
        self.dice_label = QLabel()
        self.dice_label.setAlignment(Qt.AlignCenter)
        self.dice_label.setFixedSize(120, 120)   # размер “окна” под кубик
        left_layout.addWidget(self.dice_label)
        
        left_layout.addWidget(self.label_current)
        left_layout.addWidget(self.label_phase)
        left_layout.addWidget(self.label_last_roll)

        left_layout.addWidget(QLabel("Игроки:"))
        self.players_list = QListWidget()
        left_layout.addWidget(self.players_list, stretch=1)

        # --- настройки отображения списка игроков как плиток с монеткой ---
        self.players_list.setViewMode(QListView.IconMode)
        self.players_list.setFlow(QListView.LeftToRight)
        self.players_list.setWrapping(True)
        self.players_list.setIconSize(QSize(40, 40))
        self.players_list.setResizeMode(QListView.Adjust)
        self.players_list.setSpacing(8)

        # Загружаем иконку монетки один раз
        self.coin_icon = None
        if os.path.exists(COIN_IMG_PATH):
            pixmap = QPixmap(COIN_IMG_PATH)
            if not pixmap.isNull():
                self.coin_icon = QIcon(pixmap)

        # Правая колонка: карты, рынок, действия, лог
        right_layout = QVBoxLayout()
        root_layout.addLayout(right_layout, 3)

        # Блок: карты текущего игрока
        right_layout.addWidget(QLabel("Карты текущего игрока:"))

        # Карты текущего игрока
        self.player_cards_list = QListWidget()
        
        right_layout.addWidget(self.player_cards_list, stretch=3)

        # --- настройки отображения карт игрока ---
        self.player_cards_list.setViewMode(QListView.IconMode)      # плитки, а не список
        self.player_cards_list.setFlow(QListView.LeftToRight)       # слева направо
        self.player_cards_list.setWrapping(True)                    # перенос по строкам
        self.player_cards_list.setIconSize(QSize(CARD_W, CARD_H))         # размер карты
        self.player_cards_list.setResizeMode(QListView.Adjust)
        self.player_cards_list.setSpacing(8)

        # Рынок
        right_layout.addWidget(QLabel("Рынок:"))

        self.market_list = QListWidget()
        right_layout.addWidget(self.market_list, stretch=3)

        # --- настройки отображения рынка ---
        self.market_list.setViewMode(QListView.IconMode)
        self.market_list.setFlow(QListView.LeftToRight)
        self.market_list.setWrapping(True)
        self.market_list.setIconSize(QSize(CARD_W, CARD_H))
        self.market_list.setResizeMode(QListView.Adjust)
        self.market_list.setSpacing(8)



        # Немного пространства перед действиями
        right_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Minimum))

        
        right_layout.addWidget(QLabel("Доступные действия:"))

        self.actions_container = QWidget()
        self.actions_layout = QHBoxLayout(self.actions_container)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(8)

        # Горизонтальный скролл (если много действий)
        self.actions_scroll = QScrollArea()
        self.actions_scroll.setWidgetResizable(True)
        self.actions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.actions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.actions_scroll.setFrameShape(QFrame.NoFrame)
        self.actions_scroll.setWidget(self.actions_container)

        right_layout.addWidget(self.actions_scroll)


        right_layout.addWidget(QLabel("Лог:"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(140)  # фиксированная высота
        right_layout.addWidget(self.log)


        # Инициализация UI по состоянию игры
        self._refresh_full_ui()

        
        self._dice_timer: QTimer | None = None
        self._dice_sequence: list[int] = []


    # КУБИК
    def _set_dice_face(self, value: int) -> None:
        """Поставить на кубике картинку для значения 1..6."""
        img_name = f"{value}.png"
        img_path = os.path.join(DICE_IMG_DIR, img_name)

        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            # немного подмасштабировать под QLabel
            pixmap = pixmap.scaled(
                self.dice_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.dice_label.setPixmap(pixmap)
        else:
            # если вдруг файл не нашёлся – очищаем
            self.dice_label.clear()


    def _start_dice_animation(self, final_value: int) -> None:
        """
        Простая “анимация” кубика:
        - несколько случайных значений;
        - затем финальное.
        """
        import random

        # последовательность временных значений + финальное
        seq: list[int] = []
        for _ in range(8):         # сколько раз “мигнёт”
            seq.append(random.randint(1, 6))
        seq.append(final_value)

        self._dice_sequence = seq

        if self._dice_timer is None:
            self._dice_timer = QTimer(self)
            self._dice_timer.timeout.connect(self._on_dice_timer)

        self._dice_timer.start(70)  # интервал между кадрами (мс)


    def _on_dice_timer(self) -> None:
        if not self._dice_sequence:
            if self._dice_timer is not None:
                self._dice_timer.stop()
            return

        value = self._dice_sequence.pop(0)
        self._set_dice_face(value)



    # === Коилчество игроков ======================================================

    def _ask_num_players(self) -> None:
        """Спрашивает количество игроков перед началом партии."""
        while True:
            num, ok = QInputDialog.getText(
                self,
                "Количество игроков",
                f"Введите количество игроков:",
            )
            if not ok:
                # Если пользователь нажал Cancel – поставим какое-нибудь имя по умолчанию
                self.num_players = 2
                break
            num = num.strip()
            if not num.isdigit():
                continue  # нормальное имя
            num = int(num)
            break
        self.num_players = num

    # === Имена игроков ======================================================

    def _ask_player_names(self) -> None:
        """Спрашивает имена для всех игроков перед началом партии."""
        for idx, player in enumerate(self.game.players):
            while True:
                name, ok = QInputDialog.getText(
                    self,
                    "Имя игрока",
                    f"Введите имя для игрока {idx + 1}:",
                )
                if not ok:
                    # Нажали Cancel — поставим дефолтное имя
                    name = f"Игрок {idx + 1}"
                    break
                name = name.strip()
                if name:
                    break
            player.name = name

    # === Обновление UI ======================================================

    def _refresh_full_ui(self) -> None:
        """Полностью обновить отображение (инфо, игроки, карты, рынок, действия)."""
        self._update_info_labels()
        self._update_players_list()
        self._update_player_cards()
        self._update_market()
        self._rebuild_actions()

    def _update_info_labels(self) -> None:
        idx = self.game.current_player
        current_player = self.game.players[idx]
        name = getattr(current_player, "name", f"Игрок {idx + 1}")

        self.label_current.setText(f"Текущий игрок: {name} (#{idx + 1})")
        self.label_phase.setText(f"Фаза: {self.game.phase.value}")

        if self.game.last_roll is None:
            self.label_last_roll.setText("Последний бросок: —")
        else:
            self.label_last_roll.setText(f"Последний бросок: {self.game.last_roll}")

        if self.game.done:
            winner_name = getattr(self.game.players[self.game.winner], "name", f"Игрок {self.game.winner + 1}")
            self.label_phase.setText(f"Игра окончена! Победитель: {winner_name}")

    def _update_players_list(self) -> None:
        self.players_list.clear()
        for idx, player in enumerate(self.game.players):
            name = getattr(player, "name", f"Игрок {idx + 1}")
            # Текст будет ПОД иконкой (IconMode): имя и количество монет
            text = f"{name}\n{player.coins} монет"

            item = QListWidgetItem(text)

            # Если иконка монетки загрузилась – ставим её
            if self.coin_icon is not None:
                item.setIcon(self.coin_icon)

            # Можно дополнительно подсветить текущего игрока позже
            self.players_list.addItem(item)


    def _update_player_cards(self) -> None:
        """Обновить список карт текущего игрока."""
        # self.player_cards_list.clear()
        # player = self.game.current_player_state()

        # if not player.establishments:
        #     self.player_cards_list.addItem("Нет построенных предприятий")
        #     return

        # for card_id, count in player.establishments.items():
        #     if count <= 0:
        #         continue
        #     card_def = get_card_def(card_id)
        #     numbers = ",".join(str(n) for n in card_def.activation_numbers)
        #     text = (
        #         f"{card_def.name} x{count} | "
        #         f"цвет: {card_def.color.value}, "
        #         f"доход: {card_def.income}, "
        #         f"кубик: {numbers}"
        #     )
        #     self.player_cards_list.addItem(text)
        self.player_cards_list.clear()
        player = self.game.current_player_state()

        if not player.establishments:
            self.player_cards_list.addItem("Нет построенных предприятий")
            return

        for card_id, count in player.establishments.items():
            if count <= 0:
                continue
            card_def = get_card_def(card_id)
            numbers = ",".join(str(n) for n in card_def.activation_numbers)

            text = f"{card_def.name} x{count}"

            item = QListWidgetItem(text)

            # картинка, если указана
            if card_def.image:
                img_path = os.path.join(CARDS_IMG_DIR, card_def.image)
                if os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    icon = QIcon(pixmap)
                    item.setIcon(icon)

            self.player_cards_list.addItem(item)


        # Достопримечательности
        built_landmarks = [lid for lid, built in player.landmarks.items() if built]
        if built_landmarks:
            self.player_cards_list.addItem("--- Достопримечательности ---")
            for lid in built_landmarks:
                ldef = get_card_def(lid)
                self.player_cards_list.addItem(f"{ldef.name} (построено)")



    def _update_market(self) -> None:
        """Обновить список карт на рынке."""
        self.market_list.clear()
        market = self.game.market

        if not market.available:
            self.market_list.addItem("Рынок пуст")
            return

        for card_id, qty in market.available.items():
            if qty <= 0:
                continue
            card_def = get_card_def(card_id)
            numbers = ",".join(str(n) for n in card_def.activation_numbers)

            text = f"{card_def.name} ({qty} шт.)"

            item = QListWidgetItem(text)

            if card_def.image:
                img_path = os.path.join(CARDS_IMG_DIR, card_def.image)
                if os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    icon = QIcon(pixmap)
                    item.setIcon(icon)

            self.market_list.addItem(item)


    def _clear_actions_layout(self) -> None:
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _rebuild_actions(self) -> None:
        self._clear_actions_layout()

        if self.game.done:
            return

        idx = self.game.current_player
        actions: List[Action] = legal_actions(self.game, idx)

        if not actions:
            label = QLabel("Нет доступных действий")
            self.actions_layout.addWidget(label)
            return

        for action in actions:
            btn = QPushButton(self._format_action_text(action))

            # Крупная “пилюлька”
            btn.setMinimumHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setCursor(Qt.PointingHandCursor)

            # Лёгкий стиль (подгони под свою тему, если хочешь)
            btn.setStyleSheet("""
                QPushButton {
                    border-radius: 8px;
                    padding: 6px 16px;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    opacity: 0.9;
                }
            """)

            btn.clicked.connect(lambda checked=False, a=action: self._on_action_clicked(a))
            self.actions_layout.addWidget(btn)

        # Немного свободного места справа
        self.actions_layout.addStretch(1)

    def _format_action_text(self, action: Action) -> str:
        """Красивый текст для кнопки действия."""
        if action.type == ActionType.ROLL:
            return "Бросить кубик"

        if action.type == ActionType.END_BUY:
            return "Завершить фазу покупки"

        if action.type in (ActionType.BUY_CARD, ActionType.BUILD_LANDMARK) and action.card_id:
            card_def = get_card_def(action.card_id)
            if action.type == ActionType.BUY_CARD:
                return f"Купить: {card_def.name} (стоимость {card_def.cost}, доход {card_def.income})"
            else:
                return f"Построить: {card_def.name} (стоимость {card_def.cost})"

        return action.type.value

    # === Обработка действий ==================================================

    def _on_action_clicked(self, action: Action) -> None:
        """Когда игрок нажимает кнопку действия."""
        if self.game.done:
            return

        idx = self.game.current_player
        current_player = self.game.players[idx]
        name = getattr(current_player, "name", f"Игрок {idx + 1}")

        try:
            if action.type == ActionType.ROLL:
                dice = _roll_dice()

                # Запускаем анимацию кубика
                self._start_dice_animation(dice)

                # Применяем действие к игре
                self.game = apply_action(self.game, action, dice_value=dice)
                self._append_log(f"{name} бросает кубик: выпало {dice}")

            else:
                self.game = apply_action(self.game, action)
                self._append_log(self._describe_non_roll_action(name, action))

        except Exception as ex:
            QMessageBox.warning(self, "Ошибка", str(ex))
            self._append_log(f"Ошибка: {ex}")
            return

        # После действия обновляем UI
        self._refresh_full_ui()

    def _describe_non_roll_action(self, player_name: str, action: Action) -> str:
        """Текст для лога для не-ROLL действий."""
        if action.type == ActionType.END_BUY:
            return f"{player_name} завершает фазу покупки"

        if action.type in (ActionType.BUY_CARD, ActionType.BUILD_LANDMARK) and action.card_id:
            card_def = get_card_def(action.card_id)
            if action.type == ActionType.BUY_CARD:
                return f"{player_name} покупает карту: {card_def.name} за {card_def.cost} монет"
            else:
                return f"{player_name} строит достопримечательность: {card_def.name} за {card_def.cost} монет"

        return f"{player_name} выполняет действие: {action.type.value}"

    def _append_log(self, text: str) -> None:
        self.log.append(text)

