# Статистический анализ

import numpy as np
from scipy.stats import chi2, norm
import streamlit as st

def calculate_basic_stats(batch_sizes, defect_counts):
    """Рассчитывает базовую статистику"""
    total_batches = len(batch_sizes)
    total_parts = sum(batch_sizes)
    total_defects = sum(defect_counts)
    avg_defect_rate = total_defects / total_parts if total_parts > 0 else 0
    return total_batches, total_parts, total_defects, avg_defect_rate

def perform_chi2_test(batch_sizes, defect_counts, avg_defect_rate):
    """Выполняет тест хи-квадрат"""
    observed = np.array(defect_counts)
    expected = np.array(batch_sizes) * avg_defect_rate
    
    if np.any(expected < 5):
        st.warning("⚠️ Некоторые ожидаемые частоты < 5. Результаты могут быть ненадежными!")
    
    chi2_stat = ((observed - expected)**2 / expected).sum()
    df = len(observed) - 2
    p_value = 1 - chi2.cdf(chi2_stat, df)
    
    return chi2_stat, df, p_value