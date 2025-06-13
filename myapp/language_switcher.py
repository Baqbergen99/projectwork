from django.conf import settings
from django.utils import translation

def switch_language(request, language_code):
    """
    Переключает язык интерфейса и сохраняет его в сессии.
    """
    if language_code in [lang[0] for lang in settings.LANGUAGES]:
        translation.activate(language_code)
        request.session[translation.LANGUAGE_SESSION_KEY] = language_code
    return None