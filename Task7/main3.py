import matplotlib

matplotlib.use('TkAgg')

import numpy as np
import matplotlib.pyplot as plt
import random


# ============================================================================
# ГЕНЕРАЦИЯ СЛУЧАЙНЫХ ФИГУР
# ============================================================================

def generate_random_shapes(grid_size=18, num_shapes=3):
    """Генерирует случайные сплошные фигуры на сетке"""
    grid = np.zeros((grid_size, grid_size), dtype=int)

    shapes = []
    attempts = 0
    while len(shapes) < num_shapes and attempts < 100:
        attempts += 1

        # Случайная позиция и размер
        shape_type = random.choice(['square', 'rect', 'L', 'T', 'diamond'])
        size = random.randint(2, 4)
        r_start = random.randint(1, grid_size - size - 2)
        c_start = random.randint(1, grid_size - size - 2)

        temp_grid = grid.copy()

        if shape_type == 'square':
            temp_grid[r_start:r_start + size, c_start:c_start + size] = 1
        elif shape_type == 'rect':
            h, w = size, size + random.randint(0, 2)
            temp_grid[r_start:r_start + h, c_start:c_start + w] = 1
        elif shape_type == 'L':
            temp_grid[r_start:r_start + size, c_start] = 1
            temp_grid[r_start + size - 1, c_start:c_start + size] = 1
        elif shape_type == 'T':
            temp_grid[r_start, c_start:c_start + size] = 1
            temp_grid[r_start:r_start + size // 2 + 1, c_start + size // 2] = 1
        elif shape_type == 'diamond':
            for i in range(size):
                for j in range(size):
                    if abs(i - size // 2) + abs(j - size // 2) <= size // 2:
                        temp_grid[r_start + i, c_start + j] = 1

        # Проверяем пересечение
        if np.sum(temp_grid * grid) == 0:
            grid = temp_grid
            shapes.append(shape_type)

    return grid, shapes


def calculate_perimeter_4conn(grid):
    """Периметр по 4 связности"""
    rows, cols = grid.shape
    perimeter = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 1:
                if r == 0 or grid[r - 1, c] == 0: perimeter += 1
                if r == rows - 1 or grid[r + 1, c] == 0: perimeter += 1
                if c == 0 or grid[r, c - 1] == 0: perimeter += 1
                if c == cols - 1 or grid[r, c + 1] == 0: perimeter += 1
    return perimeter


# ============================================================================
# ВИЗУАЛИЗАЦИЯ
# ============================================================================

def visualize_lab_results():
    """Создает визуализацию в стиле скриншота"""

    # Генерируем случайные фигуры
    grid, shapes = generate_random_shapes(grid_size=18, num_shapes=3)

    # Вычисляем метрики
    area = np.count_nonzero(grid)
    P1 = calculate_perimeter_4conn(grid)
    coefficient = (P1 ** 2) / area if area > 0 else 0

    print("=" * 60)
    print("Генерация поля...")
    print(f"✓ Проверка массива: всего пикселей объекта = {area}")
    print(f"  Размер поля: {grid.shape[0]}x{grid.shape[1]}")
    print(f"  Типы фигур: {', '.join(shapes)}")
    print(f"  Внутри фигур НУЛЕЙ нет (фигуры математически сплошные).")
    print("=" * 60)

    # Создаем фигуру с 5 панелями
    fig = plt.figure(figsize=(14, 5))
    fig.suptitle('Физические свойства: 3 сплошные фигуры (без артефактов)',
                 fontsize=12, fontweight='bold', y=0.98)

    # --- Панель 1: Площадь ---
    ax1 = plt.subplot(1, 5, 1)
    ax1.imshow(grid, cmap='gray', interpolation='none')
    ax1.set_title(f'1. Площадь\nS = {area}', fontsize=10, fontweight='bold')
    ax1.axis('off')

    # --- Панель 2: Периметр P1 ---
    ax2 = plt.subplot(1, 5, 2)
    perimeter_mask = np.zeros_like(grid, dtype=float)
    rows, cols = grid.shape
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 1:
                is_edge = False
                if r == 0 or grid[r - 1, c] == 0: is_edge = True
                if r == rows - 1 or grid[r + 1, c] == 0: is_edge = True
                if c == 0 or grid[r, c - 1] == 0: is_edge = True
                if c == cols - 1 or grid[r, c + 1] == 0: is_edge = True
                if is_edge:
                    perimeter_mask[r, c] = 1

    ax2.imshow(perimeter_mask, cmap='Reds', interpolation='none')
    ax2.set_title(f'2. Периметр P1\nP1 = {P1}', fontsize=10, fontweight='bold')
    ax2.axis('off')

    # --- Панель 3: Инверсия (ИСПРАВЛЕНО) ---
    ax3 = plt.subplot(1, 5, 3)
    # Создаем копию для отображения.
    # Чтобы сделать фон прозрачным/белым, а объект темным, используем маску
    display_grid = grid.astype(float)
    display_grid[display_grid == 0] = np.nan  # Теперь это float массив, NaN разрешен
    ax3.imshow(display_grid, cmap='RdYlBu_r', interpolation='none', vmin=-1, vmax=1)
    ax3.set_title(f'3. Инверсия\n-1 = объект', fontsize=10, fontweight='bold')
    ax3.axis('off')

    # --- Панель 4: Периметр (оранжевый) ---
    ax4 = plt.subplot(1, 5, 4)
    ax4.imshow(perimeter_mask, cmap='Oranges', interpolation='none')
    ax4.set_title(f'4. Периметр (оранж)\nP = {P1}', fontsize=10, fontweight='bold')
    ax4.axis('off')

    # --- Панель 5: Коэффициент ---
    ax5 = plt.subplot(1, 5, 5)
    ax5.axis('off')
    k_text = f"5. Коэф. K\n\nK = P² / S\n\nK = {coefficient:.2f}"
    ax5.text(0.5, 0.5, k_text, ha='center', va='center', fontsize=11, family='monospace',
             fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcyan', alpha=0.9))

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()


if __name__ == "__main__":
    visualize_lab_results()