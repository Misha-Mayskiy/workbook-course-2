import tkinter as tk
from tkinter import ttk, messagebox
from backend import TruthTableCalculator

class TruthTableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Таблица истинности")
        self.root.geometry("700x600")
        
        self.calculator = TruthTableCalculator()
        self.current_filter = 'all'
        self.edit_mode = False
        self.edited_results = None
        
        self.create_widgets()
    
    def create_widgets(self):
        # Заголовок
        tk.Label(self.root, text="Генератор таблицы истинности", 
                font=("Arial", 16, "bold")).pack(pady=10)
        
        # Ввод выражения
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Label(input_frame, text="Выражение:").pack(anchor="w")
        self.expression_entry = tk.Entry(input_frame, font=("Arial", 12))
        self.expression_entry.pack(fill="x", pady=5)
        self.expression_entry.bind("<Return>", lambda e: self.calculate())
        
        # Примеры
        examples = ["w and x", "w or x", "not w", "(x or y) and (not z)"]
        example_frame = tk.Frame(input_frame)
        example_frame.pack(fill="x", pady=5)
        
        for example in examples:
            tk.Button(example_frame, text=example, 
                     command=lambda e=example: self.set_example(e)).pack(side="left", padx=2)
        
        # Кнопки управления
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="Вычислить", command=self.calculate,
                 bg="#4CAF50", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=5)
        
        # Режимы
        self.edit_var = tk.BooleanVar()
        tk.Checkbutton(control_frame, text="Режим редактирования", 
                      variable=self.edit_var, command=self.toggle_edit_mode).pack(side="left", padx=10)
        
        self.restore_btn = tk.Button(control_frame, text="Восстановить выражение", 
                                    command=self.restore_expression, state="disabled",
                                    bg="#FF9800", fg="white")
        self.restore_btn.pack(side="left", padx=5)
        
        # Фильтры
        filter_frame = tk.Frame(self.root)
        filter_frame.pack(pady=5)
        
        tk.Label(filter_frame, text="Фильтры:").pack(side="left")
        
        filters = [("Все", "all"), ("True", "true"), ("False", "false"), ("Меньшинство", "minority")]
        for text, filter_type in filters:
            tk.Button(filter_frame, text=text, 
                     command=lambda f=filter_type: self.apply_filter(f)).pack(side="left", padx=2)
        
        # Таблица результатов
        table_frame = tk.Frame(self.root)
        table_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        columns = ("w", "x", "y", "z", "Результат")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<Double-1>", self.edit_result)
        
        # Информация
        self.info_label = tk.Label(self.root, text="", fg="blue")
        self.info_label.pack(pady=5)
    
    def set_example(self, example):
        self.expression_entry.delete(0, tk.END)
        self.expression_entry.insert(0, example)
    
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
        # Очистить таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Получить данные для отображения
        if self.edited_results:
            # Применяем фильтр к отредактированным данным
            if self.current_filter == 'all':
                results = self.edited_results
            elif self.current_filter == 'true':
                results = [r for r in self.edited_results if r['result']]
            elif self.current_filter == 'false':
                results = [r for r in self.edited_results if not r['result']]
            elif self.current_filter == 'minority':
                true_count = sum(1 for r in self.edited_results if r['result'])
                false_count = len(self.edited_results) - true_count
                if true_count < false_count:
                    results = [r for r in self.edited_results if r['result']]
                elif false_count < true_count:
                    results = [r for r in self.edited_results if not r['result']]
                else:
                    results = self.edited_results
        else:
            results = self.calculator.get_filtered_results(self.current_filter)
        
        # Заполнить таблицу
        for result in results:
            result_text = "True" if result['result'] else "False"
            color = "green" if result['result'] else "red"
            
            item = self.tree.insert("", "end", 
                                  values=(result['w'], result['x'], result['y'], result['z'], result_text))
            self.tree.set(item, "Результат", result_text)
        
        # Обновить информацию
        self.update_info()
    
    def update_info(self):
        if self.edited_results:
            true_count = sum(1 for r in self.edited_results if r['result'])
            total = len(self.edited_results)
        else:
            stats = self.calculator.get_stats()
            if not stats:
                return
            true_count = stats['true']
            total = stats['total']
        
        false_count = total - true_count
        
        if true_count < false_count:
            minority = f"True в меньшинстве ({true_count})"
        elif false_count < true_count:
            minority = f"False в меньшинстве ({false_count})"
        else:
            minority = "Равное количество"
        
        info = f"Всего: {total} | True: {true_count} | False: {false_count} | {minority} | Фильтр: {self.current_filter}"
        self.info_label.config(text=info)
    
    def toggle_edit_mode(self):
        self.edit_mode = self.edit_var.get()
        if self.edit_mode:
            self.restore_btn.config(state="normal")
        else:
            self.restore_btn.config(state="disabled")
            self.edited_results = None
            self.update_table()
    
    def edit_result(self, event):
        if not self.edit_mode:
            return
        
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, "values")
        
        # Инициализируем edited_results если нужно
        if not self.edited_results:
            self.edited_results = self.calculator.results.copy()
        
        # Находим соответствующую запись и переключаем результат
        w, x, y, z = int(values[0]), int(values[1]), int(values[2]), int(values[3])
        
        for result in self.edited_results:
            if (result['w'] == w and result['x'] == x and 
                result['y'] == y and result['z'] == z):
                result['result'] = not result['result']
                break
        
        self.update_table()
    
    def restore_expression(self):
        if not self.edited_results:
            messagebox.showinfo("Инфо", "Нет изменений для восстановления")
            return
        
        expression = self.calculator.create_expression_from_table(self.edited_results)
        
        # Показать в новом окне
        dialog = tk.Toplevel(self.root)
        dialog.title("Восстановленное выражение")
        dialog.geometry("400x200")
        
        tk.Label(dialog, text="Восстановленное выражение:", font=("Arial", 12, "bold")).pack(pady=10)
        
        text_widget = tk.Text(dialog, height=5, wrap=tk.WORD)
        text_widget.pack(pady=10, padx=20, fill="both", expand=True)
        text_widget.insert("1.0", expression)
        
        def use_expression():
            self.expression_entry.delete(0, tk.END)
            self.expression_entry.insert(0, expression)
            dialog.destroy()
        
        tk.Button(dialog, text="Использовать", command=use_expression,
                 bg="#4CAF50", fg="white").pack(pady=5)

def main():
    root = tk.Tk()
    app = TruthTableApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()