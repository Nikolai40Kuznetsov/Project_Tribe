import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRect

CELL_SIZE = 150
COLS = 12
ROWS = 6
FIELD_W = CELL_SIZE * COLS
FIELD_H = CELL_SIZE * ROWS


class GridWidget(QWidget):
    """Игровое поле с сеткой и рекой."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(FIELD_W, FIELD_H)

        self.tiles = [[{"col": c, "row": r, "is_river": False} for c in range(COLS)] for r in range(ROWS)]
        self.generate_river()

    def generate_river(self):
        if random.random() < 0.5:
            r = random.randint(1, ROWS - 2)
            c = 0
            while c < COLS:
                self.tiles[r][c]["is_river"] = True
                if random.random() < 0.3 and c < COLS - 1:
                    dr = random.choice([-1, 1])
                    if 0 < r + dr < ROWS - 1:
                        r += dr
                c += 1
        else:
            c = random.randint(1, COLS - 2)
            r = 0
            while r < ROWS:
                self.tiles[r][c]["is_river"] = True
                if random.random() < 0.3 and r < ROWS - 1:
                    dc = random.choice([-1, 1])
                    if 0 < c + dc < COLS - 1:
                        c += dc
                r += 1

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        for r in range(ROWS):
            for c in range(COLS):
                if self.tiles[r][c]["is_river"]:
                    rect = QRect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    painter.setBrush(QColor(100, 150, 255))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(rect)

        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)

        x = 0
        while x <= self.width():
            painter.drawLine(x, 0, x, self.height())
            x += CELL_SIZE

        y = 0
        while y <= self.height():
            painter.drawLine(0, y, self.width(), y)
            y += CELL_SIZE


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GridWidget()
    window.show()
    sys.exit(app.exec_())
