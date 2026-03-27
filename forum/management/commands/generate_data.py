from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Генерирует тестовых пользователей для DEVHUB'

    def handle(self, *args, **kwargs):
        self.stdout.write('Очистка старых тестовых пользователей...')
        # Удаляем всех, кроме суперпользователей, чтобы не сбросить главный админский аккаунт
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write('Создание персонажей с разной репутацией...')
        users_data = [
            {'username': 'CodeSensei', 'email': 'sensei@dev.ru', 'role': 'admin', 'rep': 250},   # Ветеран
            {'username': 'DebugLife', 'email': 'debug@dev.ru', 'role': 'mod', 'rep': 150},      # Опытный
            {'username': 'Frontend_Queen', 'email': 'alice@dev.ru', 'role': 'user', 'rep': 70},   # Участник форума
            {'username': 'PythonWiz', 'email': 'wiz@dev.ru', 'role': 'user', 'rep': 20},       # Новичок
            {'username': 'CyberPunk', 'email': 'punk@dev.ru', 'role': 'user', 'rep': -20},     # Нарушитель
        ]
        
        for u_data in users_data:
            user, created = User.objects.get_or_create(
                username=u_data['username'], 
                email=u_data['email'],
                defaults={'role': u_data['role'], 'reputation': u_data['rep']}
            )
            if created:
                user.set_password('devhub2026')
                user.save()

        self.stdout.write(self.style.SUCCESS('Пользователи успешно созданы! Пароль для всех: devhub2026'))