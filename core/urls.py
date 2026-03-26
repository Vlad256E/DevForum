from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView
from forum.views import catalog_view, category_detail_view, create_topic_view 
from users.views import register_view, login_view, profile_view

# Импорты из приложения forum
from forum.views import (
    home_view, 
    admin_panel_view, 
    add_category, 
    delete_category, 
    dashboard_view, 
    topic_view,
    catalog_view,
    category_detail_view
)

# Импорты из приложения users
from users.views import register_view, login_view

urlpatterns = [
    # 1. Служебные пути
    path('admin/', admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),

    # 2. Главная страница
    path('', home_view, name='home'),

    # 3. Форум и модерация
    path('dashboard/', dashboard_view, name='dashboard'),
    path('topic/<int:topic_id>/', topic_view, name='topic'),
    path('messages/', TemplateView.as_view(template_name='forum/messages.html'), name='messages'), # Пока остается статичным HTML

    # 4. Внутренняя Админ-панель на сайте
    path('admin-panel/', admin_panel_view, name='admin_panel'),
    path('admin-panel/category/add/', add_category, name='add_category'),
    path('admin-panel/category/<int:category_id>/delete/', delete_category, name='delete_category'),

    # 5. Профили и авторизация
    path('profile/', profile_view, name='profile'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),

    path('catalog/', catalog_view, name='catalog'),
    path('category/<int:category_id>/', category_detail_view, name='category_detail'),

    path('topic/create/', create_topic_view, name='create_topic'), 
]