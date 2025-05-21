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
            self.add_error('password1', 'Пароль не соответствует требованиям.')
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