import tkinter as tk


class Shape:
    """Базовый класс для всех фигур."""

    def __init__(self, color="black"):
        self.color = color

    def draw(self, canvas):
        raise NotImplementedError("Этот метод должен быть переопределен в дочернем классе")


class Point(Shape):
    """Класс для представления и отрисовки точки."""

    def __init__(self, x, y, color="black"):
        super().__init__(color)
        self.x = x
        self.y = y

    def draw(self, canvas):
        # Точка рисуется как маленький круг
        canvas.create_oval(self.x - 1, self.y - 1, self.x + 1, self.y + 1, fill=self.color, outline=self.color)


class LineDirect(Shape):
    """Класс для представления и отрисовки отрезка."""

    def __init__(self, start_point, end_point, color="black"):
        super().__init__(color)
        self.start_point = start_point
        self.end_point = end_point

    def draw(self, canvas):
        canvas.create_line(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y, fill=self.color)


class Quadrilateral(Shape):
    """Класс для представления и отрисовки четырехугольника."""

    def __init__(self, p1, p2, p3, p4, color="blue"):
        super().__init__(color)
        self.points = [p1, p2, p3, p4]

    def draw(self, canvas):
        coords = [c for p in self.points for c in (p.x, p.y)]
        canvas.create_polygon(coords, outline=self.color, fill='')


class Triangle(Shape):
    """Класс для представления и отрисовки треугольника."""

    def __init__(self, p1, p2, p3, color="red"):
        super().__init__(color)
        self.points = [p1, p2, p3]

    def draw(self, canvas):
        coords = [c for p in self.points for c in (p.x, p.y)]
        canvas.create_polygon(coords, outline=self.color, fill='')


class Circle(Shape):
    """Класс для представления и отрисовки круга."""

    def __init__(self, center, radius, color="green"):
        super().__init__(color)
        self.center = center
        self.radius = radius

    def draw(self, canvas):
        x0 = self.center.x - self.radius
        y0 = self.center.y - self.radius
        x1 = self.center.x + self.radius
        y1 = self.center.y + self.radius
        canvas.create_oval(x0, y0, x1, y1, outline=self.color)


class ShapeVisualizer(tk.Tk):
    """Основной класс приложения для визуализации фигур."""

    def __init__(self):
        super().__init__()
        self.title("Визуализация Геометрических Фигур")
        self.canvas = tk.Canvas(self, width=600, height=400, bg="white")
        self.canvas.pack(pady=20, padx=20)
        self.shapes = self.create_shapes()
        self.draw_shapes()

    @staticmethod
    def create_shapes():
        """Создает экземпляры различных геометрических фигур."""
        return [
            Point(50, 50),
            LineDirect(Point(100, 50), Point(250, 100)),
            Quadrilateral(Point(300, 50), Point(400, 20), Point(450, 80), Point(320, 120), color="purple"),
            Triangle(Point(50, 150), Point(150, 150), Point(100, 250)),
            Circle(Point(350, 250), 70, color="orange")
        ]

    def draw_shapes(self):
        """Отрисовывает все фигуры на холсте."""
        for shape in self.shapes:
            shape.draw(self.canvas)


if __name__ == "__main__":
    app = ShapeVisualizer()
    app.mainloop()
