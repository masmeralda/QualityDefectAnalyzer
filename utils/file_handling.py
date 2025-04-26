# Работа с файлами

import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import streamlit as st

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