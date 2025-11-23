# ui/main_window_dice.py
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable
import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter

from ui.config import DICE_IMG_DIR

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class DiceMixin:
    def _set_dice_face(self: "MainWindow", value) -> None:
        """
        value может быть:
          - int  -> один кубик;
          - list/tuple[int] -> несколько кубиков (мы рисуем первые два).
        """
        # нормализуем к списку
        if isinstance(value, (list, tuple)):
            faces = [int(v) for v in value]
        else:
            faces = [int(value)]

        # оставляем только нормальные грани 1..6
        faces = [f for f in faces if 1 <= f <= 6]
        if not faces:
            self.dice_label.clear()
            return

        # ------- один кубик (как раньше) -------------------------------------
        if len(faces) == 1:
            face = faces[0]
            img_name = f"{face}.png"
            img_path = os.path.join(DICE_IMG_DIR, img_name)
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self.dice_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.dice_label.setPixmap(pixmap)
                self.dice_label.setText("")
            else:
                self.dice_label.clear()
            return

        # ------- два кубика: рисуем оба в одном pixmap ----------------------
        faces = faces[:2]
        w = max(1, self.dice_label.width())
        h = max(1, self.dice_label.height())

        canvas = QPixmap(w, h)
        canvas.fill(Qt.transparent)

        painter = QPainter(canvas)
        try:
            die_w = int(w * 0.55)
            die_h = int(h * 0.55)

            pixmaps = []
            for f in faces:
                path = os.path.join(DICE_IMG_DIR, f"{f}.png")
                pm = QPixmap(path)
                if pm.isNull():
                    continue
                pm = pm.scaled(
                    die_w,
                    die_h,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                pixmaps.append(pm)

            if not pixmaps:
                self.dice_label.clear()
                return

            if len(pixmaps) == 1:
                # если удалось загрузить только один — рисуем его по центру
                pm = pixmaps[0]
                x = (w - pm.width()) // 2
                y = (h - pm.height()) // 2
                painter.drawPixmap(x, y, pm)
            else:
                pm1, pm2 = pixmaps[0], pixmaps[1]
                # первый — левее и ниже
                x1 = int(w * 0.05)
                y1 = int(h * 0.40)
                # второй — правее и выше
                x2 = int(w * 0.40)
                y2 = int(h * 0.05)
                painter.drawPixmap(x1, y1, pm1)
                painter.drawPixmap(x2, y2, pm2)
        finally:
            painter.end()

        self.dice_label.setPixmap(canvas)
        self.dice_label.setText("")

    def _start_dice_animation(self: "MainWindow", final_face: int) -> None:
        """
        Анимация "крутящегося" кубика. Для 2 кубиков мы анимируем просто
        один, а в конце, после анимации, покажем оба реально выпавших.
        """
        import random

        seq: list[int] = [random.randint(1, 6) for _ in range(8)]
        seq.append(final_face)
        self._dice_sequence = seq

        if self._dice_timer is None:
            self._dice_timer = QTimer(self)
            self._dice_timer.timeout.connect(self._on_dice_timer)

        self._dice_timer.start(70)

    def _on_dice_timer(self: "MainWindow") -> None:
        if not self._dice_sequence:
            if self._dice_timer is not None:
                self._dice_timer.stop()

            # после анимации показываем реальный бросок:
            # один или два кубика (берём из self._last_dice_values)
            last_values = getattr(self, "_last_dice_values", None)
            if last_values:
                self._set_dice_face(last_values)
            return

        value = self._dice_sequence.pop(0)
        # во время анимации крутим один кубик
        self._set_dice_face(value)


# # ui/main_window_dice.py
# from __future__ import annotations

# from typing import TYPE_CHECKING
# import os

# from PySide6.QtCore import Qt, QTimer
# from PySide6.QtGui import QPixmap

# from ui.config import DICE_IMG_DIR

# if TYPE_CHECKING:
#     from ui.main_window import MainWindow


# class DiceMixin:
#     def _set_dice_face(self: "MainWindow", value: int) -> None:
#         img_name = f"{value}.png"
#         img_path = os.path.join(DICE_IMG_DIR, img_name)
#         pixmap = QPixmap(img_path)
#         if not pixmap.isNull():
#             pixmap = pixmap.scaled(
#                 self.dice_label.size(),
#                 Qt.KeepAspectRatio,
#                 Qt.SmoothTransformation,
#             )
#             self.dice_label.setPixmap(pixmap)
#             self.dice_label.setText("")  # на всякий случай
#         else:
#             # нет картинки (например, значение 7-12) — просто показываем число
#             self.dice_label.setPixmap(QPixmap())
#             self.dice_label.setText(str(value))

#     def _start_dice_animation(self: "MainWindow", final_value: int) -> None:
#         import random

#         seq: list[int] = [random.randint(1, 6) for _ in range(8)]
#         seq.append(final_value)
#         self._dice_sequence = seq

#         if self._dice_timer is None:
#             self._dice_timer = QTimer(self)
#             self._dice_timer.timeout.connect(self._on_dice_timer)

#         self._dice_timer.start(70)

#     def _on_dice_timer(self: "MainWindow") -> None:
#         if not self._dice_sequence:
#             if self._dice_timer is not None:
#                 self._dice_timer.stop()
#             return

#         value = self._dice_sequence.pop(0)
#         self._set_dice_face(value)
