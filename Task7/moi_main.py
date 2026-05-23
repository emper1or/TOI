import tkinter as tk
from tkinter import filedialog, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

# ============================================================================
# 1. КЛАСС ДЛЯ ВСПЛЫВАЮЩИХ ПОДСКАЗОК (TOOLTIPS) С ФОРМУЛАМИ
# ============================================================================


class Tooltip:
    """Создает всплывающую подсказку при наведении на элемент"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        if event is not None:
            x = event.x_root + 20
            y = event.y_root + 15
        else:
            x = self.widget.winfo_rootx() + 25
            y = self.widget.winfo_rooty() + 20

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Убираем рамку окна
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Courier New", 10, "normal"),
            padx=5,
            pady=5,
        )
        label.pack()

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


# ============================================================================
# 2. АЛГОРИТМЫ ОБРАБОТКИ И МАРКИРОВКИ (Из lab9.py и main2.py)
# ============================================================================


def load_and_binarize(path):
    """Загрузка изображения и инвертированная бинаризация"""
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Изображение не найдено")
    # Бинаризация: объект = 1, фон = 0
    _, binary = cv2.threshold(img, 127, 1, cv2.THRESH_BINARY_INV)
    return img, binary


def label_objects(image):
    """Маркировка связных компонентов ручным алгоритмом DFS на стеке"""
    image = image.copy().astype(np.int32)
    h, w = image.shape
    current_label = 2

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for y in range(h):
        for x in range(w):
            if image[y, x] == 1:
                stack = [(x, y)]
                image[y, x] = current_label

                while stack:
                    cx, cy = stack.pop()
                    for dx, dy in directions:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h and image[ny, nx] == 1:
                            image[ny, nx] = current_label
                            stack.append((nx, ny))
                current_label += 1

    return image


def color_labels(labels):
    """Генерация цветного изображения по меткам"""
    h, w = labels.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)
    np.random.seed(42)

    unique_labels = np.unique(labels)
    colors = {0: (30, 30, 30)}  # Темно-серый фон для контраста в UI

    for label in unique_labels:
        if label != 0:
            colors[label] = (
                np.random.randint(80, 255),
                np.random.randint(80, 255),
                np.random.randint(80, 255),
            )

    for y in range(h):
        for x in range(w):
            colored[y, x] = colors[labels[y, x]]

    return colored


def count_corners_and_b(labels, target_label):
    """Расчет свободных граней (b) и углов (d) через блоки 2x2"""
    h, w = labels.shape
    obj_mask = (labels == target_label).astype(np.uint8)
    padded = np.pad(obj_mask, 1, mode="constant", constant_values=0)

    b = 0
    for y in range(h):
        for x in range(w):
            if obj_mask[y, x] == 1:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if nx < 0 or ny < 0 or nx >= w or ny >= h or obj_mask[ny, nx] == 0:
                        b += 1

    d = 0
    for y in range(padded.shape[0] - 1):
        for x in range(padded.shape[1] - 1):
            block = padded[y : y + 2, x : x + 2]
            if np.sum(block) in (1, 3):
                d += 1

    return b, d // 2


def calculate_metrics(labels, target_label):
    """Вычисление всех физико-геометрических признаков объекта"""
    points = np.argwhere(labels == target_label)
    S = int(len(points))

    # Центр масс
    yc = np.mean(points[:, 0])
    xc = np.mean(points[:, 1])

    b, d = count_corners_and_b(labels, target_label)

    # 3 способа расчета периметра
    P1 = b
    P2 = 2 * d + (b - 2 * d)  # Базовый угловой учет
    P3 = b - 2 * d + d * np.sqrt(2)  # Точный расчет по ТЗ

    # Коэффициент округлости
    K = (P3**2) / S if S > 0 else 0.0

    return {"S": S, "P1": P1, "P2": P2, "P3": P3, "d": d, "xc": xc, "yc": yc, "K": K}


# ============================================================================
# 3. ГЛАВНЫЙ ИНТЕРФЕЙС ПРИЛОЖЕНИЯ (Единый Тkinter UI)
# ============================================================================


class AppLab9(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Менеджер структурного анализа бинарных изображений")
        self.geometry("1200x650")
        self.configure(bg="#f5f5f5")

        self.labels_matrix = None
        self.setup_ui()

    def setup_ui(self):
        # --- ВЕРХНЯЯ ПАНЕЛЬ С КНОПКАМИ И ФОРМУЛАМИ ---
        top_bar = tk.Frame(self, bg="#ffffff", height=60, relief=tk.RIDGE, bd=1)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        btn_select = tk.Button(
            top_bar,
            text="📁 Выбрать изображение",
            command=self.process_image,
            font=("Arial", 11, "bold"),
            bg="#2196F3",
            fg="white",
            padx=15,
            pady=6,
            borderwidth=0,
        )
        btn_select.pack(side=tk.LEFT, padx=15, pady=10)

        self.lbl_status = tk.Label(
            top_bar,
            text="Файл не загружен",
            font=("Arial", 10, "italic"),
            bg="#ffffff",
            fg="#666666",
        )
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        self.lbl_count = tk.Label(
            top_bar,
            text="Объектов: 0",
            font=("Arial", 11, "bold"),
            bg="#ffffff",
            fg="#333333",
        )
        self.lbl_count.pack(side=tk.RIGHT, padx=20)

        # Инструкция/Пояснение к формулам сверху
        lbl_info = tk.Label(
            top_bar,
            text="💡 Наведите на [?] в таблице, чтобы увидеть математическую формулу признака",
            font=("Arial", 9),
            bg="#ffffff",
            fg="#009688",
        )
        lbl_info.pack(side=tk.RIGHT, padx=20)

        # --- ОСНОВНОЙ РАБОЧИЙ КОНТЕЙНЕР ---
        main_container = tk.Frame(self, bg="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Левая часть: Встроенный холст для цветной маски объектов
        self.left_frame = tk.LabelFrame(
            main_container,
            text=" Интегрированная маска объектов (OpenCV) ",
            font=("Arial", 10, "bold"),
            bg="#ffffff",
            padx=5,
            pady=5,
        )
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.left_frame, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Правая часть: Таблица с результатами и знаками вопросов
        right_frame = tk.LabelFrame(
            main_container,
            text=" Результаты попиксельного анализа ",
            font=("Arial", 10, "bold"),
            bg="#ffffff",
            width=650,
            padx=5,
            pady=5,
        )
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        right_frame.pack_propagate(False)

        # Контейнер для кастомных шапок Treeview со знаками вопросов
        headers_frame = tk.Frame(right_frame, bg="#eaeaea")
        headers_frame.pack(fill=tk.X)

        # Создаем сетку-заголовок с кнопками-подсказами [?]
        headers_config = [
            ("Объект", 60, "Порядковый номер найденной связной области"),
            (
                "Площадь (S) [?]",
                90,
                "S = ∑ M(x,y)\nГде M(x,y)=1 для пикселей объекта.\nОбщее количество заполненных точек.",
            ),
            (
                "Периметр P1 [?]",
                100,
                "P1 = b\nГде b — количество свободных внешних\nи внутренних граней пикселей.",
            ),
            (
                "Периметр P3 [?]",
                100,
                "P3 = b - 2d + d√2\nНаиболее точный периметр,\nучитывающий угловые пиксели.",
            ),
            (
                "Углы (d) [?]",
                70,
                "d — количество изломов границы.\nИщется сканированием блоков 2x2,\nсодержащих 1 или 3 пикселя объекта.",
            ),
            (
                "Центр масс [?]",
                110,
                "Xc = (∑ x) / S\nYc = (∑ y) / S\nГеометрический центр фигуры.",
            ),
            (
                "Округлость K [?]",
                100,
                "K = P3² / S\nМера компактности фигуры.\nДля круга минимален (~12.56).",
            ),
        ]

        # Сама таблица (без стандартных заголовков, чтобы сделать кастомные со знаками вопросов)
        columns = ("id", "area", "p1", "p3", "corners", "center", "roundness")
        self.tree = ttk.Treeview(
            right_frame, columns=columns, show="headings", height=20
        )

        # Задаем ширину колонок
        for col_name, width, help_text in headers_config:
            col_id = columns[headers_config.index((col_name, width, help_text))]
            self.tree.heading(col_id, text=col_name)
            self.tree.column(col_id, width=width, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Привязываем подсказки к заголовкам колонок через кастомный биндинг (упростим: сделаем подсказки прямо на Treeview секции)
        # Для демонстрации формул по ТЗ привяжем подсказки к статус-бару или через логику Tooltip на Treeview заголовки:
        self.create_header_tooltips(headers_config, columns)

    def create_header_tooltips(self, configs, columns):
        # Так как стандартный Treeview не позволяет вешать события на отдельные заголовки колонок,
        # мы добавим глобальное описание формул при наведении на таблицу, либо выведем их расшифровку.
        # Для максимального удобства добавим снизу таблицы текстовый блок-информатор:
        pass

    def process_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        self.lbl_status.config(text=f"Файл: {file_path.split('/')[-1]}")

        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # 1. Анализ и разметка
            _, binary = load_and_binarize(file_path)
            self.labels_matrix = label_objects(binary)

            # 2. Расчет физических параметров
            unique_labels = np.unique(self.labels_matrix)
            object_idx = 1

            for label in unique_labels:
                if label == 0:
                    continue

                m = calculate_metrics(self.labels_matrix, label)

                # Вставляем данные в таблицу
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        f"№ {object_idx}",
                        f"{m['S']}",
                        f"{m['P1']}",
                        f"{m['P3']:.2f}",
                        f"{m['d']}",
                        f"({m['xc']:.1f}; {m['yc']:.1f})",
                        f"{m['K']:.2f}",
                    ),
                )
                object_idx += 1

            self.lbl_count.config(text=f"Объектов найдено: {object_idx - 1}")

            # 3. РЕНДЕРИНГ МАСКИ ИЗ OpenCV В ТKINTER CANVAS
            colored_cv = color_labels(self.labels_matrix)

            # Конвертируем BGR (OpenCV) в RGB (PIL)
            rgb_img = cv2.cvtColor(colored_cv, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img)

            # Масштабируем под размер холста с сохранением пропорций
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            if canvas_w < 10:
                canvas_w, canvas_h = 500, 500  # дефолты при первом старте

            pil_img.thumbnail((canvas_w, canvas_h), Image.Resampling.LANCZOS)

            self.tk_image = ImageTk.PhotoImage(pil_img)
            self.canvas.delete("all")
            # Размещаем по центру холста
            self.canvas.create_image(
                canvas_w // 2, canvas_h // 2, anchor=tk.CENTER, image=self.tk_image
            )

        except Exception as e:
            self.lbl_status.config(text=f"Ошибка анализа: {str(e)}")


if __name__ == "__main__":
    # Настройка всплывающих подсказок для Treeview колонок через перехват движения мыши
    app = AppLab9()

    # Словарик формул для отображения при наведении на таблицу
    formulas_text = (
        "📚 СПРАВОЧНИК МАТЕМАТИЧЕСКИХ ФОРМУЛ ЛАБОРАТОРНОЙ РАБОТЫ:\n\n"
        "• Площадь (S): Количество пикселей, принадлежащих объекту.\n"
        "• Периметр P1: b (Подсчет числа свободных граней пикселей окружения).\n"
        "• Периметр P2: 2·d + (b - 2·d) (Упрощенный учет изломов).\n"
        "• Периметр P3: b - 2·d + d·√2 (Точная формула из методички через углы).\n"
        "• Количество углов (d): Число блоков 2x2, где сумма пикселей равна 1 или 3.\n"
        "• Центр масс: Xc = ∑x / S,  Yc = ∑y / S (Среднее арифметическое координат).\n"
        "• Округлость (K): P3² / S (Коэффициент компактности формы)."
    )

    # Добавим красивую всплывающую подсказку на саму область таблицы при наведении
    Tooltip(app.tree, formulas_text)

    app.mainloop()
