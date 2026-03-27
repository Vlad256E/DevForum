from django.db import models
from django.conf import settings # Для связи с кастомным юзером
from django.contrib.auth import get_user_model

User = get_user_model() # Получаем нашу модель пользователя

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')

    def __str__(self):
        return self.name

class Topic(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    # Связи (Внешние ключи)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='topics', verbose_name='Категория')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topics', verbose_name='Автор')

    def __str__(self):
        return self.title

class Message(models.Model):
    text = models.TextField(verbose_name='Текст')
    posted_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='messages', verbose_name='Тема')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages', verbose_name='Автор')

    # Поля для редактирования
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
    is_edited = models.BooleanField(default=False, verbose_name='Изменено')

    is_helpful = models.BooleanField(default=False, verbose_name='Полезный ответ')

    def __str__(self):
        return f'Сообщение от {self.author.username} в теме {self.topic.title}'

class MessageLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_messages')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Уникальность: один пользователь = один лайк на одно сообщение
        unique_together = ('user', 'message')

class Complaint(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('resolved', 'Решено'),
        ('rejected', 'Отклонено'),
    )
    
    reason = models.TextField(verbose_name='Причина')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='complaints', verbose_name='Сообщение')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints', verbose_name='Отправитель')

    def __str__(self):
        return f'Жалоба от {self.sender.username}'
    
    
class NewsItem(models.Model):
    content = models.TextField(verbose_name='Текст новости')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['-created_at'] # Сортировка: новые сверху
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'

    def __str__(self):
        return self.content[:50]
    
class Dialog(models.Model):
    participants = models.ManyToManyField(User, related_name='dialogs', verbose_name='Участники')
    
    class Meta:
        verbose_name = 'Диалог'
        verbose_name_plural = 'Диалоги'

    def __str__(self):
        return f"Диалог {self.id}"

class PrivateMessage(models.Model):
    dialog = models.ForeignKey(Dialog, on_delete=models.CASCADE, related_name='messages', verbose_name='Диалог')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_private_messages', verbose_name='Отправитель')
    text = models.TextField(verbose_name='Текст сообщения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Личное сообщение'
        verbose_name_plural = 'Личные сообщения'