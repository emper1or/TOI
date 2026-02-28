import tkinter as tk


class ObjectCounterApp:
    def __init__(self, root, grid_size=20, cell_size=25):
        self.root = root
        self.root.title("AI Object Counter (Corner Method)")

        self.grid_size = grid_size
        self.cell_size = cell_size

        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]

        self.setup_ui()

    def setup_ui(self):
        """Создание элементов интерфейса"""
        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.btn_calc = tk.Button(
            self.toolbar, text="Посчитать объекты", command=self.calculate_objects
        )
        self.btn_calc.pack(side=tk.LEFT, padx=5)

        self.btn_clear = tk.Button(
            self.toolbar, text="Очистить поле", command=self.clear_grid
        )
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        self.label_res = tk.Label(
            self.toolbar, text="Объектов: 0", font=("Arial", 12, "bold")
        )
        self.label_res.pack(side=tk.RIGHT, padx=20)

        self.canvas_width = self.grid_size * self.cell_size
        self.canvas_height = self.grid_size * self.cell_size
        self.canvas = tk.Canvas(
            self.root, width=self.canvas_width, height=self.canvas_height, bg="white"
        )
        self.canvas.pack(padx=10, pady=10)

        self.canvas.bind("<Button-1>", self.handle_click)
        self.draw_grid_lines()

    def draw_grid_lines(self):
        """Рисует сетку"""
        for i in range(self.grid_size + 1):
            pos = i * self.cell_size
            self.canvas.create_line(pos, 0, pos, self.canvas_height, fill="lightgray")
            self.canvas.create_line(0, pos, self.canvas_width, pos, fill="lightgray")

    def handle_click(self, event):
        """Обработка клика: переключение состояния клетки"""
        col = event.x // self.cell_size
        row = event.y // self.cell_size

        if 0 <= col < self.grid_size and 0 <= row < self.grid_size:
            self.grid[row][col] = 1 - self.grid[row][col]
            self.redraw_cell(row, col)

    def redraw_cell(self, row, col):
        """Перерисовывает конкретную клетку"""
        x1 = col * self.cell_size
        y1 = row * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size

        tag = f"cell_{row}_{col}"
        self.canvas.delete(tag)

        if self.grid[row][col] == 1:
            self.canvas.create_rectangle(
                x1, y1, x2, y2, fill="black", outline="gray", tags=tag
            )

    def clear_grid(self):
        """Полная очистка поля"""
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.canvas.delete("all")
        self.draw_grid_lines()
        self.label_res.config(text="Объектов: 0")

    def get_val(self, r, c):
        """Безопасное получение значения клетки"""
        if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
            return self.grid[r][c]
        return 0

    def calculate_objects(self):
        """Алгоритм подсчета объектов"""
        ext_corners = 0
        int_corners = 0

        for r in range(-1, self.grid_size):
            for c in range(-1, self.grid_size):
                block_sum = (
                    self.get_val(r, c)
                    + self.get_val(r, c + 1)
                    + self.get_val(r + 1, c)
                    + self.get_val(r + 1, c + 1)
                )

                if block_sum == 1:
                    ext_corners += 1
                elif block_sum == 3:
                    int_corners += 1
        objects_count = (ext_corners - int_corners) / 4

        self.label_res.config(text=f"Объектов: {int(objects_count)}")

        print(f"Ext: {ext_corners}, Int: {int_corners} -> Result: {objects_count}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ObjectCounterApp(root, grid_size=20, cell_size=25)
    root.mainloop()
