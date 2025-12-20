from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from src.logic.tools import SelectionTool, CreationTool


class EditorCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(0, 0, 800, 600)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)

        # Включаем отслеживание мыши (для Hover)
        self.setMouseTracking(True)

        self.tools = {
            "select": SelectionTool(self),
            "rect": CreationTool(self, "rect"),
            "line": CreationTool(self, "line"),
            "ellipse": CreationTool(self, "ellipse")
        }
        self.current_tool = self.tools["select"]

    def set_tool(self, tool_name):
        self.current_tool = self.tools.get(tool_name, self.tools["select"])
        # Смена курсора при переключении
        if tool_name == "select":
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    # Делегирование
    def mousePressEvent(self, event):
        self.current_tool.mouse_press(event)

    def mouseMoveEvent(self, event):
        self.current_tool.mouse_move(event)

    def mouseReleaseEvent(self, event):
        self.current_tool.mouse_release(event)

    def group_selection(self):
        items = self.scene.selectedItems()
        if len(items) < 2: return

        group = Group()
        self.scene.addItem(group)  # Сначала группу на сцену
        for item in items:
            item.setSelected(False)
            group.addToGroup(item)  # Qt сам пересчитает координаты!
        group.setSelected(True)

    def ungroup_selection(self):
        for item in self.scene.selectedItems():
            if isinstance(item, Group):
                self.scene.destroyGroup(item)
