import os
from flask import current_app

def get_file_icon(filename):
    if not filename:
        return ''
    
    # Получаем расширение файла
    ext = os.path.splitext(filename)[1].lower()
    
    # Сопоставляем расширения с иконками
    icon_map = {
        '.pdf': '📄',
        '.doc': '📝',
        '.docx': '📝',
        '.txt': '📄',
        '.zip': '📦',
        '.rar': '📦',
        '.7z': '📦',
        '.jpg': '🖼️',
        '.jpeg': '🖼️',
        '.png': '🖼️',
        '.gif': '🖼️',
        '.mp4': '🎬',
        '.avi': '🎬',
        '.mov': '🎬',
        '.mp3': '🎵',
        '.wav': '🎵',
        '.xls': '📊',
        '.xlsx': '📊',
        '.ppt': '📊',
        '.pptx': '📊',
    }
    
    return icon_map.get(ext, '📎')  # 📎 - иконка по умолчанию для неизвестных типов

def register_template_helpers(app):
    app.jinja_env.globals.update(get_file_icon=get_file_icon)
