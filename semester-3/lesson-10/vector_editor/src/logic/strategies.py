import json
from abc import ABC, abstractmethod

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter


class SaveStrategy(ABC):
    @abstractmethod
    def save(self, filename, scene): pass


class JsonSaveStrategy(SaveStrategy):
    def save(self, filename, scene):
        data = {
            "version": "1.0",
            "scene": {"width": scene.width(), "height": scene.height()},
            "shapes": []
        }
        # Сохраняем от нижних слоев к верхним
        items = scene.items()[::-1]
        for item in items:
            if hasattr(item, "to_dict"):
                data["shapes"].append(item.to_dict())

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


class ImageSaveStrategy(SaveStrategy):
    def __init__(self, fmt="PNG"):
        self.fmt = fmt

    def save(self, filename, scene):
        rect = scene.sceneRect()
        image = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
        image.fill(Qt.white)  # Или прозрачным QColor(0,0,0,0)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        scene.render(painter, QRectF(image.rect()), rect)
        painter.end()
        image.save(filename, self.fmt)
