import copy
import tkinter as tk
from tkinter import filedialog, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

# ---------- АЛГОРИТМЫ ОБРАБОТКИ (ИЗ ПЕРВОГО КОДА) ----------


def binarize_image(img_grayscale):
    """Бинаризация: объекты — 1, фон — 0"""
    _, binary = cv2.threshold(img_grayscale, 127, 1, cv2.THRESH_BINARY_INV)
    return binary


def label_recursive(image):
    image = image.copy().astype(np.int32)
    h, w = image.shape
    label = 2
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]

    for y in range(h):
        for x in range(w):
            if image[y, x] == 1:
                # DFS на стеке
                stack = [(x, y)]
                image[y, x] = label
                while stack:
                    cx, cy = stack.pop()
                    for dx, dy in directions:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            if image[ny, nx] == 1:
                                image[ny, nx] = label
                                stack.append((nx, ny))
                label += 1
    return image


def label_two_pass(image):
    image = image.copy().astype(np.int32)
    h, w = image.shape
    labels = np.zeros_like(image, dtype=np.int32)
    parent = {}
    current_label = 2

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for y in range(h):
        for x in range(w):
            if image[y, x] == 0:
                continue
            neighbors = []
            if y > 0 and labels[y - 1, x] > 0:
                neighbors.append(labels[y - 1, x])
            if x > 0 and labels[y, x - 1] > 0:
                neighbors.append(labels[y, x - 1])

            if len(neighbors) == 0:
                labels[y, x] = current_label
                parent[current_label] = current_label
                current_label += 1
            else:
                smallest = min(neighbors)
                labels[y, x] = smallest
                for n in neighbors:
                    union(smallest, n)

    for y in range(h):
        for x in range(w):
            if labels[y, x] > 0:
                labels[y, x] = find(labels[y, x])
    return labels


def color_labels(labels):
    h, w = labels.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)
    unique_labels = np.unique(labels)
    np.random.seed(42)
    colors = {0: (0, 0, 0)}

    for label in unique_labels:
        if label != 0:
            colors[label] = (
                np.random.randint(50, 255),
                np.random.randint(50, 255),
                np.random.randint(50, 255),
            )

    for y in range(h):
        for x in range(w):
            colored[y, x] = colors[labels[y, x]]
    return colored


# --- ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---


class ConnectedComponentsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализ связных компонентов")
        self.root.geometry("1000x600")
        self.root.minimum_size = (800, 500)

        # Хранилище для оригинальных OpenCV изображений (чтобы не терять качество при ресайзе)
        self.img_orig_cv = None
        self.img_rec_cv = None
        self.img_two_cv = None

        # Ссылки на объекты ImageTk (Tkinter зануляет их, если не держать ссылку)
        self.photo_orig = None
        self.photo_rec = None
        self.photo_two = None

        self.create_widgets()

    def create_widgets(self):
        # Верхняя панель управления
        top_panel = tk.Frame(self.root, pady=10)
        top_panel.pack(side=tk.TOP, fill=tk.X)

        btn_select = tk.Button(
            top_panel,
            text="Выбрать изображение",
            command=self.load_image,
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5,
        )
        btn_select.pack()

        # Главный контейнер для трех колонок (адаптивная сетка)
        self.columns_frame = tk.Frame(self.root)
        self.columns_frame.pack(
            side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10
        )

        # Настраиваем веса колонок, чтобы они одинаково расширялись при растягивании окна
        self.columns_frame.columnconfigure(0, weight=1)
        self.columns_frame.columnconfigure(1, weight=1)
        self.columns_frame.columnconfigure(2, weight=1)
        self.columns_frame.rowconfigure(0, weight=1)

        # 1 Колонка: Оригинал
        self.col1 = tk.LabelFrame(
            self.columns_frame,
            text="Исходное изображение",
            font=("Arial", 10, "bold"),
            labelanchor="n",
        )
        self.col1.grid(row=0, column=0, sticky="nsew", padx=5)
        self.lbl_img1 = tk.Label(self.col1)
        self.lbl_img1.pack(fill=tk.BOTH, expand=True, pady=5)

        # 2 Колонка: Рекурсивный алгоритм
        self.col2 = tk.LabelFrame(
            self.columns_frame,
            text="Рекурсивный (DFS)",
            font=("Arial", 10, "bold"),
            labelanchor="n",
        )
        self.col2.grid(row=0, column=1, sticky="nsew", padx=5)
        self.lbl_img2 = tk.Label(self.col2)
        self.lbl_img2.pack(fill=tk.BOTH, expand=True, pady=5)

        # 3 Колонка: Двухпроходный алгоритм
        self.col3 = tk.LabelFrame(
            self.columns_frame,
            text="Двухпроходный (Two-Pass)",
            font=("Arial", 10, "bold"),
            labelanchor="n",
        )
        self.col3.grid(row=0, column=2, sticky="nsew", padx=5)
        self.lbl_img3 = tk.Label(self.col3)
        self.lbl_img3.pack(fill=tk.BOTH, expand=True, pady=5)

        # Вешаем событие изменения размера окна, чтобы динамически пересчитывать масштаб картинок
        self.root.bind("<Configure>", self.on_resize)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")],
        )
        if not file_path:
            return

        # Читаем картинку
        img_gray = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if img_gray is None:
            return

        # Нам нужен BGR формат для корректного вывода цвета в Tkinter (через RGB conversion)
        self.img_orig_cv = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)

        # Запускаем бинаризацию и алгоритмы маркеров
        binary = binarize_image(img_gray)

        rec_labels = label_recursive(binary)
        self.img_rec_cv = cv2.cvtColor(color_labels(rec_labels), cv2.COLOR_BGR2RGB)
        rec_count = len(np.unique(rec_labels)) - 1

        two_labels = label_two_pass(binary)
        self.img_two_cv = cv2.cvtColor(color_labels(two_labels), cv2.COLOR_BGR2RGB)
        two_count = len(np.unique(two_labels)) - 1

        # Обновляем текстовые подписи в рамках (LabelFrame) рядом с картинками
        self.col1.config(text="Исходное изображение")
        self.col2.config(text=f"Рекурсивный метод\nНайдено объектов: {rec_count}")
        self.col3.config(text=f"Двухпроходный метод\nНайдено объектов: {two_count}")

        # Отрисовываем картинки с учетом текущего размера окна
        self.update_images_display()

    def update_images_display(self):
        if self.img_orig_cv is None:
            return

        # Вычисляем доступный размер для одной картинки внутри виджета Label
        # Берем ширину и высоту фрейма-колонки (они делят экран на 3 части)
        target_w = max(self.col1.winfo_width() - 20, 100)
        target_h = max(self.col1.winfo_height() - 60, 100)

        def resize_cv_to_tk(cv_img):
            # Пропорциональное масштабирование (поддерживаем Aspect Ratio)
            h, w, _ = cv_img.shape
            scale = min(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)

            resized = cv2.resize(cv_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            img_pil = Image.fromarray(resized)
            return ImageTk.PhotoImage(img_pil)

        # Превращаем матрицы в объекты для Tkinter
        self.photo_orig = resize_cv_to_tk(self.img_orig_cv)
        self.photo_rec = resize_cv_to_tk(self.img_rec_cv)
        self.photo_two = resize_cv_to_tk(self.img_two_cv)

        # Обновляем контейнеры
        self.lbl_img1.config(image=self.photo_orig)
        self.lbl_img2.config(image=self.photo_rec)
        self.lbl_img3.config(image=self.photo_two)

    def on_resize(self, event):
        # Вызываем обновление картинок только при реальном изменении размеров окна приложения
        if event.widget == self.root:
            self.update_images_display()


if __name__ == "__main__":
    window = tk.Tk()
    app = ConnectedComponentsApp(window)
    window.mainloop()
