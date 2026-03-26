from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Логин (username), email и password уже встроены в AbstractUser
    
    ROLE_CHOICES = (
        ('user', 'Пользователь'),
        ('mod', 'Модератор'),
        ('admin', 'Администратор'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user', verbose_name='Роль')
    reputation = models.IntegerField(default=0, verbose_name='Репутация')

    def __str__(self):
        return self.username