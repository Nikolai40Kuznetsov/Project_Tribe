import sys
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QTabWidget,
                             QVBoxLayout, QHBoxLayout, QScrollArea,
                             QPushButton, QMenu, QAction, QDialog, QSlider,
                             QDialogButtonBox)
from PyQt5.QtCore import Qt, QRect, QPointF, QPoint
from PyQt5.QtGui import (QPainter, QColor, QPen, QFont, QPolygonF, QPixmap)

# --- Константы ---
CELL_SIZE = 100
COLS, ROWS = 18, 9
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
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8),
        (12, 0), (12, 1), (12, 2), (12, 3), (12, 4), (12, 5), (12, 6), (12, 7), (12, 8),
    ],
    "развилка": [
        (0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4),
        (9, 3), (9, 5), (10, 3), (10, 5), (11, 2), (11, 3), (11, 5), (11, 6), 
        (12, 2), (12, 6), (13, 1), (13, 2), (13, 6), (13, 7), (14, 1), (14, 7), 
        (15, 0), (15, 1), (15, 7), (15, 8), (16, 0), (16, 8), (17, 0), (17, 8)
    ],
    "остров": [
        (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), 
        (4, 2), (4, 6), (5, 2), (5, 6), (6, 2), (6, 6), (7, 2), (7, 6),
        (8, 2), (8, 6), (9, 2), (9, 6), (10, 2), (10, 6),
        (11, 2), (11, 6), (12, 2), (12, 6), (13, 2), (13, 6),
        (14, 2), (14, 3), (14, 4), (14, 5), (14, 6)
    ],
    "хуанхэ": [
        (0, 7), (0, 8),(1, 7), (1, 8), (2, 6), (2, 7), (2, 8), (3, 6), (3, 7),
        (4, 5), (4, 6), (4, 7), (5, 5), (5, 6), (6, 4), (6, 5), (6, 6), (7, 4), 
        (7, 5),(8, 3), (8, 4), (8, 5), (9, 3), (9, 4), (10, 2), (10, 3), (10, 4), 
        (11, 2), (11, 3), (12, 1), (12, 2), (12, 3), (13, 1), (13, 2), (14, 0), 
        (14, 1), (14, 2), (15, 0), (15, 1), (16, 0), (16, 1), (17, 0)
    ],
}


class TechTreeWidget(QWidget):
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
        self.burning_trees = []
        self.stones = set()
        self.rocks = set()
        self.campfires = []
        self.houses = set()
        self.pending_harvest = None
        self.resources = {"berries": 0, "wood": 0, "stone": 0, "chopper": 0, "sticks": 0, "pickaxe": 0, "burnt_spears": 0}
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

        self.tree_burning_pixmap = QPixmap("tree_burning.png")
        self.has_tree_burning_img = not self.tree_burning_pixmap.isNull()

        self.stone_pixmap = QPixmap("stone.png")
        self.has_stone_img = not self.stone_pixmap.isNull()
        
        self.campfire_pixmap = QPixmap("campfire.png")
        self.has_campfire_img = not self.campfire_pixmap.isNull()

        self.rock_pixmap = QPixmap("rock.png")
        self.has_rock_img = not self.rock_pixmap.isNull()

        self.house_pixmap = QPixmap("primitive_house.png")
        self.has_house_img = not self.house_pixmap.isNull()

        self.is_winter = False

    def set_river(self, cells):
        for r in range(ROWS):
            for c in range(COLS): self.tiles[r][c]["is_river"] = False
        for col, row in cells:
            if 0 <= col < COLS and 0 <= row < ROWS: self.tiles[row][col]["is_river"] = True

        self.groups = []
        self.bushes.clear()
        self.trees.clear()
        self.burning_trees.clear()
        self.stones.clear()
        self.rocks.clear()
        self.campfires.clear()
        self.houses.clear()
        self.resources = {"berries": 0, "wood": 0, "stone": 0, "chopper": 0, "sticks": 0, "pickaxe": 0, "burnt_spears": 0}
        self.spawn_entities()
        self.update()

    def spawn_entities(self):
        land_tiles = [(c, r) for r in range(ROWS) for c in range(COLS) if not self.tiles[r][c]["is_river"]]
        if land_tiles:
            c, r = random.choice(land_tiles)
            self.groups = [{"pos": (c, r), "count": random.randint(20, 30), "in_house": False}]
            
        occupied = [g["pos"] for g in self.groups]
        
        empty_land = [t for t in land_tiles if t not in occupied]
        
        num_bushes = min(20, len(empty_land))
        self.bushes = set(random.sample(empty_land, num_bushes))
        
        empty_land_after_bushes = [t for t in empty_land if t not in self.bushes]
        
        num_trees = min(10, len(empty_land_after_bushes))
        self.trees = set(random.sample(empty_land_after_bushes, num_trees))

        empty_land_after_trees = [t for t in empty_land_after_bushes if t not in self.trees]
        
        num_stones = min(10, len(empty_land_after_trees))
        self.stones = set(random.sample(empty_land_after_trees, num_stones))

        empty_land_after_stones = [t for t in empty_land_after_trees if t not in self.stones]
        
        num_rocks = min(5, len(empty_land_after_stones))
        self.rocks = set(random.sample(empty_land_after_stones, num_rocks))

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

    def is_near_fire(self, c, r):
        for cf in self.campfires:
            cc, cr = cf["pos"]
            if abs(cc - c) <= 1 and abs(cr - r) <= 1: return True
        for bt in self.burning_trees:
            bc, br = bt["pos"]
            if abs(bc - c) <= 1 and abs(br - r) <= 1: return True
        return False

    def next_turn(self):
        for g in self.groups:
            if g.get("in_house", False):
                continue # В доме не двигаются
            if "target" in g and g["target"]:
                hc, hr = g["pos"]
                tc, tr = g["target"]
                if (hc, hr) != (tc, tr):
                    dx = 0 if tc == hc else (1 if tc > hc else -1)
                    dy = 0 if tr == hr else (1 if tr > hr else -1)
                    nc, nr = hc + dx, hr + dy
                    can_walk = not self.tiles[nr][nc]["is_river"] or self.is_winter
                    if can_walk and self.get_group_at(nc, nr) is None:
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

        if self.is_winter:
            for g in list(self.groups):
                if g.get("in_house", False):
                    continue # В доме тепло
                if not self.is_near_fire(*g["pos"]):
                    g["count"] -= 1
                    if g["count"] <= 0:
                        self.groups.remove(g)
                        break

        for cf in list(self.campfires):
            cf["life"] -= 1
            if cf["life"] <= 0: self.campfires.remove(cf)
                
        for bt in list(self.burning_trees):
            bt["life"] -= 1
            if bt["life"] <= 0: self.burning_trees.remove(bt)

        if random.random() < 0.05 and self.trees:
            tree_pos = random.choice(list(self.trees))
            self.trees.remove(tree_pos)
            self.burning_trees.append({"pos": tree_pos, "life": 10})
                        
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
                    self.groups.append({"pos": (c, r), "count": self.split_count, "in_house": False})
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
                
                if g.get("in_house", False):
                    exit_action = QAction("Выйти из дома", self)
                    exit_action.triggered.connect(lambda: self.toggle_house(group_idx))
                    menu.addAction(exit_action)
                    menu.exec_(event.globalPos())
                    return
                    
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
                    
                # Вход в дом, если стоим на доме
                if cell in self.houses and not g.get("in_house", False):
                    enter_action = QAction("Войти в дом", self)
                    enter_action.triggered.connect(lambda: self.toggle_house(group_idx))
                    menu.addAction(enter_action)
                    
                menu.exec_(event.globalPos())
                return
                
            if cell in self.bushes:
                adjacent = any(self.is_adjacent_to_group(c, r, g["pos"]) and not g.get("in_house", False) for g in self.groups)
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
                adjacent = any(self.is_adjacent_to_group(c, r, g["pos"]) and not g.get("in_house", False) for g in self.groups)
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

            elif cell in self.stones:
                adjacent = any(self.is_adjacent_to_group(c, r, g["pos"]) and not g.get("in_house", False) for g in self.groups)
                if adjacent:
                    menu = QMenu(self)
                    collect_action = QAction("Собрать камень", self)
                    collect_action.triggered.connect(lambda: self.queue_collect_stone(c, r))
                    menu.addAction(collect_action)
                    menu.exec_(event.globalPos())
                else:
                    menu = QMenu(self)
                    menu.addAction("Слишком далеко").setEnabled(False)
                    menu.exec_(event.globalPos())

            elif cell in self.rocks:
                adjacent = any(self.is_adjacent_to_group(c, r, g["pos"]) and not g.get("in_house", False) for g in self.groups)
                has_pickaxe = self.resources.get("pickaxe", 0) > 0
                
                if adjacent and has_pickaxe:
                    menu = QMenu(self)
                    mine_action = QAction("Добыть камень", self)
                    mine_action.triggered.connect(lambda: self.queue_mine_rock(c, r))
                    menu.addAction(mine_action)
                    menu.exec_(event.globalPos())
                elif not adjacent:
                    menu = QMenu(self)
                    menu.addAction("Слишком далеко").setEnabled(False)
                    menu.exec_(event.globalPos())
                else:
                    menu = QMenu(self)
                    menu.addAction("Нужна каменная кирка").setEnabled(False)
                    menu.exec_(event.globalPos())

            # Если клетка — дом, но племени там визуально нет (оно внутри)
            if cell in self.houses:
                for idx, g in enumerate(self.groups):
                    if g["pos"] == (c, r) and g.get("in_house", False):
                        menu = QMenu(self)
                        exit_action = QAction("Выйти из дома", self)
                        exit_action.triggered.connect(lambda: self.toggle_house(idx))
                        menu.addAction(exit_action)
                        menu.exec_(event.globalPos())
                        return

            cf_at = None
            for cf in self.campfires:
                if cf["pos"] == cell: cf_at = cf; break
            bt_at = None
            for bt in self.burning_trees:
                if bt["pos"] == cell: bt_at = bt; break

            if cf_at or bt_at:
                can_maintain = False
                if self.tech_tree:
                    tech = self.tech_tree.tech_by_name("Поддержание огня")
                    if tech and tech["researched"]: can_maintain = True
                
                if can_maintain and self.resources["wood"] >= 1:
                    menu = QMenu(self)
                    maintain_action = QAction("Поддержать огонь (1 дерево)", self)
                    if cf_at: maintain_action.triggered.connect(lambda: self.maintain_fire(cf_at))
                    else: maintain_action.triggered.connect(lambda: self.maintain_fire(bt_at))
                    menu.addAction(maintain_action)
                    menu.exec_(event.globalPos())

    def toggle_house(self, group_idx):
        g = self.groups[group_idx]
        g["in_house"] = not g.get("in_house", False)
        self.update()

    def maintain_fire(self, fire_obj):
        if self.resources["wood"] >= 1:
            self.resources["wood"] -= 1
            fire_obj["life"] += 3
            if self.on_update_ui: self.on_update_ui()
            self.update()

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

    def queue_collect_stone(self, c, r):
        if (c, r) in self.stones:
            self.stones.remove((c, r))
            self.resources["stone"] += 1
            if self.on_update_ui: self.on_update_ui()
            self.update()

    def queue_mine_rock(self, c, r):
        if (c, r) in self.rocks:
            self.resources["stone"] += random.randint(3, 4)
            if self.on_update_ui: self.on_update_ui()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        for r in range(ROWS):
            for c in range(COLS):
                rect = QRect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if self.tiles[r][c]["is_river"]:
                    color = QColor(150, 200, 255) if self.is_winter else QColor(43, 171, 197)
                else:
                    color = QColor(255, 255, 255) if self.is_winter else QColor(23, 124, 19)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen); painter.drawRect(rect)

        pen = QPen(Qt.black); pen.setWidth(1); painter.setPen(pen)
        for x in range(0, self.width() + 1, CELL_SIZE): painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height() + 1, CELL_SIZE): painter.drawLine(0, y, self.width(), y)

        # Дома
        for (bc, br) in self.houses:
            cell_rect = QRect(bc * CELL_SIZE, br * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            img_size = int(CELL_SIZE * 0.9)
            img_x = cell_rect.left() + (CELL_SIZE - img_size) // 2
            img_y = cell_rect.top() + (CELL_SIZE - img_size) // 2
            img_rect = QRect(img_x, img_y, img_size, img_size)
            if self.has_house_img: painter.drawPixmap(img_rect, self.house_pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(139, 69, 19)); painter.drawRect(img_rect)

        # Скалы
        for (bc, br) in self.rocks:
            cell_rect = QRect(bc * CELL_SIZE, br * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            img_size = int(CELL_SIZE * 0.9)
            img_x = cell_rect.left() + (CELL_SIZE - img_size) // 2
            img_y = cell_rect.top() + (CELL_SIZE - img_size) // 2
            img_rect = QRect(img_x, img_y, img_size, img_size)
            if self.has_rock_img: painter.drawPixmap(img_rect, self.rock_pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(100, 100, 100)); painter.drawRect(img_rect)

        # Горящие деревья
        for bt in self.burning_trees:
            bc, br = bt["pos"]
            cell_rect = QRect(bc * CELL_SIZE, br * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            img_size = int(CELL_SIZE * 0.9)
            img_x = cell_rect.left() + (CELL_SIZE - img_size) // 2
            img_y = cell_rect.top() + (CELL_SIZE - img_size) // 2
            img_rect = QRect(img_x, img_y, img_size, img_size)
            if self.has_tree_burning_img: painter.drawPixmap(img_rect, self.tree_burning_pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(255, 100, 0)); painter.drawEllipse(img_rect)
            painter.setPen(Qt.white); painter.setFont(QFont("Arial", 10, QFont.Bold))
            painter.drawText(cell_rect, Qt.AlignTop | Qt.AlignRight, str(bt["life"]))

        # Костры
        for cf in self.campfires:
            bc, br = cf["pos"]
            cell_rect = QRect(bc * CELL_SIZE, br * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            img_size = int(CELL_SIZE * 0.75)
            img_x = cell_rect.left() + (CELL_SIZE - img_size) // 2
            img_y = cell_rect.top() + (CELL_SIZE - img_size) // 2
            img_rect = QRect(img_x, img_y, img_size, img_size)
            if self.has_campfire_img: painter.drawPixmap(img_rect, self.campfire_pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                painter.setPen(Qt.NoPen); painter.setBrush(QColor(255, 140, 0)); painter.drawEllipse(img_rect)
            painter.setPen(Qt.white); painter.setFont(QFont("Arial", 10, QFont.Bold))
            painter.drawText(cell_rect, Qt.AlignTop | Qt.AlignRight, str(cf["life"]))

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

        # Люди (только если не в доме)
        font = QFont("Arial", 12); font.setBold(True); painter.setFont(font)
        for g in self.groups:
            if g["count"] <= 0 or g.get("in_house", False): continue
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
            if g.get("in_house", False): continue
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

        self.stick_label = QLabel(); self.stick_label.setFont(QFont("Arial", 14)); self.stick_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.stick_label)

        self.stone_label = QLabel(); self.stone_label.setFont(QFont("Arial", 14)); self.stone_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.stone_label)

        self.chopper_label = QLabel(); self.chopper_label.setFont(QFont("Arial", 14)); self.chopper_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.chopper_label)

        self.pickaxe_label = QLabel(); self.pickaxe_label.setFont(QFont("Arial", 14)); self.pickaxe_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.pickaxe_label)

        self.spear_label = QLabel(); self.spear_label.setFont(QFont("Arial", 14)); self.spear_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.spear_label)
        
        self.people_label = QLabel(); self.people_label.setFont(QFont("Arial", 14)); self.people_label.setStyleSheet("padding: 10px; font-size: 16px;")
        self.layout.addWidget(self.people_label)

        self.season_label = QLabel(); self.season_label.setFont(QFont("Arial", 14)); self.season_label.setStyleSheet("padding: 10px; font-size: 16px; color: #00E5FF;")
        self.layout.addWidget(self.season_label)
        
        self.update_ui()
        
    def update_ui(self):
        self.berry_label.setText(f"🍒 Ягоды: {self.grid.resources['berries']}")
        self.wood_label.setText(f"🪵 Древесина: {self.grid.resources['wood']}")
        self.stick_label.setText(f"🥢 Палки: {self.grid.resources['sticks']}")
        self.stone_label.setText(f"🪨 Камни: {self.grid.resources['stone']}")
        self.chopper_label.setText(f"🪓 Рубила: {self.grid.resources['chopper']}")
        self.pickaxe_label.setText(f"⛏️ Кирки: {self.grid.resources['pickaxe']}")
        self.spear_label.setText(f"🔥 Обожжённые копья: {self.grid.resources.get('burnt_spears', 0)}")
        total = sum(g["count"] for g in self.grid.groups)
        self.people_label.setText(f"👥 Люди: {total}")
        
        season_text = "❄️ Зима" if self.grid.is_winter else "☀️ Тепло"
        self.season_label.setText(f"Сезон: {season_text}")


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

        self.btn_campfire = QPushButton("Создать костёр (2 дерева)")
        self.btn_campfire.setStyleSheet("""
            QPushButton {
                background-color: #d35400; color: white; 
                font-size: 16px; padding: 10px; border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover { background-color: #e67e22; }
            QPushButton:pressed { background-color: #a04000; }
            QPushButton:disabled { background-color: #7F8C8D; color: #BDC3C7; }
        """)
        self.btn_campfire.clicked.connect(self.craft_campfire)
        self.layout.addWidget(self.btn_campfire)

        self.btn_sticks = QPushButton("Сделать 5 палок (1 дерево)")
        self.btn_sticks.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad; color: white; 
                font-size: 16px; padding: 10px; border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover { background-color: #9b59b6; }
            QPushButton:pressed { background-color: #6c3483; }
            QPushButton:disabled { background-color: #7F8C8D; color: #BDC3C7; }
        """)
        self.btn_sticks.clicked.connect(self.craft_sticks)
        self.layout.addWidget(self.btn_sticks)

        self.btn_pickaxe = QPushButton("Создать каменную кирку (1 камень + 1 палка)")
        self.btn_pickaxe.setStyleSheet("""
            QPushButton {
                background-color: #2C3E50; color: white; 
                font-size: 16px; padding: 10px; border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover { background-color: #34495E; }
            QPushButton:pressed { background-color: #1A252F; }
            QPushButton:disabled { background-color: #7F8C8D; color: #BDC3C7; }
        """)
        self.btn_pickaxe.clicked.connect(self.craft_pickaxe)
        self.layout.addWidget(self.btn_pickaxe)

        self.btn_house = QPushButton("Построить дом (5 дерева)")
        self.btn_house.setStyleSheet("""
            QPushButton {
                background-color: #8B4513; color: white; 
                font-size: 16px; padding: 10px; border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover { background-color: #A0522D; }
            QPushButton:pressed { background-color: #654321; }
            QPushButton:disabled { background-color: #7F8C8D; color: #BDC3C7; }
        """)
        self.btn_house.clicked.connect(self.craft_house)
        self.layout.addWidget(self.btn_house)

        self.btn_burnt_spear = QPushButton("Создать обожжённое копьё (1 палка + рядом с огнём)")
        self.btn_burnt_spear.setStyleSheet("""
            QPushButton {
                background-color: #e67e22; color: white; 
                font-size: 16px; padding: 10px; border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover { background-color: #f39c12; }
            QPushButton:pressed { background-color: #d35400; }
            QPushButton:disabled { background-color: #7F8C8D; color: #BDC3C7; }
        """)
        self.btn_burnt_spear.clicked.connect(self.craft_burnt_spear)
        self.layout.addWidget(self.btn_burnt_spear)

        self.info_label = QLabel()
        self.info_label.setStyleSheet("padding: 10px; color: #bbb;")
        self.layout.addWidget(self.info_label)

        self.update_ui()

    def craft_chopper(self):
        if not (self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Грубые каменные инструменты")["researched"]):
            self.info_label.setText("Нужна технология 'Грубые каменные инструменты'")
            return
        if self.grid.resources["stone"] > 0:
            self.grid.resources["stone"] -= 1
            self.grid.resources["chopper"] += 1
            self.info_label.setText("Создано 1 рубило!")
            self.grid.on_update_ui()
            self.grid.next_turn()
        else:
            self.info_label.setText("Не хватает камней!")

    def craft_campfire(self):
        if not (self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Добыча огня")["researched"]):
            self.info_label.setText("Нужна технология 'Добыча огня'")
            return
        if self.grid.resources["wood"] >= 2:
            if self.grid.groups:
                g = self.grid.groups[0]
                self.grid.campfires.append({"pos": g["pos"], "life": 3})
                self.grid.resources["wood"] -= 2
                self.info_label.setText("Создан костёр на 3 хода!")
                self.grid.on_update_ui()
            else:
                self.info_label.setText("Некуда ставить костёр (нет племени)!")
        else:
            self.info_label.setText("Не хватает древесины (нужно 2)!")

    def craft_sticks(self):
        if not (self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Деревообработка")["researched"]):
            self.info_label.setText("Нужна технология 'Деревообработка'")
            return
        if self.grid.resources["wood"] >= 1:
            self.grid.resources["wood"] -= 1
            self.grid.resources["sticks"] += 5
            self.info_label.setText("Сделано 5 палок!")
            self.grid.on_update_ui()
        else:
            self.info_label.setText("Не хватает древесины!")

    def craft_pickaxe(self):
        if not (self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Насаживание на палку")["researched"]):
            self.info_label.setText("Нужна технология 'Насаживание на палку'")
            return
        if self.grid.resources["stone"] >= 1 and self.grid.resources["sticks"] >= 1:
            self.grid.resources["stone"] -= 1
            self.grid.resources["sticks"] -= 1
            self.grid.resources["pickaxe"] += 1
            self.info_label.setText("Создана каменная кирка!")
            self.grid.on_update_ui()
            self.grid.next_turn()
        else:
            self.info_label.setText("Не хватает камня или палки!")

    def craft_house(self):
        if not (self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Примитивное строительство")["researched"]):
            self.info_label.setText("Нужна технология 'Примитивное строительство'")
            return
        if self.grid.resources["wood"] >= 5:
            if self.grid.groups:
                g = self.grid.groups[0]
                self.grid.houses.add(g["pos"])
                self.grid.resources["wood"] -= 5
                self.info_label.setText("Дом построен!")
                self.grid.on_update_ui()
            else:
                self.info_label.setText("Некуда строить (нет племени)!")
        else:
            self.info_label.setText("Не хватает древесины (нужно 5)!")

    def craft_burnt_spear(self):
        if not (self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Обожжённые копья")["researched"]):
            self.info_label.setText("Нужна технология 'Обожжённые копья'")
            return
            
        if self.grid.resources["sticks"] < 1:
            self.info_label.setText("Нужна 1 палка!")
            return
            
        # Проверка, что племя рядом с огнём
        near_fire = False
        for g in self.grid.groups:
            if g.get("in_house", False): continue
            if self.grid.is_near_fire(*g["pos"]):
                near_fire = True
                break
                
        if not near_fire:
            self.info_label.setText("Племя должно быть рядом с огнём!")
            return

        self.grid.resources["sticks"] -= 1
        self.grid.resources["burnt_spears"] += 1
        self.info_label.setText("Создано обожжённое копьё!")
        self.grid.on_update_ui()

    def update_ui(self):
        has_tools = self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Грубые каменные инструменты")["researched"]
        self.btn_chop.setEnabled(has_tools and self.grid.resources["stone"] > 0)
        self.btn_chop.setText("Создать рубило (1 камень)" if has_tools else "Создать рубило (нужна технология)")

        has_fire = self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Добыча огня")["researched"]
        self.btn_campfire.setEnabled(has_fire and self.grid.resources["wood"] >= 2)
        self.btn_campfire.setText("Создать костёр (2 дерева)" if has_fire else "Создать костёр (нужна технология)")

        has_woodwork = self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Деревообработка")["researched"]
        self.btn_sticks.setEnabled(has_woodwork and self.grid.resources["wood"] >= 1)
        self.btn_sticks.setText("Сделать 5 палок (1 дерево)" if has_woodwork else "Сделать 5 палок (нужна технология)")

        has_mount = self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Насаживание на палку")["researched"]
        self.btn_pickaxe.setEnabled(has_mount and self.grid.resources["stone"] >= 1 and self.grid.resources["sticks"] >= 1)
        self.btn_pickaxe.setText("Создать каменную кирку (1 камень + 1 палка)" if has_mount else "Создать каменную кирку (нужна технология)")

        has_building = self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Примитивное строительство")["researched"]
        self.btn_house.setEnabled(has_building and self.grid.resources["wood"] >= 5)
        self.btn_house.setText("Построить дом (5 дерева)" if has_building else "Построить дом (нужна технология)")

        has_burnt_spear_tech = self.grid.tech_tree and self.grid.tech_tree.tech_by_name("Обожжённые копья")["researched"]
        self.btn_burnt_spear.setEnabled(has_burnt_spear_tech and self.grid.resources["sticks"] >= 1)
        self.btn_burnt_spear.setText("Создать обожжённое копьё (1 палка + рядом с огнём)" if has_burnt_spear_tech else "Создать обожжённое копьё (нужна технология)")


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
        
        self.crafting_tab = CraftingWidget(self.world_tab)
        self.tabs.addTab(self.crafting_tab, "Создание")

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
        
        cycle = (self.turn_count - 1) % 12
        self.world_tab.is_winter = cycle >= 9
        
        if self.turn_count % 5 == 0 and len(self.world_tab.bushes) < 30:
            land_tiles = [(c, r) for r in range(ROWS) for c in range(COLS) 
                          if not self.world_tab.tiles[r][c]["is_river"] 
                          and (c, r) not in self.world_tab.bushes
                          and (c, r) not in self.world_tab.trees
                          and (c, r) not in self.world_tab.stones
                          and (c, r) not in self.world_tab.rocks
                          and (c, r) not in self.world_tab.houses
                          and self.world_tab.get_group_at(c, r) is None]
            if land_tiles:
                new_bush = random.choice(land_tiles)
                self.world_tab.bushes.add(new_bush)
                
        if self.turn_count % 20 == 0 and len(self.world_tab.trees) < 15:
            land_tiles = [(c, r) for r in range(ROWS) for c in range(COLS) 
                          if not self.world_tab.tiles[r][c]["is_river"] 
                          and (c, r) not in self.world_tab.bushes
                          and (c, r) not in self.world_tab.trees
                          and (c, r) not in self.world_tab.stones
                          and (c, r) not in self.world_tab.rocks
                          and (c, r) not in self.world_tab.houses
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