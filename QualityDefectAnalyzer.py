import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import chisquare
import matplotlib.pyplot as plt

# ВВОД ДАННЫХ

with st.sidebar:
    st.header("⚙️ Ввод данных")
    input_method = st.radio("Способ ввода:", ["Вручную", "Загрузить CSV"])

    if input_method == "Вручную":
        batch_size = st.number_input("Размер партии", min_value=1, value=100)
        defect_count = st.number_input("Кол-во бракованных", min_value=0, value=5)

        if "data" not in st.session_state:
            st.session_state.data = {"batch_sizes": [], "defect_counts": []}

        col1, col2 = st.columns(2)
        if col1.button("➕ Добавить партию"):
            st.session_state.data["batch_sizes"].append(batch_size)
            st.session_state.data["defect_counts"].append(defect_count)
            st.success("Партия добавлена!")

        if col2.button("🗑 Очистить"):
            st.session_state.data = {"batch_sizes": [], "defect_counts": []}
            st.warning("Данные очищены!")

    else:
        uploaded_file = st.file_uploader("CSV с колонками 'batch_size' и 'defect_count'")
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                if "batch_size" in df and "defect_count" in df:
                    st.session_state.data = {
                        "batch_sizes": df["batch_size"].tolist(),
                        "defect_counts": df["defect_count"].tolist()
                    }
                    st.success("CSV успешно загружен!")
                else:
                    st.error("Файл должен содержать колонки 'batch_size' и 'defect_count'")
            except Exception as e:
                st.error(f"Ошибка при чтении: {e}")

# АНАЛИЗ И ВИЗУАЛИЗАЦИЯ

if "data" in st.session_state and st.session_state.data["batch_sizes"]:
    batch_sizes = st.session_state.data["batch_sizes"]
    defect_counts = st.session_state.data["defect_counts"]
    total_batches = len(batch_sizes)
    total_parts = sum(batch_sizes)
    total_defects = sum(defect_counts)
    avg_defect_rate = total_defects / total_parts if total_parts > 0 else 0
    expected_defects = [s * avg_defect_rate for s in batch_sizes]

    st.header("📋 Данные партий")
    df = pd.DataFrame({
        "Партия": range(1, total_batches + 1),
        "Деталей": batch_sizes,
        "Бракованных": defect_counts,
        "% брака": [d / s * 100 for d, s in zip(defect_counts, batch_sizes)]
    })
    st.dataframe(df.style.format({"% брака": "{:.2f}"}), use_container_width=True)

    st.header("📌 Сводка")
    col1, col2, col3 = st.columns(3)
    col1.metric("Всего партий", total_batches)
    col2.metric("Всего деталей", f"{total_parts:,}")
    col3.metric("Средний % брака", f"{avg_defect_rate * 100:.2f}%")

    st.header("📈 График")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(range(1, total_batches + 1), defect_counts, 
           color=["#ef4444" if d > e else "#10b981" for d, e in zip(defect_counts, expected_defects)],
           alpha=0.8, label="Фактический брак")
    ax.plot(range(1, total_batches + 1), expected_defects, "o--", color="#4f46e5", label="Ожидаемый")
    ax.set_xlabel("Партия")
    ax.set_ylabel("Кол-во бракованных")
    ax.set_title("Сравнение фактического и ожидаемого брака")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)

    st.header("📐 Статистический анализ")
    if st.button("🔍 Проверить гипотезу"):
        chi2, p_value = chisquare(f_obs=defect_counts, f_exp=expected_defects)
        col1, col2 = st.columns(2)
        col1.metric("χ² значение", f"{chi2:.3f}")
        col2.metric("p-значение", f"{p_value:.4f}")

        st.markdown("**Вывод:**")
        if p_value < 0.05:
            st.error("Гипотеза о равномерности ОТВЕРГАЕТСЯ (значимая разница обнаружена)")
        else:
            st.success("Нет оснований отвергнуть гипотезу — распределение можно считать равномерным.")
