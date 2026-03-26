from django.contrib import admin
from .models import User

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    # Какие колонки показывать в списке пользователей
    list_display = ('username', 'email', 'role', 'reputation', 'is_staff')
    # По каким полям можно фильтровать
    list_filter = ('role', 'is_staff')