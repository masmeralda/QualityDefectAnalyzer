# Статистический анализ

import numpy as np
from scipy.stats import chi2, norm
import streamlit as st
from scipy.stats import shapiro

def calculate_basic_stats(batch_sizes, defect_counts):
    """Рассчитывает базовую статистику"""
    total_batches = len(batch_sizes)
    total_parts = sum(batch_sizes)
    total_defects = sum(defect_counts)
    avg_defect_rate = total_defects / total_parts if total_parts > 0 else 0
    return total_batches, total_parts, total_defects, avg_defect_rate

def perform_chi2_test_normal(batch_sizes, defect_counts, bins=10):
    """Улучшенный тест хи-квадрат с контролем бинов"""
    defect_rates = np.array(defect_counts) / np.array(batch_sizes)
    n = len(defect_rates)
    
    if n < 30:
        st.warning("⚠️ Для надежного анализа рекомендуется ≥30 наблюдений (у вас {})".format(n))
        stat, p = shapiro(defect_rates)
        st.write(f"Shapiro-Wilk test: p-value = {p:.4f}")
        if p >= 0.05:
            st.success("Данные выглядят нормально (Shapiro-Wilk)")
        else:
            st.warning("Отклонение от нормальности (Shapiro-Wilk)")
        return  # Пропускаем хи-квадрат для малых выборок
    
    mu, sigma = np.mean(defect_rates), np.std(defect_rates)
    
    # Фиксированные бины по квантилям
    bin_edges = np.percentile(defect_rates, np.linspace(0, 100, bins+1))
    bin_edges = np.unique(bin_edges)  # Удаляем дубликаты
    
    # Расчет частот
    observed, _ = np.histogram(defect_rates, bins=bin_edges)
    expected = []
    for i in range(len(bin_edges)-1):
        lower = bin_edges[i]
        upper = bin_edges[i+1]
        prob = norm.cdf(upper, mu, sigma) - norm.cdf(lower, mu, sigma)
        expected.append(prob * n)
    
    # Фильтрация бинов (ожидаемые ≥5)
    observed = np.array(observed)
    expected = np.array(expected)
    mask = expected >= 5
    observed = observed[mask]
    expected = expected[mask]
    
    if len(observed) < 3:
        st.warning("""
        🔍 Анализ невозможен стандартным методом:
        - Ваши данные слишком однородны (разброс всего {:.2f}%)
        - Это **хороший признак** стабильного производства! 
        - **Проверка на нормальность не требуется**
                   
        Рекомендуем проверить:
        1) Достаточно ли партий для анализа?
        2) Есть ли редкие выбросы?
        """.format(100*(defect_rates.max()-defect_rates.min())))
        return None
    
    chi2_stat = np.sum((observed - expected)**2 / expected)
    df = len(observed) - 3
    p_value = 1 - chi2.cdf(chi2_stat, df)
    
    return chi2_stat, df, p_value