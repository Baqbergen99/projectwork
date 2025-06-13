import requests
from django.core.cache import cache

def translate_text(text, target_language, source_language='ru'):
    """
    Переводит текст с использованием Google Translate API.
    Кэширует результаты для оптимизации.
    """
    # Если текущий язык русский или текст пустой, возвращаем без изменений
    if target_language == 'ru' or not text:
        return text
        
    # Создаем ключ для кэша
    cache_key = f"translate_{source_language}_{target_language}_{hash(text)}"
    
    # Проверяем, есть ли перевод в кэше
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Если перевода нет в кэше, используем API
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": source_language,
            "tl": target_language,
            "dt": "t",
            "q": text
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            # Извлекаем перевод из ответа
            result = response.json()
            translated_text = ''.join([item[0] for item in result[0]])
            
            # Сохраняем в кэш на 24 часа
            cache.set(cache_key, translated_text, 60*60*24)
            
            return translated_text
        return text
    except Exception:
        # В случае ошибки возвращаем исходный текст
        return text