# ui/main_window_bots.py
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from machi_core.agents import Agent
from machi_core.rules import legal_actions

if TYPE_CHECKING:
    from ui.main_window import MainWindow

BOT_WAIT = 100

class BotsMixin:
    def _current_agent(self: "MainWindow") -> Agent | None:
        idx = self.game.current_player
        if 0 <= idx < len(self.agents):
            return self.agents[idx]
        return None

    def _maybe_schedule_bot(self: "MainWindow") -> None:
        if self.game.done:
            return
        agent = self._current_agent()
        if agent is None:
            return
        QTimer.singleShot(BOT_WAIT, self._bot_step)  # чуть подождать, чтобы было видно

    def _bot_step(self: "MainWindow") -> None:
        if self.game.done:
            return
        agent = self._current_agent()
        if agent is None:
            return

        idx = self.game.current_player
        actions = legal_actions(self.game, idx)
        if not actions:
            return

        action = agent.select_action(self.game, idx)
        self._on_action_clicked(action)
