from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'Пользователь'),
        ('mod', 'Модератор'),
        ('admin', 'Администратор'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user', verbose_name='Роль')
    reputation = models.IntegerField(default=0, verbose_name='Репутация')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='Аватарка')
    email_notifications = models.BooleanField(default=True, verbose_name='Email-уведомления')

    # Поле черного списка
    blocked_users = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='blocked_by', verbose_name='Черный список')

    def __str__(self):
        return self.username