from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext as _
from .models import Task, ActivationToken
from .forms import RegisterForm, UpdateProfileForm, TaskForm
from .auto_translate import translate_text
import json
import uuid
import logging

from rest_framework import viewsets
from .serializers import TaskSerializer

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TaskListView(ListView):
    model = Task
    template_name = 'task_list.html'
    context_object_name = 'data'

    def get_queryset(self):
        queryset = super().get_queryset()
        sort_by = self.request.GET.get('sort', '')
        if sort_by == 'price':
            def get_price(item):
                try:
                    if not item.description:
                        return 0
                    details = json.loads(item.description)
                    return float(details.get("price", 0))
                except (json.JSONDecodeError, ValueError, TypeError):
                    return 0
            queryset = sorted(queryset, key=get_price)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        properties_data = []
        
        # Получаем текущий язык
        current_language = self.request.session.get('django_language', settings.LANGUAGE_CODE)
        
        # Получаем переводы
        from .translations import TRANSLATIONS
        translations = TRANSLATIONS.get(current_language, TRANSLATIONS['ru'])
        
        for item in context['data']:
            try:
                details = json.loads(item.description) if item.description else {}
            except json.JSONDecodeError:
                details = {}
                
            # Переводим заголовок в зависимости от языка
            title = item.title
            if current_language != 'ru':
                title = translate_text(title, current_language)
            
            # Переводим все детали квартиры
            translated_details = {}
            for key, value in details.items():
                if isinstance(value, str) and value:
                    # Специальные случаи для известных значений
                    if key == 'suitable_for' and value == 'Один человек':
                        translated_details[key] = translations.get('one_person', value)
                    elif current_language != 'ru':
                        # Автоматический перевод для остальных значений
                        translated_details[key] = translate_text(value, current_language)
                    else:
                        translated_details[key] = value
                else:
                    translated_details[key] = value
                
            # Создаем словарь с данными о квартире
            prop_dict = {
                "id": item.id,
                "title": title,
                "details": translated_details,
                "created_at": item.created_at,
                "image": item.image_url if item.image_url else f"https://via.placeholder.com/300x200?text={translations['no_photo']}"
            }
            properties_data.append(prop_dict)
            
        context['data'] = properties_data
        
        # Добавляем текущий язык в контекст
        context['CURRENT_LANGUAGE'] = current_language
        
        # Добавляем переводы кнопок и текстов
        context['translations'] = translations
        
        return context

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

class TaskCreateView(AdminRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'task_form.html'
    success_url = reverse_lazy('task-list')

class TaskUpdateView(AdminRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'task_form.html'
    success_url = reverse_lazy('task-list')

class TaskDeleteView(AdminRequiredMixin, DeleteView):
    model = Task
    template_name = 'task_confirm_delete.html'
    success_url = reverse_lazy('task-list')

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

def register(request):
    logger.debug("Начало функции register")
    
    # Получаем текущий язык из сессии
    current_language = request.session.get('django_language', settings.LANGUAGE_CODE)
    
    # Получаем переводы для текущего языка
    from .translations import TRANSLATIONS
    translations = TRANSLATIONS.get(current_language, TRANSLATIONS['ru'])
    
    if request.method == 'POST':
        logger.debug("Получен POST-запрос")
        form = RegisterForm(request.POST)
        # Добавляем request в форму для доступа к языковым настройкам
        form.request = request
        
        if form.is_valid():
            logger.debug("Форма валидна")
            # Создаём и сохраняем пользователя
            user = form.save()
            user.is_active = False  # Отключаем до активации
            # Сохраняем email в модели User
            email = request.POST.get('email', '')
            if email:
                user.email = email
            user.save()
            # Создаём токен активации
            token = ActivationToken.objects.create(user=user)
            logger.debug(f"Создан токен: {token.token}")
            # Формируем ссылку для активации
            activation_link = request.build_absolute_uri(
                reverse_lazy('activate', kwargs={'token': str(token.token)})
            )
            logger.debug(f"Сформирована ссылка: {activation_link}")
            # Отправляем email (опционально, если email указан)
            if email:
                # Выбираем тему письма в зависимости от языка
                if current_language == 'ru':
                    subject = 'Подтверждение регистрации на сайте Аренда недвижимости'
                    message = f'Здравствуйте, {user.username}!\n\n' \
                              f'Чтобы активировать ваш аккаунт, перейдите по ссылке:\n' \
                              f'{activation_link}\n\n' \
                              f'Если это не вы, просто проигнорируйте это письмо.'
                elif current_language == 'en':
                    subject = 'Registration confirmation on Property Rental website'
                    message = f'Hello, {user.username}!\n\n' \
                              f'To activate your account, please follow this link:\n' \
                              f'{activation_link}\n\n' \
                              f'If this was not you, please ignore this email.'
                elif current_language == 'kk':
                    subject = 'Жылжымайтын мүлікті жалға алу сайтында тіркеуді растау'
                    message = f'Сәлеметсіз бе, {user.username}!\n\n' \
                              f'Аккаунтыңызды белсендіру үшін осы сілтемеге өтіңіз:\n' \
                              f'{activation_link}\n\n' \
                              f'Егер бұл сіз болмасаңыз, бұл хатты елемеңіз.'
                else:
                    subject = 'Подтверждение регистрации на сайте Аренда недвижимости'
                    message = f'Здравствуйте, {user.username}!\n\n' \
                              f'Чтобы активировать ваш аккаунт, перейдите по ссылке:\n' \
                              f'{activation_link}\n\n' \
                              f'Если это не вы, просто проигнорируйте это письмо.'
                
                try:
                    logger.debug("Попытка отправки email")
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=True,
                    )
                    logger.debug("Email успешно отправлен или проигнорирован")
                except Exception as e:
                    logger.error(f"Ошибка отправки email: {str(e)}")
            
            # Выбираем сообщение об успешной регистрации в зависимости от языка
            if current_language == 'ru':
                success_message = 'Регистрация начата! Пожалуйста, активируйте аккаунт (если указали email, проверьте почту).'
            elif current_language == 'en':
                success_message = 'Registration started! Please activate your account (if you provided an email, check your inbox).'
            elif current_language == 'kk':
                success_message = 'Тіркеу басталды! Аккаунтыңызды белсендіріңіз (егер электрондық поштаңызды көрсетсеңіз, поштаңызды тексеріңіз).'
            else:
                success_message = 'Регистрация начата! Пожалуйста, активируйте аккаунт (если указали email, проверьте почту).'
            
            response_data = {
                'success': True,
                'message': success_message
            }
            logger.debug(f"Ответ: {response_data}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(response_data)
            return render(request, 'activation_pending.html', {
                'username': user.username, 
                'message': response_data['message'],
                'CURRENT_LANGUAGE': current_language,
                'translations': translations
            })
        else:
            logger.debug("Форма невалидна")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                form_html = render_to_string('register.html', {
                    'form': form,
                    'CURRENT_LANGUAGE': current_language,
                    'translations': translations
                }, request=request)
                return JsonResponse({'success': False, 'form_html': form_html})
    else:
        logger.debug("Получен GET-запрос")
        form = RegisterForm()
        # Добавляем request в форму для доступа к языковым настройкам
        form.request = request
    
    return render(request, 'register.html', {
        'form': form,
        'CURRENT_LANGUAGE': current_language,
        'translations': translations
    })

def activate_account(request, token):
    try:
        activation_token = ActivationToken.objects.get(token=token, is_used=False)
        user = activation_token.user
        if user:
            user.is_active = True
            user.save()
            activation_token.is_used = True
            activation_token.save()
            login(request, user)
            return redirect('profile')
        return HttpResponse("Ошибка активации: пользователь не найден.", status=400)
    except ActivationToken.DoesNotExist:
        return HttpResponse("Недействительная или уже использованная ссылка для активации.", status=400)
    except Exception as e:
        return HttpResponse(f"Ошибка активации: {str(e)}", status=400)

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем текущий язык из сессии
        current_language = self.request.session.get('django_language', settings.LANGUAGE_CODE)
        context['CURRENT_LANGUAGE'] = current_language
        
        # Добавляем переводы
        from .translations import TRANSLATIONS
        context['translations'] = TRANSLATIONS.get(current_language, TRANSLATIONS['ru'])
        
        return context

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

@login_required
def profile(request):
    return render(request, 'profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UpdateProfileForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})

def about(request):
    # Получаем текущий язык из сессии
    current_language = request.session.get('django_language', settings.LANGUAGE_CODE)
    
    # Добавляем переводы кнопок и текстов
    from .translations import TRANSLATIONS
    translations = TRANSLATIONS.get(current_language, TRANSLATIONS['ru'])
    
    return render(request, 'about.html', {
        'CURRENT_LANGUAGE': current_language,
        'translations': translations
    })

def change_language(request, language_code):
    """
    Изменяет язык интерфейса и перенаправляет на предыдущую страницу.
    """
    # Получаем URL предыдущей страницы или главную страницу
    next_url = request.META.get('HTTP_REFERER', '/')
    
    # Проверяем, что язык допустимый
    if language_code in [lang[0] for lang in settings.LANGUAGES]:
        # Устанавливаем язык в сессии напрямую
        request.session['django_language'] = language_code
        request.session['CURRENT_LANGUAGE'] = language_code
        # Принудительно сохраняем сессию
        request.session.save()
    
    # Добавляем параметр к URL для обновления страницы
    if '?' in next_url:
        next_url += f'&lang_changed={language_code}'
    else:
        next_url += f'?lang_changed={language_code}'
    
    # Перенаправляем на предыдущую страницу с параметром
    return redirect(next_url)


def translate_view(request):
    """
    Представление для обработки AJAX-запросов на перевод текста.
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        text = request.POST.get('text', '')
        target_language = request.POST.get('language', 'en')
        
        translated = translate_text(text, target_language)
        
        return JsonResponse({'translated': translated})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
