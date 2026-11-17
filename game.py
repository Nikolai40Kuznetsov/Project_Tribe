import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QSpinBox, QLineEdit
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRect

CELL_SIZE = 125
COLS = 14
ROWS = 7
FIELD_W = CELL_SIZE * COLS
FIELD_H = CELL_SIZE * ROWS


class GridWidget(QWidget):
    """Игровое поле с сеткой и рекой."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(FIELD_W, FIELD_H)

        self.tiles = [[{"col": c, "row": r, "is_river": False} for c in range(COLS)] for r in range(ROWS)]

    def create_label(window, text, font, width, height, x, y):
        lbl = QLabel(window)
        lbl.setText(text)
        lbl.setFont(font)
        lbl.resize(width, height)
        lbl.move(x, y)
        lbl.show()
        return lbl

    def create_button(window, text, font, width, height, x, y, function):
        btn = QPushButton(window)
        btn.setText(text)
        btn.setFont(font)
        btn.resize(width, height)
        btn.move(x, y)
        btn.clicked.connect(function)
        btn.show()
        return btn

    def create_spinbox(window, font, width, height, x, y, range_bottom, range_top, value_start):
        spb = QSpinBox(window)
        spb.setFont(font)
        spb.move(x, y)
        spb.resize(width, height)
        spb.setRange(range_bottom, range_top)
        spb.setValue(value_start)
        spb.show()
        return spb

    def create_inputbox(window, placeholder_text, font, width, height, x, y):
        ipb = QLineEdit(window)
        ipb.setPlaceholderText(placeholder_text)
        ipb.setFont(font)
        ipb.move(x, y)
        ipb.resize(width, height)
        ipb.show()
        return ipb

    def set_river(self, cells):
        """Задаёт реку вручную: cells — список клеток (col, row).
        Всё, что было рекой раньше, очищается."""
        for r in range(ROWS):
            for c in range(COLS):
                self.tiles[r][c]["is_river"] = False

        for col, row in cells:
            if 0 <= col < COLS and 0 <= row < ROWS:
                self.tiles[row][col]["is_river"] = True
            else:
                print(f"Клетка ({col},{row}) вне поля — пропущена")

        self.update()

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
    grid = GridWidget()

    # Задать реку списком клеток — как захотите, так и изогнётся
    # локация "междуречье"
    # grid.set_river([(4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (9, 0), (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6)])
    # локация "развилка"
    # grid.set_river([(0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (7, 2), (7, 3), (7, 4), (8, 2), (8, 4), (9, 1), 
    #               (9, 2), (9, 4), (9, 5), (10, 1), (10, 5), (11, 0), (11, 1), (11, 5), (11, 6), (12, 0), (12, 6), (13, 0), (13, 6)])
    # локация "остров"
    # grid.set_river([(3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 1), (4, 5), (5, 1), (5, 5), (6, 1), (6, 5), (7, 1), (7, 5),
    #               (8, 1), (8, 5), (9, 1), (9, 5), (10, 1), (10, 2), (10, 3), (10, 4), (10, 5)])
    # локация "хуанхэ"
    # grid.set_river([(0, 5), (0, 6), (1, 4), (1, 5), (1, 6), (2, 4), (2, 5), (3, 3), (3, 4), (3, 5), (4, 3), 
    #                (4, 4), (5, 2), (5, 3), (5, 4), (6, 2), (6, 3), (7, 1), (7, 2), (7, 3), (8, 1), (8, 2), 
    #                (9, 0), (9, 1), (9, 2), (10, 0), (10, 1), (11, 0), (11, 1), (12, 0), (13, 0)])

    grid.show()
    sys.exit(app.exec_())
