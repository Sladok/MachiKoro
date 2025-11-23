# ui/main_window_log.py
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class LogMixin:
    def _append_log(self: "MainWindow", text: str) -> None:
        # На экране логов нет, просто печать в консоль
        print(text)

    def _append_coins_summary(self: "MainWindow") -> None:
        parts = []
        for idx, p in enumerate(self.game.players):
            name = getattr(p, "name", f"Игрок {idx + 1}")
            parts.append(f"{name}: {p.coins} монет")
        self._append_log(" | ".join(parts))
