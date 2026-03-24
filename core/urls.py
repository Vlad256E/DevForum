from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView  

urlpatterns = [
    # Админка Django
    path('admin/', admin.site.urls),
    
    # Форум (папка forum)
    path('', TemplateView.as_view(template_name='forum/index.html'), name='home'),
    path('dashboard/', TemplateView.as_view(template_name='forum/dashboard.html'), name='dashboard'),
    path('messages/', TemplateView.as_view(template_name='forum/messages.html'), name='messages'),
    path('topic/', TemplateView.as_view(template_name='forum/topic.html'), name='topic'),
    path('admin-panel/', TemplateView.as_view(template_name='forum/admin_panel.html'), name='admin_panel'),

    # Пользователи (папка users)
    path('profile/', TemplateView.as_view(template_name='users/profile.html'), name='profile'),
    path('login/', TemplateView.as_view(template_name='users/login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='users/register.html'), name='register'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
]