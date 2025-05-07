from django.db import models

class Task(models.Model):
   title = models.CharField(max_length=255) # Название задачи
   description = models.TextField(blank=True, null=True) # Описание
   created_at = models.DateTimeField(auto_now_add=True) # Дата создания
   image_url = models.URLField(blank=True, null=True) # Поле для ссылки на изображение
 
   def __str__(self):
     return self.title