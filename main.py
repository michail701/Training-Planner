import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

DATA_FILE = "trainings.json"
DATE_FORMAT = "%Y-%m-%d"


class TrainingPlannerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Training Planner")
        self.root.geometry("900x600")

        self.trainings = []

        self.date_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.duration_var = tk.StringVar()

        self.filter_type_var = tk.StringVar(value="Все")
        self.filter_date_var = tk.StringVar()

        self._build_ui()
        self.load_data(show_message=False)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        form = ttk.LabelFrame(main, text="Добавить тренировку", padding=10)
        form.pack(fill="x")

        ttk.Label(form, text="Дата (YYYY-MM-DD):").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        ttk.Entry(form, textvariable=self.date_var, width=24).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(form, text="Тип тренировки:").grid(row=0, column=2, padx=4, pady=4, sticky="w")
        ttk.Entry(form, textvariable=self.type_var, width=28).grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(form, text="Длительность (мин):").grid(row=1, column=0, padx=4, pady=4, sticky="w")
        ttk.Entry(form, textvariable=self.duration_var, width=24).grid(row=1, column=1, padx=4, pady=4)

        ttk.Button(form, text="Добавить тренировку", command=self.add_training).grid(row=2, column=0, columnspan=4, pady=(8, 2))

        filters = ttk.LabelFrame(main, text="Фильтрация", padding=10)
        filters.pack(fill="x", pady=(10, 0))

        ttk.Label(filters, text="По типу:").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        self.type_combo = ttk.Combobox(filters, textvariable=self.filter_type_var, state="readonly", width=24)
        self.type_combo.grid(row=0, column=1, padx=4, pady=4)
        self.type_combo.bind("<<ComboboxSelected>>", lambda _: self.apply_filters())

        ttk.Label(filters, text="По дате (YYYY-MM-DD):").grid(row=0, column=2, padx=4, pady=4, sticky="w")
        ttk.Entry(filters, textvariable=self.filter_date_var, width=24).grid(row=0, column=3, padx=4, pady=4)

        ttk.Button(filters, text="Применить", command=self.apply_filters).grid(row=0, column=4, padx=4, pady=4)
        ttk.Button(filters, text="Сброс", command=self.reset_filters).grid(row=0, column=5, padx=4, pady=4)

        table_frame = ttk.LabelFrame(main, text="План тренировок", padding=10)
        table_frame.pack(fill="both", expand=True, pady=(10, 0))

        columns = ("date", "type", "duration")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
        self.tree.heading("date", text="Дата")
        self.tree.heading("type", text="Тип тренировки")
        self.tree.heading("duration", text="Длительность (мин)")

        self.tree.column("date", width=180, anchor="center")
        self.tree.column("type", width=380)
        self.tree.column("duration", width=180, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        controls = ttk.Frame(main)
        controls.pack(fill="x", pady=(10, 0))
        ttk.Button(controls, text="Сохранить JSON", command=self.save_data).pack(side="left", padx=4)
        ttk.Button(controls, text="Загрузить JSON", command=self.load_data).pack(side="left", padx=4)
        ttk.Button(controls, text="Удалить выбранную", command=self.remove_selected).pack(side="left", padx=4)

    def _validate_date(self, date_text: str) -> bool:
        try:
            datetime.strptime(date_text, DATE_FORMAT)
            return True
        except ValueError:
            return False

    def add_training(self):
        date_text = self.date_var.get().strip()
        training_type = self.type_var.get().strip()
        duration_text = self.duration_var.get().strip().replace(",", ".")

        if not date_text or not training_type or not duration_text:
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return

        if not self._validate_date(date_text):
            messagebox.showerror("Ошибка", "Дата должна быть в формате YYYY-MM-DD.")
            return

        try:
            duration = float(duration_text)
            if duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Длительность должна быть положительным числом.")
            return

        self.trainings.append(
            {
                "date": date_text,
                "type": training_type,
                "duration": duration,
            }
        )

        self.date_var.set("")
        self.type_var.set("")
        self.duration_var.set("")

        self._refresh_types()
        self.apply_filters()

    def _refresh_types(self):
        values = ["Все"] + sorted({row["type"] for row in self.trainings})
        current = self.filter_type_var.get()
        self.type_combo["values"] = values
        if current not in values:
            self.filter_type_var.set("Все")

    def apply_filters(self):
        filtered = list(self.trainings)

        selected_type = self.filter_type_var.get()
        date_filter = self.filter_date_var.get().strip()

        if selected_type and selected_type != "Все":
            filtered = [row for row in filtered if row["type"] == selected_type]

        if date_filter:
            if not self._validate_date(date_filter):
                messagebox.showerror("Ошибка", "Фильтр по дате должен быть в формате YYYY-MM-DD.")
                return
            filtered = [row for row in filtered if row["date"] == date_filter]

        self._render_table(filtered)

    def _render_table(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["date"],
                    row["type"],
                    f"{row['duration']:.2f}",
                ),
            )

    def reset_filters(self):
        self.filter_type_var.set("Все")
        self.filter_date_var.set("")
        self.apply_filters()

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Сначала выберите запись.")
            return

        values = self.tree.item(selected[0], "values")
        if not values:
            return

        date_text = str(values[0])
        type_text = str(values[1])
        duration = float(str(values[2]))

        for i, item in enumerate(self.trainings):
            if item["date"] == date_text and item["type"] == type_text and abs(item["duration"] - duration) < 1e-9:
                del self.trainings[i]
                break

        self._refresh_types()
        self.apply_filters()

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.trainings, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Успех", f"Данные сохранены в {os.path.abspath(DATA_FILE)}")
        except OSError as err:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {err}")

    def load_data(self, show_message=True):
        if not os.path.exists(DATA_FILE):
            self.trainings = []
            self._refresh_types()
            self.apply_filters()
            if show_message:
                messagebox.showwarning("Внимание", "Файл trainings.json не найден.")
            return

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("Некорректный формат trainings.json")

            validated = []
            for row in data:
                if not isinstance(row, dict):
                    continue
                date_text = str(row.get("date", "")).strip()
                type_text = str(row.get("type", "")).strip()
                duration = row.get("duration")
                if self._validate_date(date_text) and type_text and isinstance(duration, (int, float)) and duration > 0:
                    validated.append({"date": date_text, "type": type_text, "duration": float(duration)})

            self.trainings = validated
            self._refresh_types()
            self.apply_filters()
            if show_message:
                messagebox.showinfo("Успех", "Данные загружены.")
        except (OSError, json.JSONDecodeError, ValueError) as err:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {err}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TrainingPlannerApp(root)
    root.mainloop()
