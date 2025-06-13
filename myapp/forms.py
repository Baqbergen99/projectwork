from django import forms

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task
import re

class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем текущий язык из запроса, если он есть
        request = kwargs.get('request')
        if request and hasattr(request, 'session'):
            from django.conf import settings
            from .translations import TRANSLATIONS
            language = request.session.get('django_language', settings.LANGUAGE_CODE)
            translations = TRANSLATIONS.get(language, TRANSLATIONS['ru'])
            
            # Обновляем сообщения об ошибках для полей пароля
            self.fields['password1'].help_text = translations.get('password_min_length')
            self.fields['password2'].help_text = translations.get('password_mismatch')

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        # Условия для пароля
        conditions = {
            'length': len(password1) >= 8,
            'letter': bool(re.search(r'[a-zA-Z]', password1)),
            'digit': bool(re.search(r'\d', password1)),
            'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password1)),
        }
        if not all(conditions.values()):
            # Получаем текущий язык
            from django.conf import settings
            from .translations import TRANSLATIONS
            request = getattr(self, 'request', None)
            language = 'ru'
            if request and hasattr(request, 'session'):
                language = request.session.get('django_language', settings.LANGUAGE_CODE)
            translations = TRANSLATIONS.get(language, TRANSLATIONS['ru'])
            
            self.add_error('password1', translations.get('password_too_short'))
            self.conditions = conditions  # Сохраняем условия для отображения в шаблоне
        return password1

class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'image_url']
        widgets = {

          
        'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Введите JSON, например: {"price": 9000, "rooms": 1, "condition": "Среднее"}'})
        }