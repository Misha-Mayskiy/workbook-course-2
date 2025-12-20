from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QUndoStack
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from src.logic.commands import AddShapeCommand, MoveCommand, DeleteCommand
from src.logic.shapes import Shape
from src.logic.tools import SelectionTool, CreationTool


class EditorCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(0, 0, 800, 600)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setMouseTracking(True)

        # 1. Сначала создаем стек истории
        self.undo_stack = QUndoStack(self)

        # 2. Передаем этот стек в КАЖДЫЙ инструмент (вторым или третьим аргументом)
        self.tools = {
            # Здесь теперь два аргумента: self и наш новый стек
            "select": SelectionTool(self, self.undo_stack),

            # Здесь теперь три аргумента: self, тип фигуры и наш стек
            "rect": CreationTool(self, "rect", self.undo_stack),
            "line": CreationTool(self, "line", self.undo_stack),
            "ellipse": CreationTool(self, "ellipse", self.undo_stack)
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

    def delete_selected(self):
        # 1. Берем список всего, что сейчас выделено
        selected = self.scene.selectedItems()
        if not selected:
            return

        # 2. Начинаем транзакцию (Макрос), чтобы удаление
        # группы объектов отменялось одним нажатием Ctrl+Z
        self.undo_stack.beginMacro("Delete Selection")

        for item in selected:
            # Проверяем, что это наша фигура
            if isinstance(item, Shape):
                # 3. Создаем команду удаления и пушим её в стек
                cmd = DeleteCommand(self.scene, item)
                self.undo_stack.push(cmd)

        self.undo_stack.endMacro()
