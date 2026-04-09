from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from .models import Category, Topic, Message, Complaint, MessageLike, NewsItem, PrivateMessage, Dialog, AuditLog
from users.models import User 
from datetime import timedelta
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Max
from django.contrib.contenttypes.models import ContentType
import json
from django.core import serializers
from django.core.paginator import Paginator

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

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ЛОГИРОВАНИЕ) ---
def log_action(moderator, obj, action_type):
    """Сериализует объект в JSON и сохраняет в лог для возможности отката"""
    data = serializers.serialize('json', [obj])
    AuditLog.objects.create(
        moderator=moderator,
        action_type=action_type,
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.id,
        action_details=data
    )

# --- ГЛАВНАЯ СТРАНИЦА ---
def home_view(request):
    categories = Category.objects.annotate(topic_count=Count('topics')).order_by('-topic_count')
    recent_topics = Topic.objects.order_by('-created_at')[:5]
    news_items = NewsItem.objects.all()[:5] 
    return render(request, 'forum/index.html', {
        'categories': categories,
        'recent_topics': recent_topics,
        'news_items': news_items
    })

# --- АДМИН ПАНЕЛЬ И ОТКАТ ---
@user_passes_test(is_admin)
def admin_panel_view(request):
    categories = Category.objects.all()
    users = User.objects.all().order_by('-date_joined')
    total_topics_count = Topic.objects.count()
    one_week_ago = timezone.now() - timezone.timedelta(days=7)
    new_users_count = User.objects.filter(date_joined__gte=one_week_ago).count()
    news_items = NewsItem.objects.all()
    logs = AuditLog.objects.all()[:20] 
    
    context = {
        'categories': categories,
        'users': users,
        'total_topics_count': total_topics_count,
        'new_users_count': new_users_count,
        'news_items': news_items,
        'logs': logs,
    }
    return render(request, 'forum/admin_panel.html', context)

@user_passes_test(is_admin)
def rollback_action(request, log_id):
    """Восстановление удаленного объекта из данных лога"""
    log_entry = get_object_or_404(AuditLog, id=log_id)
    if log_entry.action_type == 'delete' and log_entry.action_details:
        for obj in serializers.deserialize("json", log_entry.action_details):
            obj.save()
        log_entry.delete() 
        messages.success(request, 'Объект успешно восстановлен.')
    else:
        messages.error(request, 'Этот тип действия нельзя откатить.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin-panel/'))

# --- УПРАВЛЕНИЕ КАТЕГОРИЯМИ ---
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
        log_action(request.user, category, 'delete') # Логируем
        category.delete()
        messages.success(request, 'Категория удалена.')
    return redirect('admin_panel')

# --- УПРАВЛЕНИЕ НОВОСТЯМИ ---
@user_passes_test(is_admin)
def add_news(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            NewsItem.objects.create(content=content)
            messages.success(request, 'Новость добавлена.')
    return redirect('admin_panel')

@user_passes_test(is_admin)
def delete_news(request, news_id):
    if request.method == 'POST':
        get_object_or_404(NewsItem, id=news_id).delete()
        messages.success(request, 'Новость удалена.')
    return redirect('admin_panel')

# --- УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ---
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
            log_action(request.user, target_user, 'ban') # Логируем
            target_user.delete()
            messages.success(request, 'Пользователь удален.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin-panel/'))

# --- МОДЕРАЦИЯ И ЖАЛОБЫ ---
@user_passes_test(is_moderator)
def delete_topic_view(request, topic_id):
    """Удаление темы с логированием"""
    topic = get_object_or_404(Topic, id=topic_id)
    category_id = topic.category.id
    if request.method == 'POST':
        log_action(request.user, topic, 'delete') 
        topic.delete()
        messages.success(request, 'Тема удалена и занесена в лог.')
        return redirect('category_detail', category_id=category_id)
    return HttpResponseForbidden()

@user_passes_test(is_moderator)
def mark_as_helpful(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id)
    if not message_obj.is_helpful:
        log_action(request.user, message_obj, 'helpful')
        message_obj.is_helpful = True
        message_obj.save()
        reward_strategy(message_obj.author, 'helpful')
        messages.success(request, 'Сообщение отмечено как полезное.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@user_passes_test(is_moderator)
def dashboard_view(request):
    complaints = Complaint.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'forum/dashboard.html', {'complaints': complaints})

@user_passes_test(is_moderator)
def resolve_complaint(request, complaint_id, action):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if action == 'delete':
        log_action(request.user, complaint.message, 'delete') # Логируем
        complaint.message.delete() 
        complaint.status = 'resolved' # Закрываем жалобу
        complaint.save()
        messages.success(request, 'Сообщение удалено.')
    elif action == 'reject':
        complaint.status = 'rejected'
        complaint.save()
    elif action == 'penalize':
        penalty_type = request.POST.get('penalty_type')
        points = {'flood': 10, 'insult': 15, 'spam': 50}.get(penalty_type, 0)
        if points > 0:
            author = complaint.message.author
            author.reputation -= points
            author.save()
            log_action(request.user, complaint.message, 'delete') # Логируем
            complaint.message.delete()
            complaint.status = 'resolved'
            complaint.save()
            messages.success(request, f'Нарушитель оштрафован на {points} очков.')
    return redirect('dashboard')

@login_required
def report_message(request, message_id):
    if request.method == 'POST':
        msg = get_object_or_404(Message, id=message_id)
        reason_text = request.POST.get('reason', 'Жалоба на контент')
        Complaint.objects.create(message=msg, sender=request.user, reason=reason_text)
        messages.warning(request, 'Жалоба отправлена модераторам.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

# --- ТЕМЫ И СООБЩЕНИЯ ---
def topic_view(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    if request.method == 'POST' and request.user.is_authenticated:
        text = request.POST.get('text')
        if text:
            Message.objects.create(topic=topic, author=request.user, text=text)
            return redirect('topic', topic_id=topic.id)
    messages_list = topic.messages.all().order_by('posted_at').prefetch_related('likes')
    return render(request, 'forum/topic.html', {'topic': topic, 'forum_messages': messages_list})

@login_required
def toggle_like_message(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id)
    if request.user == message_obj.author:
        messages.error(request, 'Нельзя лайкать себя.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    like, created = MessageLike.objects.get_or_create(user=request.user, message=message_obj)
    if created:
        message_obj.author.reputation += 5 
        messages.success(request, 'Лайк поставлен! (+5 к репутации)')
    else:
        like.delete()
        message_obj.author.reputation -= 5
    message_obj.author.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def delete_message_view(request, message_id):
    if request.method == 'POST':
        message_obj = get_object_or_404(Message, id=message_id)
        # Если удаляет автор или модератор
        if request.user == message_obj.author or is_moderator(request.user):
            # Логируем действие, если удаляет модератор (и это не его личное сообщение)
            if is_moderator(request.user) and request.user != message_obj.author:
                log_action(request.user, message_obj, 'delete')
                
            message_obj.delete()
            messages.success(request, 'Сообщение удалено.')
        else:
            return HttpResponseForbidden("Нет прав.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def edit_message_view(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id)
    if request.user != message_obj.author:
        return HttpResponseForbidden("Вы не можете редактировать чужое сообщение.")
    if timezone.now() - message_obj.posted_at > timedelta(minutes=30):
        messages.error(request, 'Время на редактирование (30 мин) вышло.')
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
            if topic.author != request.user:
                Notification.objects.create(
                    user=topic.author,
                    text=f"Пользователь {request.user.username} ответил в вашей теме «{topic.title}»",
                    link=f"/topic/{topic.id}/"
                )
            return redirect('topic', topic_id=topic.id)
    return render(request, 'forum/create_topic.html', {'categories': categories})

# --- ЛИЧНЫЕ СООБЩЕНИЯ ---
@login_required
def messages_view(request, dialog_id=None):
    user_dialogs = request.user.dialogs.annotate(last_msg_date=Max('messages__created_at')).order_by('-last_msg_date')
    dialog_list = []
    for d in user_dialogs:
        other_user = d.participants.exclude(id=request.user.id).first()
        if other_user:
            dialog_list.append({'id': d.id, 'other_user': other_user, 'last_message': d.messages.last()})
    
    active_dialog, msgs = None, []
    if dialog_id:
        active_dialog_obj = get_object_or_404(Dialog, id=dialog_id)
        if request.user in active_dialog_obj.participants.all():
            active_dialog = {'id': active_dialog_obj.id, 'other_user': active_dialog_obj.participants.exclude(id=request.user.id).first()}
            msgs = active_dialog_obj.messages.all()

    all_users = User.objects.exclude(id=request.user.id).order_by('username')[:50]

    return render(request, 'forum/messages.html', {
        'dialogs': dialog_list,
        'active_dialog': active_dialog,
        'chat_messages': msgs,  # <--- ПЕРЕИМЕНОВАЛИ ПЕРЕМЕННУЮ ЗДЕСЬ!
        'all_users': all_users,
    })
    
    active_dialog, msgs = None, []
    if dialog_id:
        active_dialog_obj = get_object_or_404(Dialog, id=dialog_id)
        if request.user in active_dialog_obj.participants.all():
            active_dialog = {'id': active_dialog_obj.id, 'other_user': active_dialog_obj.participants.exclude(id=request.user.id).first()}
            msgs = active_dialog_obj.messages.all()

    # Получаем пользователей (исключая самого себя)
    # Ограничиваем список до 50 человек, чтобы спасти браузер от зависания
    all_users = User.objects.exclude(id=request.user.id).order_by('username')[:50]

    return render(request, 'forum/messages.html', {
        'dialogs': dialog_list,
        'active_dialog': active_dialog,
        'messages': msgs,
        'all_users': all_users, # Передаем переменную в шаблон!
    })
    
    active_dialog, msgs = None, []
    if dialog_id:
        active_dialog_obj = get_object_or_404(Dialog, id=dialog_id)
        if request.user in active_dialog_obj.participants.all():
            active_dialog = {'id': active_dialog_obj.id, 'other_user': active_dialog_obj.participants.exclude(id=request.user.id).first()}
            msgs = active_dialog_obj.messages.all()
    return render(request, 'forum/messages.html', {'dialogs': dialog_list, 'active_dialog': active_dialog, 'messages': msgs})

@login_required
def start_chat(request, username):
    other_user = get_object_or_404(User, username=username)
    
    # 1. Проверяем, не кинул ли собеседник нас в ЧС
    if request.user in other_user.blocked_users.all():
        messages.error(request, 'Этот пользователь ограничил круг лиц, которые могут присылать ему сообщения.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/messages/'))
        
    # 2. Проверяем, не кинули ли мы собеседника в ЧС
    if other_user in request.user.blocked_users.all():
        messages.error(request, 'Сначала уберите этого пользователя из чёрного списка.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/messages/'))

    # Если всё чисто, продолжаем создание диалога
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
            # Находим второго участника диалога
            other_user = dialog.participants.exclude(id=request.user.id).first()
            
            # Блокируем отправку, если кто-то из двоих находится в ЧС
            if other_user and request.user in other_user.blocked_users.all():
                messages.error(request, 'Невозможно отправить: вы находитесь в чёрном списке этого пользователя.')
            elif other_user and other_user in request.user.blocked_users.all():
                messages.error(request, 'Невозможно отправить: пользователь находится в вашем чёрном списке.')
            else:
                # Если никто никого не заблокировал — сохраняем сообщение
                PrivateMessage.objects.create(dialog=dialog, sender=request.user, text=text)
                
    return redirect('messages_with_id', dialog_id=dialog_id)    

@login_required
def delete_dialog(request, dialog_id):
    dialog = get_object_or_404(Dialog, id=dialog_id)
    if request.user in dialog.participants.all():
        dialog.delete()
        messages.success(request, 'Диалог удален.')
    return redirect('messages')

# --- КАТАЛОГ И ПОИСК ---
def catalog_view(request):
    # Получаем параметр сортировки (по умолчанию 'new')
    sort = request.GET.get('sort', 'new')
    
    # Аннотируем категории количеством тем
    categories = Category.objects.annotate(topic_count=Count('topics'))
    
    # Применяем сортировку
    if sort == 'popular':
        categories = categories.order_by('-topic_count')
    else:
        categories = categories.order_by('-id')
        
    return render(request, 'forum/catalog.html', {'categories': categories})

def category_detail_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    sort = request.GET.get('sort', 'new')
    
    # Базовый запрос
    topics_list = Topic.objects.filter(category=category)
    
    # Применяем логику сортировки
    if sort == 'popular':
        # Считаем сообщения и сортируем по их количеству (популярные сверху)
        topics_list = topics_list.annotate(messages_count=Count('messages')).order_by('-messages_count', '-created_at')
    else:
        # По умолчанию - по дате создания
        topics_list = topics_list.order_by('-created_at')
    
    # Разбиваем по 15 тем на страницу
    paginator = Paginator(topics_list, 15)
    page_number = request.GET.get('page')
    topics = paginator.get_page(page_number)
    
    return render(request, 'forum/category_detail.html', {'category': category, 'topics': topics})

def global_search_view(request):
    query = request.GET.get('q', '')
    topics = Topic.objects.filter(title__icontains=query) if query else Topic.objects.none()
    msgs_found = Message.objects.filter(text__icontains=query) if query else Message.objects.none()
    return render(request, 'forum/search_results.html', {'topics': topics, 'messages_found': msgs_found, 'query': query})

@login_required
def my_topics_view(request):
    topics = Topic.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'forum/my_topics.html', {'topics': topics})

def team_view(request): return render(request, 'forum/team.html')
def rules_view(request): return render(request, 'forum/rules.html')

@login_required
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))