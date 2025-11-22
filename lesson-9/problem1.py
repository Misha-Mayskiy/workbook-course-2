import json
import sys
import itertools
from typing import Optional, List, Dict, Tuple, Set

from PySide6.QtCore import Qt, QRectF, QLineF, QPointF, Signal, QObject
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QPainterPathStroker, QAction, QFont
from PySide6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsEllipseItem,
                               QGraphicsLineItem, QGraphicsTextItem,
                               QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QFileDialog, QMessageBox, QLabel, QPushButton, QInputDialog, QGroupBox)


# ==========================================
# 1. Configuration
# ==========================================
class GraphConfig:
    NODE_DIAMETER = 30
    NODE_RADIUS = NODE_DIAMETER / 2
    EDGE_WIDTH = 2
    MIN_DISTANCE = 50

    COLOR_BG = QColor(40, 40, 40)
    COLOR_NODE = QColor(0, 200, 255)
    COLOR_NODE_ACTIVE = QColor(255, 0, 255)
    COLOR_EDGE = QColor(200, 200, 200)
    COLOR_TEXT = QColor(255, 255, 255)
    COLOR_WEIGHT_TEXT = QColor(255, 255, 100)  # Желтый для весов

    TABLE_BG = QColor(50, 50, 50)
    TABLE_TEXT = QColor(255, 255, 255)
    TABLE_DIAGONAL = QColor(80, 80, 80)


# ==========================================
# 2. Graph Visual Entities
# ==========================================
class EdgeItem(QGraphicsLineItem):
    def __init__(self, source_item, dest_item, weight: str = ""):
        super().__init__()
        self.source = source_item
        self.dest = dest_item
        self.weight = weight

        self.setPen(QPen(GraphConfig.COLOR_EDGE, GraphConfig.EDGE_WIDTH))
        self.setZValue(0)

        # Текст веса
        self.text_item = QGraphicsTextItem(weight, self)
        self.text_item.setDefaultTextColor(GraphConfig.COLOR_WEIGHT_TEXT)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        self.text_item.setFont(font)

        self.update_geometry()

    def set_weight(self, value: str):
        self.weight = value
        self.text_item.setPlainText(value)
        self.update_geometry()

    def update_geometry(self):
        line = QLineF(self.source.scenePos(), self.dest.scenePos())
        self.setLine(line)

        # Позиционирование текста по центру линии
        if self.text_item.toPlainText():
            center = line.center()
            # Небольшой сдвиг, чтобы текст не перекрывал линию
            self.text_item.setPos(center.x() - 10, center.y() - 20)
        else:
            self.text_item.setPos(line.center())

    def shape(self):
        path = super().shape()
        stroker = QPainterPathStroker()
        stroker.setWidth(15)  # Увеличиваем область клика
        return stroker.createStroke(path)

    def mouseDoubleClickEvent(self, event):
        # Редактирование веса по двойному клику
        text, ok = QInputDialog.getText(None, "Вес ребра", "Введите вес (число):", text=self.weight)
        if ok:
            self.set_weight(text)
        super().mouseDoubleClickEvent(event)


class NodeItem(QGraphicsEllipseItem):
    def __init__(self, name: str, x: float, y: float):
        rect = QRectF(-GraphConfig.NODE_RADIUS, -GraphConfig.NODE_RADIUS,
                      GraphConfig.NODE_DIAMETER, GraphConfig.NODE_DIAMETER)
        super().__init__(rect)
        self.name = name
        self.mapped_id = None  # Для отображения результата решения (например, "3")
        self.edges: List[EdgeItem] = []

        self.setBrush(QBrush(GraphConfig.COLOR_NODE))
        self.setPen(QPen(Qt.NoPen))
        self.setPos(x, y)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self._create_labels()

    def _create_labels(self):
        # Основная метка (Имя: A, B...)
        self.label = QGraphicsTextItem(self.name, self)
        self.label.setDefaultTextColor(Qt.black)
        font = QFont()
        font.setBold(True)
        self.label.setFont(font)
        # Центрируем грубо
        self.label.setPos(-6, -10)

        # Метка сопоставления (Номер из таблицы)
        self.match_label = QGraphicsTextItem("", self)
        self.match_label.setDefaultTextColor(QColor(100, 255, 100))  # Зеленый
        f2 = QFont()
        f2.setBold(True)
        f2.setPointSize(12)
        self.match_label.setFont(f2)
        self.match_label.setPos(10, -25)

    def set_mapped_id(self, id_str: str):
        self.mapped_id = id_str
        if id_str:
            self.match_label.setPlainText(f"[{id_str}]")
        else:
            self.match_label.setPlainText("")

    def set_highlighted(self, is_active: bool):
        color = GraphConfig.COLOR_NODE_ACTIVE if is_active else GraphConfig.COLOR_NODE
        self.setBrush(QBrush(color))

    def add_connection(self, edge: EdgeItem):
        self.edges.append(edge)

    def remove_connection(self, edge: EdgeItem):
        if edge in self.edges:
            self.edges.remove(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            for edge in self.edges:
                edge.update_geometry()
        return super().itemChange(change, value)


# ==========================================
# 3. Graph Logic & Algorithm
# ==========================================
class ChainBuilder:
    def __init__(self):
        self.active_node: Optional[NodeItem] = None

    def start_or_continue(self, node: NodeItem) -> Optional[NodeItem]:
        prev_node = self.active_node
        if self.active_node:
            self.active_node.set_highlighted(False)
        self.active_node = node
        self.active_node.set_highlighted(True)
        return prev_node

    def reset(self):
        if self.active_node:
            self.active_node.set_highlighted(False)
            self.active_node = None


class GraphSolver:
    """
    Класс для поиска изоморфизма между нарисованным графом и матрицей.
    """

    @staticmethod
    def solve(graph_items: List[NodeItem], matrix_data: List[List[str]]) -> Dict[str, int]:
        """
        Возвращает словарь: {ИмяУзлаГрафа: НомерСтрокиМатрицы (1-based)}
        Или None, если решение не найдено.
        """

        # 1. Парсим граф в структуру смежности
        # G = { 'A': {'B': 10, 'C': 5}, ... }
        g_adj = {node.name: {} for node in graph_items}

        for node in graph_items:
            for edge in node.edges:
                neighbor = edge.dest if edge.source == node else edge.source
                # Пытаемся достать вес, если он число. Если нет - считаем 1 (топология)
                weight = 1
                if edge.weight.isdigit():
                    weight = int(edge.weight)
                elif edge.weight == "":
                    weight = 1  # Если вес пустой, считаем просто наличие связи

                g_adj[node.name][neighbor.name] = weight

        # 2. Парсим матрицу в структуру смежности
        # M = { 0: {1: 10, 2: 5}, ... } (индексы 0..N-1)
        size = len(matrix_data)
        m_adj = {i: {} for i in range(size)}

        for r in range(size):
            for c in range(size):
                val_str = matrix_data[r][c]
                if val_str and val_str.isdigit():
                    val = int(val_str)
                    if val > 0:
                        # Если в графе все веса = 1 (не заданы), то в матрице тоже приводим к 1 для топологического сравнения
                        # Но лучше проверить: если в графе есть хоть один вес > 1, используем строгий режим
                        m_adj[r][c] = val

        # Определяем режим сравнения: Строгий (по весам) или Топологический
        graph_has_weights = any(any(w > 1 for w in neighs.values()) for neighs in g_adj.values())

        # Если граф нарисован без весов, но таблица с весами -> игнорируем веса таблицы (ставим 1)
        if not graph_has_weights:
            for r in m_adj:
                for c in m_adj[r]:
                    m_adj[r][c] = 1

        # 3. Фильтрация по степеням вершин (Degree Heuristic)
        # Степень вершины = количество связей
        g_degrees = {name: len(neighs) for name, neighs in g_adj.items()}
        m_degrees = {idx: len(neighs) for idx, neighs in m_adj.items()}

        if sorted(g_degrees.values()) != sorted(m_degrees.values()):
            return None  # Степенные последовательности не совпадают

        node_names = list(g_adj.keys())
        matrix_indices = list(m_adj.keys())  # [0, 1, 2...]

        if len(node_names) != len(matrix_indices):
            return None

        # 4. Перебор (Backtracking / Permutations)
        # Для малых N (N < 10) простой перебор всех перестановок работает быстро (8! = 40к)
        # Но добавим оптимизацию: мапить можно только узлы с одинаковой степенью.

        # Группируем узлы по степеням
        g_by_deg = {}
        for n, deg in g_degrees.items():
            g_by_deg.setdefault(deg, []).append(n)

        m_by_deg = {}
        for idx, deg in m_degrees.items():
            m_by_deg.setdefault(deg, []).append(idx)

        # Проверка групп
        for deg in g_by_deg:
            if deg not in m_by_deg or len(g_by_deg[deg]) != len(m_by_deg[deg]):
                return None

        # Генерируем перестановки внутри групп степеней
        # Это сильно сокращает пространство поиска
        # Например, если степени [2, 2, 3, 3], мы перебираем 2! * 2! = 4 варианта вместо 4! = 24.

        keys_sorted_by_deg = sorted(g_by_deg.keys())

        # Список списков возможных кандидатов
        # structure: [ (['A', 'B'], [0, 3]), (['C'], [1]) ... ]
        groups = []
        for deg in keys_sorted_by_deg:
            groups.append((g_by_deg[deg], m_by_deg[deg]))

        # Генератор продуктов перестановок
        # itertools.product( permutations(['A','B']), permutations(['C']) ... ) - нет, нужно мапить группу на группу

        def solve_recursive(group_idx, current_mapping):
            if group_idx == len(groups):
                # Все группы назначены, проверяем изоморфизм
                return check_isomorphism(current_mapping)

            g_nodes, m_indices = groups[group_idx]

            # Перебираем все перестановки индексов для текущей группы узлов
            for p in itertools.permutations(m_indices):
                # Добавляем в маппинг
                new_mapping = current_mapping.copy()
                for i, node_name in enumerate(g_nodes):
                    new_mapping[node_name] = p[i]

                if solve_recursive(group_idx + 1, new_mapping):
                    return new_mapping

            return None

        def check_isomorphism(mapping):
            # Проверяем каждое ребро графа
            for u_name, neighbors in g_adj.items():
                u_idx = mapping[u_name]

                for v_name, weight in neighbors.items():
                    v_idx = mapping[v_name]

                    # Есть ли ребро в матрице?
                    if v_idx not in m_adj[u_idx]:
                        return False

                    # Совпадает ли вес (если веса используются)?
                    # Если в графе вес > 1, он должен совпадать.
                    # Если 1 (не задан), а в матрице число - это допустимо (мы уже нормализовали выше при graph_has_weights=False)
                    mat_weight = m_adj[u_idx][v_idx]
                    if weight != mat_weight:
                        return False
            return True

        final_mapping = solve_recursive(0, {})

        if final_mapping:
            # Преобразуем в 1-based для вывода
            return {k: v + 1 for k, v in final_mapping.items()}
        return None


class GraphManager(QObject):
    node_count_changed = Signal(int)

    def __init__(self, scene: QGraphicsScene):
        super().__init__()
        self.scene = scene
        self.node_counter = 0

    def reset(self):
        self.node_counter = 0
        self.scene.clear()
        self.node_count_changed.emit(0)

    def generate_name(self) -> str:
        n = self.node_counter
        name = ""
        while n >= 0:
            name = chr(ord('A') + (n % 26)) + name
            n = n // 26 - 1
        self.node_counter += 1
        return name

    def create_node(self, pos: QPointF, name: str = None) -> NodeItem:
        if name is None:
            name = self.generate_name()
        else:
            self.node_counter += 1
        node = NodeItem(name, pos.x(), pos.y())
        self.scene.addItem(node)
        self.node_count_changed.emit(self.get_node_count())
        return node

    def create_edge(self, u: NodeItem, v: NodeItem, weight: str = ""):
        if u == v: return
        for edge in u.edges:
            if (edge.source == u and edge.dest == v) or (edge.source == v and edge.dest == u):
                return
        edge = EdgeItem(u, v, weight)
        self.scene.addItem(edge)
        u.add_connection(edge)
        v.add_connection(edge)

    def delete_item(self, item: QGraphicsItem):
        if isinstance(item, NodeItem):
            for edge in list(item.edges):
                self.delete_item(edge)
            self.scene.removeItem(item)
            self.node_count_changed.emit(self.get_node_count())
        elif isinstance(item, EdgeItem):
            item.source.remove_connection(item)
            item.dest.remove_connection(item)
            self.scene.removeItem(item)
        elif isinstance(item, QGraphicsTextItem):
            # Если кликнули по тексту веса
            parent = item.parentItem()
            if isinstance(parent, EdgeItem):
                self.delete_item(parent)

    def get_node_count(self) -> int:
        return sum(1 for item in self.scene.items() if isinstance(item, NodeItem))

    def is_position_valid(self, pos: QPointF) -> bool:
        for item in self.scene.items():
            if isinstance(item, NodeItem):
                distance = QLineF(pos, item.scenePos()).length()
                if distance < GraphConfig.MIN_DISTANCE:
                    return False
        return True

    def get_nodes(self) -> List[NodeItem]:
        return [i for i in self.scene.items() if isinstance(i, NodeItem)]


# ==========================================
# 4. Matrix Widget
# ==========================================
class WeightMatrixWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(0)
        self.setRowCount(0)

        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {GraphConfig.TABLE_BG.name()};
                color: {GraphConfig.TABLE_TEXT.name()};
                gridline-color: #666;
            }}
            QHeaderView::section {{
                background-color: #333;
                color: white;
                padding: 4px;
                border: 1px solid #666;
            }}
            QLineEdit {{ color: white; background-color: #444; }}
            QTableCornerButton::section {{ background-color: #333; }}
        """)
        self.itemChanged.connect(self.on_item_changed)
        self.horizontalHeader().setDefaultSectionSize(40)
        self.verticalHeader().setDefaultSectionSize(30)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

    def update_size(self, node_count: int):
        old_data = self.get_data()
        self.setRowCount(node_count)
        self.setColumnCount(node_count)
        headers = [str(i + 1) for i in range(node_count)]
        self.setHorizontalHeaderLabels(headers)
        self.setVerticalHeaderLabels(headers)

        self.blockSignals(True)
        for r in range(node_count):
            for c in range(node_count):
                # Восстанавливаем старые данные, если есть
                text = ""
                if r < len(old_data) and c < len(old_data[r]):
                    text = old_data[r][c]

                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)

                if r == c:
                    item.setFlags(Qt.ItemIsEnabled)
                    item.setBackground(QBrush(GraphConfig.TABLE_DIAGONAL))
                else:
                    item.setBackground(QBrush(GraphConfig.TABLE_BG))

                self.setItem(r, c, item)
        self.blockSignals(False)

    def on_item_changed(self, item):
        row, col = item.row(), item.column()
        if row == col: return
        text = item.text()

        # Валидация: только числа
        if text and not text.isdigit():
            item.setText("")
            return

        self.blockSignals(True)
        sym_item = self.item(col, row)
        if sym_item:
            sym_item.setText(text)
        self.blockSignals(False)

    def get_data(self) -> List[List[str]]:
        rows = self.rowCount()
        data = []
        for r in range(rows):
            row_data = []
            for c in range(rows):
                item = self.item(r, c)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data

    def set_data(self, data: List[List[str]]):
        size = len(data)
        self.update_size(size)
        self.blockSignals(True)
        for r in range(size):
            for c in range(size):
                if r < len(data) and c < len(data[r]):
                    val = data[r][c]
                    item = self.item(r, c)
                    if item:
                        item.setText(val)
        self.blockSignals(False)


# ==========================================
# 5. Graph Scene
# ==========================================
class GraphScene(QGraphicsScene):
    def __init__(self, manager: GraphManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.chain_builder = ChainBuilder()
        self.setBackgroundBrush(QBrush(GraphConfig.COLOR_BG))
        self.setSceneRect(0, 0, 2000, 2000)  # Большая сцена

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.chain_builder.reset()
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        pos = event.scenePos()
        item = self.itemAt(pos, self.views()[0].transform())

        # Игнорируем клики по тексту, прокидываем их родителю (узлу или ребру)
        if isinstance(item, QGraphicsTextItem):
            item = item.parentItem()

        if event.button() == Qt.LeftButton:
            if event.modifiers() & Qt.ShiftModifier:
                # Режим создания связей
                if isinstance(item, NodeItem):
                    prev_node = self.chain_builder.start_or_continue(item)
                    if prev_node:
                        self.manager.create_edge(prev_node, item)
                    event.accept()
                    return
                else:
                    self.chain_builder.reset()
            else:
                self.chain_builder.reset()

            if item is None:
                # Клик в пустоту - создание узла
                if self.manager.is_position_valid(pos):
                    self.manager.create_node(pos)
                event.accept()
                return

            super().mousePressEvent(event)

        elif event.button() == Qt.RightButton:
            self.chain_builder.reset()
            if item:
                self.manager.delete_item(item)
                event.accept()


# ==========================================
# 6. Main Window
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЕГЭ Информатика - Задание 1 (Графы и Матрицы)")
        self.resize(1280, 720)

        # Инициализация сцены и менеджера
        self.scene = QGraphicsScene()
        self.graph_manager = GraphManager(self.scene)
        self.scene = GraphScene(self.graph_manager, self)
        self.graph_manager.scene = self.scene

        # UI Components
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)  # Можно таскать полотно

        self.matrix_widget = WeightMatrixWidget()
        self.graph_manager.node_count_changed.connect(self.matrix_widget.update_size)

        # --- Layout ---
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)

        # Левая панель (Таблица + Управление)
        left_panel = QVBoxLayout()

        # Группа таблицы
        table_group = QGroupBox("Матрица весов")
        table_layout = QVBoxLayout()
        table_layout.addWidget(self.matrix_widget)
        table_group.setLayout(table_layout)

        # Группа управления
        ctrl_group = QGroupBox("Инструменты")
        ctrl_layout = QVBoxLayout()

        self.btn_solve = QPushButton("Найти соответствие (Решить)")
        self.btn_solve.setStyleSheet("background-color: #2a82da; color: white; font-weight: bold; padding: 8px;")
        self.btn_solve.clicked.connect(self.run_solver)

        self.btn_clear_res = QPushButton("Сбросить результаты")
        self.btn_clear_res.clicked.connect(self.clear_results)

        self.btn_clear_weights = QPushButton("Удалить веса с графа")
        self.btn_clear_weights.clicked.connect(self.clear_graph_weights)

        help_lbl = QLabel(
            "Управление:\nЛКМ - создать узел / тащить\nShift+ЛКМ - создать ребро\nПКМ - удалить\nДвойной клик по ребру - вес")
        help_lbl.setStyleSheet("color: #aaa; font-size: 11px;")

        ctrl_layout.addWidget(self.btn_solve)
        ctrl_layout.addWidget(self.btn_clear_res)
        ctrl_layout.addWidget(self.btn_clear_weights)
        ctrl_layout.addWidget(help_lbl)
        ctrl_group.setLayout(ctrl_layout)

        left_panel.addWidget(table_group, stretch=2)
        left_panel.addWidget(ctrl_group, stretch=0)

        # Правая панель (Граф)
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Граф (Редактор)"))
        right_layout.addWidget(self.view)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_layout, 3)

        self.setCentralWidget(central_widget)
        self.create_menu()

    def create_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("Файл")

        save_action = QAction("Сохранить...", self)
        save_action.triggered.connect(self.save_exercise)
        file_menu.addAction(save_action)

        load_action = QAction("Загрузить...", self)
        load_action.triggered.connect(self.load_exercise)
        file_menu.addAction(load_action)

        clear_action = QAction("Очистить всё", self)
        clear_action.triggered.connect(self.clear_all)
        file_menu.addAction(clear_action)

    def run_solver(self):
        nodes = self.graph_manager.get_nodes()
        matrix = self.matrix_widget.get_data()

        if not nodes:
            QMessageBox.warning(self, "Ошибка", "Граф пуст.")
            return

        mapping = GraphSolver.solve(nodes, matrix)

        if mapping:
            # Успех
            msg_text = "Решение найдено!\n\n"
            sorted_map = sorted(mapping.items(), key=lambda x: x[0])
            for name, idx in sorted_map:
                msg_text += f"{name} -> {idx}\n"
                # Обновляем визуальные метки на узлах
                for node in nodes:
                    if node.name == name:
                        node.set_mapped_id(str(idx))

            QMessageBox.information(self, "Успех", msg_text)
        else:
            QMessageBox.critical(self, "Неудача",
                                 "Не удалось найти соответствие.\nПроверьте:\n1. Степени вершин совпадают?\n2. Веса ребер (если указаны) совпадают?")

    def clear_results(self):
        for node in self.graph_manager.get_nodes():
            node.set_mapped_id(None)

    def clear_graph_weights(self):
        for item in self.scene.items():
            if isinstance(item, EdgeItem):
                item.set_weight("")

    def clear_all(self):
        self.graph_manager.reset()
        self.matrix_widget.update_size(0)

    def save_exercise(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "JSON Files (*.json)")
        if not file_path: return

        nodes = self.graph_manager.get_nodes()
        nodes_data = []
        node_id_map = {node: i for i, node in enumerate(nodes)}

        for i, node in enumerate(nodes):
            nodes_data.append({
                "id": i, "name": node.name, "x": node.pos().x(), "y": node.pos().y()
            })

        edges_data = []
        visited = set()
        for node in nodes:
            for edge in node.edges:
                if edge not in visited:
                    visited.add(edge)
                    u_id = node_id_map.get(edge.source)
                    v_id = node_id_map.get(edge.dest)
                    if u_id is not None and v_id is not None:
                        edges_data.append({"u": u_id, "v": v_id, "w": edge.weight})

        data = {
            "graph": {
                "nodes": nodes_data, "edges": edges_data,
                "node_counter": self.graph_manager.node_counter
            },
            "matrix": self.matrix_widget.get_data()
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def load_exercise(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "JSON Files (*.json)")
        if not file_path: return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.clear_all()

            g_data = data.get("graph", {})
            self.graph_manager.node_counter = g_data.get("node_counter", 0)

            id_map = {}
            for n in g_data.get("nodes", []):
                node = self.graph_manager.create_node(QPointF(n["x"], n["y"]), n["name"])
                id_map[n["id"]] = node

            for e in g_data.get("edges", []):
                u, v = id_map.get(e["u"]), id_map.get(e["v"])
                if u and v:
                    self.graph_manager.create_edge(u, v, e.get("w", ""))

            self.matrix_widget.set_data(data.get("matrix", []))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark Theme Palette
    p = app.palette()
    p.setColor(p.ColorRole.Window, QColor(53, 53, 53))
    p.setColor(p.ColorRole.WindowText, Qt.white)
    p.setColor(p.ColorRole.Base, QColor(25, 25, 25))
    p.setColor(p.ColorRole.AlternateBase, QColor(53, 53, 53))
    p.setColor(p.ColorRole.ToolTipBase, Qt.white)
    p.setColor(p.ColorRole.ToolTipText, Qt.white)
    p.setColor(p.ColorRole.Text, Qt.white)
    p.setColor(p.ColorRole.Button, QColor(53, 53, 53))
    p.setColor(p.ColorRole.ButtonText, Qt.white)
    p.setColor(p.ColorRole.Highlight, QColor(42, 130, 218))
    p.setColor(p.ColorRole.HighlightedText, Qt.black)
    app.setPalette(p)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())