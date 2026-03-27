from __future__ import annotations

import tkinter as tk
from tkinter import ttk

GRID_SIZE = 5
CELL_SIZE = 58
FILLED_COLOR = "#1f4e79"
EMPTY_COLOR = "#f6f8fb"

LETTER_PATTERNS: dict[str, list[list[int]]] = {
    "С": [
        [0, 1, 1, 1, 1],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [0, 1, 1, 1, 1],
    ],
    "О": [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
    ],
    "Т": [
        [1, 1, 1, 1, 1],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
    ],
    "А": [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
    ],
    "П": [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
    ],
}


def xor_distance(
    input_matrix: list[list[int]], reference_matrix: list[list[int]]
) -> int:
    # Считает число несовпадающих пикселей между вводом и эталоном.
    return sum(
        input_cell ^ reference_cell
        for input_row, reference_row in zip(input_matrix, reference_matrix)
        for input_cell, reference_cell in zip(input_row, reference_row)
    )


class LetterRecognitionApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Распознавание букв 5x5")
        self.root.geometry("860x560")

        self.grid_state = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.cell_rectangles: list[list[int]] = []

        self.alphabet_var = tk.StringVar(
            value="Доступный алфавит: " + ", ".join(LETTER_PATTERNS.keys())
        )
        self.result_var = tk.StringVar(
            value="Результат детекции появится после нажатия на кнопку."
        )
        self.status_var = tk.StringVar(
            value="Заполните матрицу 5x5, затем нажмите «Распознать»."
        )

        self._build_ui()
        self._draw_grid()

    def _build_ui(self) -> None:
        # Создает две панели: слева матрица ввода, справа сведения и результат.
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(1, weight=1)

        grid_frame = ttk.LabelFrame(container, text="Матрица ввода", padding=12)
        grid_frame.grid(row=0, column=0, sticky="nsw", padx=(0, 14))

        canvas_size = GRID_SIZE * CELL_SIZE
        self.canvas = tk.Canvas(
            grid_frame,
            width=canvas_size,
            height=canvas_size,
            bg="white",
            highlightthickness=0,
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        button_row = ttk.Frame(grid_frame)
        button_row.pack(fill=tk.X, pady=(12, 0))
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)

        ttk.Button(button_row, text="Распознать", command=self.recognize).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ttk.Button(button_row, text="Очистить", command=self.clear_grid).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        info_frame = ttk.Frame(container)
        info_frame.grid(row=0, column=1, sticky="nsew")
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(2, weight=1)

        ttk.Label(
            info_frame,
            textvariable=self.alphabet_var,
            font=("Segoe UI", 12, "bold"),
            wraplength=460,
            justify=tk.LEFT,
        ).grid(row=0, column=0, sticky="ew")

        ttk.Label(
            info_frame,
            text=(
                "Закрашенная клетка = 1, пустая клетка = 0.\n"
                "Сравнение с эталонами выполняется по XOR, затем считается сумма отличий."
            ),
            wraplength=460,
            justify=tk.LEFT,
        ).grid(row=1, column=0, sticky="ew", pady=(10, 12))

        result_frame = ttk.LabelFrame(info_frame, text="Результат и веса", padding=12)
        result_frame.grid(row=2, column=0, sticky="nsew")
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(1, weight=1)

        ttk.Label(
            result_frame,
            textvariable=self.result_var,
            font=("Segoe UI", 13, "bold"),
            wraplength=420,
            justify=tk.LEFT,
        ).grid(row=0, column=0, sticky="ew")

        self.weights_text = tk.Text(
            result_frame,
            height=12,
            width=32,
            state=tk.DISABLED,
            font=("Consolas", 11),
            wrap=tk.WORD,
        )
        self.weights_text.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        ttk.Label(
            info_frame,
            textvariable=self.status_var,
            wraplength=460,
            justify=tk.LEFT,
        ).grid(row=3, column=0, sticky="ew", pady=(12, 0))

    def _draw_grid(self) -> None:
        # Рисует 5x5 ячеек и запоминает идентификаторы прямоугольников.
        self.canvas.delete("all")
        self.cell_rectangles = []

        for row in range(GRID_SIZE):
            rectangle_row: list[int] = []
            for col in range(GRID_SIZE):
                x1 = col * CELL_SIZE
                y1 = row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                rect_id = self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=EMPTY_COLOR,
                    outline="#a7b7c7",
                    width=2,
                )
                rectangle_row.append(rect_id)
            self.cell_rectangles.append(rectangle_row)

    def on_canvas_click(self, event: tk.Event[tk.Canvas]) -> None:
        # Переключает состояние клетки, по которой кликнул пользователь.
        row = event.y // CELL_SIZE
        col = event.x // CELL_SIZE
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            self.grid_state[row][col] ^= 1
            self._refresh_cell(row, col)

    def _refresh_cell(self, row: int, col: int) -> None:
        # Обновляет цвет одной ячейки в зависимости от ее бинарного значения.
        color = FILLED_COLOR if self.grid_state[row][col] else EMPTY_COLOR
        self.canvas.itemconfigure(self.cell_rectangles[row][col], fill=color)

    def clear_grid(self) -> None:
        # Сбрасывает пользовательскую матрицу и текст результата.
        self.grid_state = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                self._refresh_cell(row, col)

        self.result_var.set("Результат детекции появится после нажатия на кнопку.")
        self.status_var.set("Матрица очищена.")
        self._set_weights_text(
            "Нажмите «Распознать», чтобы увидеть веса для всех букв."
        )

    def recognize(self) -> None:
        # Вычисляет расстояния до всех эталонов и показывает ближайшую букву.
        distances = {
            letter: xor_distance(self.grid_state, pattern)
            for letter, pattern in LETTER_PATTERNS.items()
        }
        best_letter = min(distances, key=distances.get)
        best_score = distances[best_letter]

        weights_lines = ["Буква | Вес S", "--------------"]
        for letter, score in sorted(
            distances.items(), key=lambda item: (item[1], item[0])
        ):
            weights_lines.append(f"  {letter}   |   {score}")

        self.result_var.set(
            f"Наиболее вероятная буква: {best_letter} (минимальный вес S = {best_score})."
        )
        self.status_var.set(
            "Распознавание завершено. Чем меньше значение S, тем ближе введенная матрица к эталону."
        )
        self._set_weights_text("\n".join(weights_lines))

    def _set_weights_text(self, value: str) -> None:
        # Перезаписывает текстовый блок с вычисленными весами.
        self.weights_text.configure(state=tk.NORMAL)
        self.weights_text.delete("1.0", tk.END)
        self.weights_text.insert("1.0", value)
        self.weights_text.configure(state=tk.DISABLED)


def main() -> None:
    # Создает и запускает окно приложения.
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")

    app = LetterRecognitionApp(root)
    app._set_weights_text("Нажмите «Распознать», чтобы увидеть веса для всех букв.")
    root.minsize(820, 520)
    root.mainloop()


if __name__ == "__main__":
    main()
