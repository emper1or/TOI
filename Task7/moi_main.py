import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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

    # Используем 4-связность: соседями считаются только клетки сверху, снизу,
    # слева и справа. Диагональные касания не объединяют объекты.
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for y in range(h):
        for x in range(w):
            if image[y, x] == 1:
                # Найден новый объект. Все его пиксели получат одинаковую метку.
                stack = [(x, y)]
                image[y, x] = current_label

                while stack:
                    cx, cy = stack.pop()
                    for dx, dy in directions:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h and image[ny, nx] == 1:
                            # Соседний пиксель принадлежит текущему объекту:
                            # помечаем его и добавляем в стек для дальнейшего обхода.
                            image[ny, nx] = current_label
                            stack.append((nx, ny))
                current_label += 1

    return image


def color_labels(labels):
    """Генерация цветного изображения по меткам"""
    h, w = labels.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)
    # Фиксируем seed, чтобы цвета объектов не менялись при каждом запуске.
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
    """Расчет свободных граней (b) и диагональных изломов (d) через блоки 2x2"""
    h, w = labels.shape
    # Бинарная маска только для выбранного объекта
    obj_mask = (labels == target_label).astype(np.uint8)
    # Нулевая рамка для корректного обхода краев
    padded = np.pad(obj_mask, 1, mode="constant", constant_values=0)

    b = 0
    # 1. Считаем свободные грани (b)
    for y in range(h):
        for x in range(w):
            if obj_mask[y, x] == 1:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if nx < 0 or ny < 0 or nx >= w or ny >= h or obj_mask[ny, nx] == 0:
                        b += 1

    d = 0
    # 2. Считаем диагональные изломы (d)
    for y in range(padded.shape[0] - 1):
        for x in range(padded.shape[1] - 1):
            block = padded[y : y + 2, x : x + 2]
            # Истинный "диагональный излом" (внутренний угол ступенчатой границы) —
            # это блок 2x2, где ровно ТРИ пикселя объекта и ОДИН пиксель фона.
            # Внешние прямые углы (где сумма = 1) игнорируются.
            if np.sum(block) == 3:
                d += 1

    return b, d


def calculate_metrics(labels, target_label):
    """Вычисление всех физико-геометрических признаков объекта"""
    # Координаты всех пикселей, которые имеют метку анализируемого объекта.
    points = np.argwhere(labels == target_label)
    S = int(len(points))

    # Центр масс
    yc = np.mean(points[:, 0])
    xc = np.mean(points[:, 1])

    b, d = count_corners_and_b(labels, target_label)

    # 3 способа расчета периметра
    P1 = b
    P2 = d * np.sqrt(2)  # Базовый угловой учет
    P3 = b - 2 * d + d * np.sqrt(2)  # Точный расчет по ТЗ

    # Коэффициент округлости
    K = (P1**2) / S if S > 0 else 0.0

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

        self.labels_matrix = None  # Матрица меток после анализа объектов.
        self.manual_binary = None  # Матрица, которую пользователь рисует вручную.
        self.manual_editing = False  # Флаг режима редактирования ручной матрицы.
        self.manual_rows_var = tk.IntVar(value=10)
        self.manual_cols_var = tk.IntVar(value=10)
        self.manual_cell_size = 24  # Размер клетки при отрисовке ручной матрицы.
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

        manual_panel = tk.Frame(top_bar, bg="#ffffff")
        manual_panel.pack(side=tk.LEFT, padx=5, pady=8)

        tk.Label(
            manual_panel,
            text="Матрица:",
            font=("Arial", 9),
            bg="#ffffff",
            fg="#333333",
        ).pack(side=tk.LEFT, padx=(0, 4))

        tk.Spinbox(
            manual_panel,
            from_=2,
            to=50,
            width=4,
            textvariable=self.manual_rows_var,
            font=("Arial", 9),
        ).pack(side=tk.LEFT)

        tk.Label(
            manual_panel,
            text="x",
            font=("Arial", 9),
            bg="#ffffff",
            fg="#333333",
        ).pack(side=tk.LEFT, padx=3)

        tk.Spinbox(
            manual_panel,
            from_=2,
            to=50,
            width=4,
            textvariable=self.manual_cols_var,
            font=("Arial", 9),
        ).pack(side=tk.LEFT)

        tk.Button(
            manual_panel,
            text="Создать",
            command=self.create_manual_matrix,
            font=("Arial", 9, "bold"),
            bg="#607D8B",
            fg="white",
            padx=8,
            pady=4,
            borderwidth=0,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            manual_panel,
            text="Анализ матрицы",
            command=self.process_manual_matrix,
            font=("Arial", 9, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=8,
            pady=4,
            borderwidth=0,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            manual_panel,
            text="Очистить",
            command=self.clear_manual_matrix,
            font=("Arial", 9),
            bg="#eeeeee",
            fg="#333333",
            padx=8,
            pady=4,
            borderwidth=0,
        ).pack(side=tk.LEFT)

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
        self.canvas.bind("<Button-1>", self.toggle_manual_cell)

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

    def clear_results(self):
        """Очищает таблицу результатов перед новым анализом"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def create_manual_matrix(self):
        """Создает пустую бинарную матрицу заданного пользователем размера"""
        rows = self.manual_rows_var.get()
        cols = self.manual_cols_var.get()

        if rows < 2 or cols < 2:
            messagebox.showwarning(
                "Ошибка", "Размерность матрицы должна быть не меньше 2x2"
            )
            return

        self.manual_binary = np.zeros((rows, cols), dtype=np.uint8)
        self.manual_editing = True
        self.labels_matrix = None
        self.clear_results()
        self.lbl_count.config(text="Объектов: 0")
        self.lbl_status.config(
            text=f"Ручной режим: матрица {rows}x{cols}. Кликайте по клеткам"
        )
        self.draw_manual_matrix()

    def draw_manual_matrix(self):
        """Отрисовывает ручную матрицу на холсте"""
        if self.manual_binary is None:
            return

        self.manual_editing = True
        rows, cols = self.manual_binary.shape
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 10:
            canvas_w, canvas_h = 500, 500

        # Размер клетки подбирается так, чтобы вся матрица помещалась на холсте.
        cell_w = max(8, min(36, (canvas_w - 20) // cols))
        cell_h = max(8, min(36, (canvas_h - 20) // rows))
        self.manual_cell_size = min(cell_w, cell_h)

        grid_w = cols * self.manual_cell_size
        grid_h = rows * self.manual_cell_size
        start_x = max(10, (canvas_w - grid_w) // 2)
        start_y = max(10, (canvas_h - grid_h) // 2)

        self.manual_grid_origin = (start_x, start_y)
        self.canvas.delete("all")

        for y in range(rows):
            for x in range(cols):
                x1 = start_x + x * self.manual_cell_size
                y1 = start_y + y * self.manual_cell_size
                x2 = x1 + self.manual_cell_size
                y2 = y1 + self.manual_cell_size
                value = self.manual_binary[y, x]
                # Единица обозначает пиксель объекта, ноль — фон.
                fill = "#222222" if value == 1 else "#ffffff"
                text = "1" if value == 1 and self.manual_cell_size >= 18 else ""

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill,
                    outline="#777777",
                    width=1,
                )
                if text:
                    self.canvas.create_text(
                        (x1 + x2) // 2,
                        (y1 + y2) // 2,
                        text=text,
                        fill="#ffffff",
                        font=("Arial", 9, "bold"),
                    )

    def toggle_manual_cell(self, event):
        """Переключает значение клетки ручной матрицы по клику мыши"""
        if self.manual_binary is None or not self.manual_editing:
            return

        start_x, start_y = self.manual_grid_origin
        x = (event.x - start_x) // self.manual_cell_size
        y = (event.y - start_y) // self.manual_cell_size
        rows, cols = self.manual_binary.shape

        if 0 <= x < cols and 0 <= y < rows:
            # Повторный клик по клетке возвращает ее в противоположное состояние.
            self.manual_binary[y, x] = 0 if self.manual_binary[y, x] else 1
            self.draw_manual_matrix()

    def clear_manual_matrix(self):
        """Сбрасывает ручную матрицу в нули"""
        if self.manual_binary is None:
            self.create_manual_matrix()
            return

        self.manual_binary[:, :] = 0
        self.labels_matrix = None
        self.clear_results()
        self.lbl_count.config(text="Объектов: 0")
        self.lbl_status.config(text="Ручная матрица очищена")
        self.draw_manual_matrix()

    def process_manual_matrix(self):
        """Запускает анализ матрицы, нарисованной пользователем"""
        if self.manual_binary is None:
            self.create_manual_matrix()

        if self.manual_binary is None:
            return

        if not np.any(self.manual_binary):
            messagebox.showwarning(
                "Пустая матрица", "Нарисуйте объект единицами перед анализом"
            )
            return

        self.analyze_binary(self.manual_binary, "Ручная матрица")

    def analyze_binary(self, binary, source_name):
        """Выполняет маркировку объектов и выводит признаки в таблицу"""
        self.clear_results()
        self.labels_matrix = label_objects(binary)

        unique_labels = np.unique(self.labels_matrix)
        object_idx = 1

        for label in unique_labels:
            if label == 0:
                continue

            # Для каждой связной области отдельно считаются площадь, периметры,
            # углы, центр масс и коэффициент округлости.
            m = calculate_metrics(self.labels_matrix, label)

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
        self.lbl_status.config(text=f"{source_name}: анализ выполнен")
        self.render_labels_matrix()

    def render_labels_matrix(self):
        """Показывает цветную карту найденных объектов на холсте"""
        if self.labels_matrix is None:
            return

        self.manual_editing = False
        colored_cv = color_labels(self.labels_matrix)
        rgb_img = cv2.cvtColor(colored_cv, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 10:
            canvas_w, canvas_h = 500, 500

        # Масштабируем изображение без сглаживания, чтобы пиксельная структура
        # бинарной матрицы оставалась хорошо заметной.
        pil_img.thumbnail((canvas_w, canvas_h), Image.Resampling.NEAREST)

        self.tk_image = ImageTk.PhotoImage(pil_img)
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_w // 2, canvas_h // 2, anchor=tk.CENTER, image=self.tk_image
        )

    def process_image(self):
        """Выбирает файл изображения и запускает его бинарный анализ"""
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

        try:
            # 1. Анализ и разметка
            _, binary = load_and_binarize(file_path)
            # При загрузке изображения ручной режим отключается.
            self.manual_binary = None
            self.manual_editing = False
            self.analyze_binary(binary, file_path.split("/")[-1])

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
