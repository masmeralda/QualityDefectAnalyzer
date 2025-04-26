import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Настройки шрифтов
FONT_CONFIG = {
    'regular': {
        'path': os.path.join("fonts", "DejaVuSans.ttf"),
        'name': 'DejaVuSans'
    },
    'bold': {
        'path': os.path.join("fonts", "DejaVuSans-Bold.ttf"),
        'name': 'DejaVuSans-Bold'
    },
    'fallback': {
        'regular': 'Helvetica',
        'bold': 'Helvetica-Bold'
    }
}

# Настройки страницы
PAGE_CONFIG = {
    'page_title': "Анализ брака в производстве",
    'page_icon': "📊",
    'layout': "wide"
}

def setup_fonts():
    try:
        pdfmetrics.registerFont(TTFont(
            FONT_CONFIG['regular']['name'],
            FONT_CONFIG['regular']['path']
        ))
        pdfmetrics.registerFont(TTFont(
            FONT_CONFIG['bold']['name'],
            FONT_CONFIG['bold']['path']
        ))
        return FONT_CONFIG['regular']['name'], FONT_CONFIG['bold']['name']
    except Exception:
        return FONT_CONFIG['fallback']['regular'], FONT_CONFIG['fallback']['bold']