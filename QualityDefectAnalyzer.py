import os
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import chi2, binom, norm

# Настройка страницы
st.set_page_config(page_title="Анализ брака в производстве", page_icon="📊", layout="wide")
st.title("📊 Анализ распределения бракованных деталей")

def ensure_csv_folder():
    if not os.path.exists("csv-файлы"):
        os.makedirs("csv-файлы")

# Функция для очистки данных
def clear_data():
    st.session_state.pop('data', None)
    st.session_state.pop('editable_df', None)
    st.success("Данные успешно очищены!")

with st.sidebar:
    st.header("⚙️ Ввод данных")
    input_method = st.radio("Способ ввода:", ["Вручную", "Загрузить CSV"])

    if input_method == "Загрузить CSV":
        uploaded_file = st.file_uploader("CSV с колонками 'batch_size' и 'defect_count'")
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                if "batch_size" in df.columns and "defect_count" in df.columns:
                    st.session_state.data = {
                        "batch_sizes": df["batch_size"].tolist(),
                        "defect_counts": df["defect_count"].tolist()
                    }
                    st.success("CSV успешно загружен!")
                else:
                    st.error("Файл должен содержать колонки 'batch_size' и 'defect_count'")
            except Exception as e:
                st.error(f"Ошибка при чтении: {e}")
    
    # Добавляем кнопку очистки данных в боковое меню
    if st.button("🧹 Очистить все данные", on_click=clear_data):
        pass  # Действие выполняется в функции clear_data

if input_method == "Вручную":
    st.header("📝 Ввод данных партий")
    
    if 'editable_df' not in st.session_state:
        st.session_state.editable_df = pd.DataFrame(columns=['Размер партии', 'Бракованные детали'])
        st.session_state.editable_df.loc[0] = [100, 5]
    
    def add_row():
        st.session_state.editable_df.loc[len(st.session_state.editable_df)] = [100, 5]
    
    def delete_row():
        if len(st.session_state.editable_df) > 1:
            st.session_state.editable_df = st.session_state.editable_df.iloc[:-1]
    
    edited_df = st.data_editor(
        st.session_state.editable_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Размер партии": st.column_config.NumberColumn(min_value=1),
            "Бракованные детали": st.column_config.NumberColumn(min_value=0)
        }
    )
    
    col1, col2, col3 = st.columns(3)
    col1.button("➕ Добавить строку", on_click=add_row)
    col2.button("➖ Удалить последнюю строку", on_click=delete_row)
    
    if col3.button("💾 Сохранить данные"):
        st.session_state.data = {
            "batch_sizes": edited_df['Размер партии'].tolist(),
            "defect_counts": edited_df['Бракованные детали'].tolist()
        }
        st.success("Данные сохранены для анализа!")
    
    if st.button("📤 Сохранить таблицу в CSV"):
        ensure_csv_folder()
        csv_path = os.path.join("csv-файлы", "defect_data.csv")
        
        export_df = pd.DataFrame({
            'batch_size': edited_df['Размер партии'],
            'defect_count': edited_df['Бракованные детали']
        })
        
        export_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        st.success(f"Файл сохранён в: {csv_path}")

if "data" in st.session_state and st.session_state.data["batch_sizes"]:
    batch_sizes = st.session_state.data["batch_sizes"]
    defect_counts = st.session_state.data["defect_counts"]
    total_batches = len(batch_sizes)
    total_parts = sum(batch_sizes)
    total_defects = sum(defect_counts)
    avg_defect_rate = total_defects / total_parts if total_parts > 0 else 0

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

    st.header("📈 Графики распределения")
    
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    expected_defects = [s * avg_defect_rate for s in batch_sizes]
    ax1.bar(range(1, total_batches + 1), defect_counts, 
           color=["#ef4444" if d > e else "#10b981" for d, e in zip(defect_counts, expected_defects)],
           alpha=0.8, label="Фактический брак")
    ax1.plot(range(1, total_batches + 1), expected_defects, "o--", color="#4f46e5", label="Ожидаемый (биномиальное)")
    ax1.set_xlabel("Номер партии")
    ax1.set_ylabel("Количество бракованных деталей")
    ax1.set_title("Сравнение фактического и ожидаемого количества брака")
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig1)

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    defect_rates = np.array(defect_counts) / np.array(batch_sizes)
    ax2.hist(defect_rates, bins=15, density=True, alpha=0.6, color='#3b82f6', label='Фактическое распределение')
    
    mu = avg_defect_rate
    sigma = np.sqrt(mu*(1-mu)/np.mean(batch_sizes))
    x = np.linspace(max(0, mu-3*sigma), min(1, mu+3*sigma), 100)
    ax2.plot(x, norm.pdf(x, mu, sigma), 'r-', lw=2, label='Теоретическое нормальное приближение')
    
    ax2.set_xlabel('Доля бракованных деталей')
    ax2.set_ylabel('Плотность вероятности')
    ax2.legend()
    ax2.grid(True)
    st.pyplot(fig2)

    st.header("📐 Проверка гипотезы хи-квадрат")
    st.markdown("**Проверяемая гипотеза:** Брак в партиях соответствует биномиальному распределению.")
    
    if st.button("🔍 Выполнить проверку гипотезы"):
        observed = np.array(defect_counts)
        expected = np.array(batch_sizes) * avg_defect_rate
        
        if np.any(expected < 5):
            st.warning("⚠️ Некоторые ожидаемые частоты < 5. Результаты могут быть ненадежными!")
        
        chi2_stat = ((observed - expected)**2 / expected).sum()
        df = len(observed) - 2
        p_value = 1 - chi2.cdf(chi2_stat, df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("χ² статистика", f"{chi2_stat:.3f}")
        col2.metric("Степени свободы", df)
        col3.metric("p-значение", f"{p_value:.4f}")
        
        st.markdown("**Интерпретация:**")
        if p_value < 0.05:
            st.error("Гипотеза отвергается (p < 0.05) - распределение брака НЕ соответствует биномиальному закону.")
        else:
            st.success("Гипотеза не отвергается - распределение брака соответствует биномиальному закону.")
        
        with st.expander("ℹ️ О методе анализа"):
            st.markdown("""
            **Методика проверки:**
            1. Нулевая гипотеза: количество бракованных деталей в партиях подчиняется биномиальному распределению
            2. Используется критерий согласия хи-квадрат Пирсона
            3. Ожидаемые частоты рассчитываются как: `n[i] * p`, где `p` - общая вероятность брака
            4. Степени свободы: `k - 2`, где `k` - число партий (мы оценили параметр `p` из данных)
            
            **Условия применимости:**
            - Все ожидаемые частоты должны быть ≥ 5
            - Размеры партий не должны сильно различаться
            """)
else:
    if input_method == "Вручную":
        st.info("ℹ️ Введите данные в таблицу выше и нажмите 'Сохранить данные'")
    else:
        st.info("ℹ️ Загрузите CSV-файл через боковую панель")