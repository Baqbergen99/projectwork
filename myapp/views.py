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
from .models import Task, ActivationToken
from .forms import RegisterForm, UpdateProfileForm, TaskForm
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
        for item in context['data']:
            try:
                details = json.loads(item.description) if item.description else {}
            except json.JSONDecodeError:
                details = {}
            prop_dict = {
                "id": item.id,
                "title": item.title,
                "details": details,
                "created_at": item.created_at,
                "image": item.image_url if item.image_url else "https://via.placeholder.com/300x200?text=Нет фото"
            }
            properties_data.append(prop_dict)
        context['data'] = properties_data
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
    if request.method == 'POST':
        logger.debug("Получен POST-запрос")
        form = RegisterForm(request.POST)
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
            response_data = {
                'success': True,
                'message': 'Регистрация начата! Пожалуйста, активируйте аккаунт (если указали email, проверьте почту).'
            }
            logger.debug(f"Ответ: {response_data}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(response_data)
            return render(request, 'activation_pending.html', {'username': user.username, 'message': response_data['message']})
        else:
            logger.debug("Форма невалидна")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                form_html = render_to_string('register.html', {'form': form}, request=request)
                return JsonResponse({'success': False, 'form_html': form_html})
    else:
        logger.debug("Получен GET-запрос")
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

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
    return render(request, 'about.html')