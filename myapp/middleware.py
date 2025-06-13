from django.utils.deprecation import MiddlewareMixin
from django.utils import translation
from django.conf import settings

class LanguageMiddleware(MiddlewareMixin):
    """
    Middleware для установки языка из сессии для каждого запроса.
    """
    def process_request(self, request):
        # Получаем язык из сессии или используем язык по умолчанию
        language = request.session.get('django_language', settings.LANGUAGE_CODE)
        # Активируем язык
        translation.activate(language)
        # Сохраняем язык в request для использования в шаблонах
        request.LANGUAGE_CODE = language