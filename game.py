import sys
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QTabWidget,
                             QVBoxLayout, QHBoxLayout, QScrollArea,
                             QPushButton, QMenu, QAction, QDialog, QSlider,
                             QDialogButtonBox)
from PyQt5.QtCore import Qt, QRect, QPointF, QPoint
from PyQt5.QtGui import (QPainter, QColor, QPen, QFont, QPolygonF, QPixmap)

# --- Константы ---
CELL_SIZE = 125
COLS, ROWS = 14, 7
FIELD_W, FIELD_H = COLS * CELL_SIZE, ROWS * CELL_SIZE


# --- Данные технологий ---
TECHS = [
    {"name": "Собирательство", "req": [], "researched": True, "cost": 0},
    {"name": "Поддержание огня", "req": ["Собирательство"], "cost": 20, "pos": "top"},
    {"name": "Грубые каменные инструменты", "req": ["Собирательство"], "cost": 15, "pos": "bottom"},
    {"name": "Приготовление пищи", "req": ["Поддержание огня"], "cost": 5, "pos": "top"},
    {"name": "Добыча огня", "req": ["Поддержание огня"], "cost": 12, "pos": "middle"},
    {"name": "Обожжённые копья", "req": ["Поддержание огня"], "cost": 10, "pos": "bottom"},
    {"name": "Деревообработка", "req": ["Грубые каменные инструменты"], "cost": 12, "pos": "middle"},
    {"name": "Охота", "req": ["Грубые каменные инструменты"], "cost": 25, "pos": "bottom"},
    {"name": "Плоты", "req": ["Деревообработка"], "cost": 5, "pos": "top"},
    {"name": "Насаживание на палку", "req": ["Деревообработка"], "cost": 5, "pos": "middle"},
    {"name": "Примитивное строительство", "req": ["Деревообработка"], "cost": 5, "pos": "bottom"},
    {"name": "Каменные копья", "req": ["Насаживание на палку"], "cost": 5, "pos": "top"},
    {"name": "Метательное оружие", "req": ["Насаживание на палку"], "cost": 5, "pos": "bottom"},
]


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
    # ... (код без изменений, он большой, я его сохранил)
    NODE_W, NODE_H = 306, 85
    LEVEL_GAP_X = 140
    NODE_GAP_Y = 25
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
        self.techs = [{"name": t["name"], "req": list(t["req"]),
                       "researched": t.get("researched", False),
                       "cost": t.get("cost", 0),
                       "pos": t.get("pos", "middle"),
                       "progress": 0} for t in TECHS]
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
                if t["progress"] >= t["cost"]:
                    self.statuses[t["name"]] = "available"
                else:
                    self.statuses[t["name"]] = "locked"
            else:
                self.statuses[t["name"]] = "locked"

    def tick(self):
        changed = False
        for t in self.techs:
            if t["researched"]: continue
            if all(self.tech_by_name(r)["researched"] for r in t["req"]):
                if t["progress"] < t["cost"]:
                    t["progress"] += 1
                    changed = True
        if changed:
            self.update_state()
            self.update()

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
        for t in self.techs:
            by_level.setdefault(levels[t["name"]], []).append(t["name"])

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
                t = self.tech_by_name(name)
                parents = t["req"]
                if not parents: continue
                
                parent_ys = [self.node_rects[p].center().y() for p in parents]
                avg_parent_y = sum(parent_ys) // len(parent_ys)
                
                pos_offset = 0
                if t["pos"] == "top":
                    pos_offset = -self.NODE_H - 10
                elif t["pos"] == "bottom":
                    pos_offset = self.NODE_H + 10

                target_y = avg_parent_y + pos_offset
                current_y = self.node_rects[name].top()
                delta = target_y - (current_y + self.NODE_H // 2)
                self.node_rects[name].translate(0, delta)

        for lvl, names in by_level.items():
            for i in range(1, len(names)):
                prev_name = names[i - 1]
                curr_name = names[i]
                
                prev_bottom = self.node_rects[prev_name].bottom()
                curr_top = self.node_rects[curr_name].top()
                
                if curr_top < prev_bottom + self.NODE_GAP_Y:
                    shift_amount = (prev_bottom + self.NODE_GAP_Y) - curr_top
                    self.node_rects[curr_name].translate(0, shift_amount)

        max_bottom = max(rect.bottom() for rect in self.node_rects.values())
        self.min_height = max_bottom + self.MARGIN

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
            if missing: self.setToolTip("Сначала исследуйте: " + ", ".join(missing))
            else: self.setToolTip(f"Идет изучение... {tech['progress']} / {tech['cost']}")

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
        glow_pen = QPen(self.LINE_GLOW); glow_pen.setWidth(6); glow_pen.setCapStyle(Qt.RoundCap)
        main_pen = QPen(self.LINE); main_pen.setWidth(2); main_pen.setCapStyle(Qt.RoundCap); main_pen.setJoinStyle(Qt.MiterJoin)
        
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
            
            cost_text = f"{t['cost']}"
            if not t["researched"] and t["cost"] > 0:
                cost_text = f"{t['progress']} / {t['cost']}"
                
            painter.setFont(cost_font)
            painter.setPen(self.COST if status != "locked" else QColor(220, 170, 160))
            painter.drawText(header.adjusted(12, 0, -12, 0), Qt.AlignVCenter | Qt.AlignRight, cost_text)
            
            if status == "locked":
                missing = [r for r in t["req"] if not self.tech_by_name(r)["researched"]]
                if missing:
                    painter.setFont(QFont("Arial", 8)); painter.setPen(QColor(255, 210, 200))
                    painter.drawText(QRect(rect.left() + 12, rect.bottom() - 24, rect.width() - 24, 20),
                                     Qt.AlignLeft | Qt.AlignVCenter, "нужно: " + ", ".join(missing))
                elif t["progress"] < t["cost"]:
                    painter.setFont(QFont("Arial", 8)); painter.setPen(QColor(180, 220, 180))
                    painter.drawText(QRect(rect.left() + 12, rect.bottom() - 24, rect.width() - 24, 20),
                                     Qt.AlignLeft | Qt.AlignVCenter, "изучается...")

    def _draw_legend(self, painter):
        legend_y = 8; x = self.MARGIN
        painter.setFont(QFont("Arial", 9))
        for status, label in [("researched", "исследовано"), ("available", "доступно"), ("locked", "недоступно")]:
            painter.setPen(Qt.NoPen); painter.setBrush(self.COLORS[status])
            swatch = QRect(x, legend_y, 16, 16); painter.drawRect(swatch)
            painter.setPen(Qt.white); painter.drawText(swatch.right() + 8, legend_y + 14, label)
            x = swatch.right() + 8 + painter.fontMetrics().horizontalAdvance(label) + 30


class SplitDialog(QDialog):
    def __init__(self, max_people, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Разделить племя")
        self.setFixedSize(300, 120)
        self.setStyleSheet("background-color: #2C3E50; color: white;")
        
        layout = QVBoxLayout(self)
        
        self.label = QLabel(f"Отделить людей (из {max_people}):")
        layout.addWidget(self.label)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(max_people - 1 if max_people > 1 else 1)
        self.slider.setValue(1)
        layout.addWidget(self.slider)
        
        self.value_label = QLabel("1")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        self.slider.valueChanged.connect(lambda v: self.value_label.setText(str(v)))
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_value(self):
        return self.slider.value()


class GridWidget(QWidget):
    def __init__(self, on_update_ui=None, on_tick=None, tech_tree=None):
        super().__init__()
        self.setFixedSize(FIELD_W, FIELD_H)
        self.on_update_ui = on_update_ui
        self.on_tick = on_tick
        self.tech_tree = tech_tree
        
        self.tiles = [[{"col": c, "row": r, "is_river": False} for c in range(COLS)] for r in range(ROWS)]
        
        self.groups = []
        self.humans_target = None
        self.bushes = set()
        self.trees = set()
        self.stones = set()
        self.pending_harvest = None
        self.resources = {"berries": 0, "wood": 0, "stone": 0, "chopper": 0}
        self.moving_mode = False
        
        self.split_mode = False
        self.split_target_group_idx = None
        self.split_count = 0
        
        self.human_pixmap = QPixmap("human.png")
        self.has_human_img = not self.human_pixmap.isNull()
        
        self.bush_pixmap = QPixmap("berries.png")
        self.has_bush_img = not self.bush_pixmap.isNull()

        self.tree_pixmap = QPixmap("tree.png")
        self.has_tree_img = not self.tree_pixmap.isNull()

        self.stone_pixmap = QPixmap("stone.png")
        self.has_stone_img = not self.stone_pixmap.isNull()

    def set_river(self, cells):
        for r in range(ROWS):
            for c in range(COLS): self.tiles[r][c]["is_river"] = False
        for col, row in cells:
            if 0 <= col < COLS and 0 <= row < ROWS: self.tiles[row][col]["is_river"] = True

        self.groups = []
        self.bushes.clear()
        self.trees.clear()
        self.stones.clear()
        self.resources = {"berries": 0, "wood": 0, "stone": 0, "chopper": 0}
        self.spawn_entities()
        self.update()

    def spawn_entities(self):
        land_tiles = [(c, r) for r in range(ROWS) for c in range(COLS) if not self.tiles[r][c]["is_river"]]
        if land_tiles:
            c, r = random.choice(land_tiles)
            self.groups = [{"pos": (c, r), "count": random.randint(10, 15)}]
            
        occupied = [g["pos"] for g in self.groups]
        
        # Кусты (10)
        empty_land = [t for t in land_tiles if t not in occupied]
        num_bushes = min(10, len(empty_land))
        self.bushes = set(random.sample(empty_land, num_bushes))
        
        # Деревья (5)
        empty_land_after_bushes = [t for t in empty_land if t not in self.bushes]
        num_trees = min(5, len(empty_land_after_bushes))
        self.trees = set(random.sample(empty_land_after_bushes, num_trees))

        # Камни (5)
        empty_land_after_trees = [t for t in empty_land_after_bushes if t not in self.trees]
        num_stones = min(5, len(empty_land_after_trees))
        self.stones = set(random.sample(empty_land_after_trees, num_stones))

    def cell_at(self, pos: QPoint):
        c = pos.x() // CELL_SIZE
        r = pos.y() // CELL_SIZE
        if 0 <= c < COLS and 0 <= r < ROWS: return (c, r)
        return None

    def get_group_at(self, c, r):
        for i, g in enumerate(self.groups):
            if g["pos"] == (c, r):
                return i
        return None

    def is_adjacent_to_group(self, c, r, group_pos):
        hc, hr = group_pos
        return abs(hc - c) <= 1 and abs(hr - r) <= 1

    def next_turn(self):
        for g in self.groups:
            if "target" in g and g["target"]:
                hc, hr = g["pos"]
                tc, tr = g["target"]
                if (hc, hr) != (tc, tr):
                    dx = 0 if tc == hc else (1 if tc > hc else -1)
                    dy = 0 if tr == hr else (1 if tr > hr else -1)
                    nc, nr = hc + dx, hr + dy
                    if not self.tiles[nr][nc]["is_river"] and self.get_group_at(nc, nr) is None:
                        g["pos"] = (nc, nr)
                    else:
                        g["target"] = None
                if g["pos"] == g["target"]:
                    g["target"] = None
                    
        if self.pending_harvest:
            if self.pending_harvest in self.bushes:
                self.bushes.remove(self.pending_harvest)
                self.resources["berries"] += 10
            self.pending_harvest = None
            
        total_people = sum(g["count"] for g in self.groups)
        if total_people > 0:
            if self.resources["berries"] > 0:
                self.resources["berries"] -= 1
            else:
                if self.groups:
                    largest = max(self.groups, key=lambda x: x["count"])
                    largest["count"] -= 1
                    if largest["count"] <= 0:
                        self.groups.remove(largest)
                        
        if self.on_tick:
            self.on_tick()

        if self.on_update_ui: self.on_update_ui()
        self.update()

    def mousePressEvent(self, event):
        cell = self.cell_at(event.pos())
        if not cell: return
        c, r = cell

        if event.button() == Qt.LeftButton:
            if self.split_mode:
                if not self.tiles[r][c]["is_river"] and self.get_group_at(c, r) is None:
                    self.groups.append({"pos": (c, r), "count": self.split_count})
                    self.groups[self.split_target_group_idx]["count"] -= self.split_count
                    if self.groups[self.split_target_group_idx]["count"] <= 0:
                        self.groups.pop(self.split_target_group_idx)
                    self.split_mode = False
                    self.split_target_group_idx = None
                    self.split_count = 0
                    self.setCursor(Qt.ArrowCursor)
                    self.update()
            elif self.moving_mode:
                if hasattr(self, 'moving_group_idx'):
                    g = self.groups[self.moving_group_idx]
                    g["target"] = (c, r)
                    self.moving_mode = False
                    self.setCursor(Qt.ArrowCursor)
                    self.update()
            elif self.pending_harvest:
                self.pending_harvest = None
                self.update()
                
        elif event.button() == Qt.RightButton:
            group_idx = self.get_group_at(c, r)
            
            if group_idx is not None:
                menu = QMenu(self)
                g = self.groups[group_idx]
                
                move_action = QAction("Идти в точку", self)
                move_action.triggered.connect(lambda: self.start_move_mode_for(group_idx))
                menu.addAction(move_action)
                
                if g["count"] > 1:
                    split_action = QAction("Разделить", self)
                    split_action.triggered.connect(lambda: self.start_split_mode(group_idx))
                    menu.addAction(split_action)
                
                adjacent_idx = None
                for idx, other_g in enumerate(self.groups):
                    if idx == group_idx: continue
                    oc, orr = other_g["pos"]
                    if abs(oc - c) + abs(orr - r) == 1:
                        adjacent_idx = idx
                        break
                
                if adjacent_idx is not None:
                    unite_action = QAction("Объединить", self)
                    unite_action.triggered.connect(lambda: self.unite_groups(group_idx, adjacent_idx))
                    menu.addAction(unite_action)
                    
                menu.exec_(event.globalPos())
                return
                
            if cell in self.bushes:
                adjacent = any(self.is_adjacent_to_group(c, r, g["pos"]) for g in self.groups)
                if adjacent:
                    menu = QMenu(self)
                    harvest_action = QAction("Собирать", self)
                    harvest_action.triggered.connect(lambda: self.queue_harvest(c, r))
                    menu.addAction(harvest_action)
                    menu.exec_(event.globalPos())
                else:
                    menu = QMenu(self)
                    menu.addAction("Слишком далеко").setEnabled(False)
                    menu.exec_(event.globalPos())
                    
            elif cell in self.trees:
                adjacent = any(self.is_adjacent_to_group(c, r, g["pos"]) for g in self.groups)
                has_chopper = self.resources.get("chopper", 0) > 0
                
                if adjacent and has_chopper:
                    menu = QMenu(self)
                    chop_action = QAction("Срубить", self)
                    chop_action.triggered.connect(lambda: self.queue_chop(c, r))
                    menu.addAction(chop_action)
                    menu.exec_(event.globalPos())
                elif not adjacent:
                    menu = QMenu(self)
                    menu.addAction("Слишком далеко").setEnabled(False)
                    menu.exec_(event.globalPos())
                else:
                    menu = QMenu(self)
                    menu.addAction("Нужно рубило").setEnabled(False)
                    menu.exec_(event.globalPos())

    def start_move_mode_for(self, group_idx):
        self.moving_group_idx = group_idx
        self.moving_mode = True
        self.setCursor(Qt.CrossCursor)

    def start_split_mode(self, group_idx):
        g = self.groups[group_idx]
        if g["count"] <= 1: return
        dialog = SplitDialog(g["count"], self)
        if dialog.exec_() == QDialog.Accepted:
            self.split_count = dialog.get_value()
            self.split_target_group_idx = group_idx
            self.split_mode = True
            self.setCursor(Qt.PointingHandCursor)

    def unite_groups(self, target_idx, source_idx):
        if target_idx == source_idx: return
        target_g = self.groups[target_idx]
        source_g = self.groups[source_idx]
        target_g["count"] += source_g["count"]
        self.groups.remove(source_g)
        self.update()

    def mouseMoveEvent(self, event):
        if self.moving_mode or self.split_mode:
            self.setCursor(Qt.CrossCursor if self.moving_mode else Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def queue_harvest(self, c, r):
        self.pending_harvest = (c, r)
        self.update()

    def queue_chop(self, c, r):
        if (c, r) in self.trees:
            self.trees.remove((c, r))
            self.resources["wood"] += random.randint(4, 7)
            if self.on_update_ui: self.on_update_ui()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        for r in range(ROWS):
            for c in range(COLS):
                rect = QRect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                painter.setBrush(QColor(43, 171, 197) if self.tiles[r][c]["is_river"] else QColor(23, 124, 19))
                painter.setPen(Qt.NoPen); painter.drawRect(rect)

        pen = QPen(Qt.black); pen.setWidth(1); painter.setPen(pen)
        for x in range(0, self.width() + 1, CELL_SIZE): painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height() + 1, CELL_SIZE): painter.drawLine(0, y, self.width(), y)

        # Камни
        for (bc, br) in self.stones:
            cell_rect = QRect(bc * CELL_SIZE, br * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            img_size = int(CELL_SIZE * 0.75)
            img_x = cell_rect.left() + (CELL_SIZE - img_size) // 2
            img_y = cell_rect.top() + (CELL_SIZE - img_size) // 2
            img_rect = QRect(img_x, img_y, img_size, img_size)
            if self.has_stone_img: painter.drawPixmap(img_rect, self.stone_pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(150, 150, 150)); painter.drawEllipse(img_rect)

        # Деревья
        for (bc, br) in self.trees:
            cell_rect = QRect(bc * CELL_SIZE, br * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            img_size = int(CELL_SIZE * 0.9)
            img_x = cell_rect.left() + (CELL_SIZE - img_size) // 2
            img_y = cell_rect.top() + (CELL_SIZE - img_size) // 2
            img_rect = QRect(img_x, img_y, img_size, img_size)
            if self.has_tree_img: painter.drawPixmap(img_rect, self.tree_pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(34, 139, 34)); painter.drawEllipse(img_rect)

        # Кусты
        for (bc, br) in self.bushes:
            cell_rect = QRect(bc * CELL_SIZE, br * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            img_size = int(CELL_SIZE * 0.75)
            img_x = cell_rect.left() + (CELL_SIZE - img_size) // 2
            img_y = cell_rect.top() + (CELL_SIZE - img_size) // 2
            img_rect = QRect(img_x, img_y, img_size, img_size)
            if self.has_bush_img: painter.drawPixmap(img_rect, self.bush_pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(200, 50, 50)); painter.drawEllipse(img_rect)

        # Люди
        font = QFont("Arial", 12); font.setBold(True); painter.setFont(font)
        for g in self.groups:
            if g["count"] <= 0: continue
            hc, hr = g["pos"]
            cell_rect = QRect(hc * CELL_SIZE, hr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            img_size = int(CELL_SIZE * 0.75)
            img_x = cell_rect.left() + (CELL_SIZE - img_size) // 2
            img_y = cell_rect.top() + (CELL_SIZE - img_size) // 2 - 10
            img_rect = QRect(img_x, img_y, img_size, img_size)
            
            if self.has_human_img: painter.drawPixmap(img_rect, self.human_pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(200, 150, 100)); painter.drawEllipse(img_rect)

            text_rect = QRect(hc * CELL_SIZE, hr * CELL_SIZE + CELL_SIZE - 30, CELL_SIZE, 30)
            painter.setPen(Qt.NoPen); painter.setBrush(QColor(0, 0, 0, 150))
            painter.drawRoundedRect(text_rect.adjusted(10, 2, -10, -2), 4, 4)
            painter.setPen(QColor(255, 255, 255)); painter.drawText(text_rect, Qt.AlignCenter, str(g["count"]))

        for g in self.groups:
            if "target" in g and g["target"]:
                tc, tr = g["target"]
                target_rect = QRect(tc * CELL_SIZE, tr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                painter.setPen(QPen(QColor(255, 255, 0), 3, Qt.DashLine)); painter.setBrush(Qt.NoBrush)
                painter.drawRect(target_rect.adjusted(2, 2, -2, -2))

        if self.pending_harvest:
            pc, pr = self.pending_harvest
            target_rect = QRect(pc * CELL_SIZE, pr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            painter.setPen(QPen(QColor(255, 165, 0), 3, Qt.DashLine)); painter.setBrush(Qt.NoBrush)
            painter.drawRect(target_rect.adjusted(2, 2, -2, -2))


class ResourcesWidget(QWidget):
    def __init__(self, grid_widget):
        super().__init__()
        self.grid = grid_widget
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.setStyleSheet("background-color: #121216; color: #eee;")
        
        title = QLabel("Ресурсы племени")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #fff; padding: 10px;")
        self.layout.addWidget(title)
        
        self.berry_label = QLabel(); self.berry_label.setFont(QFont("Arial", 14)); self.berry_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.berry_label)

        self.wood_label = QLabel(); self.wood_label.setFont(QFont("Arial", 14)); self.wood_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.wood_label)

        self.stone_label = QLabel(); self.stone_label.setFont(QFont("Arial", 14)); self.stone_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.stone_label)

        self.chopper_label = QLabel(); self.chopper_label.setFont(QFont("Arial", 14)); self.chopper_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.chopper_label)
        
        self.people_label = QLabel(); self.people_label.setFont(QFont("Arial", 14)); self.people_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.people_label)
        
        self.update_ui()
        
    def update_ui(self):
        self.berry_label.setText(f"🍒 Ягоды: {self.grid.resources['berries']}")
        self.wood_label.setText(f"🪵 Древесина: {self.grid.resources['wood']}")
        self.stone_label.setText(f"🪨 Камни: {self.grid.resources['stone']}")
        self.chopper_label.setText(f"🪓 Рубила: {self.grid.resources['chopper']}")
        total = sum(g["count"] for g in self.grid.groups)
        self.people_label.setText(f"👥 Люди: {total}")


class CraftingWidget(QWidget):
    def __init__(self, grid_widget):
        super().__init__()
        self.grid = grid_widget
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.setStyleSheet("background-color: #121216; color: #eee;")
        
        title = QLabel("Создание предметов")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #fff; padding: 10px;")
        self.layout.addWidget(title)
        
        self.btn_chop = QPushButton("Создать рубило (1 камень)")
        self.btn_chop.setStyleSheet("""
            QPushButton {
                background-color: #2C3E50; color: white; 
                font-size: 16px; padding: 10px; border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover { background-color: #34495E; }
            QPushButton:pressed { background-color: #1A252F; }
            QPushButton:disabled { background-color: #7F8C8D; color: #BDC3C7; }
        """)
        self.btn_chop.clicked.connect(self.craft_chopper)
        self.layout.addWidget(self.btn_chop)

        self.info_label = QLabel()
        self.info_label.setStyleSheet("padding: 10px; color: #bbb;")
        self.layout.addWidget(self.info_label)

        self.update_ui()

    def craft_chopper(self):
        # Проверка технологии
        has_tools = False
        if self.grid.tech_tree:
            tools_tech = self.grid.tech_tree.tech_by_name("Грубые каменные инструменты")
            if tools_tech and tools_tech["researched"]:
                has_tools = True
                
        if not has_tools:
            self.info_label.setText("Нужна технология 'Грубые каменные инструменты'")
            return
            
        if self.grid.resources["stone"] > 0:
            self.grid.resources["stone"] -= 1
            self.grid.resources["chopper"] += 1
            self.info_label.setText("Создано 1 рубило!")
            self.grid.on_update_ui()
        else:
            self.info_label.setText("Не хватает камней!")

    def update_ui(self):
        # Активность кнопки
        has_tools = False
        if self.grid.tech_tree:
            tools_tech = self.grid.tech_tree.tech_by_name("Грубые каменные инструменты")
            if tools_tech and tools_tech["researched"]:
                has_tools = True
                
        can_craft = has_tools and self.grid.resources["stone"] > 0
        self.btn_chop.setEnabled(can_craft)
        
        if not has_tools:
            self.btn_chop.setText("Создать рубило (нужна технология)")
        elif self.grid.resources["stone"] <= 0:
            self.btn_chop.setText("Создать рубило (нет камней)")
        else:
            self.btn_chop.setText("Создать рубило (1 камень)")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Игра")
        self.turn_count = 1

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        
        world_page = QWidget()
        world_layout = QVBoxLayout(world_page)
        world_layout.setContentsMargins(0, 0, 0, 0)
        
        info_layout = QHBoxLayout()
        self.turn_label = QLabel(f"Ход: {self.turn_count}")
        self.turn_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        info_layout.addWidget(self.turn_label)
        info_layout.addStretch()
        world_layout.addLayout(info_layout)
        
        self.tech_tree = TechTreeWidget()
        
        self.world_tab = GridWidget(on_update_ui=self.on_update_ui, on_tick=self.on_tick, tech_tree=self.tech_tree)
        world_layout.addWidget(self.world_tab)
        
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

        tech_page = QWidget()
        tech_page.setStyleSheet("background-color: #121216;")
        tech_layout = QVBoxLayout(tech_page)
        title_label = QLabel("Клик по доступной технологии исследует её (когда прогресс достигнет нужного значения).")
        title_label.setStyleSheet("color: #ddd;")
        tech_layout.addWidget(title_label)
        
        scroll = QScrollArea()
        scroll.setWidget(self.tech_tree)
        scroll.setWidgetResizable(True)
        scroll.viewport().setStyleSheet("background-color: #121216;")
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #121216; }")
        tech_layout.addWidget(scroll)
        self.tabs.addTab(tech_page, "Технологии")
        
        # -- Вкладка Создание --
        self.crafting_tab = CraftingWidget(self.world_tab)
        self.tabs.addTab(self.crafting_tab, "Создание")

        # -- Вкладка Ресурсы --
        self.resources_tab = ResourcesWidget(self.world_tab)
        self.tabs.addTab(self.resources_tab, "Ресурсы")

        main_layout.addWidget(self.tabs)
        self.resize(FIELD_W + 200, FIELD_H + 150)

        self.init_game()

    def init_game(self):
        layout_name, layout_cells = random.choice(list(RIVER_LAYOUTS.items()))
        self.world_tab.set_river(layout_cells)
        self.setWindowTitle(f"Игра — река: {layout_name}")
        self.on_update_ui()

    def on_tick(self):
        self.turn_count += 1
        self.turn_label.setText(f"Ход: {self.turn_count}")
        self.tech_tree.tick()
        self.crafting_tab.update_ui()
        
        # Рост кустов каждые 5 ходов
        if self.turn_count % 5 == 0 and len(self.world_tab.bushes) < 15:
            land_tiles = [(c, r) for r in range(ROWS) for c in range(COLS) 
                          if not self.world_tab.tiles[r][c]["is_river"] 
                          and (c, r) not in self.world_tab.bushes
                          and (c, r) not in self.world_tab.trees
                          and (c, r) not in self.world_tab.stones
                          and self.world_tab.get_group_at(c, r) is None]
            if land_tiles:
                new_bush = random.choice(land_tiles)
                self.world_tab.bushes.add(new_bush)
                
        # Рост деревьев каждые 20 ходов
        if self.turn_count % 20 == 0 and len(self.world_tab.trees) < 10:
            land_tiles = [(c, r) for r in range(ROWS) for c in range(COLS) 
                          if not self.world_tab.tiles[r][c]["is_river"] 
                          and (c, r) not in self.world_tab.bushes
                          and (c, r) not in self.world_tab.trees
                          and (c, r) not in self.world_tab.stones
                          and self.world_tab.get_group_at(c, r) is None]
            if land_tiles:
                new_tree = random.choice(land_tiles)
                self.world_tab.trees.add(new_tree)

    def on_update_ui(self):
        self.resources_tab.update_ui()
        if hasattr(self, 'crafting_tab'):
            self.crafting_tab.update_ui()
        self.world_tab.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())