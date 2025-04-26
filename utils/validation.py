import pandas as pd
import streamlit as st

def validate_data(df):
    """Проверяет данные на корректность и возвращает False при обнаружении ошибок"""
    is_valid = True
    
    # Проверка на пустые значения
    empty_rows = df[df.isnull().any(axis=1)]
    if not empty_rows.empty:
        st.error(f"Ошибка: Пустые значения в строках: {', '.join(map(str, empty_rows.index + 1))}")
        is_valid = False
    
    # Проверка на отрицательные значения размера партии
    invalid_size_rows = df[df['Размер партии'] <= 0]
    if not invalid_size_rows.empty:
        st.error(f"Ошибка: Неположительный размер партии в строках: {', '.join(map(str, invalid_size_rows.index + 1))}")
        is_valid = False
        
    # Проверка на отрицательные значения брака
    invalid_defect_rows = df[df['Бракованные детали'] < 0]
    if not invalid_defect_rows.empty:
        st.error(f"Ошибка: Отрицательное количество брака в строках: {', '.join(map(str, invalid_defect_rows.index + 1))}")
        is_valid = False
    
    # Проверка, что количество брака не превышает размер партии
    invalid_ratio_rows = df[df['Бракованные детали'] > df['Размер партии']]
    if not invalid_ratio_rows.empty:
        st.error(f"Ошибка: Брака больше чем деталей в строках: {', '.join(map(str, invalid_ratio_rows.index + 1))}")
        is_valid = False
    
    return is_valid