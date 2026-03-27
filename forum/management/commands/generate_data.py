import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from forum.models import Category, Topic, Message

User = get_user_model()

class Command(BaseCommand):
    help = 'Генерирует тестовые данные для форума (юзеры, категории, темы, сообщения)'

    def handle(self, *args, **kwargs):
        self.stdout.write('Удаляем старые данные (опционально)...')
        # Раскомментируй следующие строки, если хочешь очищать базу перед каждой новой генерацией
        # Message.objects.all().delete()
        # Topic.objects.all().delete()
        # Category.objects.all().delete()

        self.stdout.write('Создаем тестовых пользователей...')
        users = []
        for i in range(1, 6):
            username = f'TestUser_{i}'
            # get_or_create позволяет не дублировать юзеров при повторном запуске
            user, created = User.objects.get_or_create(username=username, email=f'user{i}@test.com')
            if created:
                user.set_password('testpassword123')
                user.save()
            users.append(user)

        self.stdout.write('Создаем категории...')
        cat_data = [
            {'name': 'Python', 'desc': 'Обсуждение языка Python и фреймворков'},
            {'name': 'JavaScript', 'desc': 'Всё о JS, React, Vue и Node.js'},
            {'name': 'DevOps', 'desc': 'Docker, CI/CD, сервера и деплой'},
        ]
        
        categories = []
        for data in cat_data:
            cat, _ = Category.objects.get_or_create(name=data['name'], defaults={'description': data['desc']})
            categories.append(cat)

        self.stdout.write('Создаем темы и сообщения...')
        # Для каждой категории создаем по 5 тем
        for cat in categories:
            for i in range(1, 6):
                topic_title = f'Тестовая тема №{i} в разделе {cat.name}'
                topic, created = Topic.objects.get_or_create(
                    title=topic_title,
                    category=cat,
                    defaults={'author': random.choice(users)}
                )

                # Если тема только что создана, добавляем в неё от 3 до 8 сообщений
                if created:
                    for j in range(random.randint(3, 8)):
                        Message.objects.create(
                            topic=topic,
                            author=random.choice(users),
                            text=f'Это автоматически сгенерированное сообщение №{j+1} для теста интерфейса и пагинации.'
                        )

        self.stdout.write(self.style.SUCCESS('Успешно! Тестовые данные сгенерированы.'))