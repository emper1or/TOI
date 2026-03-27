from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np
from PIL import Image, ImageTk

PREVIEW_SIZE = (420, 420)


def clamp_to_byte(value: float) -> np.uint8:
    # Ограничивает вычисленное значение диапазоном допустимого байта изображения.
    return np.uint8(min(255, max(0, round(value))))


def apply_manual_convolution(
    image_array: np.ndarray,
    kernel: np.ndarray,
    normalize: bool,
) -> np.ndarray:
    # Выполняет ручную свертку RGB-изображения ядром 3x3 с обработкой границ.
    if image_array.ndim != 3 or image_array.shape[2] != 3:
        raise ValueError("Ожидается цветное RGB-изображение.")

    height, width, channels = image_array.shape
    result = np.zeros((height, width, channels), dtype=np.uint8)

    kernel_sum = float(kernel.sum())
    divider = kernel_sum if normalize and abs(kernel_sum) > 1e-12 else 1.0

    for y in range(height):
        for x in range(width):
            for channel in range(channels):
                total = 0.0
                for ky in range(-1, 2):
                    for kx in range(-1, 2):
                        source_y = min(max(y + ky, 0), height - 1)
                        source_x = min(max(x + kx, 0), width - 1)
                        pixel = float(image_array[source_y, source_x, channel])
                        total += pixel * float(kernel[ky + 1, kx + 1])

                total /= divider
                result[y, x, channel] = clamp_to_byte(total)

    return result


class ConvolutionApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Ручная свертка изображения")
        self.root.geometry("1100x760")

        self.original_image: Image.Image | None = None
        self.filtered_image: Image.Image | None = None
        self.original_preview: ImageTk.PhotoImage | None = None
        self.filtered_preview: ImageTk.PhotoImage | None = None
        self.current_path: Path | None = None

        self.kernel_vars = [
            [tk.StringVar(value="0") for _ in range(3)] for _ in range(3)
        ]
        self.kernel_vars[1][1].set("1")
        self.normalize_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(
            value="Загрузите изображение, затем задайте ядро и примените фильтр."
        )

        self._build_ui()

    def _build_ui(self) -> None:
        # Собирает основное окно: панель параметров слева и область предпросмотра справа.
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        controls = ttk.LabelFrame(container, text="Параметры фильтра", padding=12)
        controls.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Button(controls, text="Открыть изображение", command=self.load_image).pack(
            fill=tk.X, pady=(0, 10)
        )

        kernel_frame = ttk.Frame(controls)
        kernel_frame.pack(pady=(0, 10))

        for row in range(3):
            for col in range(3):
                entry = ttk.Entry(
                    kernel_frame,
                    textvariable=self.kernel_vars[row][col],
                    justify="center",
                    width=8,
                )
                entry.grid(row=row, column=col, padx=4, pady=4)

        ttk.Checkbutton(
            controls,
            text="Нормировать по сумме ядра",
            variable=self.normalize_var,
        ).pack(anchor=tk.W, pady=(0, 10))

        ttk.Button(controls, text="Применить фильтр", command=self.apply_filter).pack(
            fill=tk.X, pady=(0, 10)
        )
        ttk.Button(controls, text="Сохранить результат", command=self.save_image).pack(
            fill=tk.X
        )

        info_text = (
            "Границы обрабатываются по ближайшему граничному пикселю.\n"
            "Если нормировка выключена, результат ограничивается в диапазоне 0..255.\n"
            "Если сумма ядра равна 0, нормировка не применяется."
        )
        ttk.Label(controls, text=info_text, wraplength=240, justify=tk.LEFT).pack(
            anchor=tk.W, pady=(16, 0)
        )
        ttk.Label(
            controls,
            textvariable=self.status_var,
            wraplength=240,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, fill=tk.X, pady=(12, 0))

        preview_area = ttk.Frame(container)
        preview_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))

        self.original_label = self._create_preview_block(
            preview_area, "Исходное изображение", 0
        )
        self.filtered_label = self._create_preview_block(
            preview_area, "Результат фильтрации", 1
        )

    def _create_preview_block(
        self, parent: ttk.Frame, title: str, column: int
    ) -> ttk.Label:
        # Создает отдельный блок для показа исходного изображения или результата.
        block = ttk.LabelFrame(parent, text=title, padding=10)
        block.grid(row=0, column=column, sticky="nsew", padx=6)
        parent.columnconfigure(column, weight=1)
        parent.rowconfigure(0, weight=1)

        label = ttk.Label(block, text="Нет изображения", anchor="center")
        label.pack(fill=tk.BOTH, expand=True)
        return label

    def load_image(self) -> None:
        # Загружает изображение с диска и показывает его в левой панели предпросмотра.
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        image = Image.open(file_path).convert("RGB")
        self.original_image = image
        self.filtered_image = None
        self.current_path = Path(file_path)

        self._update_preview(image, self.original_label, original=True)
        self.filtered_label.configure(
            image="", text="Результат появится после фильтрации"
        )
        self.status_var.set(f"Загружено изображение: {self.current_path}")

    def _read_kernel(self) -> np.ndarray:
        # Считывает значения из полей ввода и формирует матрицу ядра 3x3.
        values: list[list[float]] = []
        for row in self.kernel_vars:
            kernel_row: list[float] = []
            for cell in row:
                text = cell.get().strip().replace(",", ".")
                kernel_row.append(float(text))
            values.append(kernel_row)
        return np.array(values, dtype=np.float64)

    def apply_filter(self) -> None:
        # Запускает фильтрацию по введенному ядру и обновляет правую панель результата.
        if self.original_image is None:
            messagebox.showwarning("Нет изображения", "Сначала загрузите изображение.")
            return

        try:
            kernel = self._read_kernel()
        except ValueError:
            messagebox.showerror(
                "Ошибка ядра", "Все элементы ядра должны быть числами."
            )
            return

        source_array = np.array(self.original_image, dtype=np.float64)
        filtered_array = apply_manual_convolution(
            image_array=source_array,
            kernel=kernel,
            normalize=self.normalize_var.get(),
        )

        self.filtered_image = Image.fromarray(filtered_array, mode="RGB")
        self._update_preview(self.filtered_image, self.filtered_label, original=False)

        kernel_sum = float(kernel.sum())
        normalization_text = "включена" if self.normalize_var.get() else "выключена"
        self.status_var.set(
            f"Фильтрация завершена. Сумма ядра: {kernel_sum:.4g}. Нормировка {normalization_text}."
        )

    def save_image(self) -> None:
        # Сохраняет уже вычисленное изображение в выбранный пользователем файл.
        if self.filtered_image is None:
            messagebox.showwarning("Нет результата", "Сначала примените фильтр.")
            return

        initial_name = "filtered.png"
        if self.current_path is not None:
            initial_name = f"{self.current_path.stem}_filtered.png"

        file_path = filedialog.asksaveasfilename(
            title="Сохранить результат",
            defaultextension=".png",
            initialfile=initial_name,
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("BMP", "*.bmp"),
            ],
        )
        if not file_path:
            return

        self.filtered_image.save(file_path)
        self.status_var.set(f"Результат сохранен: {file_path}")

    def _update_preview(
        self, image: Image.Image, target: ttk.Label, original: bool
    ) -> None:
        # Подготавливает уменьшенную копию изображения и закрепляет ее в интерфейсе.
        preview = image.copy()
        preview.thumbnail(PREVIEW_SIZE)
        tk_image = ImageTk.PhotoImage(preview)
        target.configure(image=tk_image, text="")
        target.image = tk_image

        if original:
            self.original_preview = tk_image
        else:
            self.filtered_preview = tk_image


def main() -> None:
    # Создает и запускает главное окно приложения.
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")

    app = ConvolutionApp(root)
    root.minsize(980, 620)
    root.mainloop()


if __name__ == "__main__":
    main()
