# Функции для графиков

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

def create_comparison_plot(batch_sizes, defect_counts, avg_defect_rate):
    """Создает график сравнения фактического и ожидаемого брака"""
    fig, ax = plt.subplots(figsize=(10, 5))
    expected_defects = [s * avg_defect_rate for s in batch_sizes]
    ax.bar(range(1, len(batch_sizes) + 1), defect_counts, 
          color=["#ef4444" if d > e else "#10b981" for d, e in zip(defect_counts, expected_defects)],
          alpha=0.8, label="Фактический брак")
    ax.plot(range(1, len(batch_sizes) + 1), expected_defects, "o--", color="#4f46e5", label="Ожидаемый (биномиальное)")
    ax.set_xlabel("Номер партии")
    ax.set_ylabel("Количество бракованных деталей")
    ax.set_title("Сравнение фактического и ожидаемого количества брака")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)
    return fig

def create_distribution_plot(batch_sizes, defect_counts, avg_defect_rate):
    """График распределения долей брака"""
    try:
        batch_sizes = np.array(batch_sizes, dtype=float)
        defect_counts = np.array(defect_counts, dtype=float)
        defect_rates = defect_counts / batch_sizes
        n = len(defect_rates)

        fig, ax = plt.subplots(figsize=(10, 6))

        # Автоматические бины с ограничением по X
        counts, bins, patches = ax.hist(
            defect_rates,
            bins='auto',
            alpha=0.7,
            color='#3b82f6',
            label='Фактическое распределение',
            edgecolor='black',
            density=True
        )

        # Нормальное распределение
        if n >= 5:
            mu = np.mean(defect_rates)
            sigma = np.std(defect_rates)
            
            # Центрируем диапазон вокруг среднего (3 сигмы в каждую сторону)
            x_min = max(0, mu - 4*sigma)  # Не меньше 0
            x_max = min(0.03, mu + 4*sigma)  # Ограничиваем разумным максимумом
            
            x = np.linspace(x_min, x_max, 500)
            y = norm.pdf(x, mu, sigma)

            ax.plot(x, y, 'r-', lw=2,
                   label=f'Нормальное распределение\n(μ={mu:.4f}, σ={sigma:.4f})')

            # Устанавливаем границы оси X симметрично относительно среднего
            padding = 0.001  # Небольшой отступ
            ax.set_xlim([
                max(0, mu - 5*sigma - padding),  # Левая граница
                min(0.03, mu + 5*sigma + padding)  # Правая граница
            ])

        # Оформление
        ax.set_xlabel('Доля бракованных деталей')
        ax.set_ylabel('Плотность вероятности')
        ax.set_title(f'Распределение долей брака (n={n})')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        return fig

    except Exception as e:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'Ошибка построения графика:\n{str(e)}',
               ha='center', va='center')
        ax.axis('off')
        return fig

