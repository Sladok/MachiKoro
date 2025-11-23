# ui/main_window_actions.py
from __future__ import annotations

from typing import TYPE_CHECKING, List
from random import randint

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QMessageBox, QSizePolicy

from machi_core.actions import Action, ActionType
from machi_core.cards import get_card_def
from machi_core.rules import apply_action, legal_actions
from machi_core.state import Phase

if TYPE_CHECKING:
    from ui.main_window import MainWindow


def _roll_dice() -> int:
    return randint(1, 6)


class ActionsMixin:
    # ===== панель действий ===================================================
    def _clear_actions_layout(self: "MainWindow") -> None:
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _rebuild_actions(self: "MainWindow") -> None:
        self._clear_actions_layout()

        if self.game.done:
            return

        # если ходит бот – человеку кнопки не показываем
        if self._current_agent() is not None:
            return

        idx = self.game.current_player
        actions: List[Action] = legal_actions(self.game, idx)
        if not actions:
            return

        filtered_actions: List[Action] = [
            a for a in actions if a.type != ActionType.BUY_CARD
        ]

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
            btn.setMinimumHeight(36)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, a=action: self._on_action_clicked(a)
            )
            self.actions_layout.addWidget(btn)

        self.actions_layout.addStretch(1)

    def _format_action_text(self: "MainWindow", action: Action) -> str:
        if action.type == ActionType.ROLL:
            return "Бросить кубик"
        if action.type == ActionType.END_BUY:
            return "Завершить ход"
        if action.type == ActionType.BUILD_LANDMARK and action.card_id:
            card_def = get_card_def(action.card_id)
            return f"Построить: {card_def.name} (стоимость {card_def.cost})"
        return action.type.value

    # ===== клики по рынку и действиям =======================================

    def _on_market_card_clicked(self: "MainWindow", card_id: str) -> None:
        """Клик по карте на рынке (попытка покупки)."""
        if self.game.done:
            return
        if self._current_agent() is not None:
            return
        if self.game.phase != Phase.BUY:
            return
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

    def _on_action_clicked(self: "MainWindow", action: Action) -> None:
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
                self._append_log(f"{name} бросает кубик: выпало {dice}")
            else:
                self.game = apply_action(self.game, action)
                self._append_log(self._describe_non_roll_action(name, action))

            # забираем лог ядра, если он есть
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

        self._refresh_full_ui()
        self._maybe_schedule_bot()
        self._append_coins_summary()

    def _describe_non_roll_action(
        self: "MainWindow", player_name: str, action: Action
    ) -> str:
        from machi_core.actions import ActionType as AT

        if action.type == AT.END_BUY:
            return f"{player_name} завершает ход"
        if action.type == AT.BUILD_LANDMARK and action.card_id:
            card_def = get_card_def(action.card_id)
            return (
                f"{player_name} строит достопримечательность: "
                f"{card_def.name} за {card_def.cost} монет"
            )
        if action.type == AT.BUY_CARD and action.card_id:
            card_def = get_card_def(action.card_id)
            return (
                f"{player_name} покупает карту: "
                f"{card_def.name} за {card_def.cost} монет"
            )
        return f"{player_name} выполняет действие: {action.type.value}"
