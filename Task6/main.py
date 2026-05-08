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


# ТВОИ АЛГОРИТМЫ (БЕЗ ИЗМЕНЕНИЙ)
def dfs_method(mat):
    rows = len(mat)
    cols = len(mat[0])

    def dfs(r, c, label):
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return
        if mat[r][c] != 1:
            return
        mat[r][c] = label
        dfs(r + 1, c, label)
        dfs(r - 1, c, label)
        dfs(r, c + 1, label)
        dfs(r, c - 1, label)

    label = 2
    count = 0
    for i in range(rows):
        for j in range(cols):
            if mat[i][j] == 1:
                dfs(i, j, label)
                label += 1
                count += 1
    return mat, count


def row_method(mat):
    rows = len(mat)
    cols = len(mat[0])
    label = 2
    equivalence = []
    for i in range(rows):
        for j in range(cols):
            if mat[i][j] == 1:
                left = mat[i][j - 1] if j > 0 else 0
                up = mat[i - 1][j] if i > 0 else 0
                if left == 0 and up == 0:
                    mat[i][j] = label
                    label += 1
                elif left != 0 and up == 0:
                    mat[i][j] = left
                elif left == 0 and up != 0:
                    mat[i][j] = up
                else:
                    mat[i][j] = left
                    if left != up:
                        equivalence.append((up, left))
    for a, b in equivalence:
        for i in range(rows):
            for j in range(cols):
                if mat[i][j] == a:
                    mat[i][j] = b
    unique = set()
    for row in mat:
        for val in row:
            if val > 1:
                unique.add(val)
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
