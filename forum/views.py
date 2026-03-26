from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from .models import Category, Topic, Message, Complaint
from users.models import User # Импортируем модель пользователя

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
    # Получаем все темы этой категории, сортируем от новых к старым
    topics = category.topics.all().order_by('-created_at') 
    return render(request, 'forum/category_detail.html', {'category': category, 'topics': topics})