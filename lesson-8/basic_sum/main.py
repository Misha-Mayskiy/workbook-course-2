import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from compiled_ui import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.calculate_sum)

    def calculate_sum(self):
        try:
            num1 = float(self.lineEdit.text())
            num2 = float(self.lineEdit_2.text())
            total_sum = num1 + num2
            self.label.setText(str(total_sum))

        except ValueError:
            self.label.setText("Ошибка ввода")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
