from abc import ABC, abstractmethod

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView
from src.logic.factory import ShapeFactory


class Tool(ABC):
    def __init__(self, view):
        self.view = view
        self.scene = view.scene

    @abstractmethod
    def mouse_press(self, event): pass

    @abstractmethod
    def mouse_move(self, event): pass

    @abstractmethod
    def mouse_release(self, event): pass


class SelectionTool(Tool):
    def mouse_press(self, event):
        # Пробрасываем событие стандартному Qt для выделения/движения
        QGraphicsView.mousePressEvent(self.view, event)
        # Если кликнули по фигуре - сжимаем кулак
        if self.view.itemAt(event.pos()):
            self.view.setCursor(Qt.ClosedHandCursor)

    def mouse_move(self, event):
        QGraphicsView.mouseMoveEvent(self.view, event)
        # Эффект наведения (Hover)
        if not (event.buttons() & Qt.LeftButton):
            if self.view.itemAt(event.pos()):
                self.view.setCursor(Qt.OpenHandCursor)
            else:
                self.view.setCursor(Qt.ArrowCursor)

    def mouse_release(self, event):
        QGraphicsView.mouseReleaseEvent(self.view, event)
        self.view.setCursor(Qt.ArrowCursor)


class CreationTool(Tool):
    def __init__(self, view, shape_type):
        super().__init__(view)
        self.shape_type = shape_type
        self.temp_shape = None
        self.start_pos = None

    def mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = self.view.mapToScene(event.pos())
            # Сразу создаем фигуру через фабрику
            self.temp_shape = ShapeFactory.create_shape(
                self.shape_type, self.start_pos, self.start_pos, "black"
            )
            self.scene.addItem(self.temp_shape)

    def mouse_move(self, event):
        if self.temp_shape:
            current_pos = self.view.mapToScene(event.pos())
            self.temp_shape.set_geometry(self.start_pos, current_pos)

    def mouse_release(self, event):
        self.temp_shape = None
        self.start_pos = None
