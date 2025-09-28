import tkinter as tk
from tkinter import ttk, messagebox
from backend import TruthTableCalculator


class TruthTableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Truth PROJECT")
        self.root.geometry("900x700")

        self.calculator = TruthTableCalculator()
        self.current_filter = 'all'
        self.edit_mode = False
        self.edited_results = None

        self.create_widgets()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.normal_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.normal_frame, text="Таблица истинности")

        self.ege_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ege_frame, text="Решатель ЕГЭ")

        self.create_normal_tab()
        self.create_ege_tab()

    def create_normal_tab(self):
        tk.Label(self.normal_frame, text="Генератор таблицы истинности",
                 font=("Arial", 16, "bold")).pack(pady=10)

        input_frame = tk.Frame(self.normal_frame)
        input_frame.pack(pady=10, padx=20, fill="x")

        tk.Label(input_frame, text="Выражение (используйте x, y, z, w и синтаксис Python):").pack(anchor="w")
        self.expression_entry = tk.Entry(input_frame, font=("Arial", 12))
        self.expression_entry.pack(fill="x", pady=5)
        self.expression_entry.bind("<Return>", lambda e: self.calculate())

        examples = ["(x and not y) or (y == z) or w", "x or y", "not w", "(x or y) and (not z)"]
        example_frame = tk.Frame(input_frame)
        example_frame.pack(fill="x", pady=5)

        for example in examples:
            tk.Button(example_frame, text=example,
                      command=lambda e=example: self.set_example(e)).pack(side="left", padx=2)

        control_frame = tk.Frame(self.normal_frame)
        control_frame.pack(pady=10)

        tk.Button(control_frame, text="Вычислить", command=self.calculate,
                  bg="#4CAF50", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=5)

        self.edit_var = tk.BooleanVar()
        tk.Checkbutton(control_frame, text="Режим редактирования",
                       variable=self.edit_var, command=self.toggle_edit_mode).pack(side="left", padx=10)

        self.restore_btn = tk.Button(control_frame, text="Восстановить выражение",
                                     command=self.restore_expression, state="disabled",
                                     bg="#FF9800", fg="white")
        self.restore_btn.pack(side="left", padx=5)

        filter_frame = tk.Frame(self.normal_frame)
        filter_frame.pack(pady=5)
        tk.Label(filter_frame, text="Фильтры:").pack(side="left")

        filters = [("Все", "all"), ("True", "true"), ("False", "false"), ("Меньшинство", "minority")]
        for text, filter_type in filters:
            tk.Button(filter_frame, text=text,
                      command=lambda f=filter_type: self.apply_filter(f)).pack(side="left", padx=2)

        table_frame = tk.Frame(self.normal_frame)
        table_frame.pack(pady=10, padx=20, fill="both", expand=True)

        columns = ("w", "x", "y", "z", "Результат")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self.edit_result)
        self.info_label = tk.Label(self.normal_frame, text="", fg="blue")
        self.info_label.pack(pady=5)

    def create_ege_tab(self):
        tk.Label(self.ege_frame, text="Решатель задач ЕГЭ (задание 2)",
                 font=("Arial", 16, "bold")).pack(pady=10)
        instruction = tk.Label(self.ege_frame,
                               text="Введите выражение (переменные x, y, z, w; синтаксис Python: and, or, not, ==).\n"
                                    "Заполните неполную таблицу. Для неизвестных значений оставьте ячейку пустой.",
                               font=("Arial", 10))
        instruction.pack(pady=5)
        input_frame = tk.Frame(self.ege_frame)
        input_frame.pack(pady=10, padx=20, fill="x")
        tk.Label(input_frame, text="Логическое выражение:").pack(anchor="w")
        self.ege_expression_entry = tk.Entry(input_frame, font=("Arial", 12))
        self.ege_expression_entry.pack(fill="x", pady=2)

        ege_example_frame = tk.Frame(input_frame)
        ege_example_frame.pack(fill="x", pady=5)
        tk.Label(ege_example_frame, text="Пример:").pack(anchor="w")
        ege_example = "(x and not y) or (y == z) or w"
        tk.Button(ege_example_frame, text=ege_example,
                  command=lambda e=ege_example: self.set_ege_example(e)).pack(side="left", padx=2)

        button_frame = tk.Frame(input_frame)
        button_frame.pack(fill="x", pady=10)

        tk.Button(button_frame, text="Решить задачу",
                  command=self.solve_ege_task,
                  bg="#4CAF50", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=5)

        table_ege_frame = tk.Frame(self.ege_frame)
        table_ege_frame.pack(pady=10, padx=20, fill="both", expand=True)

        left_frame = tk.Frame(table_ege_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right_frame = tk.Frame(table_ege_frame)
        right_frame.pack(side="right", fill="both", expand=True)
        tk.Label(left_frame, text="Неполная таблица истинности:", font=("Arial", 12, "bold")).pack(anchor="w")
        ege_columns = ("F1", "F2", "F3", "F4", "Результат")
        self.ege_input_tree = ttk.Treeview(left_frame, columns=ege_columns, show="headings", height=8)
        for col in ege_columns:
            self.ege_input_tree.heading(col, text=col)
            self.ege_input_tree.column(col, width=60, anchor="center")
        ege_input_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.ege_input_tree.yview)
        self.ege_input_tree.configure(yscrollcommand=ege_input_scrollbar.set)
        self.ege_input_tree.pack(side="left", fill="both", expand=True)
        ege_input_scrollbar.pack(side="right", fill="y")

        table_control_frame = tk.Frame(left_frame)
        table_control_frame.pack(fill="x", pady=5)
        tk.Button(table_control_frame, text="Добавить строку",
                  command=self.add_ege_row).pack(side="left", padx=2)
        tk.Button(table_control_frame, text="Удалить строку",
                  command=self.delete_ege_row).pack(side="left", padx=2)
        tk.Button(table_control_frame, text="Очистить",
                  command=self.clear_ege_table).pack(side="left", padx=2)

        tk.Label(right_frame, text="Результаты решения:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.ege_results_text = tk.Text(right_frame, height=15, wrap=tk.WORD, font=("Arial", 10))
        ege_results_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.ege_results_text.yview)
        self.ege_results_text.configure(yscrollcommand=ege_results_scrollbar.set)
        self.ege_results_text.pack(side="left", fill="both", expand=True)
        ege_results_scrollbar.pack(side="right", fill="y")
        self.ege_input_tree.bind("<Double-1>", self.edit_ege_cell)

    def set_example(self, example):
        self.expression_entry.delete(0, tk.END)
        self.expression_entry.insert(0, example)

    def set_ege_example(self, example):
        self.ege_expression_entry.delete(0, tk.END)
        self.ege_expression_entry.insert(0, example)

    def solve_ege_task(self):
        expression = self.ege_expression_entry.get().strip()
        if not expression:
            messagebox.showwarning("Внимание", "Введите выражение")
            return

        incomplete_table = []
        for item in self.ege_input_tree.get_children():
            values = self.ege_input_tree.item(item, "values")
            if len(values) == 5:
                try:
                    row = {
                        'F1': int(values[0]) if values[0] else None,
                        'F2': int(values[1]) if values[1] else None,
                        'F3': int(values[2]) if values[2] else None,
                        'F4': int(values[3]) if values[3] else None,
                    }
                    if not values[4]:
                        messagebox.showerror("Ошибка", "Значение в столбце 'Результат' не может быть пустым.")
                        return
                    row['result'] = bool(int(values[4]))
                    incomplete_table.append(row)
                except (ValueError, IndexError):
                    messagebox.showerror("Ошибка", "Все значения в таблице должны быть 0, 1 или пустыми.")
                    return

        if not incomplete_table:
            messagebox.showwarning("Внимание", "Заполните таблицу")
            return

        try:
            solutions = self.calculator.solve_ege_task(expression, incomplete_table)
            self.ege_results_text.delete("1.0", tk.END)
            if not solutions:
                self.ege_results_text.insert("1.0", "Решений не найдено.\n\nПроверьте выражение и таблицу.")
            else:
                self.ege_results_text.insert("1.0", f"Найдено решений: {len(solutions)}\n\n")
                for i, solution in enumerate(solutions, 1):
                    self.ege_results_text.insert(tk.END, f"Решение {i}: {solution}\n")
                if len(solutions) == 1:
                    self.ege_results_text.insert(tk.END, "\n✓ Найдено единственное решение!")

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def add_ege_row(self):
        self.ege_input_tree.insert("", "end", values=("", "", "", "", "0"))

    def delete_ege_row(self):
        selection = self.ege_input_tree.selection()
        if selection:
            self.ege_input_tree.delete(selection[0])

    def clear_ege_table(self):
        for item in self.ege_input_tree.get_children():
            self.ege_input_tree.delete(item)

    def edit_ege_cell(self, event):
        selection = self.ege_input_tree.selection()
        if not selection: return

        item = selection[0]
        col_id_str = self.ege_input_tree.identify_column(event.x)

        try:
            col_index = int(col_id_str.replace('#', '')) - 1
            values = list(self.ege_input_tree.item(item, "values"))

            if 0 <= col_index < 4:  # Столбцы переменных F1-F4
                current_value = values[col_index]
                if current_value == "0":
                    new_value = "1"
                elif current_value == "1":
                    new_value = ""
                else:
                    new_value = "0"
                values[col_index] = new_value
            elif col_index == 4:  # Столбец результата
                current_value = values[col_index]
                new_value = "1" if current_value == "0" else "0"
                values[col_index] = new_value

            self.ege_input_tree.item(item, values=values)
        except (ValueError, IndexError):
            pass  # Клик вне ячеек

    def calculate(self):
        expression = self.expression_entry.get().strip()
        if not expression:
            messagebox.showwarning("Внимание", "Введите выражение")
            return
        try:
            self.calculator.calculate(expression)
            self.edited_results = None
            self.current_filter = 'all'
            self.update_table()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def apply_filter(self, filter_type):
        self.current_filter = filter_type
        self.update_table()

    def update_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        source_results = self.edited_results if self.edited_results is not None else self.calculator.results
        if self.current_filter == 'all':
            results_to_show = source_results
        elif self.current_filter == 'true':
            results_to_show = [r for r in source_results if r['result']]
        elif self.current_filter == 'false':
            results_to_show = [r for r in source_results if not r['result']]
        else:  # minority
            true_count = sum(1 for r in source_results if r['result'])
            false_count = len(source_results) - true_count
            if true_count < false_count:
                results_to_show = [r for r in source_results if r['result']]
            elif false_count < true_count:
                results_to_show = [r for r in source_results if not r['result']]
            else:
                results_to_show = source_results

        vars_to_display = self.calculator.variables
        if not vars_to_display: return

        self.tree['columns'] = vars_to_display + ['Результат']
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")

        for result in results_to_show:
            values_tuple = tuple(result.get(var, '') for var in vars_to_display) + (
                "True" if result['result'] else "False",)
            self.tree.insert("", "end", values=values_tuple)

        self.update_info()

    def update_info(self):
        source_results = self.edited_results if self.edited_results is not None else self.calculator.results
        if not source_results:
            self.info_label.config(text="")
            return

        true_count = sum(1 for r in source_results if r['result'])
        total = len(source_results)
        false_count = total - true_count

        if true_count < false_count:
            minority = f"True в меньшинстве ({true_count})"
        elif false_count < true_count:
            minority = f"False в меньшинстве ({false_count})"
        else:
            minority = "Равное количество"

        self.info_label.config(
            text=f"Всего: {total} | True: {true_count} | False: {false_count} | {minority} | Фильтр: {self.current_filter}")

    def toggle_edit_mode(self):
        self.edit_mode = self.edit_var.get()
        self.restore_btn.config(state="normal" if self.edit_mode else "disabled")
        if not self.edit_mode:
            self.edited_results = None
            self.update_table()

    def edit_result(self, event):
        if not self.edit_mode or not self.calculator.results: return
        selection = self.tree.selection()
        if not selection: return

        if self.edited_results is None:
            self.edited_results = [r.copy() for r in self.calculator.results]

        selected_item_values = self.tree.item(selection[0], "values")

        # Находим соответствующую строку в наших данных
        for result in self.edited_results:
            matches = True
            for i, var in enumerate(self.calculator.variables):
                if str(result.get(var, '')) != str(selected_item_values[i]):
                    matches = False
                    break
            if matches:
                result['result'] = not result['result']
                break
        self.update_table()

    def restore_expression(self):
        if self.edited_results is None:
            messagebox.showinfo("Инфо", "Нет изменений для восстановления")
            return

        try:
            expression = self.calculator.create_expression_from_table(self.edited_results)
            dialog = tk.Toplevel(self.root)
            dialog.title("Восстановленное выражение")
            dialog.geometry("400x200")
            tk.Label(dialog, text="Восстановленное выражение:", font=("Arial", 12, "bold")).pack(pady=10)
            text_widget = tk.Text(dialog, height=5, wrap=tk.WORD)
            text_widget.pack(pady=10, padx=20, fill="both", expand=True)
            text_widget.insert("1.0", expression)
            tk.Button(dialog, text="Использовать", command=lambda: (self.set_example(expression), dialog.destroy()),
                      bg="#4CAF50", fg="white").pack(pady=5)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать выражение: {e}")


def main():
    root = tk.Tk()
    app = TruthTableApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
