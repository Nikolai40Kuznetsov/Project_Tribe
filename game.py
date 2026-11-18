import sys
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QTabWidget,
                             QVBoxLayout, QHBoxLayout, QScrollArea,
                             QPushButton, QMenu, QAction)
from PyQt5.QtCore import Qt, QRect, QPointF, QPoint
from PyQt5.QtGui import (QPainter, QColor, QPen, QFont, QPolygonF, QPixmap)

# --- Константы ---
CELL_SIZE = 125
COLS, ROWS = 14, 7
FIELD_W, FIELD_H = COLS * CELL_SIZE, ROWS * CELL_SIZE


# --- Данные технологий ---
TECHS = [
    {"name": "Собирательство",   "req": [], "researched": True, "cost": 0},
    {"name": "Поддержание огня", "req": ["Собирательство"], "cost": 20},
    {"name": "Грубые каменные инструменты", "req": ["Собирательство"], "cost": 15},
    {"name": "Охота", "req": ["Грубые каменные инструменты"], "cost": 25},
    {"name": "Добыча огня", "req": ["Поддержание огня"], "cost": 12},
]


# --- Раскладки рек ---
RIVER_LAYOUTS = {
    "междуречье": [
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6),
        (9, 0), (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6),
    ],
    "развилка": [
        (0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3),
        (7, 2), (7, 3), (7, 4), (8, 2), (8, 4), (9, 1),
        (9, 2), (9, 4), (9, 5), (10, 1), (10, 5), (11, 0),
        (11, 1), (11, 5), (11, 6), (12, 0), (12, 6), (13, 0), (13, 6),
    ],
    "остров": [
        (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 1), (4, 5),
        (5, 1), (5, 5), (6, 1), (6, 5), (7, 1), (7, 5),
        (8, 1), (8, 5), (9, 1), (9, 5),
        (10, 1), (10, 2), (10, 3), (10, 4), (10, 5),
    ],
    "хуанхэ": [
        (0, 5), (0, 6), (1, 4), (1, 5), (1, 6), (2, 4), (2, 5),
        (3, 3), (3, 4), (3, 5), (4, 3),
        (4, 4), (5, 2), (5, 3), (5, 4), (6, 2), (6, 3),
        (7, 1), (7, 2), (7, 3), (8, 1), (8, 2),
        (9, 0), (9, 1), (9, 2), (10, 0), (10, 1),
        (11, 0), (11, 1), (12, 0), (13, 0),
    ],
}


class TechTreeWidget(QWidget):
    """Дерево технологий (осталось без изменений)."""
    # ... (код TechTreeWidget оставлен без изменений, чтобы не раздувать ответ)
    NODE_W, NODE_H = 306, 85
    LEVEL_GAP_X = 140
    NODE_GAP_Y = 35
    MARGIN = 32
    COLORS = {
        "researched": QColor(24, 90, 32), "available": QColor(90, 90, 90), "locked": QColor(100, 28, 24),
    }
    BORDER = {
        "researched": QColor(57, 255, 20), "available": QColor(189, 195, 199), "locked": QColor(255, 65, 54),
    }
    TEXT = QColor(240, 240, 240)
    COST = QColor(240, 220, 140)
    BG = QColor(18, 18, 22)
    LINE = QColor(0, 229, 255)
    LINE_GLOW = QColor(0, 229, 255, 70)
    GAP_FROM_PARENT = 14
    GAP_BEFORE_CHILD = 20

    def __init__(self):
        super().__init__()
        self.techs = [{"name": t["name"], "req": list(t["req"]), "researched": t.get("researched", False),
                       "cost": t.get("cost", 0)} for t in TECHS]
        self.statuses = {}
        self.node_rects = {}
        self.update_state()
        self.compute_layout()
        self.setMinimumSize(self.min_width, self.min_height)

    def sizeHint(self): return self.minimumSize()
    def minimumSizeHint(self): return self.minimumSize()

    def tech_by_name(self, name):
        return next(t for t in self.techs if t["name"] == name)

    def update_state(self):
        self.statuses = {}
        for t in self.techs:
            if t["researched"]:
                self.statuses[t["name"]] = "researched"
            elif all(self.tech_by_name(r)["researched"] for r in t["req"]):
                self.statuses[t["name"]] = "available"
            else:
                self.statuses[t["name"]] = "locked"

    def compute_layout(self):
        memo = {}
        def level_of(name):
            if name in memo: return memo[name]
            reqs = self.tech_by_name(name)["req"]
            memo[name] = 1 + max((level_of(r) for r in reqs), default=-1)
            return memo[name]

        levels = {t["name"]: level_of(t["name"]) for t in self.techs}
        max_level = max(levels.values()) if levels else 0
        by_level = {}
        for t in self.techs: by_level.setdefault(levels[t["name"]], []).append(t["name"])

        self.min_width = (self.MARGIN * 2 + (max_level + 1) * self.NODE_W + max_level * self.LEVEL_GAP_X)
        max_rows = max(len(v) for v in by_level.values()) if by_level else 1
        self.min_height = (self.MARGIN * 2 + 40 + max_rows * self.NODE_H + (max_rows - 1) * self.NODE_GAP_Y)

        self.node_rects = {}
        for lvl, names in by_level.items():
            total_h = len(names) * self.NODE_H + (len(names) - 1) * self.NODE_GAP_Y
            start_y = self.MARGIN + 40 + max(0, (self.min_height - 80 - total_h) // 2)
            x = self.MARGIN + lvl * (self.NODE_W + self.LEVEL_GAP_X)
            for idx, name in enumerate(names):
                y = start_y + idx * (self.NODE_H + self.NODE_GAP_Y)
                self.node_rects[name] = QRect(x, y, self.NODE_W, self.NODE_H)

        for lvl in range(1, max_level + 1):
            for name in by_level.get(lvl, []):
                parents = self.tech_by_name(name)["req"]
                if not parents: continue
                parent_ys = [self.node_rects[p].center().y() for p in parents]
                target_y = sum(parent_ys) // len(parent_ys)
                current_y = self.node_rects[name].top()
                delta = target_y - (current_y + self.NODE_H // 2)
                self.node_rects[name].translate(0, delta)
                names_in_lvl = by_level[lvl]
                idx = names_in_lvl.index(name)
                if idx > 0:
                    prev_node = names_in_lvl[idx - 1]
                    prev_bottom = self.node_rects[prev_node].bottom()
                    if self.node_rects[name].top() < prev_bottom + 10:
                        self.node_rects[name].moveTop(prev_bottom + 10)
                if self.node_rects[name].bottom() > self.min_height - self.MARGIN:
                    self.min_height = self.node_rects[name].bottom() + self.MARGIN

    def node_at(self, pos):
        for name, rect in self.node_rects.items():
            if rect.contains(pos): return name
        return None

    def mousePressEvent(self, event):
        name = self.node_at(event.pos())
        if not name: return
        tech = self.tech_by_name(name)
        if self.statuses[name] == "available":
            tech["researched"] = True
            self.update_state()
            self.update()
        elif self.statuses[name] == "locked":
            missing = [r for r in tech["req"] if not self.tech_by_name(r)["researched"]]
            self.setToolTip("Сначала исследуйте: " + ", ".join(missing))

    def mouseMoveEvent(self, event): pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), self.BG)
        self._draw_connections(painter)
        self._draw_nodes(painter)
        self._draw_legend(painter)

    def _draw_connection_group(self, painter, parents_pts, entry_pt):
        if not parents_pts: return
        max_parent_x = max(x for x, _ in parents_pts)
        entry_x, entry_y = entry_pt
        bus_min_x = max_parent_x + self.GAP_FROM_PARENT
        bus_max_x = entry_x - self.GAP_BEFORE_CHILD
        bus_x = (bus_min_x + bus_max_x) // 2 if bus_min_x < bus_max_x else (max_parent_x + entry_x) // 2
        all_y = [y for _, y in parents_pts] + [entry_y]
        top_y, bot_y = min(all_y), max(all_y)
        for (px, py) in parents_pts:
            if abs(px - bus_x) >= 2: painter.drawLine(px, py, bus_x, py)
        if abs(bot_y - top_y) > 1: painter.drawLine(bus_x, top_y, bus_x, bot_y)
        painter.drawLine(bus_x, entry_y, entry_x, entry_y)
        self._draw_arrow_head(painter, entry_x, entry_y, size=6)

    def _draw_arrow_head(self, painter, tip_x, tip_y, size=6):
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.LINE)
        p1 = QPointF(tip_x, tip_y)
        p2 = QPointF(tip_x - size, tip_y - size * 0.75)
        p3 = QPointF(tip_x - size, tip_y + size * 0.75)
        painter.drawPolygon(QPolygonF([p1, p2, p3]))

    def _draw_connections(self, painter):
        glow_pen = QPen(self.LINE_GLOW)
        glow_pen.setWidth(6)
        glow_pen.setCapStyle(Qt.RoundCap)
        main_pen = QPen(self.LINE)
        main_pen.setWidth(2)
        main_pen.setCapStyle(Qt.RoundCap)
        main_pen.setJoinStyle(Qt.MiterJoin)
        groups = []
        for t in self.techs:
            if not t["req"]: continue
            child_rect = self.node_rects[t["name"]]
            entry_pt = (child_rect.left() - self.GAP_BEFORE_CHILD, child_rect.center().y())
            parents_pts = []
            for r in t["req"]:
                pr = self.node_rects[r]
                parents_pts.append((pr.right() + 4, pr.center().y()))
            groups.append((parents_pts, entry_pt))
        painter.setPen(glow_pen)
        for parents_pts, entry_pt in groups: self._draw_connection_group_no_arrow(painter, parents_pts, entry_pt)
        painter.setPen(main_pen)
        for parents_pts, entry_pt in groups: self._draw_connection_group(painter, parents_pts, entry_pt)

    def _draw_connection_group_no_arrow(self, painter, parents_pts, entry_pt):
        if not parents_pts: return
        max_parent_x = max(x for x, _ in parents_pts)
        entry_x, entry_y = entry_pt
        bus_min_x = max_parent_x + self.GAP_FROM_PARENT
        bus_max_x = entry_x - self.GAP_BEFORE_CHILD
        bus_x = (bus_min_x + bus_max_x) // 2 if bus_min_x < bus_max_x else (max_parent_x + entry_x) // 2
        all_y = [y for _, y in parents_pts] + [entry_y]
        top_y, bot_y = min(all_y), max(all_y)
        for (px, py) in parents_pts:
            if abs(px - bus_x) >= 2: painter.drawLine(px, py, bus_x, py)
        if abs(bot_y - top_y) > 1: painter.drawLine(bus_x, top_y, bus_x, bot_y)
        painter.drawLine(bus_x, entry_y, entry_x, entry_y)

    def _draw_nodes(self, painter):
        title_font = QFont("Arial", 11); title_font.setBold(True)
        cost_font = QFont("Arial", 10); cost_font.setBold(True)
        for t in self.techs:
            rect = self.node_rects[t["name"]]
            status = self.statuses[t["name"]]
            painter.setPen(QPen(self.BORDER[status], 3))
            painter.setBrush(self.COLORS[status])
            painter.drawRoundedRect(rect, 5, 5)
            header = QRect(rect.left(), rect.top(), rect.width(), 38)
            painter.setPen(Qt.NoPen); painter.setBrush(QColor(0, 0, 0, 80))
            painter.drawRect(header)
            painter.setPen(self.TEXT); painter.setFont(title_font)
            painter.drawText(header.adjusted(12, 0, -12, 0), Qt.AlignVCenter | Qt.AlignLeft, t["name"])
            painter.setFont(cost_font)
            painter.setPen(self.COST if status != "locked" else QColor(220, 170, 160))
            painter.drawText(header.adjusted(12, 0, -12, 0), Qt.AlignVCenter | Qt.AlignRight, f'{t.get("cost", 0)}')
            if status == "locked":
                missing = [r for r in t["req"] if not self.tech_by_name(r)["researched"]]
                if missing:
                    painter.setFont(QFont("Arial", 8)); painter.setPen(QColor(255, 210, 200))
                    painter.drawText(QRect(rect.left() + 12, rect.bottom() - 24, rect.width() - 24, 20),
                                     Qt.AlignLeft | Qt.AlignVCenter, "нужно: " + ", ".join(missing))

    def _draw_legend(self, painter):
        legend_y = 8; x = self.MARGIN
        painter.setFont(QFont("Arial", 9))
        for status, label in [("researched", "исследовано"), ("available", "доступно"), ("locked", "заблокировано")]:
            painter.setPen(Qt.NoPen); painter.setBrush(self.COLORS[status])
            swatch = QRect(x, legend_y, 16, 16); painter.drawRect(swatch)
            painter.setPen(Qt.white); painter.drawText(swatch.right() + 8, legend_y + 14, label)
            x = swatch.right() + 8 + painter.fontMetrics().horizontalAdvance(label) + 30


class GridWidget(QWidget):
    """Игровое поле с сеткой, рекой, людьми и ресурсами."""
    def __init__(self, on_update_ui=None):
        super().__init__()
        self.setFixedSize(FIELD_W, FIELD_H)
        self.on_update_ui = on_update_ui
        
        # Состояние мира
        self.tiles = [[{"col": c, "row": r, "is_river": False} for c in range(COLS)] for r in range(ROWS)]
        self.humans_pos = (0, 0)
        self.humans_count = 0
        self.humans_target = None
        
        # Ресурсы (кусты)
        self.bushes = set() # набор координат (col, row)
        
        # Действия на текущий ход
        self.pending_harvest = None
        self.resources = {"berries": 0}
        
        # Состояния UI
        self.moving_mode = False
        
        # Загрузка картинок
        self.human_pixmap = QPixmap("human.png")
        self.has_human_img = not self.human_pixmap.isNull()
        
        self.bush_pixmap = QPixmap("berries.png")
        self.has_bush_img = not self.bush_pixmap.isNull()

    def set_river(self, cells):
        for r in range(ROWS):
            for c in range(COLS):
                self.tiles[r][c]["is_river"] = False
        for col, row in cells:
            if 0 <= col < COLS and 0 <= row < ROWS:
                self.tiles[row][col]["is_river"] = True

        # Сброс и спавн
        self.humans_pos = (0, 0)
        self.humans_count = 0
        self.bushes.clear()
        self.resources = {"berries": 0}
        self.spawn_entities()
        self.update()

    def spawn_entities(self):
        # Спавн людей
        land_tiles = [(c, r) for r in range(ROWS) for c in range(COLS) if not self.tiles[r][c]["is_river"]]
        if land_tiles:
            self.humans_pos = random.choice(land_tiles)
            self.humans_count = random.randint(10, 15)
            
        # Спавн 10 кустов
        empty_land = [t for t in land_tiles if t != self.humans_pos]
        num_bushes = min(10, len(empty_land))
        self.bushes = set(random.sample(empty_land, num_bushes))

    def cell_at(self, pos: QPoint):
        c = pos.x() // CELL_SIZE
        r = pos.y() // CELL_SIZE
        if 0 <= c < COLS and 0 <= r < ROWS:
            return (c, r)
        return None

    def is_adjacent_to_humans(self, c, r):
        hc, hr = self.humans_pos
        return abs(hc - c) <= 1 and abs(hr - r) <= 1

    # --- Логика ходов ---
    def next_turn(self):
        # 1. Перемещение
        if self.humans_target:
            hc, hr = self.humans_pos
            tc, tr = self.humans_target
            
            if (hc, hr) != (tc, tr):
                # Шаг по направлению
                dx = 0 if tc == hc else (1 if tc > hc else -1)
                dy = 0 if tr == hr else (1 if tr > hr else -1)
                
                nc, nr = hc + dx, hr + dy
                
                # Проверка на воду
                if not self.tiles[nr][nc]["is_river"]:
                    self.humans_pos = (nc, nr)
                else:
                    # Если в воду, стоим на месте (или можно искать обход, но пока просто стоп)
                    self.humans_target = None
            
            # Если достигли цели
            if self.humans_pos == self.humans_target:
                self.humans_target = None
                
        # 2. Сбор
        if self.pending_harvest:
            if self.pending_harvest in self.bushes:
                self.bushes.remove(self.pending_harvest)
                self.resources["berries"] += 1
            self.pending_harvest = None
            
        if self.on_update_ui:
            self.on_update_ui()
        self.update()

    # --- Управление мышью ---
    def mousePressEvent(self, event):
        cell = self.cell_at(event.pos())
        if not cell:
            return
            
        c, r = cell

        if event.button() == Qt.LeftButton:
            if self.moving_mode:
                self.humans_target = (c, r)
                self.moving_mode = False
                self.update()
            elif self.pending_harvest:
                self.pending_harvest = None
                self.update()
                
        elif event.button() == Qt.RightButton:
            # ПКМ по людям
            if cell == self.humans_pos:
                menu = QMenu(self)
                move_action = QAction("Идти в точку", self)
                move_action.triggered.connect(self.start_move_mode)
                menu.addAction(move_action)
                menu.exec_(event.globalPos())
                return
                
            # ПКМ по кусту
            if cell in self.bushes:
                if self.is_adjacent_to_humans(c, r):
                    menu = QMenu(self)
                    harvest_action = QAction("Собирать", self)
                    harvest_action.triggered.connect(lambda: self.queue_harvest(c, r))
                    menu.addAction(harvest_action)
                    menu.exec_(event.globalPos())
                else:
                    menu = QMenu(self)
                    menu.addAction("Слишком далеко").setEnabled(False)
                    menu.exec_(event.globalPos())

    def start_move_mode(self):
        self.moving_mode = True
        self.setCursor(Qt.CrossCursor)

    def mouseMoveEvent(self, event):
        if self.moving_mode:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def queue_harvest(self, c, r):
        self.pending_harvest = (c, r)
        self.update()

    # --- Отрисовка ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Тайлы
        for r in range(ROWS):
            for c in range(COLS):
                rect = QRect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if self.tiles[r][c]["is_river"]:
                    painter.setBrush(QColor(43, 171, 197))
                else:
                    painter.setBrush(QColor(23, 124, 19))
                painter.setPen(Qt.NoPen)
                painter.drawRect(rect)

        # Сетка
        pen = QPen(Qt.black); pen.setWidth(1); painter.setPen(pen)
        for x in range(0, self.width() + 1, CELL_SIZE): painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height() + 1, CELL_SIZE): painter.drawLine(0, y, self.width(), y)

        # Кусты
        for (bc, br) in self.bushes:
            cell_rect = QRect(bc * CELL_SIZE, br * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            img_size = int(CELL_SIZE * 0.75)
            img_x = cell_rect.left() + (CELL_SIZE - img_size) // 2
            img_y = cell_rect.top() + (CELL_SIZE - img_size) // 2
            img_rect = QRect(img_x, img_y, img_size, img_size)
            
            if self.has_bush_img:
                painter.drawPixmap(img_rect, self.bush_pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(34, 139, 34))
                painter.drawEllipse(img_rect)

        # Люди
        if self.humans_count > 0:
            hc, hr = self.humans_pos
            cell_rect = QRect(hc * CELL_SIZE, hr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            
            img_size = int(CELL_SIZE * 0.75)
            img_x = cell_rect.left() + (CELL_SIZE - img_size) // 2
            img_y = cell_rect.top() + (CELL_SIZE - img_size) // 2 - 10
            img_rect = QRect(img_x, img_y, img_size, img_size)
            
            if self.has_human_img:
                painter.drawPixmap(img_rect, self.human_pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(200, 150, 100))
                painter.drawEllipse(img_rect)

            # Подпись
            font = QFont("Arial", 12); font.setBold(True); painter.setFont(font)
            text_rect = QRect(hc * CELL_SIZE, hr * CELL_SIZE + CELL_SIZE - 30, CELL_SIZE, 30)
            painter.setPen(Qt.NoPen); painter.setBrush(QColor(0, 0, 0, 150))
            painter.drawRoundedRect(text_rect.adjusted(10, 2, -10, -2), 4, 4)
            painter.setPen(QColor(255, 255, 255)); painter.drawText(text_rect, Qt.AlignCenter, str(self.humans_count))

        # Отрисовка индикаторов действий (выбора)
        if self.humans_target:
            tc, tr = self.humans_target
            target_rect = QRect(tc * CELL_SIZE, tr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            painter.setPen(QPen(QColor(255, 255, 0), 3, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(target_rect.adjusted(2, 2, -2, -2))
            
        if self.pending_harvest:
            pc, pr = self.pending_harvest
            target_rect = QRect(pc * CELL_SIZE, pr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            painter.setPen(QPen(QColor(255, 165, 0), 3, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(target_rect.adjusted(2, 2, -2, -2))


class ResourcesWidget(QWidget):
    """Вкладка с ресурсами."""
    def __init__(self, grid_widget):
        super().__init__()
        self.grid = grid_widget
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        
        # Стилизация
        self.setStyleSheet("background-color: #121216; color: #eee;")
        
        title = QLabel("Ресурсы племени")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #fff; padding: 10px;")
        self.layout.addWidget(title)
        
        self.berry_label = QLabel()
        self.berry_label.setFont(QFont("Arial", 14))
        self.berry_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.berry_label)
        
        self.update_ui()
        
    def update_ui(self):
        self.berry_label.setText(f"🍒 Ягоды: {self.grid.resources['berries']}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Игра")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Верхняя часть: вкладки
        self.tabs = QTabWidget()
        
        # -- Вкладка Мир --
        world_page = QWidget()
        world_layout = QVBoxLayout(world_page)
        world_layout.setContentsMargins(0, 0, 0, 0)
        
        # Создаем GridWidget с коллбэком на обновление UI
        self.world_tab = GridWidget(on_update_ui=self.on_update_ui)
        world_layout.addWidget(self.world_tab)
        
        # Добавляем кнопку внизу вкладки "Мир"
        btn_layout = QHBoxLayout()
        self.btn_next_turn = QPushButton("Следующий ход")
        self.btn_next_turn.setStyleSheet("""
            QPushButton {
                background-color: #2C3E50; color: white; 
                font-size: 16px; padding: 10px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #34495E; }
            QPushButton:pressed { background-color: #1A252F; }
        """)
        self.btn_next_turn.clicked.connect(self.world_tab.next_turn)
        btn_layout.addWidget(self.btn_next_turn)
        
        world_layout.addLayout(btn_layout)
        self.tabs.addTab(world_page, "Мир")

        # -- Вкладка Технологии --
        tech_page = QWidget()
        tech_page.setStyleSheet("background-color: #121216;")
        tech_layout = QVBoxLayout(tech_page)
        title_label = QLabel("Клик по доступной технологии исследует её.")
        title_label.setStyleSheet("color: #ddd;")
        tech_layout.addWidget(title_label)
        self.tech_tree = TechTreeWidget()
        scroll = QScrollArea()
        scroll.setWidget(self.tech_tree)
        scroll.setWidgetResizable(True)
        scroll.viewport().setStyleSheet("background-color: #121216;")
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #121216; }")
        tech_layout.addWidget(scroll)
        self.tabs.addTab(tech_page, "Технологии")
        
        # -- Вкладка Ресурсы --
        self.resources_tab = ResourcesWidget(self.world_tab)
        self.tabs.addTab(self.resources_tab, "Ресурсы")

        main_layout.addWidget(self.tabs)
        self.resize(FIELD_W + 200, FIELD_H + 150)

        # Инициализация
        self.init_game()

    def init_game(self):
        layout_name, layout_cells = random.choice(list(RIVER_LAYOUTS.items()))
        self.world_tab.set_river(layout_cells)
        self.setWindowTitle(f"Игра — река: {layout_name}")
        self.on_update_ui()

    def on_update_ui(self):
        # Обновляем ресурсы и любые другие виджеты
        self.resources_tab.update_ui()
        self.world_tab.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())