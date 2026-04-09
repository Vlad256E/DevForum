from urllib import request

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .models import User
from django.contrib.auth.decorators import login_required
from forum.models import Topic, Message as ForumMessage
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth import update_session_auth_hash

def register_view(request):
    # Если юзер уже авторизован, отправляем его на главную
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        # Получаем данные из атрибутов name="..." твоей HTML-формы
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Простые проверки
        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают!')
            return redirect('register')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким логином уже существует!')
            return redirect('register')
            
        # Создаем пользователя (используем create_user, чтобы пароль захешировался)
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Сразу авторизуем его после успешной регистрации
        login(request, user, backend='users.backends.EmailOrUsernameModelBackend')
        return redirect('home')
        
    return render(request, 'users/register.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember') # Получаем значение чекбокса 'Запомнить меня'
        
        # authenticate теперь будет использовать наш кастомный EmailOrUsernameModelBackend
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Логика "Запомнить меня"
            if remember:
                # Сессия живет 30 дней (в секундах)
                request.session.set_expiry(2592000) 
            else:
                # Сессия очистится при закрытии браузера
                request.session.set_expiry(0)
                
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль')
            return redirect('login')
            
    return render(request, 'users/login.html')

@login_required
def profile_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # --- 1. ОБНОВЛЕНИЕ ОСНОВНЫХ ДАННЫХ ---
        if action == 'update_profile':
            new_username = request.POST.get('username')
            new_email = request.POST.get('email')
            email_notif = request.POST.get('email_notifications') == 'on' 

            if new_username != request.user.username and User.objects.filter(username=new_username).exists():
                messages.error(request, 'Пользователь с таким логином уже существует.')
            else:
                request.user.username = new_username
                request.user.email = new_email
                request.user.email_notifications = email_notif
                request.user.save()
                messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')

        # --- 2. ОБНОВЛЕНИЕ ПАРОЛЯ ---
        elif action == 'update_password':
            new_password = request.POST.get('new_password')
            new_password_confirm = request.POST.get('new_password_confirm')
            
            if not new_password or not new_password_confirm:
                messages.error(request, 'Пароль не может быть пустым.')
            elif new_password != new_password_confirm:
                messages.error(request, 'Пароли не совпадают.')
            else:
                # Обязательно используем set_password, чтобы пароль зашифровался!
                request.user.set_password(new_password)
                request.user.save()
                # Обновляем сессию, чтобы юзера не разлогинило после смены пароля
                update_session_auth_hash(request, request.user) 
                messages.success(request, 'Пароль успешно обновлен!')
            return redirect('profile')

    # Если это GET-запрос (просто загрузка страницы)
    user_topics_count = Topic.objects.filter(author=request.user).count()
    user_replies_count = ForumMessage.objects.filter(author=request.user).count()
    
    return render(request, 'users/profile.html', {
        'user_topics_count': user_topics_count,
        'user_replies_count': user_replies_count
    })

@login_required
def toggle_block_user(request, user_id):
    user_to_block = get_object_or_404(User, id=user_id)
    
    # Нельзя заблокировать самого себя
    if user_to_block != request.user:
        if user_to_block in request.user.blocked_users.all():
            request.user.blocked_users.remove(user_to_block)
            messages.success(request, f'Пользователь {user_to_block.username} убран из черного списка.')
        else:
            request.user.blocked_users.add(user_to_block)
            messages.success(request, f'Пользователь {user_to_block.username} добавлен в черный список.')
            
    # Возвращаем пользователя на ту же страницу, откуда он нажал кнопку
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def update_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        # Удаляем старую аватарку из памяти, если нужно (опционально)
        request.user.avatar = request.FILES['avatar']
        request.user.save()
    return redirect('profile') # Укажи здесь name твоего URL личного кабинета