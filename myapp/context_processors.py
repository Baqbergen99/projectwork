from django.conf import settings
from .translations import TRANSLATIONS

def language_context(request):
    """
    Добавляет доступные языки и переводы в контекст шаблона.
    """
    # Получаем текущий язык из сессии или используем язык по умолчанию
    current_language = request.session.get('django_language', settings.LANGUAGE_CODE)
    
    # Получаем переводы для текущего языка
    translations = TRANSLATIONS.get(current_language, TRANSLATIONS['ru'])
    
    return {
        'LANGUAGES': settings.LANGUAGES,
        'CURRENT_LANGUAGE': current_language,
        'translations': translations
    }