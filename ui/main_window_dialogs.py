# ui/main_window_dialogs.py
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QInputDialog
from machi_core.agents import RandomBot

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class DialogsMixin:
    def _ask_num_players(self: "MainWindow") -> None:
        while True:
            num_str, ok = QInputDialog.getText(
                self,
                "Количество игроков",
                "Введите количество игроков (2–6):",
            )
            if not ok:
                self.num_players = 2
                return

            num_str = num_str.strip()
            if not num_str.isdigit():
                continue

            num = int(num_str)
            if not (2 <= num <= 6):
                continue

            self.num_players = num
            return

    def _ask_player_names(self: "MainWindow") -> None:
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

    def _setup_agents(self: "MainWindow") -> None:
        """Для каждого игрока: человек или бот."""
        for idx, player in enumerate(self.game.players):
            default_index = 0 if idx == 0 else 1
            choice, ok = QInputDialog.getItem(
                self,
                "Тип игрока",
                f"Игрок {idx + 1} ({getattr(player, 'name', '') or 'без имени'}): кто это?",
                ["Человек", "Бот (простая стратегия)"],
                default_index,
                False,
            )
            if not ok:
                choice = "Человек"
            self.agents[idx] = RandomBot() if choice.startswith("Бот") else None
