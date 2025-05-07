from django.shortcuts import render
from .models import Task
import json
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

def home(request):
    # Очищаем базу данных для тестирования (можно убрать после проверки)
    Task.objects.all().delete()

    # Проверяем, есть ли данные в базе, если нет — добавляем примерные данные
    if not Task.objects.exists():
        properties = [
            {
                "title": "ул. Мира, 8, кв. 10",
                "description": json.dumps({
                    "price": 90000,
                    "condition": "Среднее",
                    "rooms": 1,
                    "suitable_for": "Один человек",
                    "security": "Камеры есть",
                    "view": "Вид во двор",
                    "balcony": "Есть"
                }),
                "image_url": "https://frankfurt.apollo.olxcdn.com/v1/files/n2sk0bhbrpoo2-KZ/image"
            },
            {
                "title": "ул. Ленина, 12, кв. 45",
                "description": json.dumps({
                    "price": 120000,
                    "condition": "Отличное",
                    "rooms": 2,
                    "suitable_for": "Семья или студенты",
                    "security": "Территория охраняется, есть камеры",
                    "view": "Вид во двор",
                    "balcony": "Есть"
                }),
                "image_url": "https://frankfurt.apollo.olxcdn.com/v1/files/q9onug0fds1u2-KZ/image"
            },
            {
                "title": "пр. Победы, 5, кв. 23",
                "description": json.dumps({
                    "price": 150000,
                    "condition": "Хорошее",
                    "rooms": 3,
                    "suitable_for": "Семья с детьми",
                    "security": "Территория охраняется",
                    "view": "Вид на парк",
                    "balcony": "Нет"
                }),
                "image_url": "https://old.highvill.kz/i/uploads/pr-39078-14092.jpg"
            }
        ]
        for prop in properties:
            Task.objects.create(
                title=prop["title"],
                description=prop["description"],
                image_url=prop["image_url"]
            )

    # Получаем все объекты
    data = Task.objects.all()

    # Логируем содержимое базы данных для отладки
    for item in data:
        logger.info(f"Task: {item.title}, Description: {item.description}, Image URL: {item.image_url}")

    # Функция для безопасного извлечения цены
    def get_price(item):
        try:
            if not item.description:
                return 0
            details = json.loads(item.description)
            return float(details.get("price", 0))
        except (json.JSONDecodeError, ValueError, TypeError):
            return 0

    # Сортировка по цене, если запрошена
    sort_by = request.GET.get('sort', '')
    if sort_by == 'price':
        data = sorted(data, key=get_price)

    # Парсим description как JSON для передачи в шаблон
    properties_data = []
    for item in data:
        try:
            details = json.loads(item.description) if item.description else {}
        except json.JSONDecodeError:
            details = {}  # Если JSON некорректен, используем пустой словарь
        prop_dict = {
            "id": item.id,
            "title": item.title,
            "details": details,
            "created_at": item.created_at,
            "image": item.image_url if item.image_url else "https://via.placeholder.com/300x200?text=Нет фото"
        }
        properties_data.append(prop_dict)

    return render(request, 'home.html', {'data': properties_data})

def about(request):
    return render(request, 'about.html')