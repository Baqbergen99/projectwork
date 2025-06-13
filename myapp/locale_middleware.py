from django.utils import translation
from django.conf import settings
from django.urls import is_valid_path
from django.http import HttpResponseRedirect
from django.urls.base import get_script_prefix
from .auto_translate import translate_text

class LocaleMiddleware:
    """
    Middleware для обработки языковых настроек на основе URL и автоматического перевода.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Активируем язык
        language = translation.get_language_from_request(request)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        
        # Добавляем функцию перевода в request для использования в шаблонах
        request.translate = lambda text: translate_text(text, language)
        
        # Получаем ответ
        response = self.get_response(request)
        
        # Деактивируем язык
        translation.deactivate()
        
        return response