# frontend.py
import tkinter as tk
from tkinter import font, messagebox
import math
import collections
import backend


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Интерактивный решатель задачи 1 ЕГЭ")
        self.geometry("1100x700")

        # --- Стили ---
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(size=10)
        self.header_font = font.Font(family="Arial", size=12, weight="bold")
        self.result_font = font.Font(family="Courier", size=14, weight="bold")

        # --- Основная структура окна ---
        main_pane = tk.PanedWindow(self, sashrelief=tk.RAISED, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Левая панель для ввода данных
        left_frame = tk.Frame(main_pane)
        self._create_input_widgets(left_frame)
        main_pane.add(left_frame, minsize=480)

        # Правая панель для визуализации и результата
        right_frame = tk.Frame(main_pane)
        self._create_output_widgets(right_frame)
        main_pane.add(right_frame, minsize=500)

        # --- Инициализация состояния ---
        self.checkbox_vars = []
        self.dimension = 0
        self.node_positions = {}

        # Генерация сетки по умолчанию
        self.dimension_spinbox.invoke('buttonup')  # Установим 7 для примера
        self.dimension_spinbox.invoke('buttonup')
        self.after(100, self.draw_graph_from_text)  # Первичная отрисовка графа из примера

    def _create_input_widgets(self, parent):
        """Создает все виджеты для ввода данных на левой панели."""
        parent.columnconfigure(0, weight=1)

        # 1. Настройка размерности
        dim_frame = tk.Frame(parent)
        dim_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tk.Label(dim_frame, text="1. Размерность таблицы:", font=self.header_font).pack(side=tk.LEFT)
        self.dimension_spinbox = tk.Spinbox(dim_frame, from_=2, to=12, width=5, command=self.generate_matrix_grid)
        self.dimension_spinbox.pack(side=tk.LEFT, padx=10)
        self.dimension_spinbox.delete(0, "end")
        self.dimension_spinbox.insert(0, "6")

        # 2. Сетка для матрицы
        tk.Label(parent, text="2. Расставьте связи (звёздочки):", font=self.header_font).grid(row=1, column=0,
                                                                                              sticky="w")
        self.matrix_frame = tk.Frame(parent, relief=tk.SOLID, borderwidth=1)
        self.matrix_frame.grid(row=2, column=0, sticky="ew", pady=5)

        # 3. Ввод графа (буквы)
        graph_frame = tk.Frame(parent)
        graph_frame.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        parent.rowconfigure(3, weight=1)  # Позволяем этому фрейму расширяться

        graph_label_frame = tk.Frame(graph_frame)
        graph_label_frame.pack(fill="x")
        tk.Label(graph_label_frame, text="3. Рёбра графа (напр. A-B):", font=self.header_font).pack(side="left")

        update_graph_button = tk.Button(graph_label_frame, text="Обновить граф", command=self.draw_graph_from_text)
        update_graph_button.pack(side="right")

        self.edges_text = tk.Text(graph_frame, height=5, relief=tk.SOLID, borderwidth=1)
        self.edges_text.pack(fill="both", expand=True, pady=5)
        self.edges_text.insert("1.0", "А-Б\nБ-В\nБ-Г\nВ-Г\nГ-Д\nД-Е")  # Пример

        # 4. Ввод искомых вершин
        target_frame = tk.Frame(parent)
        target_frame.grid(row=4, column=0, sticky="ew", pady=10)
        tk.Label(target_frame, text="4. Искомые вершины:", font=self.header_font).pack(side=tk.LEFT)
        self.targets_entry = tk.Entry(target_frame, relief=tk.SOLID, borderwidth=1)
        self.targets_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.targets_entry.insert(0, "А, Е")  # Пример

        # 5. Кнопки Очистки
        clear_buttons_frame = tk.Frame(parent)
        clear_buttons_frame.grid(row=5, column=0, sticky="ew")
        tk.Button(clear_buttons_frame, text="Очистить всё", command=self.clear_all).pack(side="right")

    def _create_output_widgets(self, parent):
        """Создает холст для рисования и поле для вывода результата."""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        tk.Label(parent, text="Визуализация графа по текстовому описанию", font=self.header_font).grid(row=0, column=0,
                                                                                                       pady=(0, 10))
        self.canvas = tk.Canvas(parent, bg="white", relief=tk.SOLID, borderwidth=1)
        self.canvas.grid(row=1, column=0, sticky="nsew")

        solve_button = tk.Button(parent, text="Найти ответ", font=self.header_font, bg="#4CAF50", fg="white",
                                 command=self.solve_problem)
        solve_button.grid(row=2, column=0, sticky="ew", pady=(10, 5), ipady=5)

        self.result_label = tk.Label(parent, text="...", font=self.result_font, bg="lightgrey", relief=tk.RIDGE,
                                     padx=10, pady=5)
        self.result_label.grid(row=3, column=0, sticky="ew", ipady=5)
        self.canvas.bind("<Configure>", lambda e: self.draw_graph_from_text())

    def generate_matrix_grid(self):
        """Генерирует сетку из чекбоксов для ввода матрицы."""
        try:
            new_dim = int(self.dimension_spinbox.get())
            if new_dim == self.dimension: return
        except ValueError:
            return

        self.dimension = new_dim
        for widget in self.matrix_frame.winfo_children():
            widget.destroy()

        self.checkbox_vars = [[tk.BooleanVar(value=False) for _ in range(self.dimension)] for _ in
                              range(self.dimension)]

        for i in range(self.dimension + 1):
            self.matrix_frame.grid_columnconfigure(i, weight=1)
            self.matrix_frame.grid_rowconfigure(i, weight=1)
            for j in range(self.dimension + 1):
                if i == 0 and j == 0: continue
                if i == 0:
                    tk.Label(self.matrix_frame, text=f"П{j}", font=("Arial", 10, "bold")).grid(row=i, column=j,
                                                                                               sticky="nsew")
                elif j == 0:
                    tk.Label(self.matrix_frame, text=f"П{i}", font=("Arial", 10, "bold")).grid(row=i, column=j,
                                                                                               sticky="nsew")
                else:
                    row, col = i - 1, j - 1
                    if row == col:
                        tk.Frame(self.matrix_frame, bg="lightgrey").grid(row=i, column=j, sticky="nsew", padx=1, pady=1)
                    else:
                        var = self.checkbox_vars[row][col]
                        cb = tk.Checkbutton(self.matrix_frame, variable=var,
                                            command=lambda r=row, c=col: self.sync_checkboxes(r, c))
                        # Нижний треугольник делаем неактивным для наглядности
                        if col < row:
                            cb.configure(state=tk.DISABLED)
                        cb.grid(row=i, column=j, sticky="nsew")

    def sync_checkboxes(self, r, c):
        """Синхронизирует состояние симметричных чекбоксов."""
        val = self.checkbox_vars[r][c].get()
        self.checkbox_vars[c][r].set(val)

    def draw_graph_from_text(self):
        """Рисует граф на холсте на основе текстового поля с ребрами."""
        self.canvas.delete("all")

        try:
            adj_list, nodes = backend._parse_edges(self.edges_text.get("1.0", tk.END))
        except (ValueError, IndexError):
            self.canvas.create_text(10, 10, anchor="nw", text="Ошибка в формате ребер...", fill="red",
                                    font=("Arial", 12))
            return

        if not nodes: return

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        center_x, center_y = width / 2, height / 2
        radius = min(width, height) * 0.4
        node_radius = 16

        # 1. Вычисляем координаты вершин по кругу
        self.node_positions = {}
        for i, node_name in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes) - math.pi / 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            self.node_positions[node_name] = (x, y)

        # 2. Рисуем рёбра
        for u, neighbors in adj_list.items():
            for v in neighbors:
                # Рисуем каждое ребро только один раз
                if u < v:
                    p1 = self.node_positions.get(u)
                    p2 = self.node_positions.get(v)
                    if p1 and p2:
                        self.canvas.create_line(p1, p2, fill="gray", width=2, tags="edge")

        # 3. Рисуем вершины
        for name, (x, y) in self.node_positions.items():
            self.canvas.create_oval(x - node_radius, y - node_radius, x + node_radius, y + node_radius,
                                    fill="lightblue", outline="black", width=2, tags="node")
            self.canvas.create_text(x, y, text=name, font=("Arial", 12, "bold"), tags="node_label")

    def clear_all(self):
        """Очищает все поля ввода."""
        self.edges_text.delete("1.0", tk.END)
        self.targets_entry.delete(0, tk.END)
        for row in self.checkbox_vars:
            for var in row:
                var.set(False)
        self.result_label.config(text="...", bg="lightgrey", fg="black")
        self.draw_graph_from_text()

    def solve_problem(self):
        """Собирает данные, вызывает backend и показывает результат."""
        matrix_rows = []
        for r in range(self.dimension):
            row_str = ["1" if self.checkbox_vars[r][c].get() else "0" for c in range(self.dimension)]
            matrix_rows.append(" ".join(row_str))
        matrix_str = "\n".join(matrix_rows)

        edges_str = self.edges_text.get("1.0", tk.END)
        targets_str = self.targets_entry.get()

        if not matrix_str.strip() or not edges_str.strip() or not targets_str.strip():
            self.update_result("Заполните все поля!", is_error=True)
            return

        result = backend.solve(matrix_str, edges_str, targets_str)

        if "ошибка" in result.lower():
            self.update_result(result, is_error=True)
        else:
            self.update_result(f"Ответ: {result}", is_error=False)

    def update_result(self, text, is_error=False):
        """Обновляет текстовое поле с результатом, меняя цвет."""
        if is_error:
            self.result_label.config(text=text, bg="#FFCDD2", fg="#D32F2F")  # red
        else:
            self.result_label.config(text=text, bg="#C8E6C9", fg="#388E3C")  # green


if __name__ == "__main__":
    app = App()
    app.mainloop()
