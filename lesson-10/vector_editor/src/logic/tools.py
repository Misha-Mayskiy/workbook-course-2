from abc import ABC, abstractmethod

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView
from src.logic.commands import AddShapeCommand, MoveCommand
from src.logic.factory import ShapeFactory


class Tool(ABC):
    def __init__(self, view):
        self.view = view
        self.scene = view.scene
        self.start_pos = None

    @abstractmethod
    def mouse_press(self, event): pass

    @abstractmethod
    def mouse_move(self, event): pass

    @abstractmethod
    def mouse_release(self, event): pass


class SelectionTool(Tool):
    def __init__(self, view, undo_stack):
        super().__init__(view)
        self.undo_stack = undo_stack
        self.item_positions = {}

    def mouse_press(self, event):
        # Пробрасываем стандартное выделение Qt
        QGraphicsView.mousePressEvent(self.view, event)
        # Запоминаем, где стояли предметы ДО того, как мы их потащили
        self.item_positions = {i: i.pos() for i in self.scene.selectedItems()}

    def mouse_move(self, event):
        QGraphicsView.mouseMoveEvent(self.view, event)
        # Логика курсора "руки"
        if not (event.buttons() & Qt.LeftButton):
            if self.view.itemAt(event.pos()):
                self.view.setCursor(Qt.OpenHandCursor)
            else:
                self.view.setCursor(Qt.ArrowCursor)

    def mouse_release(self, event):
        QGraphicsView.mouseReleaseEvent(self.view, event)

        # Проверяем: кто-нибудь реально сдвинулся?
        moved = []
        for item, old_pos in self.item_positions.items():
            if item.pos() != old_pos:
                moved.append((item, old_pos, item.pos()))

        # Если были сдвиги - создаем одну общую команду (Макрос)
        if moved:
            self.undo_stack.beginMacro("Перемещение")
            for item, old, new in moved:
                self.undo_stack.push(MoveCommand(item, old, new))
            self.undo_stack.endMacro()

        self.view.setCursor(Qt.ArrowCursor)
        self.item_positions.clear()


# 3. ИНСТРУМЕНТ СОЗДАНИЯ
class CreationTool(Tool):
    def __init__(self, view, shape_type, undo_stack):
        super().__init__(view)
        self.shape_type = shape_type
        self.undo_stack = undo_stack
        self.temp_shape = None

    def mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = self.view.mapToScene(event.pos())
            # Создаем черновик
            self.temp_shape = ShapeFactory.create_shape(
                self.shape_type, self.start_pos, self.start_pos, "black"
            )
            self.scene.addItem(self.temp_shape)

    def mouse_move(self, event):
        if self.temp_shape:
            current_pos = self.view.mapToScene(event.pos())
            self.temp_shape.set_geometry(self.start_pos, current_pos)

    def mouse_release(self, event):
        if self.temp_shape:
            # Сначала удаляем черновик
            self.scene.removeItem(self.temp_shape)
            final_shape = self.temp_shape
            self.temp_shape = None

            # Отдаем команду на добавление в стек
            command = AddShapeCommand(self.scene, final_shape)
            self.undo_stack.push(command)

        self.start_pos = None
