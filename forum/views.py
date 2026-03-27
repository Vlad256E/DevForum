from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from .models import Category, Topic, Message, Complaint, MessageLike, NewsItem, PrivateMessage, Dialog
from users.models import User 
from datetime import timedelta
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Max

# --- ЛОГИКА РЕПУТАЦИИ ---
def update_reputation(user, points):
    user.reputation += points
    user.save()

def reward_strategy(user, action_type):
    points = 15 if action_type == 'helpful' else 1
    update_reputation(user, points)

# --- ПРОВЕРКИ ПРАВ ---
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

def is_moderator(user):
    return user.is_authenticated and (user.is_superuser or user.role in ['admin', 'mod'])

# --- ГЛАВНАЯ СТРАНИЦА (Объединенная версия) ---
def home_view(request):
    # Категории с подсчетом тем и сортировкой
    categories = Category.objects.annotate(topic_count=Count('topics')).order_by('-topic_count')
    # 5 свежих тем
    recent_topics = Topic.objects.order_by('-created_at')[:5]
    # 5 последних новостей (теперь они точно попадут на экран!)
    news_items = NewsItem.objects.all()[:5] 

    return render(request, 'forum/index.html', {
        'categories': categories,
        'recent_topics': recent_topics,
        'news_items': news_items
    })

# --- АДМИН ПАНЕЛЬ ---
@user_passes_test(is_admin)
def admin_panel_view(request):
    categories = Category.objects.all()
    users = User.objects.all().order_by('-date_joined')
    total_topics_count = Topic.objects.count()
    one_week_ago = timezone.now() - timezone.timedelta(days=7)
    new_users_count = User.objects.filter(date_joined__gte=one_week_ago).count()
    news_items = NewsItem.objects.all()
    
    context = {
        'categories': categories,
        'users': users,
        'total_topics_count': total_topics_count,
        'new_users_count': new_users_count,
        'news_items': news_items,
    }
    return render(request, 'forum/admin_panel.html', context)

@user_passes_test(is_admin)
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        if name:
            if Category.objects.filter(name__iexact=name).exists():
                messages.error(request, 'Категория с таким названием уже существует!')
            else:
                Category.objects.create(name=name, description=description)
                messages.success(request, 'Категория успешно добавлена.')
    return redirect('admin_panel')

@user_passes_test(is_admin)
def delete_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        category.delete()
        messages.success(request, 'Категория удалена.')
    return redirect('admin_panel')

# --- МОДЕРАЦИЯ ---
@user_passes_test(is_moderator)
def dashboard_view(request):
    complaints = Complaint.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'forum/dashboard.html', {'complaints': complaints})

# --- ТЕМЫ И КАТАЛОГ ---
def catalog_view(request):
    sort = request.GET.get('sort', 'new')
    categories = Category.objects.annotate(topic_count=Count('topics'))
    if sort == 'popular':
        categories = categories.order_by('-topic_count')
    else:
        categories = categories.order_by('-id')
    return render(request, 'forum/catalog.html', {'categories': categories})

def category_detail_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    topics = Topic.objects.filter(category=category)
    sort = request.GET.get('sort', 'new')
    if sort == 'popular':
        topics = topics.annotate(msg_count=Count('messages')).order_by('-msg_count')
    else:
        topics = topics.order_by('-created_at') 
    return render(request, 'forum/category_detail.html', {'category': category, 'topics': topics})

def topic_view(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    if request.method == 'POST' and request.user.is_authenticated:
        text = request.POST.get('text')
        if text:
            Message.objects.create(topic=topic, author=request.user, text=text)
            return redirect('topic', topic_id=topic.id)
    
    # Загружаем сообщения и сразу подтягиваем лайки для скорости
    messages_list = topic.messages.all().order_by('posted_at').prefetch_related('likes')
    return render(request, 'forum/topic.html', {'topic': topic, 'forum_messages': messages_list})

@login_required
def toggle_like_message(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id)
    if request.user == message_obj.author:
        messages.error(request, 'Нельзя лайкать самого себя.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    like, created = MessageLike.objects.get_or_create(user=request.user, message=message_obj)
    if created:
        # Согласно RewardAction из Лабораторной №10: Лайк = +5 баллов
        message_obj.author.reputation += 5
        messages.success(request, 'Вам понравилось это сообщение! (+5 баллов автору)')
    else:
        like.delete()
        message_obj.author.reputation -= 5
        messages.info(request, 'Лайк убран.')
    
    message_obj.author.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@user_passes_test(is_moderator)
def mark_as_helpful(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id)
    if not message_obj.is_helpful:
        message_obj.is_helpful = True
        message_obj.save()
        # Согласно Лабораторной №10: "Ответ отмечен как решение" = +30 баллов
        message_obj.author.reputation += 30
        message_obj.author.save()
        messages.success(request, 'Сообщение отмечено как решение! (+30 баллов автору)')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def create_topic_view(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        text = request.POST.get('text')
        if title and category_id and text:
            category = get_object_or_404(Category, id=category_id)
            topic = Topic.objects.create(title=title, category=category, author=request.user)
            Message.objects.create(topic=topic, author=request.user, text=text)
            return redirect('topic', topic_id=topic.id)
    return render(request, 'forum/create_topic.html', {'categories': categories})

# --- СООБЩЕНИЯ И ЛАЙКИ ---
@login_required
def edit_message_view(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id)
    if request.user != message_obj.author:
        return HttpResponseForbidden("Вы не можете редактировать чужое сообщение.")
    if timezone.now() - message_obj.posted_at > timedelta(minutes=30):
        messages.error(request, 'Время на редактирование вышло.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    if request.method == 'POST':
        new_text = request.POST.get('text')
        if new_text and new_text != message_obj.text:
            message_obj.text = new_text
            message_obj.is_edited = True
            message_obj.save()
            messages.success(request, 'Сообщение изменено.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def toggle_like_message(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id)
    if request.user == message_obj.author:
        messages.error(request, 'Нельзя лайкать себя.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    like, created = MessageLike.objects.get_or_create(user=request.user, message=message_obj)
    if created:
        message_obj.author.reputation += 1
        messages.success(request, 'Лайк поставлен.')
    else:
        like.delete()
        message_obj.author.reputation -= 1
        messages.info(request, 'Лайк убран.')
    message_obj.author.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def delete_message_view(request, message_id):
    if request.method == 'POST':
        message_obj = get_object_or_404(Message, id=message_id)
        if request.user == message_obj.author or is_moderator(request.user):
            message_obj.delete()
            messages.success(request, 'Сообщение удалено.')
        else:
            return HttpResponseForbidden("Нет прав.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

# --- ЛИЧНЫЕ СООБЩЕНИЯ (Диалоги) ---
@login_required
def messages_view(request, dialog_id=None):
    user_dialogs = request.user.dialogs.annotate(last_msg_date=Max('messages__created_at')).order_by('-last_msg_date')
    dialog_list = []
    for d in user_dialogs:
        other_user = d.participants.exclude(id=request.user.id).first()
        if other_user:
            dialog_list.append({'id': d.id, 'other_user': other_user, 'last_message': d.messages.last()})
    
    active_dialog = None
    msgs = []
    if dialog_id:
        active_dialog_obj = get_object_or_404(Dialog, id=dialog_id)
        if request.user in active_dialog_obj.participants.all():
            active_dialog = {'id': active_dialog_obj.id, 'other_user': active_dialog_obj.participants.exclude(id=request.user.id).first()}
            msgs = active_dialog_obj.messages.all()
    
    all_users = User.objects.exclude(id=request.user.id)
    return render(request, 'forum/messages.html', {'dialogs': dialog_list, 'active_dialog': active_dialog, 'messages': msgs, 'all_users': all_users})

@login_required
def start_chat(request, username):
    other_user = get_object_or_404(User, username=username)
    dialog = Dialog.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not dialog:
        dialog = Dialog.objects.create()
        dialog.participants.add(request.user, other_user)
    return redirect('messages_with_id', dialog_id=dialog.id)

@login_required
def send_private_message(request, dialog_id):
    if request.method == 'POST':
        dialog = get_object_or_404(Dialog, id=dialog_id)
        text = request.POST.get('content')
        if text and request.user in dialog.participants.all():
            PrivateMessage.objects.create(dialog=dialog, sender=request.user, text=text)
    return redirect('messages_with_id', dialog_id=dialog_id)

# --- УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ И НОВОСТЯМИ ---
@user_passes_test(is_admin)
def add_news(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        if content: NewsItem.objects.create(content=content)
    return redirect('admin_panel')

@user_passes_test(is_admin)
def delete_news(request, news_id):
    if request.method == 'POST':
        get_object_or_404(NewsItem, id=news_id).delete()
    return redirect('admin_panel')

@user_passes_test(is_admin)
def set_user_role(request, user_id, role):
    target_user = get_object_or_404(User, id=user_id)
    if role in ['user', 'mod', 'admin']:
        target_user.role = role
        target_user.is_staff = (role in ['mod', 'admin'])
        target_user.save()
        messages.success(request, f'Роль {target_user.username} изменена.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin-panel/'))

@user_passes_test(is_admin)
def delete_user_view(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        if not target_user.is_superuser:
            target_user.delete()
            messages.success(request, 'Пользователь удален.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin-panel/'))

def team_view(request): return render(request, 'forum/team.html')
def rules_view(request): return render(request, 'forum/rules.html')

def global_search_view(request):
    query = request.GET.get('q', '')
    topics = Topic.objects.filter(title__icontains=query) if query else Topic.objects.none()
    msgs_found = Message.objects.filter(text__icontains=query) if query else Message.objects.none()
    return render(request, 'forum/search_results.html', {'topics': topics, 'messages_found': msgs_found, 'query': query})

# Добавь эту функцию в forum/views.py
@user_passes_test(is_moderator)
def mark_as_helpful(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id)
    if not message_obj.is_helpful:
        message_obj.is_helpful = True
        message_obj.save()
        # По логике RewardAction из лабы: полезный ответ = 15 баллов
        reward_strategy(message_obj.author, 'helpful')
        messages.success(request, 'Сообщение отмечено как полезное. Автор получил +15 к репутации.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

# toggle_like_message, чтобы она давала 5 баллов (как в RewardAction лабы)
@login_required
def toggle_like_message(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id)
    if request.user == message_obj.author:
        messages.error(request, 'Нельзя лайкать себя.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    
    like, created = MessageLike.objects.get_or_create(user=request.user, message=message_obj)
    if created:
        message_obj.author.reputation += 5 # Соответствует RewardAction из твоей лабы
        messages.success(request, 'Лайк поставлен! (+5 к репутации автора)')
    else:
        like.delete()
        message_obj.author.reputation -= 5
        messages.info(request, 'Лайк убран.')
    
    message_obj.author.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

# Добавь это в forum/views.py

@login_required
def report_message(request, message_id):
    """Отправка жалобы на сообщение"""
    if request.method == 'POST':
        msg = get_object_or_404(Message, id=message_id)
        
        # Получаем причину из скрытого поля формы в шаблоне
        reason_text = request.POST.get('reason', 'Жалоба на контент')
        
        # ИСПРАВЛЕНО: используем sender вместо user
        Complaint.objects.create(
            message=msg, 
            sender=request.user, 
            reason=reason_text
        )
        
        messages.warning(request, 'Жалоба отправлена модераторам.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@user_passes_test(is_moderator)
def delete_topic_view(request, topic_id):
    """Позволяет модератору или админу удалить тему целиком"""
    topic = get_object_or_404(Topic, id=topic_id)
    category_id = topic.category.id
    
    if request.method == 'POST':
        topic_title = topic.title
        topic.delete()
        messages.success(request, f'Тема "{topic_title}" успешно удалена.')
        # После удаления темы возвращаем пользователя в категорию, где она была
        return redirect('category_detail', category_id=category_id)
        
    return HttpResponseForbidden("Метод не поддерживается")

@user_passes_test(is_moderator)
def resolve_complaint(request, complaint_id, action):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if action == 'delete':
        complaint.message.delete() 
        messages.success(request, 'Сообщение удалено (без штрафа).')
        
    elif action == 'reject':
        complaint.status = 'rejected'
        complaint.save()
        messages.info(request, 'Жалоба отклонена.')
        
    elif action == 'penalize':
        # Получаем тип штрафа из выпадающего списка
        penalty_type = request.POST.get('penalty_type')
        points_to_deduct = 0
        
        # Сверяем со стратегией наказаний
        if penalty_type == 'flood':
            points_to_deduct = 10
        elif penalty_type == 'insult':
            points_to_deduct = 15
        elif penalty_type == 'spam':
            points_to_deduct = 50

        if points_to_deduct > 0:
            author = complaint.message.author
            author.reputation -= points_to_deduct
            author.save()
            complaint.message.delete() # Каскадно удалит и саму жалобу
            messages.success(request, f'Нарушитель оштрафован на {points_to_deduct} очков. Сообщение удалено.')

    return redirect('dashboard')

@login_required
def delete_dialog(request, dialog_id):
    dialog = get_object_or_404(Dialog, id=dialog_id)
    # Проверяем, что юзер действительно состоит в этом диалоге
    if request.user in dialog.participants.all():
        dialog.delete()
        messages.success(request, 'Диалог удален.')
    return redirect('messages')

@login_required
def my_topics_view(request):
    topics = Topic.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'forum/my_topics.html', {'topics': topics})