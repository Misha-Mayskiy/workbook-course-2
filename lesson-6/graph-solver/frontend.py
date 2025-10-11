# frontend.py
import tkinter as tk
from tkinter import ttk, font
import math
import random
import re
import collections
import backend


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Интерактивный решатель задачи 1 ЕГЭ")
        self.geometry("1200x800")
        self.minsize(1100, 700)

        # --- Стили и цвета ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.colors = {
            "bg": "#f0f0f0",
            "frame_bg": "#fafafa",
            "header": "#003366",
            "button": "#005a9c",
            "button_fg": "white",
            "success": "#2E7D32",
            "success_bg": "#E8F5E9",
            "error": "#C62828",
            "error_bg": "#FFEBEE",
        }
        self.configure(bg=self.colors['bg'])

        self.header_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=10)
        self.result_font = font.Font(family="Courier New", size=14, weight="bold")

        # --- Основная структура окна ---
        main_pane = tk.PanedWindow(self, sashrelief=tk.RAISED, orient=tk.HORIZONTAL, bg=self.colors['bg'])
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = self._create_left_panel(main_pane)
        main_pane.add(left_frame, minsize=520, width=550)

        right_frame = self._create_right_panel(main_pane)
        main_pane.add(right_frame, minsize=500)

        # --- Инициализация состояния ---
        self.matrix_widgets = []
        self.dimension = 0
        self.node_positions = {}

        self.after(50, self.on_mode_change)  # Первичная генерация

    def _create_left_panel(self, parent):
        frame = ttk.Frame(parent, padding=10)
        frame.columnconfigure(0, weight=1)
        settings_frame = ttk.LabelFrame(frame, text="1. Настройки", padding=10)
        settings_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        ttk.Label(settings_frame, text="Размерность:").grid(row=0, column=0, sticky="w")
        self.dimension_spinbox = ttk.Spinbox(settings_frame, from_=2, to=15, width=5, command=self.generate_matrix_grid)
        self.dimension_spinbox.set("7")
        self.dimension_spinbox.grid(row=0, column=1, sticky="w", padx=5)
        self.is_weighted_var = tk.BooleanVar(value=True)
        weighted_check = ttk.Checkbutton(settings_frame, text="Учитывать длины дорог (веса)",
                                         variable=self.is_weighted_var, command=self.on_mode_change)
        weighted_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        self.matrix_lf = ttk.LabelFrame(frame, text="2. Таблица длин", padding=10)
        self.matrix_lf.grid(row=1, column=0, sticky="ew", pady=5)
        self.matrix_frame = ttk.Frame(self.matrix_lf)
        self.matrix_frame.pack(fill="both", expand=True)
        graph_frame = ttk.LabelFrame(frame, text="3. Описание графа", padding=10)
        graph_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        frame.rowconfigure(2, weight=1)
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(1, weight=1)
        self.graph_label = ttk.Label(graph_frame, text="Рёбра графа (напр. A-B 15):", font=self.label_font)
        self.graph_label.grid(row=0, column=0, sticky="w")
        self.edges_text = tk.Text(graph_frame, height=8, relief=tk.SOLID, borderwidth=1, font=("Consolas", 10))
        self.edges_text.grid(row=1, column=0, sticky="nsew", pady=5)
        target_frame = ttk.LabelFrame(frame, text="4. Искомые вершины", padding=10)
        target_frame.grid(row=3, column=0, sticky="ew", pady=5)
        self.targets_entry = ttk.Entry(target_frame)
        self.targets_entry.pack(fill=tk.X, expand=True)
        return frame

    def _create_right_panel(self, parent):
        frame = ttk.Frame(parent, padding=10)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        vis_header_frame = ttk.Frame(frame)
        vis_header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(vis_header_frame, text="Визуализация графа", font=self.header_font,
                  foreground=self.colors['header']).pack(side="left")
        ttk.Button(vis_header_frame, text="Обновить граф", command=self.draw_graph).pack(side="right")
        self.canvas = tk.Canvas(frame, bg="white", relief=tk.SOLID, borderwidth=1, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda e: self.draw_graph())
        solve_button = ttk.Button(frame, text="НАЙТИ ОТВЕТ", style="Accent.TButton", command=self.solve_problem)
        self.style.configure("Accent.TButton", font=self.header_font, padding=10, background=self.colors['button'],
                             foreground=self.colors['button_fg'])
        solve_button.grid(row=2, column=0, sticky="ew", pady=(10, 5))
        self.result_label = ttk.Label(frame, text="...", font=self.result_font, padding=10, background="lightgrey",
                                      relief=tk.RIDGE, anchor="center")
        self.result_label.grid(row=3, column=0, sticky="ew")
        return frame

    def on_mode_change(self):
        is_weighted = self.is_weighted_var.get()
        self.edges_text.delete("1.0", tk.END)
        self.targets_entry.delete(0, tk.END)
        if is_weighted:
            self.matrix_lf.config(text="2. Таблица длин")
            self.graph_label.config(text="Рёбра графа (напр. A-B 15):")
            self.edges_text.insert("1.0", "А-Б 13\nА-В 7\nБ-В 6\nБ-Г 15\nВ-Д 10\nГ-Е 5\nД-Е 8\nД-Ж 9\nЕ-Ж 11")
            self.targets_entry.insert(0, "Г, Д")
        else:
            self.matrix_lf.config(text="2. Таблица связей (звёздочки)")
            self.graph_label.config(text="Рёбра графа (напр. A-B):")
            self.edges_text.insert("1.0", "А-Б\nБ-В\nБ-Г\nВ-Г\nГ-Д\nД-Е")
            self.targets_entry.insert(0, "А, Е")
        self.generate_matrix_grid()
        self.draw_graph()

    def generate_matrix_grid(self):
        try:
            new_dim = int(self.dimension_spinbox.get())
        except ValueError:
            return
        self.dimension = new_dim
        for widget in self.matrix_frame.winfo_children(): widget.destroy()
        self.matrix_widgets = [[None] * self.dimension for _ in range(self.dimension)]
        is_weighted = self.is_weighted_var.get()
        vcmd = (self.register(lambda P: P.isdigit() or P == ""), '%P')
        for i in range(self.dimension + 1):
            self.matrix_frame.grid_columnconfigure(i, weight=1, minsize=35)
            self.matrix_frame.grid_rowconfigure(i, weight=1)
            for j in range(self.dimension + 1):
                if i == 0 and j == 0: continue
                header_style = {'font': self.label_font, 'anchor': 'center'}
                if i == 0:
                    ttk.Label(self.matrix_frame, text=f"П{j}", **header_style).grid(row=i, column=j, sticky="nsew")
                elif j == 0:
                    ttk.Label(self.matrix_frame, text=f"П{i}", **header_style).grid(row=i, column=j, sticky="nsew")
                else:
                    r, c = i - 1, j - 1
                    if r == c:
                        ttk.Frame(self.matrix_frame, style='Disabled.TFrame').grid(row=i, column=j, sticky="nsew",
                                                                                   padx=1, pady=1)
                    elif is_weighted:
                        entry = ttk.Entry(self.matrix_frame, justify='center', validate='key', validatecommand=vcmd,
                                          width=4)
                        entry.grid(row=i, column=j, sticky="nsew", padx=1, pady=1)
                        entry.bind("<KeyRelease>", lambda e, ro=r, co=c: self.sync_entries(ro, co))
                        if c < r: entry.config(state=tk.DISABLED)
                        self.matrix_widgets[r][c] = entry
                    else:
                        var = tk.BooleanVar()
                        cb = ttk.Checkbutton(self.matrix_frame, variable=var,
                                             command=lambda ro=r, co=c: self.sync_checkboxes(ro, co))
                        if c < r: cb.config(state=tk.DISABLED)
                        cb.grid(row=i, column=j, sticky="nsew")
                        self.matrix_widgets[r][c] = var

    def sync_entries(self, r, c):
        source = self.matrix_widgets[r][c]
        target = self.matrix_widgets[c][r]
        target.config(state=tk.NORMAL)
        if target.get() != source.get():
            target.delete(0, tk.END)
            target.insert(0, source.get())
        target.config(state=tk.DISABLED)

    def sync_checkboxes(self, r, c):
        val = self.matrix_widgets[r][c].get()
        self.matrix_widgets[c][r].set(val)

    def _parse_graph_for_drawing(self):
        adj, nodes, weights = collections.defaultdict(list), set(), {}
        is_weighted = self.is_weighted_var.get()
        text = self.edges_text.get("1.0", tk.END)
        for line in text.strip().split('\n'):
            parts = [p for p in re.split(r'[\s,-]+', line.strip().upper()) if p]
            if len(parts) >= 2:
                u, v = parts[0], parts[1]
                adj[u].append(v);
                adj[v].append(u)
                nodes.add(u);
                nodes.add(v)
                if is_weighted and len(parts) > 2 and parts[2].isdigit():
                    weights[tuple(sorted((u, v)))] = parts[2]
        return adj, sorted(list(nodes)), weights

    def _calculate_force_directed_layout(self, adj, nodes, width, height):
        if not nodes: return {}
        pos = {node: (random.uniform(20, width - 20), random.uniform(20, height - 20)) for node in nodes}
        area = width * height
        k = 0.9 * math.sqrt(area / len(nodes))
        iterations = 80
        temp = width / 10.0
        for i in range(iterations):
            disp = {node: [0.0, 0.0] for node in nodes}
            for u in nodes:
                for v in nodes:
                    if u == v: continue
                    dx, dy = pos[u][0] - pos[v][0], pos[u][1] - pos[v][1]
                    dist = math.sqrt(dx * dx + dy * dy) + 0.0001
                    force = k * k / dist
                    disp[u][0] += dx / dist * force
                    disp[u][1] += dy / dist * force
            edges = []
            for u in nodes:
                for v in adj[u]:
                    if u < v: edges.append((u, v))
            for u, v in edges:
                dx, dy = pos[u][0] - pos[v][0], pos[u][1] - pos[v][1]
                dist = math.sqrt(dx * dx + dy * dy) + 0.0001
                force = dist * dist / k
                disp[u][0] -= dx / dist * force
                disp[u][1] -= dy / dist * force
                disp[v][0] += dx / dist * force
                disp[v][1] += dy / dist * force
            for node in nodes:
                dx, dy = disp[node]
                dist = math.sqrt(dx * dx + dy * dy) + 0.0001
                new_x = pos[node][0] + (dx / dist) * min(dist, temp)
                new_y = pos[node][1] + (dy / dist) * min(dist, temp)
                pos[node] = (max(20, min(width - 20, new_x)), max(20, min(height - 20, new_y)))
            temp *= 0.98
        return pos

    def draw_graph(self):
        self.canvas.delete("all")
        adj, nodes, weights = self._parse_graph_for_drawing()
        if not nodes: return

        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if width < 50 or height < 50:  # Избегаем отрисовки на слишком маленьком холсте
            self.after(50, self.draw_graph)
            return

        self.node_positions = self._calculate_force_directed_layout(adj, nodes, width, height)
        node_radius, font_size = 18, 12

        # Рёбра
        for u, v_list in adj.items():
            for v in v_list:
                if u < v:
                    p1, p2 = self.node_positions.get(u), self.node_positions.get(v)
                    if not (p1 and p2): continue
                    self.canvas.create_line(p1, p2, fill="grey", width=2)
                    w = weights.get(tuple(sorted((u, v))))
                    if w:
                        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2

                        ### ИСПРАВЛЕНО: КРИТИЧЕСКАЯ ОШИБКА ###
                        # Рисуем подложку (прямоугольник), чтобы текст был читаемым
                        # Это заменяет неработающий параметр insertbackground
                        text_id = self.canvas.create_text(mx, my, text=w, font=(None, 10), fill="darkblue")
                        bbox = self.canvas.bbox(text_id)
                        rect_id = self.canvas.create_rectangle(bbox, fill="white", outline="white")
                        self.canvas.tag_lower(rect_id, text_id)  # Помещаем прямоугольник под текст

        # Вершины
        for name, (x, y) in self.node_positions.items():
            self.canvas.create_oval(x - node_radius, y - node_radius, x + node_radius, y + node_radius,
                                    fill="skyblue", outline=self.colors['button'], width=2)
            self.canvas.create_text(x, y, text=name, font=("Segoe UI", font_size, "bold"), fill="black")

    def solve_problem(self):
        is_weighted = self.is_weighted_var.get()
        matrix_rows = []
        for r in range(self.dimension):
            if is_weighted:
                row_str = [self.matrix_widgets[r][c].get() or "0" for c in range(self.dimension)]
            else:
                row_str = ["1" if self.matrix_widgets[r][c].get() else "0" for c in range(self.dimension)]
            matrix_rows.append(" ".join(row_str))

        matrix_str = "\n".join(matrix_rows)
        edges_str = self.edges_text.get("1.0", tk.END)
        targets_str = self.targets_entry.get()

        if not matrix_str.strip() or not edges_str.strip() or not targets_str.strip():
            self.update_result("Заполните все поля!", is_error=True)
            return

        result = backend.solve(matrix_str, edges_str, targets_str, is_weighted)

        if "ошибка" in result.lower():
            self.update_result(result, is_error=True)
        else:
            self.update_result(f"Ответ: {result}", is_error=False)

    def update_result(self, text, is_error=False):
        color, bg_color = (self.colors['error'], self.colors['error_bg']) if is_error else (self.colors['success'],
                                                                                            self.colors['success_bg'])
        self.result_label.config(text=text, foreground=color, background=bg_color)


if __name__ == "__main__":
    app = App()
    app.mainloop()
