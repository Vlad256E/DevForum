import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from forum.models import Category, Topic, Message, MessageLike, Complaint, NewsItem
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными для DEVHUB'

    def handle(self, *args, **kwargs):
        self.stdout.write('Начинаю генерацию данных...')

        # 1. Создание категорий (Базовые и Основные) [cite: 54, 106]
        categories_data = [
            ('Программирование', 'Обсуждение языков программирования, алгоритмов и паттернов.'),
            ('Веб-разработка', 'Frontend, Backend, фреймворки и инструменты.'),
            ('Дизайн Ui/UX', 'Тренды в дизайне, разбор кейсов и инструментов.'),
            ('Железо и Софт', 'Обзоры комплектующих и операционных систем.'),
            ('Флудильня', 'Общение на любые темы, не связанные с IT.'),
        ]
        
        categories = []
        for name, desc in categories_data:
            cat, created = Category.objects.get_or_create(name=name, defaults={'description': desc})
            categories.append(cat)
        self.stdout.write(f'Создано категорий: {len(categories)}')

        # 2. Создание 15 пользователей с разным рейтингом и ролями [cite: 50, 102]
        # Роли: 'user', 'mod'. Админ остается существующим.
        usernames = [
            'PythonGuru', 'FrontendQueen', 'BugHunter', 'CyberSafe', 'DataWizard',
            'CodeNinja', 'DevOpsMaster', 'SwiftDev', 'GoRunner', 'RustLover',
            'Mod_Sergey', 'Mod_Anna', 'TechLead', 'JuniorDev', 'SeniorArch'
        ]
        
        users = []
        for i, uname in enumerate(usernames):
            # Первые два из списка Mod_ будут модераторами [cite: 5, 101]
            role = 'mod' if 'Mod_' in uname else 'user'
            
            # Распределяем репутацию для разных рангов (Новичок, Участник, Опытный, Ветеран) 
            reputation = random.choice([10, 65, 125, 300]) 
            
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': f'{uname.lower()}@example.com',
                    'role': role,
                    'reputation': reputation,
                    'is_staff': (role == 'mod')
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            users.append(user)
        self.stdout.write(f'Создано пользователей: {len(users)}')

        # 3. Создание тем и сообщений [cite: 33, 38, 63]
        topics_titles = [
            'Как выучить Python за месяц?', 'Лучшие шрифты для VS Code', 
            'React против Vue в 2026 году', 'Почему C++ всё еще жив?',
            'Ошибки при проектировании БД', 'Как пройти собеседование в FAANG',
            'Мой первый пет-проект на Rust', 'Что купить: Mac или ThinkPad?'
        ]

        messages_pool = [
            "Отличный вопрос! Я считаю, что главное — практика.",
            "Не согласен, теория важнее на начальном этапе.",
            "Посмотрите документацию, там всё подробно расписано.",
            "Кто-нибудь сталкивался с ошибкой 403 при деплое?",
            "Лайк за пост, очень полезно!",
            "Это уже обсуждали сто раз, используйте поиск по форуму.",
        ]

        for title in topics_titles:
            author = random.choice(users)
            category = random.choice(categories)
            topic, _ = Topic.objects.get_or_create(
                title=title, 
                category=category, 
                author=author
            )
            
            # Добавляем сообщения в тему [cite: 39, 63]
            for _ in range(random.randint(3, 7)):
                msg_author = random.choice(users)
                msg = Message.objects.create(
                    topic=topic,
                    author=msg_author,
                    text=random.choice(messages_pool)
                )
                
                # 4. Создание лайков [cite: 43, 68]
                if random.random() > 0.5:
                    liker = random.choice(users)
                    if liker != msg_author:
                        MessageLike.objects.get_or_create(user=liker, message=msg)

        # 5. Создание жалоб для проверки панели модератора 
        reasons = ['Спам', 'Оскорбление', 'Флуд в тематическом разделе']
        pending_msgs = Message.objects.all()[:3]
        for msg in pending_msgs:
            Complaint.objects.get_or_create(
                message=msg,
                sender=random.choice(users),
                defaults={'reason': random.choice(reasons), 'status': 'pending'}
            )

        # 6. Новости
        NewsItem.objects.get_or_create(content="Форум DEVHUB успешно запущен в тестовом режиме!")
        NewsItem.objects.get_or_create(content="Обновление правил: за спам теперь полагается штраф -50 репутации.")

        self.stdout.write(self.style.SUCCESS('База данных успешно наполнена!'))