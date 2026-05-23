import tkinter as tk
from tkinter import messagebox, ttk

import cv2
import numpy as np


# ==================================================
# Логика морфологии (Ваша классическая реализация)
# ==================================================
def dilation(binary):
    padded = np.pad(binary, pad_width=1, mode="constant", constant_values=0)
    result = binary.copy()
    h, w = binary.shape
    pixels_to_add = []

    for y in range(h):
        for x in range(w):
            neighborhood = padded[y : y + 3, x : x + 3]
            total = np.sum(neighborhood)
            # Если в окрестности 3х3 есть хоть одна единица,
            # а сам пиксель еще пустой — добавим его
            if total > 0 and binary[y, x] == 0:
                pixels_to_add.append((y, x))

    for y, x in pixels_to_add:
        result[y, x] = 1

    return result, pixels_to_add


def erosion(binary):
    padded = np.pad(binary, pad_width=1, mode="constant", constant_values=0)
    result = binary.copy()
    h, w = binary.shape
    pixels_to_remove = []

    for y in range(h):
        for x in range(w):
            if binary[y, x] == 1:
                neighborhood = padded[y : y + 3, x : x + 3]
                total = np.sum(neighborhood)
                # Если окрестность заполнена не полностью, удаляем пиксель
                if total != 9:
                    pixels_to_remove.append((y, x))

    for y, x in pixels_to_remove:
        result[y, x] = 0

    return result, pixels_to_remove


def generate_random_binary():
    img = np.zeros((20, 20), dtype=np.uint8)
    rng = np.random.default_rng()

    # Случайные круги
    for _ in range(3):
        center_x = rng.integers(4, 16)
        center_y = rng.integers(4, 16)
        radius = rng.integers(2, 4)
        cv2.circle(img, (center_x, center_y), radius, 1, -1)

    # Случайные прямоугольники
    for _ in range(2):
        x1 = rng.integers(0, 15)
        y1 = rng.integers(0, 15)
        w = rng.integers(3, 6)
        h = rng.integers(3, 6)
        cv2.rectangle(img, (x1, y1), (x1 + w, y1 + h), 1, -1)

    return img


# ==================================================
# Графический интерфейс (UI)
# ==================================================
class MorphologyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Бинарная Морфология Изображений")
        self.root.geometry("750x600")
        self.root.configure(bg="#f0f0f0")

        # Инициализация матрицы
        self.binary_matrix = generate_random_binary()
        self.grid_labels = []

        self.setup_ui()
        self.draw_matrix()

    def setup_ui(self):
        # --- Левая панель: Сетка пикселей ---
        self.matrix_frame = tk.Frame(self.root, bd=2, relief=tk.GROOVE, bg="white")
        self.matrix_frame.pack(
            side=tk.LEFT, padx=20, pady=20, fill=tk.BOTH, expand=True
        )

        # --- Правая панель: Управление ---
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(side=tk.RIGHT, padx=20, pady=20, fill=tk.Y)

        title_label = tk.Label(
            control_frame, text="Управление", font=("Arial", 16, "bold"), bg="#f0f0f0"
        )
        title_label.pack(pady=10)

        # Кнопки
        btn_style = {"font": ("Arial", 11), "width": 20, "pady": 5}

        btn_dilation = tk.Button(
            control_frame,
            text="1. Наращивание",
            bg="#d4edda",
            fg="#155724",
            **btn_style,
            command=self.apply_dilation,
        )
        btn_dilation.pack(pady=5)

        btn_erosion = tk.Button(
            control_frame,
            text="2. Эрозия",
            bg="#f8d7da",
            fg="#721c24",
            **btn_style,
            command=self.apply_erosion,
        )
        btn_erosion.pack(pady=5)

        btn_new = tk.Button(
            control_frame,
            text="3. Новая сцена",
            bg="#cce5ff",
            fg="#004085",
            **btn_style,
            command=self.new_scene,
        )
        btn_new.pack(pady=20)

        # Панель логов
        log_label = tk.Label(
            control_frame,
            text="Лог изменений:",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
        )
        log_label.pack(anchor=tk.W)

        self.log_text = tk.Text(
            control_frame, width=25, height=15, font=("Courier New", 9)
        )
        self.log_text.pack(pady=5)

    def draw_matrix(self):
        # Очищаем старую сетку label'ов, если она была
        for row in self.grid_labels:
            for lbl in row:
                lbl.destroy()
        self.grid_labels.clear()

        h, w = self.binary_matrix.shape

        # Настраиваем адаптивные размеры сетки
        for i in range(h):
            self.matrix_frame.rowconfigure(i, weight=1)
            self.matrix_frame.columnconfigure(i, weight=1)

        # Отрисовка пикселей в виде цветных квадратиков
        for y in range(h):
            row_labels = []
            for x in range(w):
                val = self.binary_matrix[y, x]
                # Единица — черная/синяя (объект), Ноль — белая (фон)
                color = "#2c3e50" if val == 1 else "#ffffff"

                lbl = tk.Label(self.matrix_frame, bg=color, bd=1, relief="solid")
                lbl.grid(row=y, column=x, sticky="nsew")
                row_labels.append(lbl)
            self.grid_labels.append(row_labels)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def apply_dilation(self):
        self.binary_matrix, added_pixels = dilation(self.binary_matrix)
        self.draw_matrix()

        self.log_message("--- Наращивание ---")
        if added_pixels:
            self.log_message(f"Добавлено пикселей: {len(added_pixels)}")
            for y, x in added_pixels[:5]:  # Выведем первые 5 координат
                self.log_message(f" Координата: ({y},{x})")
            if len(added_pixels) > 5:
                self.log_message(" ... и другие.")
        else:
            self.log_message("Нет изменений")

    def apply_erosion(self):
        self.binary_matrix, removed_pixels = erosion(self.binary_matrix)
        self.draw_matrix()

        self.log_message("--- Эрозия ---")
        if removed_pixels:
            self.log_message(f"Удалено пикселей: {len(removed_pixels)}")
            for y, x in removed_pixels[:5]:
                self.log_message(f" Координата: ({y},{x})")
            if len(removed_pixels) > 5:
                self.log_message(" ... и другие.")
        else:
            self.log_message("Нет изменений")

    def new_scene(self):
        self.binary_matrix = generate_random_binary()
        self.draw_matrix()
        self.log_text.delete("1.0", tk.END)
        self.log_message("Сгенерирована новая сцена.")


if __name__ == "__main__":
    root = tk.Tk()
    app = MorphologyApp(root)
    root.mainloop()
