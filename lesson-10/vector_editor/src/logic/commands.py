from PySide6.QtGui import QUndoCommand


class AddShapeCommand(QUndoCommand):
    def __init__(self, scene, item):
        super().__init__()
        self.scene, self.item = scene, item
        self.setText(f"Добавить {item.type_name}")

    def redo(self):
        if self.item.scene() != self.scene:
            self.scene.addItem(self.item)

    def undo(self):
        self.scene.removeItem(self.item)


class MoveCommand(QUndoCommand):
    def __init__(self, item, old_pos, new_pos):
        super().__init__()
        self.item, self.old_pos, self.new_pos = item, old_pos, new_pos
        self.setText(f"Переместить {item.type_name}")

    def redo(self): self.item.setPos(self.new_pos)

    def undo(self): self.item.setPos(self.old_pos)


class DeleteCommand(QUndoCommand):
    def __init__(self, scene, item):
        super().__init__()
        self.scene, self.item = scene, item
        self.setText(f"Удалить {item.type_name}")

    def redo(self): self.scene.removeItem(self.item)

    def undo(self): self.scene.addItem(self.item)


class ChangeColorCommand(QUndoCommand):
    def __init__(self, item, new_color):
        super().__init__()
        self.item, self.new_color = item, new_color
        self.old_color = item.color_name if hasattr(item, 'color_name') else "black"
        self.setText(f"Изменить цвет на {new_color}")

    def redo(self): self.item.set_active_color(self.new_color)

    def undo(self): self.item.set_active_color(self.old_color)
