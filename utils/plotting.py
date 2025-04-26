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
    """Создает график распределения доли брака"""
    fig, ax = plt.subplots(figsize=(10, 5))
    defect_rates = np.array(defect_counts) / np.array(batch_sizes)
    ax.hist(defect_rates, bins=15, density=True, alpha=0.6, color='#3b82f6', label='Фактическое распределение')
    
    mu = avg_defect_rate
    sigma = np.sqrt(mu*(1-mu)/np.mean(batch_sizes))
    x = np.linspace(max(0, mu-3*sigma), min(1, mu+3*sigma), 100)
    ax.plot(x, norm.pdf(x, mu, sigma), 'r-', lw=2, label='Теоретическое нормальное приближение')
    
    ax.set_xlabel('Доля бракованных деталей')
    ax.set_ylabel('Плотность вероятности')
    ax.legend()
    ax.grid(True)
    return fig