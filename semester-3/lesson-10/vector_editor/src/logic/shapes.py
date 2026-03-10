from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor, QPainterPath
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItemGroup


# --- БАЗОВЫЙ КЛАСС ---
class Shape(QGraphicsPathItem):
    def __init__(self, color: str = "black", stroke_width: int = 2):
        # Защита от создания экземпляра базового класса
        if self.__class__ == Shape:
            raise TypeError("Нельзя создавать экземпляры класса Shape напрямую!")
        super().__init__()
        self.color_name = color
        self.width = stroke_width
        self._setup_style()
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsMovable)

    def _setup_style(self):
        pen = QPen(QColor(self.color_name))
        pen.setWidth(self.width)
        self.setPen(pen)

    def set_active_color(self, color: str):
        self.color_name = color
        self._setup_style()

    def set_geometry(self, start_point: QPointF, end_point: QPointF):
        raise NotImplementedError("Реализуйте в подклассе")

    def to_dict(self) -> dict:
        # Сохраняем общие свойства: тип, позицию в Qt и цвет
        return {
            "type": self.type_name,
            "pos": [self.x(), self.y()],
            "props": {"color": self.color_name}
        }

    def set_stroke_width(self, width: int):
        self.width = width
        self._setup_style()


# --- КЛАСС ГРУППЫ (Composite) ---

class Group(QGraphicsItemGroup, Shape):
    def __init__(self):
        # Важно: вызываем конструкторы обоих родителей вручную
        QGraphicsItemGroup.__init__(self)
        self.color_name = "multiple"
        self.width = 2

        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable)
        self.setHandlesChildEvents(True)

    @property
    def type_name(self):
        return "group"

    def set_active_color(self, color: str):
        for child in self.childItems():
            if isinstance(child, Shape):
                child.set_active_color(color)

    def to_dict(self) -> dict:
        # Рекурсивно собираем данные всех детей
        children_data = [child.to_dict() for child in self.childItems() if isinstance(child, Shape)]
        d = Shape.to_dict(self)  # Берем базовые поля (type, pos)
        d["children"] = children_data
        return d

    def set_geometry(self, start, end):
        pass

    def set_stroke_width(self, width: int):
        for child in self.childItems():
            if isinstance(child, Shape):
                child.set_stroke_width(width)


# --- КОНКРЕТНЫЕ ФИГУРЫ ---

class Rectangle(Shape):
    def __init__(self, x, y, w, h, color="black"):
        super().__init__(color)
        # Добавляем подчеркивание, чтобы не конфликтовать с Qt
        self._x, self._y, self._w, self._h = x, y, w, h
        self._create_geometry()

    def set_geometry(self, start_point, end_point):
        self._x = min(start_point.x(), end_point.x())
        self._y = min(start_point.y(), end_point.y())
        self._w = abs(end_point.x() - start_point.x())
        self._h = abs(end_point.y() - start_point.y())
        self._create_geometry()

    def _create_geometry(self):
        path = QPainterPath()
        path.addRect(self._x, self._y, self._w, self._h)
        self.setPath(path)

    @property
    def type_name(self): return "rect"

    def to_dict(self):
        d = super().to_dict()
        d["props"].update({"x": self._x, "y": self._y, "w": self._w, "h": self._h})
        return d


class Ellipse(Shape):
    def __init__(self, x, y, w, h, color="black"):
        super().__init__(color)
        self.set_geometry(QPointF(x, y), QPointF(x + w, y + h))

    @property
    def type_name(self): return "ellipse"

    def set_geometry(self, start, end):
        x, y = min(start.x(), end.x()), min(start.y(), end.y())
        w, h = abs(end.x() - start.x()), abs(end.y() - start.y())
        path = QPainterPath()
        path.addEllipse(x, y, w, h)
        self.setPath(path)

    def to_dict(self):
        d = super().to_dict()
        r = self.path().boundingRect()
        d["props"].update({"x": r.x(), "y": r.y(), "w": r.width(), "h": r.height()})
        return d


class Line(Shape):
    def __init__(self, x1, y1, x2, y2, color="black"):
        super().__init__(color)
        self.set_geometry(QPointF(x1, y1), QPointF(x2, y2))

    @property
    def type_name(self): return "line"

    def set_geometry(self, start, end):
        path = QPainterPath()
        path.moveTo(start)
        path.lineTo(end)
        self.setPath(path)

    def to_dict(self):
        d = super().to_dict()
        p = self.path()
        # Для линии сохраняем две точки
        d["props"].update({
            "x1": p.elementAt(0).x, "y1": p.elementAt(0).y,
            "x2": p.elementAt(1).x, "y2": p.elementAt(1).y
        })
        return d
