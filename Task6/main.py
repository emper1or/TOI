import copy
import tkinter as tk
from tkinter import messagebox

# ТВОЯ МАТРИЦА
matrix = [
    [0, 1, 1, 0, 0, 0, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 1, 1, 1, 1],
    [1, 1, 1, 0, 0, 0, 0, 0, 1, 1],
    [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 1, 0, 1, 1, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 1, 1, 0],
    [0, 1, 0, 0, 0, 0, 0, 1, 1, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
]


def print_matrix(mat, title):
    print(title)
    for row in mat:
        print(" ".join(f"{val:2}" for val in row))
    print()


# ТВОИ АЛГОРИТМЫ
def dfs_method(mat):
    rows = len(mat)
    cols = len(mat[0])

    print("\n=== Рекурсивный метод ===")
    print_matrix(mat, "Исходная матрица:")

    def dfs(r, c, label, depth=0):
        indent = "  " * depth
        if r < 0 or r >= rows or c < 0 or c >= cols:
            print(f"{indent}Клетка ({r}, {c}) вне матрицы, возврат")
            return
        if mat[r][c] != 1:
            print(
                f"{indent}Клетка ({r}, {c}) уже не равна 1 "
                f"(значение: {mat[r][c]}), возврат"
            )
            return

        print(f"{indent}Клетка ({r}, {c}) получает метку {label}")
        mat[r][c] = label
        dfs(r + 1, c, label, depth + 1)
        dfs(r - 1, c, label, depth + 1)
        dfs(r, c + 1, label, depth + 1)
        dfs(r, c - 1, label, depth + 1)

    label = 2
    count = 0
    for i in range(rows):
        for j in range(cols):
            if mat[i][j] == 1:
                print(f"Найден новый объект в клетке ({i}, {j}), метка {label}")
                dfs(i, j, label)
                print_matrix(mat, f"Матрица после обработки объекта {label}:")
                label += 1
                count += 1
    print(f"Рекурсивный метод завершен. Найдено объектов: {count}")
    return mat, count


def row_method(mat):
    rows = len(mat)
    cols = len(mat[0])
    label = 2
    equivalence = []

    print("\n=== Построчный метод ===")
    print_matrix(mat, "Исходная матрица:")

    for i in range(rows):
        print(f"Обработка строки {i}")
        for j in range(cols):
            if mat[i][j] == 1:
                left = mat[i][j - 1] if j > 0 else 0
                up = mat[i - 1][j] if i > 0 else 0
                print(f"  Клетка ({i}, {j}): left={left}, up={up}")
                if left == 0 and up == 0:
                    mat[i][j] = label
                    print(f"    Соседей нет, назначена новая метка {label}")
                    label += 1
                elif left != 0 and up == 0:
                    mat[i][j] = left
                    print(f"    Взята метка слева: {left}")
                elif left == 0 and up != 0:
                    mat[i][j] = up
                    print(f"    Взята метка сверху: {up}")
                else:
                    mat[i][j] = left
                    print(f"    Взята метка слева: {left}")
                    if left != up:
                        equivalence.append((up, left))
                        print(f"    Добавлена эквивалентность: {up} -> {left}")
        print_matrix(mat, f"Матрица после строки {i}:")

    if equivalence:
        print(f"Эквивалентные метки для объединения: {equivalence}")
    else:
        print("Эквивалентных меток нет")

    for a, b in equivalence:
        print(f"Замена метки {a} на {b}")
        for i in range(rows):
            for j in range(cols):
                if mat[i][j] == a:
                    mat[i][j] = b
        print_matrix(mat, f"Матрица после замены {a} -> {b}:")

    unique = set()
    for row in mat:
        for val in row:
            if val > 1:
                unique.add(val)
    print(f"Построчный метод завершен. Найдено объектов: {len(unique)}")
    return mat, len(unique)


# --- ИНТЕРФЕЙС (UI) ---


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Маркировка изображений")
        self.cells = []
        self.current_matrix = copy.deepcopy(matrix)

        # Палитра цветов для маркеров (10, 20, 30...)
        self.colors = {0: "white", 1: "gray"}
        self.marker_colors = [
            "#FF5733",
            "#33FF57",
            "#3357FF",
            "#F333FF",
            "#FFF333",
            "#33FFF3",
        ]

        self.create_widgets()
        self.draw_matrix()

    def create_widgets(self):
        # Сетка
        self.grid_frame = tk.Frame(self.root)
        self.grid_frame.pack(pady=10)

        # Кнопки управления
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="Рекурсивный", command=lambda: self.run_algo("dfs")
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            btn_frame, text="Построчный", command=lambda: self.run_algo("row")
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Сброс", command=self.reset).pack(
            side=tk.LEFT, padx=5
        )

    def draw_matrix(self):
        # Очистка старой сетки
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        self.cells = []
        for i in range(len(self.current_matrix)):
            row_cells = []
            for j in range(len(self.current_matrix[0])):
                val = self.current_matrix[i][j]
                color = self.get_color(val)
                lbl = tk.Label(
                    self.grid_frame,
                    text=str(val) if val != 0 else "",
                    width=4,
                    height=2,
                    relief="ridge",
                    bg=color,
                )
                lbl.grid(row=i, column=j)
                row_cells.append(lbl)
            self.cells.append(row_cells)

    def get_color(self, val):
        if val == 0:
            return "white"
        if val == 1:
            return "#D3D3D3"  # серый для неразмеченных
        # Для маркеров (2, 3, 4...) выбираем цвет из списка по кругу
        return self.marker_colors[(val - 2) % len(self.marker_colors)]

    def run_algo(self, mode):
        # Запуск твоего алгоритма
        if mode == "dfs":
            res, count = dfs_method(copy.deepcopy(self.current_matrix))
        else:
            res, count = row_method(copy.deepcopy(self.current_matrix))

        self.current_matrix = res
        self.draw_matrix()
        messagebox.showinfo("Готово", f"Объектов найдено: {count}")

    def reset(self):
        self.current_matrix = copy.deepcopy(matrix)
        self.draw_matrix()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
