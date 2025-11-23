# ui/main_window_dice.py
from __future__ import annotations

from typing import TYPE_CHECKING
import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap

from ui.config import DICE_IMG_DIR

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class DiceMixin:
    def _set_dice_face(self: "MainWindow", value: int) -> None:
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

    def _start_dice_animation(self: "MainWindow", final_value: int) -> None:
        import random

        seq: list[int] = [random.randint(1, 6) for _ in range(8)]
        seq.append(final_value)
        self._dice_sequence = seq

        if self._dice_timer is None:
            self._dice_timer = QTimer(self)
            self._dice_timer.timeout.connect(self._on_dice_timer)

        self._dice_timer.start(70)

    def _on_dice_timer(self: "MainWindow") -> None:
        if not self._dice_sequence:
            if self._dice_timer is not None:
                self._dice_timer.stop()
            return

        value = self._dice_sequence.pop(0)
        self._set_dice_face(value)
