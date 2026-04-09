import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from forum.models import Category, Topic, Message, MessageLike, Complaint, NewsItem

User = get_user_model()

class Command(BaseCommand):
    help = 'Заполняет базу данных реалистичными тестовыми данными для DEVHUB'

    def handle(self, *args, **kwargs):
        self.stdout.write('Начинаю генерацию расширенной базы контента...')

        # Опционально: можно раскомментировать строки ниже, чтобы очищать старые данные перед новой генерацией
        # Category.objects.all().delete()
        # Topic.objects.all().delete()

        # 1. Создание актуальных IT-категорий
        categories_data = [
            ('Python', 'Всё о Python: фреймворки (Django, FastAPI), скрипты, парсинг и архитектура.'),
            ('Frontend & JavaScript', 'React, Vue, Angular, ванильный JS, HTML/CSS и веб-дизайн.'),
            ('Backend & Архитектура', 'Обсуждение серверной логики, микросервисов, Go, Rust, Java и C#.'),
            ('DevOps & Инфраструктура', 'Docker, Kubernetes, CI/CD, администрирование Linux и облака.'),
            ('Базы данных', 'SQL (PostgreSQL, MySQL) и NoSQL (MongoDB, Redis), оптимизация запросов.'),
            ('Мобильная разработка', 'iOS (Swift), Android (Kotlin), кроссплатформа (Flutter, React Native).'),
            ('Карьера и работа', 'Собеседования, резюме, зарплаты, релокация и поиск первой работы.'),
            ('Флудильня', 'Свободное общение на любые темы, не связанные напрямую с кодом.'),
        ]
        
        categories = {}
        for name, desc in categories_data:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
            categories[name] = cat
        self.stdout.write(f'Создано категорий: {len(categories)}')

        # 2. Создание пула пользователей с разными рангами
        usernames = [
            'PythonGuru', 'FrontendQueen', 'BugHunter', 'CyberSafe', 'DataWizard',
            'CodeNinja', 'DevOpsMaster', 'SwiftDev', 'GoRunner', 'RustLover',
            'Mod_Sergey', 'Mod_Anna', 'TechLead', 'JuniorDev', 'SeniorArch',
            'DbAdmin', 'AI_Enthusiast', 'ReactFanboy', 'LinuxUser', 'SysAdmin'
        ]
        
        users = []
        for uname in usernames:
            role = 'mod' if 'Mod_' in uname else 'user'
            # Репутация подбирается так, чтобы показать разные ранги (от Новичка до Ветерана)
            reputation = random.choice([5, 45, 125, 250, 400]) 
            
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
        self.stdout.write(f'Пользователей в базе: {len(users)}')

        # 3. База осмысленных обсуждений по категориям
        forum_content = {
            'Python': [
                {
                    'title': 'Стоит ли переходить с Django на FastAPI в 2026?',
                    'messages': [
                        'Всем привет! Начинаем новый микросервис, думаю взять FastAPI вместо привычного Django. Какие подводные камни?',
                        'FastAPI быстрее и круче работает с асинхронщиной. Если не нужна огромная встроенная админка Django, бери смело.',
                        'Согласен, Pydantic рулит! Но экосистема плагинов у Django всё ещё богаче.',
                        'У нас в проде FastAPI уже 2 года, полёт нормальный. Главное правильно настроить SQLAlchemy.'
                    ]
                },
                {
                    'title': 'Помогите разобраться с GIL в Python 3.13+',
                    'messages': [
                        'Читал, что GIL наконец-то можно отключать. Кто-то уже пробовал в реальных задачах? Дает ли это ощутимый прирост скорости?',
                        'Дает, но только если у тебя CPU-bound задачи (математика, парсинг больших данных). Для I/O разницы особо не заметишь.',
                        'Плюс многие старые C-расширения ломаются без GIL. Будь осторожен и проверяй зависимости в requirements.txt.'
                    ]
                }
            ],
            'Frontend & JavaScript': [
                {
                    'title': 'React Compiler - как оно в реальных проектах?',
                    'messages': [
                        'Кто уже успел пощупать новый React Compiler? Реально ли можно забыть про useMemo и useCallback?',
                        'Перформанс вырос заметно, но на старых проектах пришлось попотеть с миграцией.',
                        'У меня сломалась пара кастомных хуков, пришлось переписывать. Но в целом фича огонь, кода стало меньше.'
                    ]
                },
                {
                    'title': 'TailwindCSS или CSS Modules?',
                    'messages': [
                        'Начинаю новый пет-проект. Раньше писал на SCSS/Modules, сейчас все хвалят Tailwind. В чем его реальный профит?',
                        'Скорость разработки. Не нужно придумывать дурацкие имена классам вроде .header-wrapper-inner и прыгать между файлами.',
                        'Минус Tailwind — HTML превращается в кашу из классов. Но к этому быстро привыкаешь, особенно с компонентами.'
                    ]
                }
            ],
            'Backend & Архитектура': [
                {
                    'title': 'Переписали монолит на Go, делюсь опытом',
                    'messages': [
                        'Полгода назад начали пилить микросервисы на Go вместо старого PHP-монолита. Потребление памяти упало в 10 раз.',
                        'Звучит круто! А как решали проблему с распределенными транзакциями?',
                        'Использовали паттерн Saga и Kafka как брокер сообщений. Было больно дебажить поначалу, но справились.',
                        'Go шикарен для таких задач. Главное не плодить микросервисы там, где они объективно не нужны.'
                    ]
                }
            ],
            'DevOps & Инфраструктура': [
                {
                    'title': 'Утекает память в Docker-контейнере (Node.js)',
                    'messages': [
                        'Странная проблема: контейнер с NestJS стабильно падает по OOM каждые 3 дня. Утечек в коде вроде не нашел.',
                        'Проверь лимиты памяти в docker-compose. И попробуй запустить Node с флагом --max-old-space-size.',
                        'А еще посмотри, не копятся ли у тебя логи внутри контейнера. У нас как-то раз логгер забил всю память.'
                    ]
                }
            ],
            'Карьера и работа': [
                {
                    'title': 'Собеседования в бигтех в 2026 году',
                    'messages': [
                        'Подскажите, насколько сейчас душат алгоритмами на позицию мидла? Год назад было жестко.',
                        'Алгоритмы все еще просят, LeetCode Medium минимум. Но стали гораздо больше спрашивать про System Design.',
                        'Согласен, сейчас архитектура важнее. И еще делают огромный упор на софт-скиллы и работу в команде.'
                    ]
                },
                {
                    'title': 'Ревью резюме (Backend Python)',
                    'messages': [
                        'Ребят, посмотрите резюме, пожалуйста. Ищу работу джуном уже 3 месяца, отказы без фидбека.',
                        'Убери из навыков "уверенный пользователь ПК" и Word. Выдели пет-проекты жирным и добавь нормальные ссылки на GitHub.',
                        'И распиши подробнее, ЧТО ИМЕННО ты делал в проектах, а не просто список использованных библиотек.'
                    ]
                }
            ]
        }

        # Генерация топиков и сообщений
        for cat_name, topics in forum_content.items():
            if cat_name not in categories:
                continue
                
            category = categories[cat_name]
            for topic_data in topics:
                # Автор темы
                author = random.choice(users)
                topic, _ = Topic.objects.get_or_create(
                    title=topic_data['title'],
                    category=category,
                    author=author
                )
                
                # Создаем сообщения. Первое — от автора темы, остальные — ответы случайных юзеров
                for idx, text in enumerate(topic_data['messages']):
                    msg_author = author if idx == 0 else random.choice([u for u in users if u != author])
                    
                    msg, created_msg = Message.objects.get_or_create(
                        topic=topic,
                        text=text,
                        defaults={'author': msg_author}
                    )
                    
                    # 4. Рандомные лайки на сообщения
                    if created_msg and random.random() > 0.3:
                        likers = random.sample(users, k=random.randint(1, 5))
                        for liker in likers:
                            if liker != msg.author:
                                MessageLike.objects.get_or_create(user=liker, message=msg)
                                
                    # Установка отметки "Полезный ответ" (рандомно для одного из ответов)
                    if created_msg and idx > 0 and random.random() > 0.8:
                        msg.is_helpful = True
                        msg.save()

        # 5. Создание жалоб для проверки панели модератора
        reasons = ['Спам', 'Оскорбление участника', 'Флуд в тематическом разделе', 'Реклама казино']
        pending_msgs = Message.objects.order_by('?')[:5]
        for msg in pending_msgs:
            Complaint.objects.get_or_create(
                message=msg,
                sender=random.choice(users),
                defaults={'reason': random.choice(reasons), 'status': 'pending'}
            )

        # 6. Обновление новостной ленты
        NewsItem.objects.get_or_create(content="Форум DEVHUB переведен на новый дизайн TailwindCSS!")
        NewsItem.objects.get_or_create(content="Мы добавили систему репутации. Теперь за полезные ответы начисляются очки!")
        NewsItem.objects.get_or_create(content="На следующей неделе пройдет АМА-сессия с Senior DevOps инженером.")

        self.stdout.write(self.style.SUCCESS('База данных успешно наполнена качественным контентом!'))