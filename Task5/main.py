import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from PIL import Image, ImageOps, ImageTk


class BinarizationApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Бинаризация изображения")
        self.root.geometry("1200x700")

        self.original_image: Image.Image | None = None
        self.gray_array: np.ndarray | None = None
        self.binary_image: Image.Image | None = None
        self.original_preview: ImageTk.PhotoImage | None = None
        self.binary_preview: ImageTk.PhotoImage | None = None
        self.histogram_values: np.ndarray | None = None
        self.threshold_line = None

        self.threshold_var = tk.IntVar(value=128)
        self.threshold_text = tk.StringVar(value="Порог: 128")

        self._build_ui()

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

        images_frame = ttk.LabelFrame(main_frame, text="Изображения", padding=12)
        images_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        images_frame.columnconfigure((0, 1), weight=1)
        images_frame.rowconfigure(1, weight=1)

        ttk.Label(images_frame, text="Оригинал").grid(row=0, column=0, pady=(0, 8))
        ttk.Label(images_frame, text="Бинаризация").grid(row=0, column=1, pady=(0, 8))

        self.original_label = ttk.Label(images_frame, anchor="center", relief="solid")
        self.original_label.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

        self.binary_label = ttk.Label(images_frame, anchor="center", relief="solid")
        self.binary_label.grid(row=1, column=1, sticky="nsew", padx=(8, 0))

        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)

        controls = ttk.LabelFrame(right_panel, text="Управление", padding=12)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        controls.columnconfigure(0, weight=1)

        ttk.Button(
            controls,
            text="Загрузить изображение",
            command=self.load_image,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 12))

        ttk.Label(controls, text="Ручной порог").grid(row=1, column=0, sticky="w")

        ttk.Scale(
            controls,
            from_=0,
            to=255,
            orient="horizontal",
            variable=self.threshold_var,
            command=self.on_threshold_change,
        ).grid(row=2, column=0, sticky="ew", pady=(6, 6))

        ttk.Label(controls, textvariable=self.threshold_text).grid(
            row=3, column=0, sticky="w", pady=(0, 12)
        )

        ttk.Button(
            controls,
            text="Найти порог",
            command=self.apply_otsu_threshold,
        ).grid(row=4, column=0, sticky="ew")

        histogram_frame = ttk.LabelFrame(
            right_panel, text="Гистограмма яркости", padding=12
        )
        histogram_frame.grid(row=1, column=0, sticky="nsew")
        histogram_frame.columnconfigure(0, weight=1)
        histogram_frame.rowconfigure(0, weight=1)

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_xlim(0, 255)
        self.axes.set_xlabel("Яркость")
        self.axes.set_ylabel("Количество пикселей N")
        self.axes.set_title("Гистограмма не загружена")
        self.figure.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.figure, master=histogram_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self._draw_empty_histogram()

    def load_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff"),
                ("Все файлы", "*.*"),
            ],
        )
        if not file_path:
            return

        try:
            image = Image.open(file_path)
        except OSError as error:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{error}")
            return

        self.original_image = ImageOps.exif_transpose(image).convert("RGB")
        gray_image = self.original_image.convert("L")
        self.gray_array = np.asarray(gray_image, dtype=np.uint8)
        self.histogram_values = np.bincount(
            self.gray_array.ravel(), minlength=256
        ).astype(np.int64)

        self._show_preview(self.original_image, self.original_label, is_original=True)
        self._update_histogram()
        self.apply_threshold(self.threshold_var.get())
        self.root.title(f"Бинаризация изображения - {Path(file_path).name}")

    def on_threshold_change(self, value: str) -> None:
        threshold = int(float(value))
        self.threshold_text.set(f"Порог: {threshold}")
        if self.gray_array is not None:
            self.apply_threshold(threshold)

    def apply_threshold(self, threshold: int) -> None:
        if self.gray_array is None:
            return

        binary_array = np.where(self.gray_array >= threshold, 255, 0).astype(np.uint8)
        self.binary_image = Image.fromarray(binary_array, mode="L")
        self._show_preview(self.binary_image, self.binary_label, is_original=False)
        self._update_threshold_line(threshold)

    def apply_otsu_threshold(self) -> None:
        if self.gray_array is None:
            messagebox.showinfo("Нет изображения", "Сначала загрузите изображение.")
            return

        threshold = self.calculate_otsu_threshold(self.gray_array)
        self.threshold_var.set(threshold)
        self.threshold_text.set(f"Порог: {threshold}")
        self.apply_threshold(threshold)

    @staticmethod
    def calculate_otsu_threshold(gray_array: np.ndarray) -> int:
        histogram = np.bincount(gray_array.ravel(), minlength=256).astype(np.float64)
        total_pixels = gray_array.size
        probabilities = histogram / total_pixels

        intensity_values = np.arange(256, dtype=np.float64)
        q1 = np.cumsum(probabilities)
        mu1_numerator = np.cumsum(probabilities * intensity_values)
        total_mean = mu1_numerator[-1]

        valid_mask = (q1 > 0) & (q1 < 1)
        mu1 = np.zeros_like(mu1_numerator)
        mu2 = np.zeros_like(mu1_numerator)
        mu1[valid_mask] = mu1_numerator[valid_mask] / q1[valid_mask]
        mu2[valid_mask] = (
            total_mean - mu1_numerator[valid_mask]
        ) / (1 - q1[valid_mask])

        between_class_variance = np.zeros_like(probabilities)
        between_class_variance[valid_mask] = (
            q1[valid_mask]
            * (1 - q1[valid_mask])
            * (mu1[valid_mask] - mu2[valid_mask]) ** 2
        )

        return int(np.argmax(between_class_variance))

    def _show_preview(
        self, image: Image.Image, label: ttk.Label, *, is_original: bool
    ) -> None:
        preview = image.copy()
        preview.thumbnail((420, 420))
        photo = ImageTk.PhotoImage(preview)
        label.configure(image=photo)
        label.image = photo

        if is_original:
            self.original_preview = photo
        else:
            self.binary_preview = photo

    def _draw_empty_histogram(self) -> None:
        self.axes.clear()
        self.axes.set_xlim(0, 255)
        self.axes.set_xlabel("Яркость")
        self.axes.set_ylabel("Количество пикселей N")
        self.axes.set_title("Загрузите изображение")
        self.threshold_line = self.axes.axvline(
            self.threshold_var.get(), color="crimson", linewidth=2
        )
        self.canvas.draw_idle()

    def _update_histogram(self) -> None:
        if self.histogram_values is None:
            self._draw_empty_histogram()
            return

        self.axes.clear()
        x_values = np.arange(256)
        self.axes.bar(
            x_values,
            self.histogram_values,
            width=1.0,
            color="#6fa8dc",
            edgecolor="#3d6f99",
        )
        self.axes.set_xlim(0, 255)
        self.axes.set_xlabel("Яркость")
        self.axes.set_ylabel("Количество пикселей N")
        self.axes.set_title("Распределение яркости")
        self.axes.grid(axis="y", alpha=0.25)
        self.threshold_line = self.axes.axvline(
            self.threshold_var.get(),
            color="crimson",
            linewidth=2,
            label="Порог t",
        )
        self.axes.legend(loc="upper right")
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _update_threshold_line(self, threshold: int) -> None:
        if self.threshold_line is None:
            return

        self.threshold_line.set_xdata([threshold, threshold])
        self.canvas.draw_idle()


def main() -> None:
    root = tk.Tk()
    BinarizationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
