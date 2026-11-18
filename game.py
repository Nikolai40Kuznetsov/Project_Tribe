import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QTabWidget,
                             QVBoxLayout, QHBoxLayout, QScrollArea)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QPen, QFont


CELL_SIZE = 125
COLS, ROWS = 14, 7
FIELD_W, FIELD_H = COLS * CELL_SIZE, ROWS * CELL_SIZE


# --------------------- Технологии ---------------------

# req — список технологий, которые нужно исследовать раньше.
TECHS = [
    {"name": "Собирательство",  "req": [], "researched": True},
    {"name": "Поддержание огня", "req": [], "researched": True},
    {"name": "Добыча огня",     "req": ["Собирательство", "Поддержание огня"]},
    {"name": "Ручное рубило",   "req": ["Собирательство"]},
    {"name": "Каменные топоры", "req": ["Ручное рубило"]},
    {"name": "Охота",           "req": ["Добыча огня", "Ручное рубило"]},
]


class TechTreeWidget(QWidget):
    """Дерево технологий: клик по доступной технологии исследует её."""
    NODE_W, NODE_H = 190, 40
    LEVEL_GAP_X = 90
    NODE_GAP_Y = 22
    MARGIN = 20

    COLORS = {
        "researched": QColor(23, 245, 10),
        "available":  QColor(167, 171, 174),
        "locked":     QColor(217, 42, 8),
    }
    STATUS_LABELS = {
        "researched": "исследовано",
        "available":  "можно исследовать",
        "locked":     "недоступно",
    }

    def __init__(self):
        super().__init__()
        self.techs = [{"name": t["name"], "req": list(t["req"]),
                       "researched": t.get("researched", False)} for t in TECHS]
        self.statuses = {}
        self.node_rects = {}
        self.update_state()
        self.compute_layout()
        self.setMouseTracking(True)
        self.setMinimumSize(self.min_width, self.min_height)

    def tech_by_name(self, name):
        return next(t for t in self.techs if t["name"] == name)

    def update_state(self):
        """Пересчитать статусы: researched / available / locked."""
        self.statuses = {}
        for t in self.techs:
            if t["researched"]:
                self.statuses[t["name"]] = "researched"
            elif all(self.tech_by_name(r)["researched"] for r in t["req"]):
                self.statuses[t["name"]] = "available"
            else:
                self.statuses[t["name"]] = "locked"

    def compute_layout(self):
        """Раскладка: уровень = 1 + макс. уровень предков; колонка слева направо."""
        memo = {}

        def level_of(name):
            if name in memo:
                return memo[name]
            reqs = self.tech_by_name(name)["req"]
            memo[name] = 1 + max((level_of(r) for r in reqs), default=-1)
            return memo[name]

        by_level = {}
        for t in self.techs:
            by_level.setdefault(level_of(t["name"]), []).append(t["name"])

        self.node_rects = {}
        max_level = max(by_level)
        self.min_width = (self.MARGIN + (max_level + 1) *
                          (self.NODE_W + self.LEVEL_GAP_X))
        self.min_height = self.MARGIN + len(self.techs) * (self.NODE_H + self.NODE_GAP_Y)

        for lvl, names in by_level.items():
            for idx, name in enumerate(names):
                x = self.MARGIN + lvl * (self.NODE_W + self.LEVEL_GAP_X)
                y = self.MARGIN + idx * (self.NODE_H + self.NODE_GAP_Y)
                self.node_rects[name] = QRect(x, y, self.NODE_W, self.NODE_H)

    def node_at(self, pos):
        for name, rect in self.node_rects.items():
            if rect.contains(pos):
                return name
        return None

    def mousePressEvent(self, event):
        name = self.node_at(event.pos())
        if not name:
            return
        tech = self.tech_by_name(name)
        if self.statuses[name] == "available":
            tech["researched"] = True
            self.update_state()
            self.update()
        elif self.statuses[name] == "locked":
            missing = [r for r in tech["req"] if not self.tech_by_name(r)["researched"]]
            self.setToolTip("Сначала исследуйте: " + ", ".join(missing))

    def mouseMoveEvent(self, event):
        name = self.node_at(event.pos())
        if name:
            tech = self.tech_by_name(name)
            status = self.STATUS_LABELS[self.statuses[name]]
            req_text = ", ".join(tech["req"]) if tech["req"] else "нет требований"
            self.setToolTip(f"{name}\nСтатус: {status}\nТребует: {req_text}")
        else:
            self.setToolTip("")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Стрелки от каждой зависимости к технологии
        pen = QPen(QColor(60, 60, 60))
        pen.setWidth(2)
        painter.setPen(pen)
        for t in self.techs:
            if not t["req"]:
                continue
            x1 = self.node_rects[t["name"]].left()
            y1 = self.node_rects[t["name"]].center().y()
            for req in t["req"]:
                x2 = self.node_rects[req].right()
                y2 = self.node_rects[req].center().y()
                painter.drawLine(x2, y2, x1 - 8, y1)
                # наконечник стрелки
                painter.drawLine(x1 - 8, y1, x1 - 3, y1 - 4)
                painter.drawLine(x1 - 8, y1, x1 - 3, y1 + 4)

        # Узлы
        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)
        for t in self.techs:
            rect = self.node_rects[t["name"]]
            status = self.statuses[t["name"]]

            painter.setPen(QPen(Qt.black, 2))
            painter.setBrush(self.COLORS[status])
            painter.drawRoundedRect(rect, 8, 8)

            painter.setPen(Qt.black)
            painter.drawText(rect.adjusted(6, 0, -6, 0),
                             Qt.AlignCenter, t["name"])

            if status == "locked":
                missing = [r for r in t["req"]
                           if not self.tech_by_name(r)["researched"]]
                if missing:
                    painter.setPen(QColor(90, 20, 20))
                    small = QFont()
                    small.setPointSize(8)
                    painter.setFont(small)
                    painter.drawText(QRect(rect.left(), rect.bottom() - 16,
                                           rect.width(), 16),
                                     Qt.AlignHCenter,
                                     "нужно: " + ", ".join(missing))
                    painter.setFont(font)

        # Легенда
        legend_y = 4
        x = self.MARGIN
        painter.setFont(QFont("Arial", 9))
        for status, label in [("researched", "исследовано"),
                              ("available", "доступно"),
                              ("locked", "заблокировано")]:
            painter.setPen(Qt.black)
            painter.setBrush(self.COLORS[status])
            swatch = QRect(x, legend_y, 12, 12)
            painter.drawRect(swatch)
            painter.drawText(swatch.right() + 5, legend_y + 11, label)
            x = swatch.right() + 5 + painter.fontMetrics().horizontalAdvance(label) + 20


class GridWidget(QWidget):
    """Игровое поле с сеткой и рекой."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(FIELD_W, FIELD_H)
        self.tiles = [[{"col": c, "row": r, "is_river": False}
                       for c in range(COLS)] for r in range(ROWS)]

    def set_river(self, cells):
        for r in range(ROWS):
            for c in range(COLS):
                self.tiles[r][c]["is_river"] = False
        for col, row in cells:
            if 0 <= col < COLS and 0 <= row < ROWS:
                self.tiles[row][col]["is_river"] = True
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        for r in range(ROWS):
            for c in range(COLS):
                rect = QRect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                painter.setBrush(QColor(43, 171, 197) if self.tiles[r][c]["is_river"]
                                 else QColor(23, 124, 19))
                painter.setPen(Qt.NoPen)
                painter.drawRect(rect)

        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        for x in range(0, self.width() + 1, CELL_SIZE):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height() + 1, CELL_SIZE):
            painter.drawLine(0, y, self.width(), y)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Игра")

        tabs = QTabWidget()
        tabs.addTab(GridWidget(), "Мир")

        tech_page = QWidget()
        tech_layout = QVBoxLayout(tech_page)
        tech_layout.addWidget(QLabel("Клик по доступной технологии исследует её."))
        self.tech_tree = TechTreeWidget()
        scroll = QScrollArea()
        scroll.setWidget(self.tech_tree)
        scroll.setWidgetResizable(False)
        tech_layout.addWidget(scroll)

        tabs.addTab(tech_page, "Технологии")

        outer = QVBoxLayout(self)
        outer.addWidget(tabs)
        self.setLayout(outer)
        self.resize(FIELD_W, FIELD_H + 40)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
