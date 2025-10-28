import sys
import time
from typing import List, Optional
from PyQt6 import QtWidgets, QtCore, QtGui

from backend import GameRules, EGESolver


def compress_ranges(nums: List[int]) -> str:
    """Сжать список чисел в диапазоны: [1,2,3,7,9,10] -> '1–3, 7, 9–10'."""
    if not nums:
        return ""
    nums = sorted(set(nums))
    ranges = []
    start = prev = nums[0]
    for x in nums[1:]:
        if x == prev + 1:
            prev = x
            continue
        if start == prev:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}–{prev}")
        start = prev = x
    if start == prev:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}–{prev}")
    return ", ".join(ranges)


class IntListEditor(QtWidgets.QWidget):
    """Удобный редактор списка целых чисел с добавлением/удалением/сбросом."""
    valuesChanged = QtCore.pyqtSignal()

    def __init__(self, title: str, placeholder: str, default: List[int], min_val: int = 1,
                 forbid_value: Optional[int] = None, tooltip: str = ""):
        super().__init__()
        self.min_val = min_val
        self.forbid_value = forbid_value

        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel(title)
        if tooltip:
            lbl.setToolTip(tooltip)
        header.addWidget(lbl)
        header.addStretch(1)
        layout.addLayout(header)

        line_layout = QtWidgets.QHBoxLayout()
        self.edit = QtWidgets.QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setValidator(QtGui.QIntValidator(0, 1_000_000_000, self))
        btn_add = QtWidgets.QPushButton("Добавить")
        btn_add.setAutoDefault(False)
        btn_clear = QtWidgets.QToolButton()
        btn_clear.setText("Сброс")
        btn_clear.setToolTip("Очистить список")

        line_layout.addWidget(self.edit, 2)
        line_layout.addWidget(btn_add, 1)
        line_layout.addWidget(btn_clear)
        layout.addLayout(line_layout)

        self.listw = QtWidgets.QListWidget()
        self.listw.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listw.setToolTip("Двойной клик — удалить. Delete — удалить выбранные. Enter в поле — добавить.")
        layout.addWidget(self.listw)

        btn_row = QtWidgets.QHBoxLayout()
        self.btn_del = QtWidgets.QPushButton("Удалить выбранные")
        self.btn_del.setAutoDefault(False)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_del)
        layout.addLayout(btn_row)

        btn_add.clicked.connect(self._on_add)
        btn_clear.clicked.connect(self.clear)
        self.btn_del.clicked.connect(self._on_delete_selected)
        self.listw.itemDoubleClicked.connect(self._on_item_double)
        # Добавление по Enter
        self.edit.returnPressed.connect(self._on_add)

        self.set_values(default)

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        if e.key() == QtCore.Qt.Key.Key_Delete:
            self._on_delete_selected()
        else:
            super().keyPressEvent(e)

    def _on_add(self):
        text = self.edit.text().strip()
        if not text:
            return
        try:
            v = int(text)
        except ValueError:
            return
        if v < self.min_val:
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), f"Значение должно быть ≥ {self.min_val}")
            return
        if self.forbid_value is not None and v == self.forbid_value:
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), f"Значение {v} недопустимо")
            return
        if v in self.values():
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), f"{v} уже есть в списке")
            return
        self.listw.addItem(str(v))
        self.edit.clear()
        self.valuesChanged.emit()

    def _on_delete_selected(self):
        for it in self.listw.selectedItems():
            row = self.listw.row(it)
            self.listw.takeItem(row)
        self.valuesChanged.emit()

    def _on_item_double(self, item: QtWidgets.QListWidgetItem):
        row = self.listw.row(item)
        self.listw.takeItem(row)
        self.valuesChanged.emit()

    def values(self) -> List[int]:
        vals = []
        for i in range(self.listw.count()):
            vals.append(int(self.listw.item(i).text()))
        return vals

    def set_values(self, vals: List[int]):
        self.listw.clear()
        for v in sorted(set(vals)):
            if v < self.min_val:
                continue
            if self.forbid_value is not None and v == self.forbid_value:
                continue
            self.listw.addItem(str(v))
        self.valuesChanged.emit()

    def clear(self):
        self.listw.clear()
        self.valuesChanged.emit()


class SolveWorker(QtCore.QObject):
    started = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(int, int)  # i, total
    finished = QtCore.pyqtSignal(list, list, list, float)
    error = QtCore.pyqtSignal(str)

    def __init__(self, rules: GameRules, start_template, s_min: int, s_max: int, parent=None):
        super().__init__(parent)
        self.rules = rules
        self.start_template = start_template
        self.s_min = s_min
        self.s_max = s_max
        self._cancelled = False

    @QtCore.pyqtSlot()
    def cancel(self):
        self._cancelled = True

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.started.emit()
            solver = EGESolver(self.rules, self.start_template, self.s_min, self.s_max)

            def cb_progress(i: int, total: int):
                self.progress.emit(i, total)

            def cb_cancel() -> bool:
                return self._cancelled

            t0 = time.perf_counter()
            s19, s20, s21 = solver.solve_all(progress_cb=cb_progress, cancel_cb=cb_cancel)
            dt = time.perf_counter() - t0
            if self._cancelled:
                raise RuntimeError("Расчёт отменён пользователем")
            self.finished.emit(s19, s20, s21, dt)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЕГЭ 19–21 Solver — удобный интерфейс")
        self.resize(1000, 760)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main = QtWidgets.QVBoxLayout(central)

        # — Заголовок и пресеты
        top_row = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Анализатор игр (ЕГЭ 19–21)")
        f = title.font()
        f.setPointSize(12)
        f.setBold(True)
        title.setFont(f)
        top_row.addWidget(title)
        top_row.addStretch(1)

        top_row.addWidget(QtWidgets.QLabel("Пресет:"))
        self.cb_preset = QtWidgets.QComboBox()
        self.cb_preset.addItems([
            "— Пользовательский —",
            "Лашин №24310: две кучи, (5, S), sum ≥ 154, ходы +1, ×3, S∈[1;130]",
        ])
        btn_apply_preset = QtWidgets.QToolButton()
        btn_apply_preset.setText("Применить")
        btn_apply_preset.setToolTip("Применить выбранный пресет к полям")
        top_row.addWidget(self.cb_preset)
        top_row.addWidget(btn_apply_preset)
        main.addLayout(top_row)

        # — Режим: количество куч
        mode_box = QtWidgets.QGroupBox("Режим")
        mode_layout = QtWidgets.QHBoxLayout(mode_box)
        self.rb_one = QtWidgets.QRadioButton("Одна куча")
        self.rb_two = QtWidgets.QRadioButton("Две кучи")
        self.rb_two.setChecked(True)
        self.rb_one.setToolTip("Игровое состояние — одна куча: (S)")
        self.rb_two.setToolTip("Игровое состояние — две кучи: (фикс., S)")
        mode_layout.addWidget(self.rb_one)
        mode_layout.addWidget(self.rb_two)
        mode_layout.addStretch(1)
        main.addWidget(mode_box)

        # — Цель игры
        goal_box = QtWidgets.QGroupBox("Цель игры")
        goal_layout = QtWidgets.QFormLayout(goal_box)
        self.cb_goal_mode = QtWidgets.QComboBox()
        self.cb_goal_mode.addItems(["sum", "max", "heap"])
        self.cb_goal_mode.setToolTip(
            "sum — игра кончается, когда сумма куч ≥ порога\n"
            "max — когда любая куча ≥ порога\n"
            "heap — когда конкретная куча ≥ порога (ниже укажите индекс)"
        )
        self.sp_target = QtWidgets.QSpinBox()
        self.sp_target.setRange(1, 1_000_000_000)
        self.sp_target.setValue(154)
        self.sp_target.setToolTip("Порог завершения: игра кончается при достижении ≥ этого числа")
        self.cb_heap_index = QtWidgets.QComboBox()
        self.cb_heap_index.addItems(["0", "1"])
        self.cb_heap_index.setEnabled(False)
        self.cb_heap_index.setToolTip("Номер кучи при типе цели 'heap' (0 — первая, 1 — вторая)")

        goal_layout.addRow("Тип цели:", self.cb_goal_mode)
        goal_layout.addRow("Порог (≥):", self.sp_target)
        goal_layout.addRow("heap_index:", self.cb_heap_index)
        main.addWidget(goal_box)

        # — Ходы
        moves_box = QtWidgets.QGroupBox("Разрешённые ходы (за ход меняется ровно одна куча)")
        moves_layout = QtWidgets.QHBoxLayout(moves_box)
        self.ed_adds = IntListEditor(
            "Добавления:",
            "например: 1",
            default=[1],
            min_val=1,
            forbid_value=None,
            tooltip="Список допустимых прибавлений (например, +1, +3). Должны быть ≥ 1."
        )
        self.ed_mults = IntListEditor(
            "Множители:",
            "например: 3",
            default=[3],
            min_val=2,
            forbid_value=1,
            tooltip="Список допустимых множителей (например, ×2, ×3). Значение 1 запрещено."
        )
        moves_layout.addWidget(self.ed_adds, 1)
        moves_layout.addWidget(self.ed_mults, 1)
        main.addWidget(moves_box)

        # — Стартовые параметры
        start_box = QtWidgets.QGroupBox("Старт позиции")
        start_layout = QtWidgets.QGridLayout(start_box)

        self.lbl_fixed = QtWidgets.QLabel("Камней в 1-й (фикс.) куче:")
        self.sp_fixed = QtWidgets.QSpinBox()
        self.sp_fixed.setRange(0, 1_000_000_000)
        self.sp_fixed.setValue(5)
        self.sp_fixed.setToolTip("Размер фиксированной кучи (для режима 'две кучи')")

        start_layout.addWidget(self.lbl_fixed, 0, 0)
        start_layout.addWidget(self.sp_fixed, 0, 1)

        start_layout.addWidget(QtWidgets.QLabel("Диапазон S: от"), 1, 0)
        self.sp_smin = QtWidgets.QSpinBox()
        self.sp_smin.setRange(0, 1_000_000_000)
        self.sp_smin.setValue(1)
        start_layout.addWidget(self.sp_smin, 1, 1)
        start_layout.addWidget(QtWidgets.QLabel("до"), 1, 2)
        self.sp_smax = QtWidgets.QSpinBox()
        self.sp_smax.setRange(0, 1_000_000_000)
        self.sp_smax.setValue(130)
        start_layout.addWidget(self.sp_smax, 1, 3)

        hint = QtWidgets.QLabel("Подсказка: при одной куче старт — (S). При двух — (фикс., S).")
        hint.setStyleSheet("color: gray;")
        start_layout.addWidget(hint, 2, 0, 1, 4)

        main.addWidget(start_box)

        # — Кнопки управления + прогресс
        actions = QtWidgets.QHBoxLayout()
        self.btn_calc = QtWidgets.QPushButton("Рассчитать")
        self.btn_calc.setDefault(True)
        self.btn_cancel = QtWidgets.QPushButton("Отмена")
        self.btn_cancel.setEnabled(False)
        self.btn_copy_all = QtWidgets.QPushButton("Скопировать итоги")
        self.btn_reset = QtWidgets.QPushButton("Сброс")
        actions.addWidget(self.btn_calc)
        actions.addWidget(self.btn_cancel)
        actions.addWidget(self.btn_copy_all)
        actions.addStretch(1)
        actions.addWidget(self.btn_reset)
        main.addLayout(actions)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(True)
        main.addWidget(self.progress)

        # — Результаты во вкладках
        tabs = QtWidgets.QTabWidget()
        self.tab_summary = QtWidgets.QWidget()
        self.tab_lists = QtWidgets.QWidget()
        tabs.addTab(self.tab_summary, "Итоги")
        tabs.addTab(self.tab_lists, "Списки S")
        main.addWidget(tabs, 1)

        # Итоги
        sum_layout = QtWidgets.QFormLayout(self.tab_summary)
        self.out19 = QtWidgets.QLabel("—")
        self.out20 = QtWidgets.QLabel("—")
        self.out21 = QtWidgets.QLabel("—")
        mono = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
        self.out19.setFont(mono)
        self.out20.setFont(mono)
        self.out21.setFont(mono)
        sum_layout.addRow("Задание 19:", self.out19)
        sum_layout.addRow("Задание 20:", self.out20)
        sum_layout.addRow("Задание 21:", self.out21)

        # Полные списки
        lists_layout = QtWidgets.QGridLayout(self.tab_lists)
        self.txt19 = QtWidgets.QPlainTextEdit()
        self.txt20 = QtWidgets.QPlainTextEdit()
        self.txt21 = QtWidgets.QPlainTextEdit()
        for t in (self.txt19, self.txt20, self.txt21):
            t.setReadOnly(True)
            t.setFont(mono)

        def header_with_copy(title, which: int):
            w = QtWidgets.QWidget()
            h = QtWidgets.QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            lab = QtWidgets.QLabel(title)
            btn = QtWidgets.QToolButton()
            btn.setText("Копировать")
            btn.clicked.connect(lambda: self.copy_list(which))
            h.addWidget(lab)
            h.addStretch(1)
            h.addWidget(btn)
            return w

        lists_layout.addWidget(header_with_copy("Задание 19 — все S:", 19), 0, 0)
        lists_layout.addWidget(self.txt19, 1, 0)
        lists_layout.addWidget(header_with_copy("Задание 20 — все S:", 20), 0, 1)
        lists_layout.addWidget(self.txt20, 1, 1)
        lists_layout.addWidget(header_with_copy("Задание 21 — все S:", 21), 0, 2)
        lists_layout.addWidget(self.txt21, 1, 2)
        lists_layout.setColumnStretch(0, 1)
        lists_layout.setColumnStretch(1, 1)
        lists_layout.setColumnStretch(2, 1)

        # — Сигналы
        self.rb_one.toggled.connect(self._on_heaps_change)
        self.cb_goal_mode.currentTextChanged.connect(self._on_goal_mode_change)
        btn_apply_preset.clicked.connect(self._apply_selected_preset)
        self.btn_calc.clicked.connect(self.on_calc)
        self.btn_cancel.clicked.connect(self.on_cancel)
        self.btn_reset.clicked.connect(self.on_reset)
        self.btn_copy_all.clicked.connect(self.copy_summary)

        # начальные состояния
        self._on_goal_mode_change(self.cb_goal_mode.currentText())
        self._on_heaps_change()

        # Стили
        self._apply_styles()

        # Загрузка настроек
        self._load_settings()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._save_settings()
        super().closeEvent(event)

    def _apply_styles(self):
        self.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                margin-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 8px;
            }
            QTextEdit, QPlainTextEdit, QListWidget {
                background: #f8f9fb;
            }
            QProgressBar {
                text-align: center;
            }
        """)

    def _load_settings(self):
        s = QtCore.QSettings("ege-tools", "game-19-21-solver")
        self.rb_two.setChecked(s.value("heaps", 2, int) == 2)
        self.rb_one.setChecked(s.value("heaps", 2, int) == 1)
        self.cb_goal_mode.setCurrentText(s.value("goal_mode", "sum"))
        self.sp_target.setValue(int(s.value("target", 154)))
        self.cb_heap_index.setCurrentIndex(int(s.value("heap_index", 0)))
        self.ed_adds.set_values([int(x) for x in s.value("adds", "1").split(",") if x.strip().isdigit()])
        self.ed_mults.set_values([int(x) for x in s.value("mults", "3").split(",") if x.strip().isdigit()])
        self.sp_fixed.setValue(int(s.value("fixed", 5)))
        self.sp_smin.setValue(int(s.value("smin", 1)))
        self.sp_smax.setValue(int(s.value("smax", 130)))

    def _save_settings(self):
        s = QtCore.QSettings("ege-tools", "game-19-21-solver")
        s.setValue("heaps", 2 if self.rb_two.isChecked() else 1)
        s.setValue("goal_mode", self.cb_goal_mode.currentText())
        s.setValue("target", self.sp_target.value())
        s.setValue("heap_index", self.cb_heap_index.currentIndex())
        s.setValue("adds", ",".join(map(str, self.ed_adds.values() or [1])))
        s.setValue("mults", ",".join(map(str, self.ed_mults.values() or [3])))
        s.setValue("fixed", self.sp_fixed.value())
        s.setValue("smin", self.sp_smin.value())
        s.setValue("smax", self.sp_smax.value())

    def _on_heaps_change(self):
        two = self.rb_two.isChecked()
        self.lbl_fixed.setEnabled(two)
        self.sp_fixed.setEnabled(two)
        self.cb_heap_index.clear()
        if two:
            self.cb_heap_index.addItems(["0", "1"])
        else:
            self.cb_heap_index.addItems(["0"])

    def _on_goal_mode_change(self, mode: str):
        self.cb_heap_index.setEnabled(mode == "heap")

    def _apply_selected_preset(self):
        name = self.cb_preset.currentText()
        if "Лашин №24310" in name:
            self.rb_two.setChecked(True)
            self.cb_goal_mode.setCurrentText("sum")
            self.sp_target.setValue(154)
            self.ed_adds.set_values([1])
            self.ed_mults.set_values([3])
            self.sp_fixed.setValue(5)
            self.sp_smin.setValue(1)
            self.sp_smax.setValue(130)
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), "Пресет применён")
        else:
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), "Выбран пользовательский режим")

    def _collect_rules(self) -> GameRules:
        heaps = 1 if self.rb_one.isChecked() else 2
        target_mode = self.cb_goal_mode.currentText()
        target = self.sp_target.value()
        heap_index = int(self.cb_heap_index.currentText()) if target_mode == "heap" else None

        adds = self.ed_adds.values()
        mults = self.ed_mults.values()
        if not adds and not mults:
            raise ValueError("Нужно указать хотя бы одно действие (добавление или множитель).")
        mults = [m for m in mults if m != 1]

        return GameRules(
            target_mode=target_mode,
            target=target,
            heap_index=heap_index,
            adds=adds,
            mults=mults,
            heaps=heaps
        )

    def _collect_start_template(self):
        if self.rb_one.isChecked():
            return (None,)
        else:
            return (self.sp_fixed.value(), None)

    def on_calc(self):
        try:
            rules = self._collect_rules()
            s_min = min(self.sp_smin.value(), self.sp_smax.value())
            s_max = max(self.sp_smin.value(), self.sp_smax.value())
            start_template = self._collect_start_template()

            # Запускаем расчёт в потоке
            self._set_busy(True, "Подготовка...")
            self.worker_thread = QtCore.QThread(self)
            self.worker = SolveWorker(rules, start_template, s_min, s_max)
            self.worker.moveToThread(self.worker_thread)

            self.worker.started.connect(lambda: self._set_busy(True, "Считаем..."))
            self.worker.progress.connect(self._on_progress)
            self.worker.finished.connect(self._on_finished)
            self.worker.error.connect(self._on_error)
            self.worker_thread.started.connect(self.worker.run)

            # Авто-очистка
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)

            self.worker_thread.start()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка", str(e))

    def on_cancel(self):
        if hasattr(self, "worker"):
            self.worker.cancel()
            self._set_busy(True, "Отмена...")

    def _set_busy(self, busy: bool, text: str = ""):
        self.progress.setVisible(busy)
        self.btn_calc.setEnabled(not busy)
        self.btn_cancel.setEnabled(busy)
        if busy:
            self.progress.setRange(0, 0)  # до первого апдейта прогресса
            self.progress.setFormat(text)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.progress.setFormat("")

    def _on_progress(self, i: int, total: int):
        if self.progress.maximum() != total:
            self.progress.setRange(0, total)
        self.progress.setValue(i)
        self.progress.setFormat(f"Идёт расчёт... {i}/{total} ({(i / total * 100):.0f}%)")

    def _on_finished(self, s19: List[int], s20: List[int], s21: List[int], dt: float):
        self._set_busy(False)
        # Итоги
        s19_min = min(s19) if s19 else None
        s20_two = sorted(s20)[:2]
        s21_max = max(s21) if s21 else None

        sum19 = f"минимальное S = {s19_min}   | всего: {len(s19)}" if s19_min is not None else "нет подходящих S"
        sum20 = f"два наименьших S = {s20_two} | всего: {len(s20)}" if s20 else "нет подходящих S"
        sum21 = f"наибольшее S = {s21_max}     | всего: {len(s21)}" if s21_max is not None else "нет подходящих S"

        self.out19.setText(sum19)
        self.out20.setText(sum20)
        self.out21.setText(sum21)

        def format_list(nums: List[int]) -> str:
            nums_sorted = sorted(nums)
            return f"Сжато: {compress_ranges(nums_sorted)}\n\nПолный список:\n{', '.join(map(str, nums_sorted))}" if nums_sorted else "—"

        self.txt19.setPlainText(format_list(s19))
        self.txt20.setPlainText(format_list(s20))
        self.txt21.setPlainText(format_list(s21))

        self.statusBar().showMessage(f"Готово за {dt:.3f} сек. Найдено: 19={len(s19)}, 20={len(s20)}, 21={len(s21)}",
                                     8000)

    def _on_error(self, msg: str):
        self._set_busy(False)
        if msg == "CANCELLED" or "отмен" in msg.lower():
            self.statusBar().showMessage("Расчёт отменён пользователем.", 5000)
        else:
            QtWidgets.QMessageBox.critical(self, "Ошибка", msg)

    def copy_list(self, which: int):
        if which == 19:
            txt = self.txt19.toPlainText()
        elif which == 20:
            txt = self.txt20.toPlainText()
        else:
            txt = self.txt21.toPlainText()
        QtWidgets.QApplication.clipboard().setText(txt)
        self.statusBar().showMessage("Списки скопированы в буфер обмена.", 4000)

    def copy_summary(self):
        s = []
        s.append("Итоги")
        s.append(f"19: {self.out19.text()}")
        s.append(f"20: {self.out20.text()}")
        s.append(f"21: {self.out21.text()}")
        QtWidgets.QApplication.clipboard().setText("\n".join(s))
        self.statusBar().showMessage("Итоги скопированы в буфер обмена.", 4000)

    def on_reset(self):
        self.cb_preset.setCurrentIndex(0)
        self.rb_two.setChecked(True)
        self.cb_goal_mode.setCurrentText("sum")
        self.sp_target.setValue(154)
        self.cb_heap_index.setCurrentIndex(0)
        self.ed_adds.set_values([1])
        self.ed_mults.set_values([3])
        self.sp_fixed.setValue(5)
        self.sp_smin.setValue(1)
        self.sp_smax.setValue(130)

        self.out19.setText("—")
        self.out20.setText("—")
        self.out21.setText("—")
        self.txt19.clear()
        self.txt20.clear()
        self.txt21.clear()
        self.statusBar().clearMessage()


def main():
    app = QtWidgets.QApplication(sys.argv)
    # Системный стиль + хорошая палитра по умолчанию
    QtWidgets.QApplication.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
