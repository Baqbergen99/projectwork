from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'image_url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Введите JSON, например: {"price": 90000, "rooms": 1, "condition": "Среднее"}'})
        }