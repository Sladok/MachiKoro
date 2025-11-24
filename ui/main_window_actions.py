# ui/main_window_actions.py
from __future__ import annotations

from typing import TYPE_CHECKING, List
from random import randint

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QMessageBox, QSizePolicy, QInputDialog

from machi_core.actions import Action, ActionType
from machi_core.cards import get_card_def
from machi_core.rules import apply_action, legal_actions
from machi_core.state import Phase

if TYPE_CHECKING:
    from ui.main_window import MainWindow


def _roll_dice(num_dice: int = 1) -> list[int]:
    """Бросить num_dice кубиков, вернуть список значений."""
    return [randint(1, 6) for _ in range(num_dice)]


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

        # нас интересует только кнопка "Завершить ход"
        end_actions = [a for a in actions if a.type == ActionType.END_BUY]
        if not end_actions:
            return

        end_action = end_actions[0]

        text = self._format_action_text(end_action)
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)

        # большая красная кнопка
        btn.setMinimumHeight(48)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: white;
                font-weight: bold;
                font-size: 13pt;
                border-radius: 8px;
                padding: 8px 24px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)

        # Qt сам подберёт ширину по тексту + padding
        btn.clicked.connect(
            lambda checked=False, a=end_action: self._on_action_clicked(a)
        )

        self.actions_layout.addWidget(btn)



    def _on_dice_label_clicked(self: "MainWindow") -> None:
        """Клик по картинке кубика в заголовке рынка."""
        # игра закончена или ходит бот — игнорируем
        if self.game.done:
            return
        
        if self._current_agent() is not None:
            return
        
        if self.game.phase != Phase.ROLL:
            return

        idx = self.game.current_player
        actions: List[Action] = legal_actions(self.game, idx)

        roll_actions = [a for a in actions if a.type == ActionType.ROLL]
        if not roll_actions:
            return

        roll_action = roll_actions[0]

        # смотрим, построен ли вокзал у текущего игрока
        player = self.game.current_player_state()
        has_station = player.has_built("train_station")

        num_dice = 1
        if has_station:
            # выбор 1 или 2 кубика
            options = ["Бросить 1 кубик", "Бросить 2 кубика"]
            text, ok = QInputDialog.getItem(
                self,
                "Бросок кубиков",
                "Сколько кубиков бросить?",
                options,
                0,
                False,
            )
            if not ok:
                return
            num_dice = 2 if "2 кубика" in text else 1

        # записываем выбор в Action и исполняем
        roll_action.num_dice = num_dice
        self._on_action_clicked(roll_action)


    def _format_action_text(self: "MainWindow", action: Action) -> str:
        if action.type == ActionType.ROLL:
            return "Бросить кубик"
        if action.type == ActionType.END_BUY:
            return "Завершить ход"
        if action.type == ActionType.BUILD_LANDMARK and action.card_id:
            card_def = get_card_def(action.card_id)
            return f"Построить: {card_def.name} (стоимость {card_def.cost})"
        return action.type.value

    def _handle_game_over(self: "MainWindow") -> None:
        """Показать, что партия закончена, и предложить рестарт."""
        winner_idx = self.game.winner
        if winner_idx is not None and 0 <= winner_idx < len(self.game.players):
            player = self.game.players[winner_idx]
            name = getattr(player, "name", f"Игрок {winner_idx + 1}")
            text = f"Игра окончена.\nПобедитель: {name}"
        else:
            text = "Игра окончена."

        res = QMessageBox.question(
            self,
            "Конец игры",
            text + "\n\nНачать новую партию?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if res == QMessageBox.Yes:
            self._reset_game()


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

    def _on_player_landmark_clicked(self: "MainWindow", player_idx: int, item) -> None:
        """Клик по достопримечательности в полосе игрока."""
        from machi_core.actions import ActionType as AT

        if self.game.done:
            return
        if self._current_agent() is not None:
            return  # сейчас ход бота

        # клики другого игрока игнорируем — строить можно только у текущего
        if player_idx != self.game.current_player:
            return

        # достопримечательности строятся только в фазе BUY
        if self.game.phase != Phase.BUY:
            return

        data = item.data(Qt.UserRole)
        if not isinstance(data, dict):
            return
        if data.get("kind") != "landmark":
            return

        landmark_id = data.get("id")
        built = bool(data.get("built"))

        if not landmark_id or built:
            # нет id или уже построена — делать нечего
            return

        player = self.game.players[player_idx]
        card_def = get_card_def(landmark_id)

        # проверяем, хватает ли монет
        if player.coins < card_def.cost:
            name = getattr(player, "name", f"Игрок {player_idx + 1}")
            self._append_log(
                f"{name} не может построить {card_def.name}: не хватает монет"
            )
            return

        # ищем легальное действие BUILD_LANDMARK именно для этой карты
        actions: List[Action] = legal_actions(self.game, player_idx)
        for act in actions:
            if act.type == AT.BUILD_LANDMARK and act.card_id == landmark_id:
                self._on_action_clicked(act)
                return

        # если сюда дошли — значит ядро не считает строительство этой карты допустимым
        self._append_log(f"Достопримечательность {card_def.name} сейчас нельзя построить")

    def _on_action_clicked(self: "MainWindow", action: Action) -> None:
        if self.game.done:
            return

        idx = self.game.current_player
        current_player = self.game.players[idx]
        name = getattr(current_player, "name", f"Игрок {idx + 1}")

        try:
            if action.type == ActionType.ROLL:
                num_dice = getattr(action, "num_dice", 1)
                dice_values = _roll_dice(num_dice)
                total = sum(dice_values)

                # сохраним реальные значения — их отрисует DiceMixin
                self._last_dice_values = dice_values

                # анимация — крутим последний кубик
                self._start_dice_animation(dice_values[-1])

                # ядру передаём только сумму
                self.game = apply_action(self.game, action, dice_value=total)

                if num_dice == 1:
                    self._append_log(f"{name} бросает кубик: выпало {total}")
                else:
                    s = " + ".join(str(v) for v in dice_values)
                    self._append_log(
                        f"{name} бросает {num_dice} кубика: {s} = {total}"
                    )
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

        if self.game.done:
            self._handle_game_over()

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
