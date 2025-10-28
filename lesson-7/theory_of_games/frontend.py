import sys
import time
import json
import csv
import re
from typing import List, Optional, Tuple, Dict
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


def make_dark_palette() -> QtGui.QPalette:
    pal = QtGui.QPalette()
    pal.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(46, 46, 46))
    pal.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(230, 230, 230))
    pal.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(28, 28, 28))
    pal.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(46, 46, 46))
    pal.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(46, 46, 46))
    pal.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor(245, 245, 245))
    pal.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(235, 235, 235))
    pal.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(56, 56, 56))
    pal.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(235, 235, 235))
    pal.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor(255, 85, 85))
    pal.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(42, 130, 218))
    pal.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(255, 255, 255))
    pal.setColor(QtGui.QPalette.ColorRole.PlaceholderText, QtGui.QColor(170, 170, 170))
    return pal


def make_light_palette() -> QtGui.QPalette:
    pal = QtWidgets.QApplication.palette()
    pal.setColor(QtGui.QPalette.ColorRole.PlaceholderText, QtGui.QColor(120, 120, 120))
    return pal


class IntListEditor(QtWidgets.QWidget):
    """Редактор списка целых чисел с добавлением/удалением/сбросом."""
    valuesChanged = QtCore.pyqtSignal()

    def __init__(self, title: str, placeholder: str, default: List[int],
                 min_val: Optional[int] = None,
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
        # Разрешаем вводить и отрицательные, и положительные
        self.edit.setValidator(QtGui.QIntValidator(-1_000_000_000, 1_000_000_000, self))
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
        if self.min_val is not None and v < self.min_val:
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
            if self.min_val is not None and v < self.min_val:
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
        self.setWindowTitle("ЕГЭ 19–21 Solver")
        self.resize(1100, 850)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main = QtWidgets.QVBoxLayout(central)

        # — Заголовок, пресеты, тема
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
        self._fill_presets()
        btn_apply_preset = QtWidgets.QToolButton()
        btn_apply_preset.setText("Применить")
        btn_apply_preset.setToolTip("Применить выбранный пресет к полям")
        top_row.addWidget(self.cb_preset)
        top_row.addWidget(btn_apply_preset)

        top_row.addSpacing(16)
        top_row.addWidget(QtWidgets.QLabel("Тема:"))
        self.cb_theme = QtWidgets.QComboBox()
        self.cb_theme.addItems(["Светлая", "Тёмная"])
        top_row.addWidget(self.cb_theme)

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
            "sum — игра кончается, когда сумма куч сравнивается с порогом\n"
            "max — когда любая куча сравнивается с порогом\n"
            "heap — когда конкретная куча сравнивается с порогом (ниже укажите индекс)"
        )
        self.cb_finish_cmp = QtWidgets.QComboBox()
        self.cb_finish_cmp.addItems(["≥ (больше или равно порогу)", "< (меньше порога)"])
        self.sp_target = QtWidgets.QSpinBox()
        self.sp_target.setRange(1, 1_000_000_000)
        self.sp_target.setValue(154)
        self.cb_heap_index = QtWidgets.QComboBox()
        self.cb_heap_index.addItems(["0", "1"])
        self.cb_heap_index.setEnabled(False)

        goal_layout.addRow("Тип цели:", self.cb_goal_mode)
        goal_layout.addRow("Условие:", self.cb_finish_cmp)
        goal_layout.addRow("Порог:", self.sp_target)
        goal_layout.addRow("heap_index:", self.cb_heap_index)
        main.addWidget(goal_box)

        # — Ходы
        moves_box = QtWidgets.QGroupBox("Разрешённые ходы (за ход меняется ровно одна куча)")
        moves_layout = QtWidgets.QHBoxLayout(moves_box)
        self.ed_adds = IntListEditor(
            "Прибавления/вычитания:",
            "например: -4, 2",
            default=[1],
            min_val=None,
            forbid_value=None,
            tooltip="Список допустимых сдвигов: можно и положительные, и отрицательные. 0 смысла не имеет."
        )
        self.ed_mults = IntListEditor(
            "Множители:",
            "например: 3",
            default=[3],
            min_val=2,
            forbid_value=1,
            tooltip="Список допустимых множителей (например, ×2, ×3). Значение 1 запрещено."
        )
        self.ed_divs = IntListEditor(
            "Делители (целочислен. деление):",
            "например: 3",
            default=[],
            min_val=2,
            forbid_value=1,
            tooltip="Список допустимых делителей (например, ÷2, ÷3). Округление вниз."
        )
        moves_layout.addWidget(self.ed_adds, 1)
        moves_layout.addWidget(self.ed_mults, 1)
        moves_layout.addWidget(self.ed_divs, 1)
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

        # — Кнопки управления + прогресс + экспорт
        actions = QtWidgets.QHBoxLayout()
        self.btn_calc = QtWidgets.QPushButton("Рассчитать")
        self.btn_calc.setDefault(True)
        self.btn_cancel = QtWidgets.QPushButton("Отмена")
        self.btn_cancel.setEnabled(False)
        self.btn_copy_all = QtWidgets.QPushButton("Скопировать итоги")
        self.btn_export_json = QtWidgets.QPushButton("Экспорт JSON")
        self.btn_export_csv = QtWidgets.QPushButton("Экспорт CSV")
        self.btn_reset = QtWidgets.QPushButton("Сброс")
        actions.addWidget(self.btn_calc)
        actions.addWidget(self.btn_cancel)
        actions.addWidget(self.btn_copy_all)
        actions.addWidget(self.btn_export_json)
        actions.addWidget(self.btn_export_csv)
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
        self.tab_strategy = QtWidgets.QWidget()
        tabs.addTab(self.tab_summary, "Итоги")
        tabs.addTab(self.tab_lists, "Списки S")
        tabs.addTab(self.tab_strategy, "Стратегия")
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

        # Стратегии
        strat_layout = QtWidgets.QVBoxLayout(self.tab_strategy)
        controls = QtWidgets.QHBoxLayout()
        controls.addWidget(QtWidgets.QLabel("Задание:"))
        self.cb_task = QtWidgets.QComboBox()
        self.cb_task.addItems(["19", "20", "21"])
        controls.addWidget(self.cb_task)
        controls.addSpacing(10)
        controls.addWidget(QtWidgets.QLabel("S:"))
        self.cb_S = QtWidgets.QComboBox()
        self.cb_S.setMinimumWidth(140)
        controls.addWidget(self.cb_S)
        self.btn_show_strat = QtWidgets.QPushButton("Показать")
        self.btn_copy_strat = QtWidgets.QToolButton()
        self.btn_copy_strat.setText("Копировать")
        controls.addSpacing(10)
        controls.addWidget(self.btn_show_strat)
        controls.addWidget(self.btn_copy_strat)
        controls.addStretch(1)
        strat_layout.addLayout(controls)

        self.txt_strategy = QtWidgets.QPlainTextEdit()
        self.txt_strategy.setReadOnly(True)
        self.txt_strategy.setFont(mono)
        self.txt_strategy.setPlaceholderText("Сначала рассчитайте S, затем выберите задание и S.")
        strat_layout.addWidget(self.txt_strategy, 1)

        # — Сигналы
        self.rb_one.toggled.connect(self._on_heaps_change)
        self.cb_goal_mode.currentTextChanged.connect(self._on_goal_mode_change)
        btn_apply_preset.clicked.connect(self._apply_selected_preset)
        self.btn_calc.clicked.connect(self.on_calc)
        self.btn_cancel.clicked.connect(self.on_cancel)
        self.btn_reset.clicked.connect(self.on_reset)
        self.btn_copy_all.clicked.connect(self.copy_summary)
        self.btn_export_json.clicked.connect(self.export_json)
        self.btn_export_csv.clicked.connect(self.export_csv)

        self.cb_task.currentTextChanged.connect(self._on_task_change)
        self.btn_show_strat.clicked.connect(self.on_show_strategy)
        self.btn_copy_strat.clicked.connect(self.copy_strategy)
        self.cb_theme.currentTextChanged.connect(self._on_theme_change)

        # начальные состояния + стили
        self._apply_styles()
        self._on_goal_mode_change(self.cb_goal_mode.currentText())
        self._on_heaps_change()

        # Служебные поля
        self._last_results: Dict[int, List[int]] = {19: [], 20: [], 21: []}
        self._last_meta: Dict[str, object] = {}

        # Настройки + тема
        self._load_settings()
        theme_name = self._settings.value("theme", "Светлая")
        idx = 0 if theme_name == "Светлая" else 1
        self.cb_theme.setCurrentIndex(idx)
        self._apply_theme(theme_name)

    @property
    def _settings(self) -> QtCore.QSettings:
        return QtCore.QSettings("ege-tools", "game-19-21-solver")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._save_settings()
        super().closeEvent(event)

    def _apply_styles(self):
        # мягкие стили, чтобы не ломать темы
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
            QProgressBar { text-align: center; }
        """)

    def _fill_presets(self):
        self.cb_preset.clear()
        self.cb_preset.addItems([
            "— Пользовательский —",
            "ЕГЭ №24115: 1 куча (S), финиш ≥444, ходы +2, +5, ×3, S∈[1;400]",
            "ЕГЭ №18064: 1 куча (S), финиш <27, ходы −3, −4, ÷3, S∈[27;200]",
        ])

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
        if "№24115" in name:
            self.rb_one.setChecked(True)
            self.cb_goal_mode.setCurrentText("heap")
            self.cb_finish_cmp.setCurrentIndex(0)  # ≥
            self.sp_target.setValue(444)
            self.cb_heap_index.setCurrentIndex(0)
            self.ed_adds.set_values([2, 5])
            self.ed_mults.set_values([3])
            self.ed_divs.set_values([])
            self.sp_smin.setValue(1)
            self.sp_smax.setValue(400)
        elif "№18064" in name:
            self.rb_one.setChecked(True)
            self.cb_goal_mode.setCurrentText("heap")
            self.cb_finish_cmp.setCurrentIndex(1)  # <
            self.sp_target.setValue(27)
            self.cb_heap_index.setCurrentIndex(0)
            self.ed_adds.set_values([-4, -3])  # порядок не важен, список сортируется
            self.ed_mults.set_values([])
            self.ed_divs.set_values([3])
            self.sp_smin.setValue(27)
            self.sp_smax.setValue(200)
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), "Пресет применён")

    def _collect_rules(self) -> GameRules:
        heaps = 1 if self.rb_one.isChecked() else 2
        target_mode = self.cb_goal_mode.currentText()
        target = self.sp_target.value()
        heap_index = int(self.cb_heap_index.currentText()) if target_mode == "heap" else None
        finish_cmp = "ge" if self.cb_finish_cmp.currentIndex() == 0 else "lt"

        adds = self.ed_adds.values()
        mults = self.ed_mults.values()
        divs = self.ed_divs.values()
        if not adds and not mults and not divs:
            raise ValueError("Нужно указать хотя бы одно действие (сдвиг, множитель или делитель).")

        return GameRules(
            target_mode=target_mode,
            target=target,
            finish_cmp=finish_cmp,
            heap_index=heap_index,
            adds=adds,
            mults=mults,
            divs=divs,
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

            self._set_busy(True, "Подготовка...")
            self.worker_thread = QtCore.QThread(self)
            self.worker = SolveWorker(rules, start_template, s_min, s_max)
            self.worker.moveToThread(self.worker_thread)

            self.worker.started.connect(lambda: self._set_busy(True, "Считаем..."))
            self.worker.progress.connect(self._on_progress)
            self.worker.finished.connect(self._on_finished)
            self.worker.error.connect(self._on_error)
            self.worker_thread.started.connect(self.worker.run)

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
        self.btn_calc.setEnabled(busy) if False else self.btn_calc.setEnabled(not busy)
        self.btn_cancel.setEnabled(busy)
        if busy:
            self.progress.setRange(0, 0)
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
        rules = self._collect_rules()
        start_template = self._collect_start_template()
        s_min = min(self.sp_smin.value(), self.sp_smax.value())
        s_max = max(self.sp_smin.value(), self.sp_smax.value())
        self._last_results = {19: s19, 20: s20, 21: s21}
        self._last_meta = dict(
            rules=dict(
                target_mode=rules.target_mode,
                target=rules.target,
                finish_cmp=rules.finish_cmp,
                heap_index=rules.heap_index,
                adds=rules.adds,
                mults=rules.mults,
                divs=rules.divs,
                heaps=rules.heaps,
            ),
            start_template=start_template,
            s_min=s_min,
            s_max=s_max,
            elapsed=dt,
        )

        # Итоги: показываем и min, и max (удобно для разных формулировок)
        def mm(vals: List[int]) -> Tuple[Optional[int], Optional[int], int]:
            return (min(vals) if vals else None, max(vals) if vals else None, len(vals))

        s19_min, s19_max, n19 = mm(s19)
        s20_min, s20_max, n20 = mm(s20)
        s21_min, s21_max, n21 = mm(s21)

        self.out19.setText(
            f"min S = {s19_min if s19_min is not None else '—'} | "
            f"max S = {s19_max if s19_max is not None else '—'} | всего: {n19}"
        )
        self.out20.setText(
            f"min S = {s20_min if s20_min is not None else '—'} | "
            f"max S = {s20_max if s20_max is not None else '—'} | "
            f"два наименьших = {sorted(s20)[:2] if n20 >= 1 else '—'} | всего: {n20}"
        )
        self.out21.setText(
            f"max S = {s21_max if s21_max is not None else '—'} | всего: {n21}"
        )

        def format_list(nums: List[int]) -> str:
            nums_sorted = sorted(nums)
            return f"Сжато: {compress_ranges(nums_sorted)}\n\nПолный список:\n{', '.join(map(str, nums_sorted))}" if nums_sorted else "—"

        self.txt19.setPlainText(format_list(s19))
        self.txt20.setPlainText(format_list(s20))
        self.txt21.setPlainText(format_list(s21))

        self._refresh_strategy_inputs()

        self.statusBar().showMessage(
            f"Готово за {dt:.3f} сек. Найдено: 19={len(s19)}, 20={len(s20)}, 21={len(s21)}",
            8000
        )

    def _refresh_strategy_inputs(self):
        task = int(self.cb_task.currentText())
        vals = sorted(self._last_results.get(task, []))
        self.cb_S.clear()
        if vals:
            for v in vals:
                self.cb_S.addItem(str(v))
            self.btn_show_strat.setEnabled(True)
        else:
            self.cb_S.addItem("— нет подходящих S —")
            self.btn_show_strat.setEnabled(False)

    def _on_task_change(self, _txt: str):
        self._refresh_strategy_inputs()

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
        self.cb_finish_cmp.setCurrentIndex(0)
        self.sp_target.setValue(154)
        self.cb_heap_index.setCurrentIndex(0)
        self.ed_adds.set_values([1])
        self.ed_mults.set_values([3])
        self.ed_divs.set_values([])
        self.sp_fixed.setValue(5)
        self.sp_smin.setValue(1)
        self.sp_smax.setValue(130)

        self.out19.setText("—")
        self.out20.setText("—")
        self.out21.setText("—")
        self.txt19.clear()
        self.txt20.clear()
        self.txt21.clear()
        self.txt_strategy.clear()
        self._last_results = {19: [], 20: [], 21: []}
        self._last_meta = {}
        self._refresh_strategy_inputs()
        self.statusBar().clearMessage()

    # ---------- Экспорт ----------
    def export_json(self):
        if not any(self._last_results.values()):
            QtWidgets.QMessageBox.information(self, "Экспорт JSON", "Сначала выполните расчёт.")
            return
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить JSON", "results.json", "JSON (*.json)")
        if not fname:
            return
        payload = dict(
            meta=self._last_meta,
            results=dict(
                task19=self._last_results[19],
                task20=self._last_results[20],
                task21=self._last_results[21],
            )
        )
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        self.statusBar().showMessage(f"JSON сохранён: {fname}", 5000)

    def export_csv(self):
        if not any(self._last_results.values()):
            QtWidgets.QMessageBox.information(self, "Экспорт CSV", "Сначала выполните расчёт.")
            return
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить CSV", "results.csv", "CSV (*.csv)")
        if not fname:
            return
        s19, s20, s21 = (sorted(self._last_results[19]), sorted(self._last_results[20]), sorted(self._last_results[21]))
        L = max(len(s19), len(s20), len(s21))
        with open(fname, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["S19", "S20", "S21"])
            for i in range(L):
                row = [
                    s19[i] if i < len(s19) else "",
                    s20[i] if i < len(s20) else "",
                    s21[i] if i < len(s21) else "",
                ]
                w.writerow(row)
        self.statusBar().showMessage(f"CSV сохранён: {fname}", 5000)

    # ---------- Стратегии ----------
    def on_show_strategy(self):
        if not any(self._last_results.values()):
            QtWidgets.QMessageBox.information(self, "Стратегия", "Сначала выполните расчёт.")
            return
        task = int(self.cb_task.currentText())
        try:
            S = int(self.cb_S.currentText())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Стратегия", "Выберите корректное S.")
            return

        rules = self._collect_rules()
        start_template = self._collect_start_template()
        solver = EGESolver(rules, start_template, S, S)

        if task == 19:
            text = solver.sample_strategy_19(S)
        elif task == 20:
            text = solver.sample_strategy_20(S, limit_examples=6)
        else:
            text = solver.sample_strategy_21(S, limit_examples=6)

        if not text:
            self.txt_strategy.setPlainText("Для выбранного S и задания стратегию построить не удалось.\n"
                                           "Убедитесь, что S входит в соответствующий список.")
        else:
            self.txt_strategy.setPlainText(text)

    def copy_strategy(self):
        QtWidgets.QApplication.clipboard().setText(self.txt_strategy.toPlainText())
        self.statusBar().showMessage("Стратегия скопирована.", 4000)

    # ---------- Тема ----------
    def _on_theme_change(self, name: str):
        self._apply_theme(name)
        self._settings.setValue("theme", name)

    def _apply_theme(self, name: str):
        app = QtWidgets.QApplication.instance()
        if name == "Тёмная":
            app.setPalette(make_dark_palette())
            tooltip_css = (
                "QToolTip { color: #fff; background-color: #2f2f2f; "
                "border: 1px solid #5a5a5a; }"
            )
        else:
            app.setPalette(make_light_palette())
            tooltip_css = (
                "QToolTip { color: #000; background-color: #ffffe1; "
                "border: 1px solid #c5c5c5; }"
            )
        # Без QToolTip.setStyleSheet — стилизуем тултипы через stylesheet приложения
        base_css = app.styleSheet() or ""
        base_css = re.sub(r"QToolTip\s*\{[^}]*\}", "", base_css)
        app.setStyleSheet(base_css + "\n" + tooltip_css)
        self.update()

    # ---------- Настройки ----------
    def _load_settings(self):
        s = self._settings
        heaps_val = int(s.value("heaps", 2))
        self.rb_two.setChecked(heaps_val == 2)
        self.rb_one.setChecked(heaps_val == 1)
        self.cb_goal_mode.setCurrentText(s.value("goal_mode", "sum"))
        self.cb_finish_cmp.setCurrentIndex(0 if s.value("finish_cmp", "ge") == "ge" else 1)
        self.sp_target.setValue(int(s.value("target", 154)))
        self.cb_heap_index.setCurrentIndex(int(s.value("heap_index", 0)))
        self._safe_set_list(self.ed_adds, s.value("adds", "1"))
        self._safe_set_list(self.ed_mults, s.value("mults", "3"))
        self._safe_set_list(self.ed_divs, s.value("divs", ""))
        self.sp_fixed.setValue(int(s.value("fixed", 5)))
        self.sp_smin.setValue(int(s.value("smin", 1)))
        self.sp_smax.setValue(int(s.value("smax", 130)))

    def _safe_set_list(self, editor: IntListEditor, raw: object):
        try:
            vals = [int(x) for x in str(raw).split(",") if str(x).strip() and re.fullmatch(r"-?\d+", str(x).strip())]
            editor.set_values(vals)
        except Exception:
            editor.set_values([])

    def _save_settings(self):
        s = self._settings
        s.setValue("heaps", 2 if self.rb_two.isChecked() else 1)
        s.setValue("goal_mode", self.cb_goal_mode.currentText())
        s.setValue("finish_cmp", "ge" if self.cb_finish_cmp.currentIndex() == 0 else "lt")
        s.setValue("target", self.sp_target.value())
        s.setValue("heap_index", self.cb_heap_index.currentIndex())
        s.setValue("adds", ",".join(map(str, self.ed_adds.values())))
        s.setValue("mults", ",".join(map(str, self.ed_mults.values())))
        s.setValue("divs", ",".join(map(str, self.ed_divs.values())))
        s.setValue("fixed", self.sp_fixed.value())
        s.setValue("smin", self.sp_smin.value())
        s.setValue("smax", self.sp_smax.value())
        s.setValue("theme", self.cb_theme.currentText())


def main():
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QApplication.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
