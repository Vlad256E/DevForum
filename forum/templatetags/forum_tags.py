# forum/templatetags/forum_tags.py
from django import template
import markdown
import bleach
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='markdown')
def markdown_format(text):
    # Разрешенные теги и атрибуты (защита от XSS)
    allowed_tags = [
        'p', 'b', 'i', 'u', 'em', 'strong', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
        'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'hr', 'br'
    ]
    allowed_attrs = {
        'a': ['href', 'title', 'target'], 
        'code': ['class'] # Разрешаем классы для подсветки кода
    }
    
    # Парсим Markdown (включая таблицы и блоки кода)
    html = markdown.markdown(text, extensions=['fenced_code', 'codehilite', 'tables'])
    # Очищаем от опасных скриптов
    clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
    return mark_safe(clean_html)