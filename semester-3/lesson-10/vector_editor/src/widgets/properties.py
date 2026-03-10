from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QSpinBox, QDoubleSpinBox, QPushButton, QColorDialog)
from src.logic.shapes import Shape


class PropertiesPanel(QWidget):
    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self._init_ui()
        self.scene.selectionChanged.connect(self.on_selection_changed)

    def _init_ui(self):
        self.setFixedWidth(220)
        self.setStyleSheet("background-color: #f8f8f8; border-left: 1px solid #ddd;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        # Заголовок и Тип объекта
        self.lbl_type = QLabel("Свойства")
        self.lbl_type.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        layout.addWidget(self.lbl_type)

        # 1. Позиция X и Y
        layout.addWidget(QLabel("Позиция (X, Y):"))
        pos_layout = QHBoxLayout()
        self.spin_x = self._create_double_spin(pos_layout, "X")
        self.spin_y = self._create_double_spin(pos_layout, "Y")
        layout.addLayout(pos_layout)

        # 2. Толщина
        layout.addWidget(QLabel("Толщина линии:"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 20)
        self.spin_width.valueChanged.connect(self.on_width_ui_changed)
        layout.addWidget(self.spin_width)

        # 3. Цвет
        layout.addWidget(QLabel("Цвет:"))
        self.btn_color = QPushButton("Выбрать цвет")
        self.btn_color.clicked.connect(self.on_color_clicked)
        layout.addWidget(self.btn_color)

        layout.addStretch()
        self.setEnabled(False)  # Выключена, пока ничего не выбрали

    def _create_double_spin(self, layout, prefix):
        spin = QDoubleSpinBox()
        spin.setRange(-2000, 2000)
        spin.setPrefix(f"{prefix}: ")
        spin.valueChanged.connect(self.on_geo_ui_changed)
        layout.addWidget(spin)
        return spin

    # --- ЛОГИКА: ИЗ МОДЕЛИ В ИНТЕРФЕЙС ---
    def on_selection_changed(self):
        items = self.scene.selectedItems()
        if not items:
            self.setEnabled(False)
            self.lbl_type.setText("Ничего не выбрано")
            return

        self.setEnabled(True)
        item = items[0]  # Берем первый выделенный объект

        # Интроспекция: узнаем тип
        name = item.type_name.capitalize() if hasattr(item, 'type_name') else "Объект"
        self.lbl_type.setText(f"Тип: {name}")

        # Блокируем сигналы, чтобы не зациклиться
        self.spin_x.blockSignals(True)
        self.spin_y.blockSignals(True)
        self.spin_width.blockSignals(True)

        self.spin_x.setValue(item.x())
        self.spin_y.setValue(item.y())
        if hasattr(item, 'pen'):
            self.spin_width.setValue(item.pen().width())
            color = item.pen().color().name()
            self.btn_color.setStyleSheet(f"background-color: {color}; border: 1px solid #999;")

        self.spin_x.blockSignals(False)
        self.spin_y.blockSignals(False)
        self.spin_width.blockSignals(False)

    def on_width_ui_changed(self, value):
        for item in self.scene.selectedItems():
            if hasattr(item, 'set_stroke_width'):
                item.set_stroke_width(value)

    def on_geo_ui_changed(self, _):
        for item in self.scene.selectedItems():
            item.setPos(self.spin_x.value(), self.spin_y.value())

    def on_color_clicked(self):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_c = color.name()
            items = self.scene.selectedItems()
            if items:
                self.undo_stack.beginMacro("Смена цвета")
                for item in items:
                    self.undo_stack.push(ChangeColorCommand(item, hex_c))
                self.undo_stack.endMacro()
            self.on_selection_changed()
