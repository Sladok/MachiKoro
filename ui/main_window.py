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
    QFrame,
)

from machi_core.state import Phase
from machi_core.rules import new_game, apply_action, legal_actions
from machi_core.actions import ActionType, Action
from machi_core.cards import get_card_def
from machi_core.agents import Agent, RandomBot



# --- Пути и размеры ---------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS_IMG_DIR = os.path.join(BASE_DIR, "assets", "images", "cards")
UI_IMG_DIR = os.path.join(BASE_DIR, "assets", "images", "ui")
DICE_IMG_DIR = os.path.join(BASE_DIR, "assets", "images", "dice")

CARD_W, CARD_H = 174, 271

COIN_IMG_PATH = os.path.join(UI_IMG_DIR, "coin1.png")


def _roll_dice() -> int:
    """UI-обёртка для броска кубика."""
    return randint(1, 6)


class MainWindow(QMainWindow):
    def __init__(self, num_players: int = 2, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Machi Koro (Desktop MVP)")
        self.resize(1200, 700)

        # --- Состояние игры ---------------------------------------------------
        self.num_players = num_players
        self._ask_num_players()

        self.game = new_game(self.num_players)
        self._ask_player_names()

        self.agents: list[Agent | None] = [None] * self.num_players
        self._setup_agents()

        # --- Центр. виджет и корневой layout --------------------------------
        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QHBoxLayout()
        central.setLayout(root_layout)

        # =====================================================================
        # ЛЕВАЯ КОЛОНКА: кубик + инфо + игроки
        # =====================================================================
        left_layout = QVBoxLayout()
        root_layout.addLayout(left_layout, 1)

        # Крупный кубик
        self.dice_label = QLabel()
        self.dice_label.setAlignment(Qt.AlignCenter)
        self.dice_label.setFixedSize(130, 130)
        left_layout.addWidget(self.dice_label)

        # Общая инфа по ходу
        self.label_current = QLabel()
        self.label_phase = QLabel()
        self.label_last_roll = QLabel()

        for lab in (self.label_current, self.label_phase, self.label_last_roll):
            lab.setWordWrap(True)

        left_layout.addWidget(self.label_current)
        left_layout.addWidget(self.label_phase)
        left_layout.addWidget(self.label_last_roll)

        # Разделитель
        left_div = QFrame()
        left_div.setFrameShape(QFrame.HLine)
        left_div.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(left_div)

        # Список игроков
        players_title = QLabel("Игроки:")
        players_title.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(players_title)

        self.players_list = QListWidget()
        left_layout.addWidget(self.players_list, stretch=1)

        self.players_list.setViewMode(QListView.IconMode)
        self.players_list.setFlow(QListView.LeftToRight)
        self.players_list.setWrapping(True)
        self.players_list.setIconSize(QSize(40, 40))
        self.players_list.setResizeMode(QListView.Adjust)
        self.players_list.setSpacing(8)

        # Иконка монетки
        self.coin_icon = None
        if os.path.exists(COIN_IMG_PATH):
            pixmap = QPixmap(COIN_IMG_PATH)
            if not pixmap.isNull():
                self.coin_icon = QIcon(pixmap)

        left_layout.addStretch(1)

        # =====================================================================
        # ПРАВАЯ КОЛОНКА: статус-хинт + карты + рынок + действия + лог
        # =====================================================================
        right_layout = QVBoxLayout()
        root_layout.addLayout(right_layout, 3)

        # Статус-хинт по фазе
        self.phase_hint_label = QLabel()
        self.phase_hint_label.setAlignment(Qt.AlignCenter)
        self.phase_hint_label.setWordWrap(True)
        phase_font = QFont()
        phase_font.setPointSize(13)
        phase_font.setBold(True)
        self.phase_hint_label.setFont(phase_font)
        self.phase_hint_label.setStyleSheet(
            "QLabel { padding: 8px; border-radius: 8px; }"
        )
        right_layout.addWidget(self.phase_hint_label)

        # Разделитель
        top_div = QFrame()
        top_div.setFrameShape(QFrame.HLine)
        top_div.setFrameShadow(QFrame.Sunken)
        right_layout.addWidget(top_div)

        # --- Карты текущего игрока -------------------------------------------
        pc_title = QLabel("Карты текущего игрока:")
        pc_title.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(pc_title)

        self.player_cards_list = QListWidget()
        right_layout.addWidget(self.player_cards_list, stretch=3)

        self.player_cards_list.setViewMode(QListView.IconMode)
        self.player_cards_list.setFlow(QListView.LeftToRight)
        self.player_cards_list.setWrapping(True)
        self.player_cards_list.setIconSize(QSize(CARD_W, CARD_H))
        self.player_cards_list.setResizeMode(QListView.Adjust)
        self.player_cards_list.setSpacing(8)
        self.player_cards_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # --- Рынок ------------------------------------------------------------
        market_title = QLabel("Рынок (клик по карте — покупка):")
        market_title.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(market_title)

        self.market_list = QListWidget()
        right_layout.addWidget(self.market_list, stretch=3)

        self.market_list.setViewMode(QListView.IconMode)
        self.market_list.setFlow(QListView.LeftToRight)
        self.market_list.setWrapping(True)
        self.market_list.setIconSize(QSize(CARD_W, CARD_H))
        self.market_list.setResizeMode(QListView.Adjust)
        self.market_list.setSpacing(8)
        self.market_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.market_list.setCursor(Qt.PointingHandCursor)
        self.market_list.itemClicked.connect(self._on_market_card_clicked)

        # Немного пространства
        right_layout.addSpacerItem(
            QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Minimum)
        )

        # --- Доступные действия ----------------------------------------------
        actions_title = QLabel("Доступные действия:")
        actions_title.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(actions_title)

        self.actions_container = QWidget()
        self.actions_layout = QHBoxLayout(self.actions_container)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(8)

        self.actions_scroll = QScrollArea()
        self.actions_scroll.setWidgetResizable(True)
        self.actions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.actions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.actions_scroll.setFrameShape(QFrame.NoFrame)
        self.actions_scroll.setWidget(self.actions_container)

        right_layout.addWidget(self.actions_scroll)

        # --- Лог --------------------------------------------------------------
        log_title = QLabel("Лог:")
        log_title.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(log_title)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(150)
        right_layout.addWidget(self.log)

        # --- Таймер и состояние анимации кубика ------------------------------
        self._dice_timer: QTimer | None = None
        self._dice_sequence: list[int] = []

        # Первый рендер UI
        self._refresh_full_ui()

    # =====================================================================
    # Вспомогательные диалоги (число игроков / имена)
    # =====================================================================

    def _ask_num_players(self) -> None:
        """Спрашивает количество игроков перед началом партии."""
        while True:
            num_str, ok = QInputDialog.getText(
                self,
                "Количество игроков",
                "Введите количество игроков:",
            )
            if not ok:
                # Cancel → дефолт
                self.num_players = 2
                return

            num_str = num_str.strip()
            if not num_str.isdigit():
                # просто попросим снова
                continue

            num = int(num_str)
            if num <= 0:
                continue

            self.num_players = num
            return

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
                    name = f"Игрок {idx + 1}"
                    break
                name = name.strip()
                if name:
                    break
            player.name = name


    # BOT
    def _setup_agents(self) -> None:
        """Спрашиваем для каждого игрока: человек или бот."""

        # импорт тут, если не импортировал QInputDialog выше
        from PySide6.QtWidgets import QInputDialog

        for idx, player in enumerate(self.game.players):
            default_index = 0 if idx == 0 else 1  # 1-й по умолчанию человек, остальные — боты

            choice, ok = QInputDialog.getItem(
                self,
                "Тип игрока",
                f"Игрок {idx + 1} ({getattr(player, 'name', '') or 'без имени'}): кто это?",
                ["Человек", "Бот (простая стратегия)"],
                default_index,
                False,
            )

            if not ok:
                # Если нажали Cancel — считаем, что это человек
                choice = "Человек"

            if choice.startswith("Бот"):
                self.agents[idx] = RandomBot()
            else:
                self.agents[idx] = None


    # === Работа ботов ===================================================

    def _current_agent(self) -> Agent | None:
        """Возвращает агента для текущего игрока (или None, если это человек)."""
        idx = self.game.current_player
        if 0 <= idx < len(self.agents):
            return self.agents[idx]
        return None

    def _maybe_schedule_bot(self) -> None:
        """Если сейчас ход бота — через паузу даём ему сделать шаг."""
        if self.game.done:
            return

        agent = self._current_agent()
        if agent is None:
            return

        # Небольшая задержка, чтобы UI обновился и было видно, что ход сменился.
        QTimer.singleShot(1500, self._bot_step)

    def _bot_step(self) -> None:
        """Один шаг бота: выбрать действие и выполнить его через общий механизм."""
        if self.game.done:
            return

        agent = self._current_agent()
        if agent is None:
            return  # вдруг за время таймера ход уже перешёл человеку

        idx = self.game.current_player
        actions = legal_actions(self.game, idx)
        if not actions:
            return

        player = self.game.players[idx]
        name = getattr(player, "name", f"Игрок {idx + 1}")
        self._append_log(f"Ход бота: {name}")

        action = agent.select_action(self.game, idx)
        self._on_action_clicked(action)
        # _on_action_clicked сам обновит UI и снова вызовет _maybe_schedule_bot()


    # =====================================================================
    # Обновление UI
    # =====================================================================

    def _refresh_full_ui(self) -> None:
        """Полностью обновить отображение (инфо, игроки, карты, рынок, действия)."""
        self._update_info_labels()
        self._update_phase_hint()
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

        if self.game.done and self.game.winner is not None:
            winner = self.game.players[self.game.winner]
            winner_name = getattr(winner, "name", f"Игрок {self.game.winner + 1}")
            self.label_phase.setText(f"Игра окончена! Победитель: {winner_name}")

    def _update_phase_hint(self) -> None:
        """Крупный текст-объяснение, что сейчас нужно делать."""
        if self.game.done and self.game.winner is not None:
            winner = self.game.players[self.game.winner]
            winner_name = getattr(winner, "name", f"Игрок {self.game.winner + 1}")
            self.phase_hint_label.setText(f"Игра окончена. Победил {winner_name}!")
            self.phase_hint_label.setStyleSheet(
                "QLabel { padding: 8px; border-radius: 8px; background-color: #2d6a4f; color: white; }"
            )
            return

        idx = self.game.current_player
        current_player = self.game.players[idx]
        name = getattr(current_player, "name", f"Игрок {idx + 1}")

        if self.game.phase == Phase.ROLL:
            text = f"Ход {name}: брось кубик 🎲"
            style = "background-color: #343a40; color: #ffd166;"
        elif self.game.phase == Phase.BUY:
            text = f"Ход {name}: купи одну карту (клик по карте на рынке) или завершай ход."
            style = "background-color: #343a40; color: #06d6a0;"
        elif self.game.phase == Phase.RESOLVE:
            text = f"Ход {name}: разыгрываются эффекты карт..."
            style = "background-color: #343a40; color: #4cc9f0;"
        else:
            text = f"Ход {name}"
            style = "background-color: #343a40; color: white;"

        self.phase_hint_label.setText(text)
        self.phase_hint_label.setStyleSheet(
            f"QLabel {{ padding: 8px; border-radius: 8px; {style} }}"
        )

    def _update_players_list(self) -> None:
        self.players_list.clear()
        current_idx = self.game.current_player

        for idx, player in enumerate(self.game.players):
            name = getattr(player, "name", f"Игрок {idx + 1}")
            built_landmarks = sum(1 for v in player.landmarks.values() if v)

            if built_landmarks:
                text = f"{name}\n{player.coins} монет, 🏛 {built_landmarks}"
            else:
                text = f"{name}\n{player.coins} монет"

            item = QListWidgetItem(text)

            if self.coin_icon is not None:
                item.setIcon(self.coin_icon)

            # Подсветим текущего игрока
            if idx == current_idx:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setBackground(Qt.black)  # аккуратная подсветка
                item.setForeground(Qt.white)

            # Tooltip с подробностями
            total_landmarks = len(player.landmarks)
            item.setToolTip(
                f"{name}\nМонеты: {player.coins}\n"
                f"Достопримечательности: {built_landmarks}/{total_landmarks}"
            )

            self.players_list.addItem(item)

    def _update_player_cards(self) -> None:
        """Обновить список карт текущего игрока."""
        self.player_cards_list.clear()
        player = self.game.current_player_state()

        if not player.establishments:
            self.player_cards_list.addItem("Нет построенных предприятий")
            return

        for card_id, count in player.establishments.items():
            if count <= 0:
                continue
            card_def = get_card_def(card_id)

            text = f"{card_def.name} x{count}"
            item = QListWidgetItem(text)

            # Картинка
            if card_def.image:
                img_path = os.path.join(CARDS_IMG_DIR, card_def.image)
                if os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    icon = QIcon(pixmap)
                    item.setIcon(icon)

            numbers = ", ".join(str(n) for n in card_def.activation_numbers)
            item.setToolTip(
                f"{card_def.name}\n"
                f"Цвет: {card_def.color.value}\n"
                f"Цена: {card_def.cost}\n"
                f"Доход: {card_def.income}\n"
                f"Активируется на: {numbers}"
            )

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

        current_player = self.game.current_player_state()

        for card_id, qty in market.available.items():
            if qty <= 0:
                continue

            card_def = get_card_def(card_id)
            numbers = ", ".join(str(n) for n in card_def.activation_numbers)

            text = f"{card_def.name} (x{qty})"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, card_id)

            # Картинка
            if card_def.image:
                img_path = os.path.join(CARDS_IMG_DIR, card_def.image)
                if os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    icon = QIcon(pixmap)
                    item.setIcon(icon)

            item.setToolTip(
                f"{card_def.name}\n"
                f"Доступно: {qty}\n"
                f"Цена: {card_def.cost}\n"
                f"Доход: {card_def.income}\n"
                f"Активируется на: {numbers}"
            )

            # Можно ли купить эту карту сейчас?
            affordable = current_player.coins >= card_def.cost

            if not affordable or self.game.phase != Phase.BUY:
                # Сделаем менее яркой и выключим клики
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                item.setForeground(Qt.gray)
            else:
                # Оставляем кликабельной
                item.setFlags(item.flags() | Qt.ItemIsEnabled)

            self.market_list.addItem(item)

    # =====================================================================
    # Действия
    # =====================================================================

    def _clear_actions_layout(self) -> None:
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _rebuild_actions(self) -> None:
        """Перестроить панель действий (кнопки)."""
        self._clear_actions_layout()

        if self.game.done:
            return

        idx = self.game.current_player
        actions: List[Action] = legal_actions(self.game, idx)

        if self._current_agent() is not None:
            label = QLabel("Ход бота…")
            self.actions_layout.addWidget(label)
            return

        if not actions:
            label = QLabel("Нет доступных действий")
            self.actions_layout.addWidget(label)
            return

        # Покупки уже делаем кликом по картам → кнопки BUY_CARD не рисуем.
        filtered_actions: List[Action] = [
            a for a in actions if a.type != ActionType.BUY_CARD
        ]

        # Немного переупорядочим: ROLL → BUILD_LANDMARK → END_BUY
        def sort_key(a: Action) -> int:
            if a.type == ActionType.ROLL:
                return 0
            if a.type == ActionType.BUILD_LANDMARK:
                return 1
            if a.type == ActionType.END_BUY:
                return 2
            return 10

        filtered_actions.sort(key=sort_key)

        for action in filtered_actions:
            btn = QPushButton(self._format_action_text(action))
            btn.setMinimumHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setCursor(Qt.PointingHandCursor)

            btn.setStyleSheet(
                """
                QPushButton {
                    border-radius: 8px;
                    padding: 6px 16px;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                }
                """
            )

            btn.clicked.connect(
                lambda checked=False, a=action: self._on_action_clicked(a)
            )
            self.actions_layout.addWidget(btn)

        self.actions_layout.addStretch(1)

    def _format_action_text(self, action: Action) -> str:
        """Красивый текст для кнопки действия."""
        if action.type == ActionType.ROLL:
            return "Бросить кубик"

        if action.type == ActionType.END_BUY:
            return "Завершить ход"

        if action.type in (ActionType.BUILD_LANDMARK,) and action.card_id:
            card_def = get_card_def(action.card_id)
            return f"Построить: {card_def.name} (стоимость {card_def.cost})"

        return action.type.value

    # =====================================================================
    # Обработка действий и рынка
    # =====================================================================

    def _on_market_card_clicked(self, item: QListWidgetItem) -> None:
        """Покупка карты кликом по карте в рынке."""
        if self.game.done:
            return

        if self._current_agent() is not None:
            return
        
        if self.game.phase != Phase.BUY:
            # Не спамим диалогами, просто игнор
            return

        card_id = item.data(Qt.UserRole)

        if not card_id:
            return

        idx = self.game.current_player
        actions: List[Action] = legal_actions(self.game, idx)

        for act in actions:
            if act.type == ActionType.BUY_CARD and act.card_id == card_id:
                self._on_action_clicked(act)
                return

        card_def = get_card_def(card_id)
        self._append_log(f"Карту {card_def.name} сейчас нельзя купить")

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
                self._start_dice_animation(dice)

                self.game = apply_action(self.game, action, dice_value=dice)
                self._append_log(f"── Ход игрока {name} ──")
                self._append_log(f"{name} бросает кубик: выпало {dice}")
            else:
                self.game = apply_action(self.game, action)
                self._append_log(self._describe_non_roll_action(name, action))

            # Если ядро пишет что-то в state.log – заберём это в UI-лог
            if hasattr(self.game, "log"):
                engine_log = getattr(self.game, "log") or []
                for line in engine_log:
                    self._append_log(line)
                try:
                    self.game.log.clear()
                except Exception:
                    pass

        except Exception as ex:
            QMessageBox.warning(self, "Ошибка", str(ex))
            self._append_log(f"Ошибка: {ex}")
            return

        # После действия обновляем UI
        self._refresh_full_ui()

        
        self._maybe_schedule_bot()  # если первый игрок — бот, он сразу начнёт ход

        # Итог по монетам после каждого действия
        self._append_coins_summary()

    def _describe_non_roll_action(self, player_name: str, action: Action) -> str:
        """Текст для лога для не-ROLL действий."""
        if action.type == ActionType.END_BUY:
            return f"{player_name} завершает ход"

        if action.type == ActionType.BUILD_LANDMARK and action.card_id:
            card_def = get_card_def(action.card_id)
            return (
                f"{player_name} строит достопримечательность: "
                f"{card_def.name} за {card_def.cost} монет"
            )

        if action.type == ActionType.BUY_CARD and action.card_id:
            card_def = get_card_def(action.card_id)
            return f"{player_name} покупает карту: {card_def.name} за {card_def.cost} монет"

        return f"{player_name} выполняет действие: {action.type.value}"

    def _append_log(self, text: str) -> None:
        self.log.append(text)
        # автоскролл вниз
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _append_coins_summary(self) -> None:
        """Строка состояния монет всех игроков."""
        parts = []
        for idx, p in enumerate(self.game.players):
            name = getattr(p, "name", f"Игрок {idx + 1}")
            parts.append(f"{name}: {p.coins} монет")
        self._append_log(" | ".join(parts))

    # =====================================================================
    # КУБИК: картинка + простая анимация
    # =====================================================================

    def _set_dice_face(self, value: int) -> None:
        """Поставить на кубике картинку для значения 1..6."""
        img_name = f"{value}.png"
        img_path = os.path.join(DICE_IMG_DIR, img_name)

        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                self.dice_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.dice_label.setPixmap(pixmap)
        else:
            self.dice_label.clear()

    def _start_dice_animation(self, final_value: int) -> None:
        """Простая анимация кубика: несколько случайных значений, затем финальное."""
        import random

        seq: list[int] = []
        for _ in range(8):
            seq.append(random.randint(1, 6))
        seq.append(final_value)

        self._dice_sequence = seq

        if self._dice_timer is None:
            self._dice_timer = QTimer(self)
            self._dice_timer.timeout.connect(self._on_dice_timer)

        self._dice_timer.start(70)

    def _on_dice_timer(self) -> None:
        if not self._dice_sequence:
            if self._dice_timer is not None:
                self._dice_timer.stop()
            return

        value = self._dice_sequence.pop(0)
        self._set_dice_face(value)



# # ui/main_window.py

# from __future__ import annotations

# from random import randint
# from typing import List
# import os
# from PySide6.QtGui import QPixmap, QIcon, QFont
# from PySide6.QtCore import Qt, QSize, QTimer
# from PySide6.QtWidgets import (
#     QWidget,
#     QMainWindow,
#     QVBoxLayout,
#     QHBoxLayout,
#     QLabel,
#     QPushButton,
#     QTextEdit,
#     QListWidget,
#     QListWidgetItem,
#     QListView,
#     QMessageBox,
#     QInputDialog,
#     QSpacerItem,
#     QSizePolicy,
#     QScrollArea,
#     QFrame
# )
# from machi_core.state import Phase
# from machi_core.rules import new_game, apply_action, legal_actions
# from machi_core.actions import ActionType, Action
# from machi_core.cards import get_card_def

# # Папка с картинками карт
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# CARDS_IMG_DIR = os.path.join(BASE_DIR, "assets", "images", "cards")

# CARD_W, CARD_H = 174, 271

# COIN_IMG_PATH = os.path.join(BASE_DIR, "assets", "images", "ui", "coin1.png")

# DICE_IMG_DIR = os.path.join(BASE_DIR, "assets", "images", "dice")

# def _roll_dice() -> int:
#     """UI-обёртка для броска кубика."""
#     return randint(1, 6)


# class MainWindow(QMainWindow):
#     def __init__(self, num_players: int = 2, parent: QWidget | None = None) -> None:
#         super().__init__(parent)

#         self.setWindowTitle("Machi Koro (Desktop MVP)")
#         self.resize(1100, 650)

#         # --- Состояние игры ---
#         self.num_players = num_players
#         self._ask_num_players()
        
#         self.game = new_game(self.num_players)
#         self._ask_player_names()

#         # --- Виджеты ---
#         central = QWidget(self)
#         self.setCentralWidget(central)

#         root_layout = QHBoxLayout()
#         central.setLayout(root_layout)

#         # Левая колонка: общая информация
#         left_layout = QVBoxLayout()
#         root_layout.addLayout(left_layout, 1)

#         self.label_current = QLabel()
#         self.label_phase = QLabel()
#         self.label_last_roll = QLabel()
        
#         # ---- КУБИК ----
#         self.dice_label = QLabel()
#         self.dice_label.setAlignment(Qt.AlignCenter)
#         self.dice_label.setFixedSize(120, 120)   # размер “окна” под кубик
#         left_layout.addWidget(self.dice_label)
        
#         left_layout.addWidget(self.label_current)
#         left_layout.addWidget(self.label_phase)
#         left_layout.addWidget(self.label_last_roll)

#         left_layout.addWidget(QLabel("Игроки:"))
#         self.players_list = QListWidget()
#         left_layout.addWidget(self.players_list, stretch=1)

#         # --- настройки отображения списка игроков как плиток с монеткой ---
#         self.players_list.setViewMode(QListView.IconMode)
#         self.players_list.setFlow(QListView.LeftToRight)
#         self.players_list.setWrapping(True)
#         self.players_list.setIconSize(QSize(40, 40))
#         self.players_list.setResizeMode(QListView.Adjust)
#         self.players_list.setSpacing(8)

#         # Загружаем иконку монетки один раз
#         self.coin_icon = None
#         if os.path.exists(COIN_IMG_PATH):
#             pixmap = QPixmap(COIN_IMG_PATH)
#             if not pixmap.isNull():
#                 self.coin_icon = QIcon(pixmap)

#         # Правая колонка: карты, рынок, действия, лог
#         right_layout = QVBoxLayout()
#         root_layout.addLayout(right_layout, 3)

#         # Блок: карты текущего игрока
#         right_layout.addWidget(QLabel("Карты текущего игрока:"))

#         # Карты текущего игрока
#         self.player_cards_list = QListWidget()
        
#         right_layout.addWidget(self.player_cards_list, stretch=3)

#         # --- настройки отображения карт игрока ---
#         self.player_cards_list.setViewMode(QListView.IconMode)      # плитки, а не список
#         self.player_cards_list.setFlow(QListView.LeftToRight)       # слева направо
#         self.player_cards_list.setWrapping(True)                    # перенос по строкам
#         self.player_cards_list.setIconSize(QSize(CARD_W, CARD_H))         # размер карты
#         self.player_cards_list.setResizeMode(QListView.Adjust)
#         self.player_cards_list.setSpacing(8)

#         # Рынок
#         right_layout.addWidget(QLabel("Рынок:"))

#         self.market_list = QListWidget()
#         right_layout.addWidget(self.market_list, stretch=3)
        
#         self.market_list.itemClicked.connect(self._on_market_card_clicked)

#         # --- настройки отображения рынка ---
#         self.market_list.setViewMode(QListView.IconMode)
#         self.market_list.setFlow(QListView.LeftToRight)
#         self.market_list.setWrapping(True)
#         self.market_list.setIconSize(QSize(CARD_W, CARD_H))
#         self.market_list.setResizeMode(QListView.Adjust)
#         self.market_list.setSpacing(8)



#         # Немного пространства перед действиями
#         right_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Minimum))

        
#         right_layout.addWidget(QLabel("Доступные действия:"))

#         self.actions_container = QWidget()
#         self.actions_layout = QHBoxLayout(self.actions_container)
#         self.actions_layout.setContentsMargins(0, 0, 0, 0)
#         self.actions_layout.setSpacing(8)

#         # Горизонтальный скролл (если много действий)
#         self.actions_scroll = QScrollArea()
#         self.actions_scroll.setWidgetResizable(True)
#         self.actions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
#         self.actions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#         self.actions_scroll.setFrameShape(QFrame.NoFrame)
#         self.actions_scroll.setWidget(self.actions_container)

#         right_layout.addWidget(self.actions_scroll)


#         right_layout.addWidget(QLabel("Лог:"))
#         self.log = QTextEdit()
#         self.log.setReadOnly(True)
#         self.log.setFixedHeight(140)  # фиксированная высота
#         right_layout.addWidget(self.log)


#         # Инициализация UI по состоянию игры
#         self._refresh_full_ui()

        
#         self._dice_timer: QTimer | None = None
#         self._dice_sequence: list[int] = []


#     # market
#     def _on_market_card_clicked(self, item: QListWidgetItem) -> None:
#         """Покупка карты кликом по карте в рынке."""
#         if self.game.done:
#             return

#         # Покупать можно только в фазу BUY
#         if self.game.phase != Phase.BUY:
#             return  # можешь тут показать всплывашку, если хочешь

#         card_id = item.data(Qt.UserRole)
#         if not card_id:
#             return

#         idx = self.game.current_player
#         actions: list[Action] = legal_actions(self.game, idx)

#         # Ищем действие BUY_CARD именно для этой карты
#         for act in actions:
#             if act.type == ActionType.BUY_CARD and act.card_id == card_id:
#                 # Используем уже существующую логику применения действий
#                 self._on_action_clicked(act)
#                 return

#         # Если сюда дошли – эту карту сейчас купить нельзя
#         card_def = get_card_def(card_id)
#         self._append_log(f"Карту {card_def.name} сейчас нельзя купить")


#     # КУБИК
#     def _set_dice_face(self, value: int) -> None:
#         """Поставить на кубике картинку для значения 1..6."""
#         img_name = f"{value}.png"
#         img_path = os.path.join(DICE_IMG_DIR, img_name)

#         pixmap = QPixmap(img_path)
#         if not pixmap.isNull():
#             # немного подмасштабировать под QLabel
#             pixmap = pixmap.scaled(
#                 self.dice_label.size(),
#                 Qt.KeepAspectRatio,
#                 Qt.SmoothTransformation,
#             )
#             self.dice_label.setPixmap(pixmap)
#         else:
#             # если вдруг файл не нашёлся – очищаем
#             self.dice_label.clear()


#     def _start_dice_animation(self, final_value: int) -> None:
#         """
#         Простая “анимация” кубика:
#         - несколько случайных значений;
#         - затем финальное.
#         """
#         import random

#         # последовательность временных значений + финальное
#         seq: list[int] = []
#         for _ in range(8):         # сколько раз “мигнёт”
#             seq.append(random.randint(1, 6))
#         seq.append(final_value)

#         self._dice_sequence = seq

#         if self._dice_timer is None:
#             self._dice_timer = QTimer(self)
#             self._dice_timer.timeout.connect(self._on_dice_timer)

#         self._dice_timer.start(70)  # интервал между кадрами (мс)


#     def _on_dice_timer(self) -> None:
#         if not self._dice_sequence:
#             if self._dice_timer is not None:
#                 self._dice_timer.stop()
#             return

#         value = self._dice_sequence.pop(0)
#         self._set_dice_face(value)



#     # === Коилчество игроков ======================================================

#     def _ask_num_players(self) -> None:
#         """Спрашивает количество игроков перед началом партии."""
#         while True:
#             num, ok = QInputDialog.getText(
#                 self,
#                 "Количество игроков",
#                 f"Введите количество игроков:",
#             )
#             if not ok:
#                 # Если пользователь нажал Cancel – поставим какое-нибудь имя по умолчанию
#                 self.num_players = 2
#                 break
#             num = num.strip()
#             if not num.isdigit():
#                 continue  # нормальное имя
#             num = int(num)
#             break
#         self.num_players = num

#     # === Имена игроков ======================================================

#     def _ask_player_names(self) -> None:
#         """Спрашивает имена для всех игроков перед началом партии."""
#         for idx, player in enumerate(self.game.players):
#             while True:
#                 name, ok = QInputDialog.getText(
#                     self,
#                     "Имя игрока",
#                     f"Введите имя для игрока {idx + 1}:",
#                 )
#                 if not ok:
#                     # Нажали Cancel — поставим дефолтное имя
#                     name = f"Игрок {idx + 1}"
#                     break
#                 name = name.strip()
#                 if name:
#                     break
#             player.name = name

#     # === Обновление UI ======================================================

#     def _refresh_full_ui(self) -> None:
#         """Полностью обновить отображение (инфо, игроки, карты, рынок, действия)."""
#         self._update_info_labels()
#         self._update_players_list()
#         self._update_player_cards()
#         self._update_market()
#         self._rebuild_actions()

#     def _update_info_labels(self) -> None:
#         idx = self.game.current_player
#         current_player = self.game.players[idx]
#         name = getattr(current_player, "name", f"Игрок {idx + 1}")

#         self.label_current.setText(f"Текущий игрок: {name} (#{idx + 1})")
#         self.label_phase.setText(f"Фаза: {self.game.phase.value}")

#         if self.game.last_roll is None:
#             self.label_last_roll.setText("Последний бросок: —")
#         else:
#             self.label_last_roll.setText(f"Последний бросок: {self.game.last_roll}")

#         if self.game.done:
#             winner_name = getattr(self.game.players[self.game.winner], "name", f"Игрок {self.game.winner + 1}")
#             self.label_phase.setText(f"Игра окончена! Победитель: {winner_name}")

#     def _update_players_list(self) -> None:
#         self.players_list.clear()
#         for idx, player in enumerate(self.game.players):
#             name = getattr(player, "name", f"Игрок {idx + 1}")
#             # Текст будет ПОД иконкой (IconMode): имя и количество монет
#             text = f"{name}\n{player.coins} монет"

#             item = QListWidgetItem(text)

#             # Если иконка монетки загрузилась – ставим её
#             if self.coin_icon is not None:
#                 item.setIcon(self.coin_icon)

#             # Можно дополнительно подсветить текущего игрока позже
#             self.players_list.addItem(item)


#     def _update_player_cards(self) -> None:
#         """Обновить список карт текущего игрока."""
#         self.player_cards_list.clear()
#         player = self.game.current_player_state()

#         if not player.establishments:
#             self.player_cards_list.addItem("Нет построенных предприятий")
#             return

#         for card_id, count in player.establishments.items():
#             if count <= 0:
#                 continue
#             card_def = get_card_def(card_id)
#             numbers = ",".join(str(n) for n in card_def.activation_numbers)

#             text = f"{card_def.name} x{count}"

#             item = QListWidgetItem(text)

#             # картинка, если указана
#             if card_def.image:
#                 img_path = os.path.join(CARDS_IMG_DIR, card_def.image)
#                 if os.path.exists(img_path):
#                     pixmap = QPixmap(img_path)
#                     icon = QIcon(pixmap)
#                     item.setIcon(icon)

#             self.player_cards_list.addItem(item)


#         # Достопримечательности
#         built_landmarks = [lid for lid, built in player.landmarks.items() if built]
#         if built_landmarks:
#             self.player_cards_list.addItem("--- Достопримечательности ---")
#             for lid in built_landmarks:
#                 ldef = get_card_def(lid)
#                 self.player_cards_list.addItem(f"{ldef.name} (построено)")



#     def _update_market(self) -> None:
#         """Обновить список карт на рынке."""
#         self.market_list.clear()
#         market = self.game.market

#         if not market.available:
#             self.market_list.addItem("Рынок пуст")
#             return

#         for card_id, qty in market.available.items():
#             if qty <= 0:
#                 continue
#             card_def = get_card_def(card_id)
#             numbers = ",".join(str(n) for n in card_def.activation_numbers)

#             text = (
#                 f"{card_def.name} | доступно: {qty}, "
#                 f"цена: {card_def.cost}, "
#                 f"доход: {card_def.income}, "
#                 f"кубик: {numbers}"
#             )

#             item = QListWidgetItem(text)

#             # ← ВАЖНО: сохраним id карты в item
#             item.setData(Qt.UserRole, card_id)

#             if card_def.image:
#                 img_path = os.path.join(CARDS_IMG_DIR, card_def.image)
#                 if os.path.exists(img_path):
#                     pixmap = QPixmap(img_path)
#                     icon = QIcon(pixmap)
#                     item.setIcon(icon)

#             self.market_list.addItem(item)


#     def _clear_actions_layout(self) -> None:
#         while self.actions_layout.count():
#             item = self.actions_layout.takeAt(0)
#             w = item.widget()
#             if w is not None:
#                 w.deleteLater()

#     def _rebuild_actions(self) -> None:
#         self._clear_actions_layout()

#         if self.game.done:
#             return

#         idx = self.game.current_player
#         actions: List[Action] = legal_actions(self.game, idx)

#         if not actions:
#             label = QLabel("Нет доступных действий")
#             self.actions_layout.addWidget(label)
#             return

#         for action in actions:
#             if action.type == ActionType.BUY_CARD:
#                 continue

#             btn = QPushButton(self._format_action_text(action))

#             # Крупная “пилюлька”
#             btn.setMinimumHeight(40)
#             btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
#             btn.setCursor(Qt.PointingHandCursor)

#             # Лёгкий стиль (подгони под свою тему, если хочешь)
#             btn.setStyleSheet("""
#                 QPushButton {
#                     border-radius: 8px;
#                     padding: 6px 16px;
#                     font-size: 11pt;
#                 }
#                 QPushButton:hover {
#                     opacity: 0.9;
#                 }
#             """)

#             btn.clicked.connect(lambda checked=False, a=action: self._on_action_clicked(a))
#             self.actions_layout.addWidget(btn)

#         # Немного свободного места справа
#         self.actions_layout.addStretch(1)

#     def _format_action_text(self, action: Action) -> str:
#         """Красивый текст для кнопки действия."""
#         if action.type == ActionType.ROLL:
#             return "Бросить кубик"

#         if action.type == ActionType.END_BUY:
#             return "Завершить фазу покупки"

#         if action.type in (ActionType.BUY_CARD, ActionType.BUILD_LANDMARK) and action.card_id:
#             card_def = get_card_def(action.card_id)
#             if action.type == ActionType.BUY_CARD:
#                 return f"Купить: {card_def.name} (стоимость {card_def.cost}, доход {card_def.income})"
#             else:
#                 return f"Построить: {card_def.name} (стоимость {card_def.cost})"

#         return action.type.value

#     # === Обработка действий ==================================================

#     def _on_action_clicked(self, action: Action) -> None:
#         """Когда игрок нажимает кнопку действия."""
#         if self.game.done:
#             return

#         idx = self.game.current_player
#         current_player = self.game.players[idx]
#         name = getattr(current_player, "name", f"Игрок {idx + 1}")

#         try:
#             if action.type == ActionType.ROLL:
#                 dice = _roll_dice()

#                 # Запускаем анимацию кубика
#                 self._start_dice_animation(dice)

#                 # Применяем действие к игре
#                 self.game = apply_action(self.game, action, dice_value=dice)
#                 self._append_log(f"{name} бросает кубик: выпало {dice}")

#             else:
#                 self.game = apply_action(self.game, action)
#                 self._append_log(self._describe_non_roll_action(name, action))

#         except Exception as ex:
#             QMessageBox.warning(self, "Ошибка", str(ex))
#             self._append_log(f"Ошибка: {ex}")
#             return

#         # После действия обновляем UI
#         self._refresh_full_ui()

#     def _describe_non_roll_action(self, player_name: str, action: Action) -> str:
#         """Текст для лога для не-ROLL действий."""
#         if action.type == ActionType.END_BUY:
#             return f"{player_name} завершает фазу покупки"

#         if action.type in (ActionType.BUY_CARD, ActionType.BUILD_LANDMARK) and action.card_id:
#             card_def = get_card_def(action.card_id)
#             if action.type == ActionType.BUY_CARD:
#                 return f"{player_name} покупает карту: {card_def.name} за {card_def.cost} монет"
#             else:
#                 return f"{player_name} строит достопримечательность: {card_def.name} за {card_def.cost} монет"

#         return f"{player_name} выполняет действие: {action.type.value}"

#     def _append_log(self, text: str) -> None:
#         self.log.append(text)

