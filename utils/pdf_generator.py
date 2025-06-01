# Генерация PDF

import os
import tempfile
import base64
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import norm  
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from scipy.stats import chi2, binom, norm
import streamlit as st
from utils.stats_analysis import perform_chi2_test_normal
from utils.plotting import create_distribution_plot, create_comparison_plot

def create_pdf_report():
    """Создает PDF отчет с результатами анализа"""
    if "data" not in st.session_state:
        st.warning("Нет данных для экспорта")
        return
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf_path = tmpfile.name
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(name='RussianTitle', 
                            fontName='DejaVuSans-Bold',
                            fontSize=18,
                            alignment=1,
                            spaceAfter=12))
    
    styles.add(ParagraphStyle(name='RussianHeading2', 
                            fontName='DejaVuSans-Bold',
                            fontSize=14,
                            spaceBefore=12,
                            spaceAfter=6))
    
    styles.add(ParagraphStyle(name='RussianNormal', 
                            fontName='DejaVuSans',
                            fontSize=10,
                            leading=12))
    
    story = []
    story.append(Paragraph("Анализ брака в производстве", styles['RussianTitle']))
    story.append(Spacer(1, 12))
    
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
    
    df = pd.DataFrame({
        "Партия": range(1, total_batches + 1),
        "Деталей": batch_sizes,
        "Бракованных": defect_counts,
        "% брака": [d / s * 100 for d, s in zip(defect_counts, batch_sizes)]
    })
    
    table_data = [df.columns.tolist()] + df.values.tolist()
    
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(t)
    story.append(Spacer(1, 24))
    
    def add_plot_to_story(fig, title):
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"temp_plot_{next(tempfile._get_candidate_names())}.png")
        fig.savefig(temp_file, bbox_inches='tight', dpi=300)
        story.append(Paragraph(title, styles['RussianHeading2']))
        story.append(Spacer(1, 12))
        story.append(Image(temp_file, width=400, height=250))
        story.append(Spacer(1, 24))
    
   # График сравнения фактического и ожидаемого брака
    fig1 = create_comparison_plot(batch_sizes, defect_counts, avg_defect_rate)
    add_plot_to_story(fig1, "Сравнение фактического и ожидаемого количества брака")
    plt.close(fig1)
    
    # График распределения долей брака (используем ту же функцию, что и на сайте)
    fig2 = create_distribution_plot(batch_sizes, defect_counts, avg_defect_rate)
    add_plot_to_story(fig2, "Распределение доли брака")
    plt.close(fig2)
    
    
    result = perform_chi2_test_normal(batch_sizes, defect_counts)
    
    if result is None:
        test_result = "<b>Результаты проверки гипотезы:</b><br/>Анализ не выполнен: данные слишком однородны или их недостаточно"
    else:
        chi2_stat, df, p_value = result
        
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
    
    doc.build(story)
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="defect_analysis_report.pdf">Скачать PDF отчет</a>'
    st.markdown(href, unsafe_allow_html=True)
    
    os.unlink(pdf_path)