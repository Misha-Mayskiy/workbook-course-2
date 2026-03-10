import pytest
from PySide6.QtCore import QPointF
from src.logic.factory import ShapeFactory


def test_rect_normalization():
    start, end = QPointF(100, 100), QPointF(10, 10)
    rect = ShapeFactory.create_shape("rect", start, end, "black")

    # Теперь проверяем нашу внутреннюю переменную
    assert rect._x == 10
    assert rect._w == 90