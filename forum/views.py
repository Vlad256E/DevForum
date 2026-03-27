from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from .models import Category, Topic, Message, Complaint, MessageLike
from users.models import User 
from datetime import timedelta
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

def is_moderator(user):
    return user.is_authenticated and (user.is_superuser or user.role in ['admin', 'mod'])

def home_view(request):
    categories = Category.objects.all()
    recent_topics = Topic.objects.order_by('-created_at')[:5] # 5 последних тем
    return render(request, 'forum/index.html', {
        'categories': categories,
        'recent_topics': recent_topics
    })

# --- АДМИН ПАНЕЛЬ (со статистикой) ---
@user_passes_test(is_admin)
def admin_panel_view(request):
    categories = Category.objects.all()
    users = User.objects.all().order_by('-date_joined')
    
    # Статистика
    total_topics_count = Topic.objects.count()
    one_week_ago = timezone.now() - timezone.timedelta(days=7)
    new_users_count = User.objects.filter(date_joined__gte=one_week_ago).count()

    context = {
        'categories': categories,
        'users': users,
        'total_topics_count': total_topics_count,
        'new_users_count': new_users_count,
    }
    return render(request, 'forum/admin_panel.html', context)

@user_passes_test(is_admin)
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        if name:
            Category.objects.create(name=name, description=description)
    return redirect('admin_panel')

@user_passes_test(is_admin)
def delete_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        category.delete()
    return redirect('admin_panel')

# --- ДАШБОРД МОДЕРАТОРА (Жалобы) ---
@user_passes_test(is_moderator)
def dashboard_view(request):
    # Получаем только нерешенные жалобы
    complaints = Complaint.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'forum/dashboard.html', {'complaints': complaints})

# --- ПРОСМОТР ТЕМЫ ---
def topic_view(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    
    # Обрабатываем отправку нового сообщения
    if request.method == 'POST' and request.user.is_authenticated:
        text = request.POST.get('text')
        if text:
            Message.objects.create(topic=topic, author=request.user, text=text)
            return redirect('topic', topic_id=topic.id) # Перезагружаем страницу, чтобы увидеть ответ

    messages = topic.messages.all().order_by('posted_at')
    return render(request, 'forum/topic.html', {'topic': topic, 'forum_messages': messages})

# --- Создание темы ---
def create_topic_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
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

# --- КАТАЛОГ И КАТЕГОРИИ ---
def catalog_view(request):
    categories = Category.objects.all()
    return render(request, 'forum/catalog.html', {'categories': categories})

def category_detail_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    topics = Topic.objects.filter(category=category)

    # Логика сортировки
    sort = request.GET.get('sort', 'new')
    if sort == 'popular':
        # Сортируем по количеству сообщений (от большего к меньшему)
        topics = topics.annotate(msg_count=Count('messages')).order_by('-msg_count')
    else:
        # По умолчанию: новые темы (замени created_at на свое поле даты создания темы)
        topics = topics.order_by('-created_at') 

    return render(request, 'forum/category_detail.html', {'category': category, 'topics': topics})

def team_view(request):
    return render(request, 'forum/team.html')

def rules_view(request):
    return render(request, 'forum/rules.html')

@login_required
def edit_message_view(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id)

    # Проверка: автор ли это?
    if request.user != message_obj.author:
        return HttpResponseForbidden("Вы не можете редактировать чужое сообщение.")

    # Проверка: прошло ли меньше 30 минут? 
    # (замени posted_at на свое название поля даты создания, если оно другое)
    time_diff = timezone.now() - message_obj.posted_at 
    
    if time_diff > timedelta(minutes=30):
        messages.error(request, 'Время на редактирование вышло (прошло более 30 минут).')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    if request.method == 'POST':
        new_text = request.POST.get('text')
        if new_text and new_text != message_obj.text:
            message_obj.text = new_text
            message_obj.is_edited = True
            message_obj.save()
            messages.success(request, 'Сообщение успешно изменено.')
            
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def toggle_like_message(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id)

    # Защита от накрутки: нельзя лайкать себя
    if request.user == message_obj.author:
        messages.error(request, 'Вы не можете ставить лайк собственному сообщению.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    # get_or_create попытается найти лайк. Если его нет — создаст (created будет True)
    like, created = MessageLike.objects.get_or_create(user=request.user, message=message_obj)

    if created:
        message_obj.author.reputation += 1
        message_obj.author.save()
        messages.success(request, 'Вам понравилось это сообщение.')
    else:
        like.delete()
        message_obj.author.reputation -= 1
        message_obj.author.save()
        messages.info(request, 'Лайк убран.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def global_search_view(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        # Ищем топики: совпадение в названии темы ИЛИ в тексте любого из её сообщений
        # distinct() убирает дубликаты, если совпадение нашлось в нескольких сообщениях одной темы
        results = Topic.objects.filter(
            Q(title__icontains=query) | Q(messages__text__icontains=query)
        ).distinct()

    return render(request, 'forum/search_results.html', {'query': query, 'results': results})