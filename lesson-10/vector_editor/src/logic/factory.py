from __future__ import annotations

from PySide6.QtCore import QPointF
from src.logic.shapes import Shape, Rectangle, Line, Ellipse, Group


class ShapeFactory:
    """
    Фабрика для создания и восстановления фигур.
    Централизованно управляет логикой рождения объектов.
    """

    @staticmethod
    def create_shape(stype: str, start: QPointF, end: QPointF, color: str) -> Shape:
        """
        Создает новую фигуру на основе жеста мыши (для CreationTool).
        Здесь происходит нормализация (min/max/abs).
        """
        # Считаем базовые параметры для прямоугольных фигур
        x = min(start.x(), end.x())
        y = min(start.y(), end.y())
        w = abs(end.x() - start.x())
        h = abs(end.y() - start.y())

        if stype == "rect":
            return Rectangle(x, y, w, h, color)

        elif stype == "ellipse":
            return Ellipse(x, y, w, h, color)

        elif stype == "line":
            # Для линии нормализация не нужна, важны точки начала и конца
            return Line(start.x(), start.y(), end.x(), end.y(), color)

        raise ValueError(f"Неизвестный тип фигуры: {stype}")

    @staticmethod
    def from_dict(data: dict) -> Shape:
        """
        Восстанавливает фигуру или группу из словаря (для загрузки из JSON).
        РЕКУРСИВНЫЙ МЕТОД.
        """
        stype = data.get("type")

        if stype == "group":
            return ShapeFactory._create_group_from_dict(data)
        else:
            return ShapeFactory._create_primitive_from_dict(data)

    @staticmethod
    def _create_primitive_from_dict(data: dict) -> Shape:
        """Вспомогательный метод для простых фигур"""
        stype = data.get("type")
        props = data.get("props", {})
        color = props.get("color", "black")

        if stype == "rect":
            obj = Rectangle(props.get('x', 0), props.get('y', 0),
                            props.get('w', 0), props.get('h', 0), color)
        elif stype == "ellipse":
            obj = Ellipse(props.get('x', 0), props.get('y', 0),
                          props.get('w', 0), props.get('h', 0), color)
        elif stype == "line":
            obj = Line(props.get('x1', 0), props.get('y1', 0),
                       props.get('x2', 0), props.get('y2', 0), color)
        else:
            raise ValueError(f"Невозможно восстановить фигуру типа: {stype}")

        # Важнейший момент Модуля 7: восстанавливаем смещение (pos)
        if "pos" in data:
            obj.setPos(data["pos"][0], data["pos"][1])

        return obj

    @staticmethod
    def _create_group_from_dict(data: dict) -> Group:
        """Вспомогательный метод для рекурсивного восстановления группы"""
        group = Group()

        # 1. Сначала ставим позицию самой группы
        if "pos" in data:
            group.setPos(data["pos"][0], data["pos"][1])

        # 2. Восстанавливаем детей (РЕКУРСИЯ)
        for child_data in data.get("children", []):
            child_obj = ShapeFactory.from_dict(child_data)
            # addToGroup сам позаботится о координатах ребенка
            group.addToGroup(child_obj)

        return group
