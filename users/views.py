from urllib import request

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .models import User
from django.contrib.auth.decorators import login_required
from forum.models import Topic, Message as ForumMessage

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
        login(request, user)
        return redirect('home')
        
    return render(request, 'users/register.html')

def login_view(request):
    # Если юзер уже авторизован, отправляем его на главную
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # authenticate проверяет, есть ли такой юзер в БД с таким паролем
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль')
            return redirect('login')
            
    return render(request, 'users/login.html')

@login_required
def profile_view(request):
    # Считаем реальное количество созданных тем и сообщений пользователя
    user_topics_count = Topic.objects.filter(author=request.user).count()
    user_replies_count = ForumMessage.objects.filter(author=request.user).count()
    
    return render(request, 'users/profile.html', {
        'user_topics_count': user_topics_count,
        'user_replies_count': user_replies_count
    })