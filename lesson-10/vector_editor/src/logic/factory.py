from src.logic.shapes import Rectangle, Line, Ellipse


class ShapeFactory:
    @staticmethod
    def create_shape(shape_type: str, start_point, end_point, color: str):
        x1, y1 = start_point.x(), start_point.y()
        x2, y2 = end_point.x(), end_point.y()

        if shape_type == 'line':
            return Line(x1, y1, x2, y2, color)

        # Нормализация для прямоугольных штук
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)

        if shape_type == 'rect':
            return Rectangle(x, y, w, h, color)
        elif shape_type == 'ellipse':
            return Ellipse(x, y, w, h, color)

        raise ValueError(f"Unknown tool: {shape_type}")

    @staticmethod
    def from_dict(data: dict):
        """Рекурсивное восстановление из JSON/Словаря"""
        stype = data.get("type")

        if stype == "group":
            group = Group()
            group.setPos(data["pos"][0], data["pos"][1])
            for child_data in data.get("children", []):
                child = ShapeFactory.from_dict(child_data)  # РЕКУРСИЯ
                group.addToGroup(child)
            return group

        # Для примитивов
        props = data.get("props", {})
        color = props.get("color", "black")

        if stype == "rect":
            obj = Rectangle(props['x'], props['y'], props['w'], props['h'], color)
        elif stype == "line":
            obj = Line(props['x1'], props['y1'], props['x2'], props['y2'], color)

        if "pos" in data:
            obj.setPos(data["pos"][0], data["pos"][1])
        return obj
