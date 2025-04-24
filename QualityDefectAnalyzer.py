import os
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import chi2, binom, norm
import tkinter as tk
from tkinter import filedialog
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import tempfile
import base64
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Настройка страницы
st.set_page_config(page_title="Анализ брака в производстве", page_icon="📊", layout="wide")
st.title("📊 Анализ распределения бракованных деталей")

# Регистрация шрифтов с поддержкой кириллицы
try:
    # DejaVu Sans — он поддерживает кириллицу
    font_path_regular = os.path.join("fonts", "DejaVuSans.ttf")
    font_path_bold = os.path.join("fonts", "DejaVuSans-Bold.ttf")
    
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path_regular))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_path_bold))
    
    FONT_NAME = 'DejaVuSans'
    FONT_BOLD = 'DejaVuSans-Bold'
except Exception as e:
    FONT_NAME = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'
    st.warning(f"Не удалось загрузить шрифты. Русский текст в PDF может отображаться некорректно. Ошибка: {e}")

def get_save_path(default_name="defect_data.csv"):
    """Открывает диалоговое окно для выбора места сохранения файла"""
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        initialfile=default_name,
        title="Выберите место для сохранения файла"
    )
    root.destroy()
    return file_path

def clear_data():
    """Очищает все данные"""
    if 'uploaded_file' in st.session_state:
        st.session_state.uploaded_file.close()
        del st.session_state.uploaded_file
    st.session_state.pop('data', None)
    st.session_state.pop('editable_df', None)
    st.session_state.pop('csv_loaded', None)
    st.success("Данные успешно очищены!")

def create_pdf_report():
    """Создает PDF отчет с результатами анализа"""
    if "data" not in st.session_state:
        st.warning("Нет данных для экспорта")
        return
    
    # Создаем временный файл для PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf_path = tmpfile.name
    
    # Создаем документ PDF
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Создаем кастомные стили с поддержкой кириллицы
    styles = getSampleStyleSheet()
    
    # Добавляем кастомные стили для русского текста
    styles.add(ParagraphStyle(name='RussianTitle', 
                            fontName=FONT_BOLD,
                            fontSize=18,
                            alignment=1,
                            spaceAfter=12))
    
    styles.add(ParagraphStyle(name='RussianHeading2', 
                            fontName=FONT_BOLD,
                            fontSize=14,
                            spaceBefore=12,
                            spaceAfter=6))
    
    styles.add(ParagraphStyle(name='RussianNormal', 
                            fontName=FONT_NAME,
                            fontSize=10,
                            leading=12))
    
    story = []
    
    # Заголовок отчета
    story.append(Paragraph("Анализ брака в производстве", styles['RussianTitle']))
    story.append(Spacer(1, 12))
    
    # Основная информация
    batch_sizes = st.session_state.data["batch_sizes"]
    defect_counts = st.session_state.data["defect_counts"]
    total_batches = len(batch_sizes)
    total_parts = sum(batch_sizes)
    total_defects = sum(defect_counts)
    avg_defect_rate = total_defects / total_parts if total_parts > 0 else 0
    
    info_text = f"""
    <b>Всего партий:</b> {total_batches}<br/>
    <b>Всего деталей:</b> {total_parts:,}<br/>
    <b>Средний % брака:</b> {avg_defect_rate * 100:.2f}%<br/>
    """
    story.append(Paragraph(info_text, styles['RussianNormal']))
    story.append(Spacer(1, 12))
    
    # Таблица данных
    df = pd.DataFrame({
        "Партия": range(1, total_batches + 1),
        "Деталей": batch_sizes,
        "Бракованных": defect_counts,
        "% брака": [d / s * 100 for d, s in zip(defect_counts, batch_sizes)]
    })
    
    # Преобразуем DataFrame в список списков для ReportLab
    table_data = [df.columns.tolist()] + df.values.tolist()
    
    # Создаем таблицу
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(t)
    story.append(Spacer(1, 24))
    
    # Сохраняем графики во временные файлы и добавляем в PDF
    def add_plot_to_story(fig, title):
        # Создаем временный файл
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"temp_plot_{next(tempfile._get_candidate_names())}.png")
        
        # Сохраняем график
        fig.savefig(temp_file, bbox_inches='tight', dpi=300)
        
        # Добавляем в историю
        story.append(Paragraph(title, styles['RussianHeading2']))
        story.append(Spacer(1, 12))
        story.append(Image(temp_file, width=400, height=250))
        story.append(Spacer(1, 24))
        # Не удаляем файл - система сама очистит временную директорию
    
    # График 1: Сравнение фактического и ожидаемого количества брака
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
    add_plot_to_story(fig1, "Сравнение фактического и ожидаемого количества брака")
    plt.close(fig1)
    
    # График 2: Распределение доли брака
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
    add_plot_to_story(fig2, "Распределение доли брака")
    plt.close(fig2)
    
    # Результаты проверки гипотезы хи-квадрат
    observed = np.array(defect_counts)
    expected = np.array(batch_sizes) * avg_defect_rate
    chi2_stat = ((observed - expected)**2 / expected).sum()
    df = len(observed) - 2
    p_value = 1 - chi2.cdf(chi2_stat, df)
    
    test_result = f"""
    <b>Результаты проверки гипотезы хи-квадрат:</b><br/>
    <b>χ² статистика:</b> {chi2_stat:.3f}<br/>
    <b>Степени свободы:</b> {df}<br/>
    <b>p-значение:</b> {p_value:.4f}<br/><br/>
    """
    
    if p_value < 0.05:
        test_result += "<b>Вывод:</b> Гипотеза отвергается (p < 0.05) - распределение брака НЕ соответствует биномиальному закону."
    else:
        test_result += "<b>Вывод:</b> Гипотеза не отвергается - распределение брака соответствует биномиальному закону."
    
    story.append(Paragraph(test_result, styles['RussianNormal']))
    story.append(Spacer(1, 24))
    
    # Собираем PDF
    doc.build(story)
    
    # Читаем PDF и создаем кнопку для скачивания
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    # Кодируем PDF в base64 для скачивания через Streamlit
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="defect_analysis_report.pdf">Скачать PDF отчет</a>'
    st.markdown(href, unsafe_allow_html=True)
    
    # Удаляем временный файл PDF
    os.unlink(pdf_path)

# Боковая панель для ввода данных
with st.sidebar:
    st.header("⚙️ Ввод данных")
    input_method = st.radio("Способ ввода:", ["Создать вручную", "Открыть CSV"])

    if input_method == "Открыть CSV":
        uploaded_file = st.file_uploader("CSV с колонками 'batch_size' и 'defect_count'", key="file_uploader")
        if uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            try:
                df = pd.read_csv(uploaded_file)
                if "batch_size" in df.columns and "defect_count" in df.columns:
                    st.session_state.editable_df = pd.DataFrame({
                        'Размер партии': df["batch_size"],
                        'Бракованные детали': df["defect_count"]
                    })
                    st.session_state.csv_loaded = True
                    st.success("CSV успешно загружен!")
                else:
                    st.error("Файл должен содержать колонки 'batch_size' и 'defect_count'")
            except Exception as e:
                st.error(f"Ошибка при чтении: {e}")
    
    if st.button("🧹 Очистить все данные", on_click=clear_data):
        pass

# Основной интерфейс
if input_method == "Создать вручную":
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
    
    if col3.button("💾 Применить"):
        st.session_state.data = {
            "batch_sizes": edited_df['Размер партии'].tolist(),
            "defect_counts": edited_df['Бракованные детали'].tolist()
        }
        st.success("Данные сохранены для анализа!")
    
    if st.button("📤 Сохранить таблицу в CSV"):
        try:
            save_path = get_save_path()
            if not save_path:
                st.warning("Сохранение отменено")
            else:
                export_df = pd.DataFrame({
                    'batch_size': edited_df['Размер партии'],
                    'defect_count': edited_df['Бракованные детали']
                })
                export_df.to_csv(save_path, index=False, encoding='utf-8-sig')
                st.success(f"Файл успешно сохранён: {save_path}")
        except Exception as e:
            st.error(f"Ошибка при сохранении: {e}")

# Редактирование загруженного CSV
elif input_method == "Открыть CSV" and st.session_state.get('csv_loaded'):
    st.header("📝 Редактирование данных производства")
    
    edited_df = st.data_editor(
        st.session_state.editable_df,
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "Размер партии": st.column_config.NumberColumn(min_value=1),
            "Бракованные детали": st.column_config.NumberColumn(min_value=0)
        }
    )
    
    col1, col2 = st.columns(2)
    
    if col1.button("💾 Применить для анализа"):
        st.session_state.data = {
            "batch_sizes": edited_df['Размер партии'].tolist(),
            "defect_counts": edited_df['Бракованные детали'].tolist()
        }
        st.success("Изменения применены для анализа!")
    
    if col2.button("📤 Сохранить как..."):
        try:
            save_path = get_save_path()
            if not save_path:
                st.warning("Сохранение отменено")
            else:
                export_df = pd.DataFrame({
                    'batch_size': edited_df['Размер партии'],
                    'defect_count': edited_df['Бракованные детали']
                })
                export_df.to_csv(save_path, index=False, encoding='utf-8-sig')
                st.success(f"Файл успешно сохранён: {save_path}")
        except Exception as e:
            st.error(f"Ошибка при сохранении: {e}")

# Анализ и визуализация данных
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
    plt.close(fig1)

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
    plt.close(fig2)

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
            3. Ожидаемые частоты рассчитываются как: n[i] * p, где p - общая вероятность брака
            4. Степени свободы: k - 2, где k - число партий (мы оценили параметр p из данных)
            
            **Условия применимости:**
            - Все ожидаемые частоты должны быть ≥ 5
            - Размеры партий не должны сильно различаться
            """)

    # Добавляем кнопку экспорта в PDF
    st.header("📤 Экспорт результатов")
    if st.button("🖨️ Экспорт в PDF"):
        create_pdf_report()
else:
    if input_method == "Создать вручную":
        st.info("ℹ️ Введите данные в таблицу выше и нажмите 'Сохранить данные'")
    elif input_method == "Открыть CSV" and not st.session_state.get('csv_loaded'):
        st.info("ℹ️ Загрузите CSV-файл через боковую панель")