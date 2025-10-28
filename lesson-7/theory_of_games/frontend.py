import sys
from typing import List

from PyQt6 import QtWidgets

from backend import GameRules, EGESolver


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЕГЭ 19–21 Solver (PyQt6)")
        self.resize(800, 650)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Режим: 1 куча / 2 кучи
        mode_box = QtWidgets.QGroupBox("Режим")
        mode_layout = QtWidgets.QHBoxLayout(mode_box)
        self.rb_one = QtWidgets.QRadioButton("Одна куча")
        self.rb_two = QtWidgets.QRadioButton("Две кучи")
        self.rb_two.setChecked(True)
        mode_layout.addWidget(self.rb_one)
        mode_layout.addWidget(self.rb_two)
        layout.addWidget(mode_box)

        # Параметры цели
        goal_box = QtWidgets.QGroupBox("Цель игры")
        goal_layout = QtWidgets.QGridLayout(goal_box)

        goal_layout.addWidget(QtWidgets.QLabel("Тип цели:"), 0, 0)
        self.cb_goal_mode = QtWidgets.QComboBox()
        self.cb_goal_mode.addItems(["sum", "max", "heap"])
        self.cb_goal_mode.setCurrentText("sum")
        goal_layout.addWidget(self.cb_goal_mode, 0, 1)

        goal_layout.addWidget(QtWidgets.QLabel("Порог (≥):"), 0, 2)
        self.ed_target = QtWidgets.QLineEdit("154")
        goal_layout.addWidget(self.ed_target, 0, 3)

        goal_layout.addWidget(QtWidgets.QLabel("heap_index (для 'heap'):"), 0, 4)
        self.ed_heap_index = QtWidgets.QLineEdit("0")
        self.ed_heap_index.setEnabled(False)
        goal_layout.addWidget(self.ed_heap_index, 0, 5)

        # Включаем/выключаем поле heap_index в зависимости от выбранного режима
        self.cb_goal_mode.currentTextChanged.connect(
            lambda t: self.ed_heap_index.setEnabled(t == "heap")
        )

        layout.addWidget(goal_box)

        # Ходы
        moves_box = QtWidgets.QGroupBox("Разрешённые ходы (к одной куче за ход)")
        moves_layout = QtWidgets.QGridLayout(moves_box)

        moves_layout.addWidget(QtWidgets.QLabel("Добавления (через запятую):"), 0, 0)
        self.ed_adds = QtWidgets.QLineEdit("1")
        moves_layout.addWidget(self.ed_adds, 0, 1)

        moves_layout.addWidget(QtWidgets.QLabel("Множители (через запятую):"), 0, 2)
        self.ed_mults = QtWidgets.QLineEdit("3")
        moves_layout.addWidget(self.ed_mults, 0, 3)

        layout.addWidget(moves_box)

        # Стартовые параметры
        start_box = QtWidgets.QGroupBox("Старт позиции")
        start_layout = QtWidgets.QGridLayout(start_box)

        # Для 1 кучи: start_template = (None,), S∈[s_min, s_max]
        # Для 2 куч: start_template = (fixed, None), S во 2-й
        self.lbl_fixed = QtWidgets.QLabel("Камней в 1-й (фикс.) куче:")
        self.ed_fixed = QtWidgets.QLineEdit("5")
        start_layout.addWidget(self.lbl_fixed, 0, 0)
        start_layout.addWidget(self.ed_fixed, 0, 1)

        start_layout.addWidget(QtWidgets.QLabel("Диапазон S: от"), 1, 0)
        self.ed_smin = QtWidgets.QLineEdit("1")
        start_layout.addWidget(self.ed_smin, 1, 1)
        start_layout.addWidget(QtWidgets.QLabel("до"), 1, 2)
        self.ed_smax = QtWidgets.QLineEdit("130")
        start_layout.addWidget(self.ed_smax, 1, 3)

        layout.addWidget(start_box)

        # Кнопка
        self.btn_calc = QtWidgets.QPushButton("Рассчитать")
        layout.addWidget(self.btn_calc)

        # Результаты
        res_box = QtWidgets.QGroupBox("Результаты")
        res_layout = QtWidgets.QVBoxLayout(res_box)
        self.txt = QtWidgets.QTextEdit()
        self.txt.setReadOnly(True)
        res_layout.addWidget(self.txt)
        layout.addWidget(res_box)

        # Сигналы
        self.rb_one.toggled.connect(self._on_mode_change)
        self.btn_calc.clicked.connect(self.on_calc)

        self._on_mode_change()

    def _on_mode_change(self):
        if self.rb_one.isChecked():
            self.lbl_fixed.setEnabled(False)
            self.ed_fixed.setEnabled(False)
        else:
            self.lbl_fixed.setEnabled(True)
            self.ed_fixed.setEnabled(True)

    @staticmethod
    def _parse_int_list(s: str) -> List[int]:
        s = s.strip()
        if not s:
            return []
        return [int(x) for x in s.replace(";", ",").split(",") if x.strip()]

    def on_calc(self):
        try:
            # Считываем настройки
            heaps = 1 if self.rb_one.isChecked() else 2
            target_mode = self.cb_goal_mode.currentText()
            target = int(self.ed_target.text())
            heap_index = int(self.ed_heap_index.text()) if target_mode == "heap" else None

            adds = self._parse_int_list(self.ed_adds.text())
            mults = self._parse_int_list(self.ed_mults.text())
            if not adds and not mults:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Нужно указать хотя бы одно действие (adds или mults).")
                return

            s_min = int(self.ed_smin.text())
            s_max = int(self.ed_smax.text())
            if s_min > s_max:
                s_min, s_max = s_max, s_min

            if heaps == 1:
                start_tmpl = (None,)
            else:
                fixed = int(self.ed_fixed.text())
                start_tmpl = (fixed, None)

            rules = GameRules(
                target_mode=target_mode,
                target=target,
                heap_index=heap_index,
                adds=adds,
                mults=mults,
                heaps=heaps
            )

            solver = EGESolver(rules, start_tmpl, s_min, s_max)
            s19, s20, s21 = solver.solve_all()

            # Готовим красивые ответы:
            # 19: минимальное S
            s19_min = min(s19) if s19 else None
            # 20: два наименьших
            s20_sorted = sorted(s20)
            s20_two = s20_sorted[:2] if len(s20_sorted) >= 2 else s20_sorted
            # 21: максимальное
            s21_max = max(s21) if s21 else None

            out = ["— Задание 19:"]
            if s19_min is None:
                out.append("   Нет подходящих S в заданном диапазоне.")
            else:
                out.append(f"   Минимальное S: {s19_min}")
                out.append(f"   Все S: {s19}")

            out.append("")
            out.append("— Задание 20:")
            if not s20_two:
                out.append("   Нет подходящих S.")
            else:
                out.append(f"   Два наименьших S: {s20_two}")
                out.append(f"   Все S: {s20_sorted}")

            out.append("")
            out.append("— Задание 21:")
            if s21_max is None:
                out.append("   Нет подходящих S.")
            else:
                out.append(f"   Наибольшее S: {s21_max}")
                out.append(f"   Все S: {s21}")

            self.txt.setPlainText("\n".join(out))

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка", str(e))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
