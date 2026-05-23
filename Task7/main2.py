import numpy as np
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from scipy import ndimage

# ==========================================
# 1. ГЕНЕРАЦИЯ ПОЛЯ (1-я фигура — квадрат с отверстием)
# ==========================================
def generate_solid_field(size=18):
    field = np.zeros((size, size), dtype=np.uint8)

    # Фигура 1: квадрат 5x5 с отверстием 3x3 внутри
    field[2:7, 1:6] = 1      # внешний квадрат
    field[3:6, 2:5] = 0      # внутреннее отверстие

    # Фигура 2: крест (толщина 2px)
    field[3:8, 10:12] = 1
    field[5:7, 8:14] = 1

    # Фигура 3: сложная форма 3x5
    field[10, 6:11] = [0, 1, 0, 0, 0]
    field[11, 6:11] = [1, 1, 1, 0, 1]
    field[12, 6:11] = [0, 1, 1, 1, 1]

    return field

# ==========================================
# 2. РАСЧЁТ МЕТРИК
# ==========================================
def get_boundary_outline(binary):
    """Создаёт оболочку вокруг фигуры (внешние маркеры)"""
    struct = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8)
    dilated = ndimage.binary_dilation(binary, structure=struct)
    return dilated ^ binary

def count_corners(binary):
    """Считает количество углов d (блоки 2x2 с суммой 1 или 3 пикселя)"""
    corners = 0
    rows, cols = binary.shape
    for y in range(rows - 1):
        for x in range(cols - 1):
            block = binary[y:y + 2, x:x + 2]
            if np.sum(block) in (1, 3):
                corners += 1
    return corners // 2

def calculate_single_metric(binary):
    """Расчёт метрик:
       P1 = b
       P2 = b - 2d + d*sqrt(2)   (ранее было d*sqrt(2))
       P3 = b - 2d + d*sqrt(2)
       K = P1² / S
    """
    if np.sum(binary) == 0:
        return {'S': 0, 'P1': 0, 'P2': 0.0, 'P3': 0.0, 'K': 0.0, 'boundary': np.zeros_like(binary)}

    S = int(np.sum(binary))
    boundary = get_boundary_outline(binary)
    b = int(np.sum(boundary))          # маркеры границы
    d = count_corners(binary)          # количество углов

    P1 = b
    P2 = b - 2 * d + d * np.sqrt(2)    # теперь P2 использует ту же формулу, что и P3
    P3 = b - 2 * d + d * np.sqrt(2)
    K = (P1 ** 2) / S if S > 0 else 0.0

    return {'S': S, 'P1': P1, 'P2': P2, 'P3': P3, 'K': K, 'boundary': boundary}

def calculate_all_figures_metrics(field):
    """Разделяет фигуры и считает метрики для каждой"""
    labeled, num_features = ndimage.label(field, structure=np.ones((3, 3)))
    metrics_list = []
    for i in range(1, num_features + 1):
        single_figure = (labeled == i).astype(np.uint8)
        metrics = calculate_single_metric(single_figure.astype(bool))
        metrics_list.append(metrics)
    return metrics_list, num_features

# ==========================================
# 3. ВИЗУАЛИЗАЦИЯ
# ==========================================
def visualize_solid(field):
    metrics_list, num_figures = calculate_all_figures_metrics(field)
    h, w = field.shape

    LIGHT_BLUE = [0.7, 0.9, 1.0]   # цвет фигур
    GRAY = [0.6, 0.6, 0.6]         # серые маркеры (для P1 и P3)
    BLACK = [0.0, 0.0, 0.0]        # чёрные маркеры (для P2)

    # общая маска границ всех фигур
    total_boundary = np.zeros((h, w), dtype=bool)
    for m in metrics_list:
        total_boundary = total_boundary | m['boundary']

    def create_image(marker_color):
        img = np.ones((h, w, 3))
        img[field == 1] = LIGHT_BLUE
        img[total_boundary == 1] = marker_color
        return img

    fig, axes = plt.subplots(1, 5, figsize=(18, 5))
    fig.suptitle('Физические свойства (1-я фигура — квадрат с отверстием)', fontsize=14, fontweight='bold')

    # текстовые блоки
    txt_S = "Площадь (S):\n" + "\n".join([f"Ф{j}: {m['S']}" for j, m in enumerate(metrics_list, 1)])
    txt_P1 = "Периметр P1 = " + "\n".join([f"Ф{j}: {m['P1']}" for j, m in enumerate(metrics_list, 1)])
    txt_P2 = "Периметр P2 = :\n" + "\n".join([f"Ф{j}: {m['P2']:.2f}" for j, m in enumerate(metrics_list, 1)])
    txt_P3 = "Периметр P3 = :\n" + "\n".join([f"Ф{j}: {m['P3']:.2f}" for j, m in enumerate(metrics_list, 1)])
    txt_K = "Коэф. округлости K:\n" + "\n".join([f"Ф{j}: {m['K']:.2f}" for j, m in enumerate(metrics_list, 1)])

    # Панель 0: Площадь (без маркеров)
    ax = axes[0]
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    img = np.ones((h, w, 3))
    img[field == 1] = LIGHT_BLUE
    ax.imshow(img)
    ax.text(0.98, 0.98, txt_S, fontsize=9, va='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    ax.set_title('1. Площадь', fontsize=11, fontweight='bold')

    # Панель 1: Периметр P1 (серые маркеры)
    ax = axes[1]
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    img = create_image(GRAY)
    ax.imshow(img)
    ax.text(0.98, 0.98, txt_P1, fontsize=9, va='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    ax.set_title('2. Периметр P1 (b)', fontsize=11, fontweight='bold')

    # Панель 2: P2 = b-2d+d√2 (чёрные маркеры)
    ax = axes[2]
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    img = create_image(BLACK)
    ax.imshow(img)
    ax.text(0.98, 0.98, txt_P2, fontsize=9, va='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    ax.set_title('3. Периметр P2 (b-2d+d√2)', fontsize=11, fontweight='bold')

    # Панель 3: P3 = b-2d+d√2 (серые маркеры)
    ax = axes[3]
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    img = create_image(GRAY)
    ax.imshow(img)
    ax.text(0.98, 0.98, txt_P3, fontsize=9, va='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    ax.set_title('4. Периметр P3 (b-2d+d√2)', fontsize=11, fontweight='bold')

    # Панель 4: Коэффициент округлости K (текст)
    ax = axes[4]
    ax.axis('off')
    ax.text(0.05, 0.95, txt_K, fontsize=11, fontweight='bold', va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='lightcyan', alpha=1.0))
    ax.set_title('5. Коэф. округлости', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.show()

    # вывод в консоль (без стикеров)
    print("\n" + "=" * 60)
    print("МЕТРИКИ ДЛЯ КАЖДОЙ ФИГУРЫ:")
    print("=" * 60)
    for j, m in enumerate(metrics_list, 1):
        print(f"\nФигура {j}:")
        print(f"  S (Площадь)        = {m['S']}")
        print(f"  P1 (b)             = {m['P1']}")
        print(f"  P2      = {m['P2']:.2f}")
        print(f"  P3      = {m['P3']:.2f}")
        print(f"  K (округлость)     = {m['K']:.2f}")
    print("=" * 60)

# ==========================================
# 4. ЗАПУСК
# ==========================================
if __name__ == "__main__":
    field = generate_solid_field()
    visualize_solid(field)