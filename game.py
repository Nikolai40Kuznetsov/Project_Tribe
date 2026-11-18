import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QSpinBox,
                             QLineEdit, QTabWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QListWidgetItem)
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
                    painter.setBrush(QColor(43, 171, 197))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(rect)
                else:
                    rect = QRect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    painter.setBrush(QColor(23, 124, 19))
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


class TechWidget(QWidget):
    """Вкладка «Технологии»: список технологий с их статусом."""
    def __init__(self):
        super().__init__()

        self.technologies = [
            {"name": "Собирательство", "researched": True},
            {"name": "Поддержание огня", "researched": True},
            {"name": "Добыча огня", "researched": False},
            {"name": "Ручное рубило", "researched": False},
            {"name": "Добыча огня", "researched": False},
            {"name": "Каменные топоры", "researched": False},
            {"name": "Охота", "researched": False},
        ]

        layout = QVBoxLayout(self)

        self.tech_list = QListWidget()
        for tech in self.technologies:
            status = "✓ исследовано" if tech["researched"] else "не исследовано"
            item = QListWidgetItem(f"{tech['name']} — {status}")
            self.tech_list.addItem(item)

        layout.addWidget(QLabel("Технологии:"))
        layout.addWidget(self.tech_list)


class MainWindow(QWidget):
    """Главное окно с вкладками."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Игра")

        tabs = QTabWidget()

        self.world_tab = GridWidget()
        self.tech_tab = TechWidget()

        tabs.addTab(self.world_tab, "Мир")
        tabs.addTab(self.tech_tab, "Технологии")

        outer = QVBoxLayout(self)
        outer.addWidget(tabs)
        self.setLayout(outer)

        self.resize(FIELD_W, FIELD_H + 40)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    # Задать реку списком клеток
    # локация "междуречье"
    # window.world_tab.set_river([(4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (9, 0), (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6)])
    # локация "развилка"
    # window.world_tab.set_river([(0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (7, 2), (7, 3), (7, 4), (8, 2), (8, 4), (9, 1),
    #               (9, 2), (9, 4), (9, 5), (10, 1), (10, 5), (11, 0), (11, 1), (11, 5), (11, 6), (12, 0), (12, 6), (13, 0), (13, 6)])
    # локация "остров"
    # window.world_tab.set_river([(3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 1), (4, 5), (5, 1), (5, 5), (6, 1), (6, 5), (7, 1), (7, 5),
    #               (8, 1), (8, 5), (9, 1), (9, 5), (10, 1), (10, 2), (10, 3), (10, 4), (10, 5)])
    # локация "хуанхэ"
    # window.world_tab.set_river([(0, 5), (0, 6), (1, 4), (1, 5), (1, 6), (2, 4), (2, 5), (3, 3), (3, 4), (3, 5), (4, 3),
    #                (4, 4), (5, 2), (5, 3), (5, 4), (6, 2), (6, 3), (7, 1), (7, 2), (7, 3), (8, 1), (8, 2),
    #                (9, 0), (9, 1), (9, 2), (10, 0), (10, 1), (11, 0), (11, 1), (12, 0), (13, 0)])

    window.show()
    sys.exit(app.exec_())
