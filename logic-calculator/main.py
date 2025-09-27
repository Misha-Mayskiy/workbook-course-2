import tkinter as tk
from tkinter import ttk, messagebox


class TruthTableApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Таблица истинности")
        self.geometry("600x400")

        # Наименование и поле для ввода выражения
        label = tk.Label(self, text="Введите выражение с w, x, y, z:")
        label.pack(pady=5)

        self.entry = tk.Entry(self, width=50)
        self.entry.pack(pady=5)

        # Кнопка запуска
        button = tk.Button(self, text="Построить таблицу", command=self.calculate_table)
        button.pack(pady=10)

        # Таблица для отображения результатов
        columns = ("w", "x", "y", "z", "result")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def calculate_table(self):
        expr = self.entry.get()
        if not expr:
            messagebox.showwarning("Ошибка", "Введите выражение!")
            return

        # Очистка прошлых результатов
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            # Перебор комбинаций значений w,x,y,z
            for w in range(2):
                for x in range(2):
                    for y in range(2):
                        for z in range(2):
                            result = eval(expr, {}, {"w": w, "x": x, "y": y, "z": z})
                            self.tree.insert("", "end", values=(w, x, y, z, result))
        except Exception as e:
            messagebox.showerror("Ошибка вычисления", str(e))


if __name__ == "__main__":
    app = TruthTableApp()
    app.mainloop()
