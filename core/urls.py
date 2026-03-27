from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView
from users.views import register_view, login_view, profile_view, toggle_block_user
from forum.views import edit_message_view, toggle_like_message, global_search_view, delete_message_view, add_news, delete_news

# Группируем импорты из приложения forum
from forum.views import (
    edit_message_view,
    home_view, 
    catalog_view, 
    category_detail_view, 
    create_topic_view, 
    topic_view,
    dashboard_view,
    admin_panel_view, 
    add_category, 
    delete_category,
    team_view, 
    rules_view
)

# Группируем импорты из приложения users
from users.views import register_view, login_view, profile_view

urlpatterns = [
    # 1. Служебные пути
    path('admin/', admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),

    # 2. Главная страница
    path('', home_view, name='home'),

    # 3. Форум и модерация
    path('catalog/', catalog_view, name='catalog'),
    path('category/<int:category_id>/', category_detail_view, name='category_detail'),
    path('topic/create/', create_topic_view, name='create_topic'), 
    path('topic/<int:topic_id>/', topic_view, name='topic'),
    path('dashboard/', dashboard_view, name='dashboard'),
    # Пока остается статичным HTML
    path('messages/', TemplateView.as_view(template_name='forum/messages.html'), name='messages'), 

    # 4. Внутренняя Админ-панель на сайте
    path('admin-panel/', admin_panel_view, name='admin_panel'),
    path('admin-panel/category/add/', add_category, name='add_category'),
    path('admin-panel/category/<int:category_id>/delete/', delete_category, name='delete_category'),

    # 5. Профили и авторизация
    path('profile/', profile_view, name='profile'),
    path('profile/block/<int:user_id>/', toggle_block_user, name='toggle_block_user'), 
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),

    path('team/', team_view, name='team'),
    path('rules/', rules_view, name='rules'),

    path('message/<int:message_id>/edit/', edit_message_view, name='edit_message'),
    path('message/<int:message_id>/like/', toggle_like_message, name='toggle_like'),
    path('search/', global_search_view, name='global_search'),

    path('message/<int:message_id>/delete/', delete_message_view, name='delete_message'),

    path('admin-panel/news/add/', add_news, name='add_news'),
    path('admin-panel/news/<int:news_id>/delete/', delete_news, name='delete_news'),
]