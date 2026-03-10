import json

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QFrame,
                               QFileDialog, QMessageBox)
from src.logic.factory import ShapeFactory
from src.logic.strategies import JsonSaveStrategy, ImageSaveStrategy
from src.widgets.canvas import EditorCanvas
from src.widgets.properties import PropertiesPanel


class VectorEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vector Editor")
        self.resize(800, 600)

        # Состояние приложения (из 1-3)
        self.current_tool = "line"

        self._setup_layout()
        self._init_ui()

    def _init_ui(self):
        # 1. Меню и Actions (из 1-2)
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        # 2. Кнопка ОТКРЫТЬ
        open_action = QAction("Open Project", self)
        open_action.setShortcut("Ctrl+O")
        # Связываем кнопку с нашим методом из Модуля 7
        open_action.triggered.connect(self.on_open_clicked)
        file_menu.addAction(open_action)

        # 3. Кнопка СОХРАНИТЬ
        save_action = QAction("Save As...", self)
        save_action.setShortcut("Ctrl+S")
        # Связываем кнопку с нашим методом из Модуля 7
        save_action.triggered.connect(self.on_save_clicked)
        file_menu.addAction(save_action)

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 2. Тулбар (из 1-2)
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.addAction(exit_action)

        # В MainWindow._init_ui
        stack = self.canvas.undo_stack
        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(stack.createUndoAction(self, "Undo"))
        edit_menu.addAction(stack.createRedoAction(self, "Redo"))

        # Кнопка Delete
        delete_action = QAction("Delete", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.canvas.delete_selected)
        self.addAction(delete_action)

        # 3. Строка состояния (из 1-1)
        self.statusBar().showMessage("Готов к работе")

    def _setup_layout(self):
        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QHBoxLayout(container)

        # Левая панель инструментов
        tools_panel = QFrame()
        tools_panel.setFixedWidth(120)
        tools_layout = QVBoxLayout(tools_panel)

        # 1. ДОБАВЛЯЕМ КНОПКУ ВЫДЕЛЕНИЯ (СТРЕЛКУ)
        self.btn_select = QPushButton("SELECT")  # Наша новая кнопка
        self.btn_line = QPushButton("Line")
        self.btn_rect = QPushButton("Rect")
        self.btn_ellipse = QPushButton("Ellipse")

        # Список для удобной настройки
        tool_buttons = [
            (self.btn_select, "select"),
            (self.btn_line, "line"),
            (self.btn_rect, "rect"),
            (self.btn_ellipse, "ellipse")
        ]

        for btn, t_name in tool_buttons:
            btn.setCheckable(True)
            # При клике вызываем переключение инструмента
            btn.clicked.connect(lambda chk=False, name=t_name: self.on_change_tool(name))
            tools_layout.addWidget(btn)

        self.btn_select.setChecked(True)  # По умолчанию выбрана стрелка
        tools_layout.addStretch()

        self.canvas = EditorCanvas()

        # Создаем панель свойств и передаем ей сцену холста
        self.props_panel = PropertiesPanel(self.canvas.scene)

        # Добавляем в основной лейаут (третьим элементом)
        main_layout.addWidget(tools_panel)
        main_layout.addWidget(self.canvas)
        main_layout.addWidget(self.props_panel)

    def on_change_tool(self, tool_name):
        self.current_tool = tool_name

        # Визуально отжимаем все кнопки и нажимаем нужную
        self.btn_select.setChecked(tool_name == "select")
        self.btn_line.setChecked(tool_name == "line")
        self.btn_rect.setChecked(tool_name == "rect")
        self.btn_ellipse.setChecked(tool_name == "ellipse")

        # Сообщаем холсту, какой инструмент теперь главный
        self.canvas.set_tool(tool_name)
        self.statusBar().showMessage(f"Активный инструмент: {tool_name}")

    def on_save_clicked(self):
        filters = "Vector Project (*.json);;PNG Image (*.png)"
        path, selected_filter = QFileDialog.getSaveFileName(self, "Сохранить", "", filters)

        if not path: return

        # Паттерн Стратегия в действии
        strategy = ImageSaveStrategy() if path.endswith(".png") else JsonSaveStrategy()

        try:
            strategy.save(path, self.canvas.scene)
            self.statusBar().showMessage(f"Успешно сохранено: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def on_open_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть", "", "Vector Project (*.json)")
        if not path: return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # СБРОС (Reset)
            self.canvas.scene.clear()
            self.canvas.undo_stack.clear()

            # ЗАГРУЗКА
            for shape_data in data.get("shapes", []):
                shape = ShapeFactory.from_dict(shape_data)
                self.canvas.scene.addItem(shape)

            self.statusBar().showMessage(f"Проект загружен: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки", str(e))
