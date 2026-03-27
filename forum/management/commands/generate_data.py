import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from forum.models import Category, Topic, Message, NewsItem
# Если ты уже добавил модели диалогов, их тоже можно импортировать здесь

User = get_user_model()

class Command(BaseCommand):
    help = 'Генерирует качественные демо-данные для DEVHUB'

    def handle(self, *args, **kwargs):
        self.stdout.write('Очистка старых данных...')
        Message.objects.all().delete()
        Topic.objects.all().delete()
        Category.objects.all().delete()
        NewsItem.objects.all().delete()

        self.stdout.write('Создание персонажей...')
        users_data = [
            {'username': 'CodeSensei', 'email': 'sensei@dev.ru', 'role': 'admin'},
            {'username': 'DebugLife', 'email': 'debug@dev.ru', 'role': 'mod'},
            {'username': 'Frontend_Queen', 'email': 'alice@dev.ru', 'role': 'user'},
            {'username': 'PythonWiz', 'email': 'wiz@dev.ru', 'role': 'user'},
            {'username': 'CyberPunk', 'email': 'punk@dev.ru', 'role': 'user'},
        ]
        
        users = []
        for u_data in users_data:
            user, created = User.objects.get_or_create(
                username=u_data['username'], 
                email=u_data['email'],
                defaults={'role': u_data['role'], 'reputation': random.randint(10, 500)}
            )
            if created:
                user.set_password('devhub2026')
                user.save()
            users.append(user)

        self.stdout.write('Наполнение новостной ленты...')
        updates = [
            "Запущена система личных сообщений! Общайтесь приватно.",
            "Обновлены аватарки: теперь профили выглядят строже.",
            "Добавлена сортировка в каталоге. Находите популярное быстрее.",
            "Правила форума дополнены разделом про этикет в комментариях."
        ]
        for text in updates:
            NewsItem.objects.create(content=text)

        self.stdout.write('Создание экосистемы разделов...')
        categories_content = {
            'Backend разработка': {
                'desc': 'Архитектура, базы данных и серверная магия на Python, Go, Node.js.',
                'topics': [
                    'Django vs FastAPI: что выбрать для нового пет-проекта?',
                    'Как оптимизировать тяжелые запросы в PostgreSQL?',
                    'Ваше мнение о микросервисах в 2026 году?'
                ]
            },
            'Frontend & UI/UX': {
                'desc': 'Создаем красивые интерфейсы. React, Vue, Tailwind и основы дизайна.',
                'topics': [
                    'Tailwind CSS: почему я больше не пишу чистый CSS.',
                    'React 19 уже близко? Обсуждаем новые фичи.',
                    'Лучшие шрифты для кода в этом году.'
                ]
            },
            'Карьера и Обучение': {
                'desc': 'Поиск работы, составление резюме и обмен опытом прохождения интервью.',
                'topics': [
                    'Как я прошел собеседование в BigTech с первого раза.',
                    'Стоит ли учить программирование с нуля прямо сейчас?',
                    'Обзор зарплат: Middle Developer в Европе и СНГ.'
                ]
            }
        }

        replies = [
            "Полностью согласен с автором! Это сэкономило мне кучу времени.",
            "А мне кажется, что старый подход был надежнее. Кто-нибудь пробовал это в продакшене?",
            "Интересная мысль, надо будет затестить на выходных.",
            "Спасибо за статью! Можете подробнее рассказать про настройку конфигов?",
            "Это база. Каждый должен знать такие вещи.",
            "Хороший вопрос! Я обычно решаю это через кэширование на стороне Redis."
        ]

        for cat_name, content in categories_content.items():
            cat = Category.objects.create(name=cat_name, description=content['desc'])
            
            for t_title in content['topics']:
                topic = Topic.objects.create(
                    title=t_title,
                    category=cat,
                    author=random.choice(users)
                )
                
                # Каждой теме добавляем по 4-7 живых ответов
                for _ in range(random.randint(4, 7)):
                    Message.objects.create(
                        topic=topic,
                        author=random.choice(users),
                        text=random.choice(replies)
                    )

        self.stdout.write(self.style.SUCCESS('Форум успешно оживлен! Данные готовы.'))