from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

# Импорты из приложения users
from users.views import (
    register_view, 
    login_view, 
    profile_view, 
    toggle_block_user, 
    update_avatar
)

# Импорты из приложения forum
from forum.views import (
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
    rules_view,
    edit_message_view, 
    toggle_like_message, 
    global_search_view, 
    delete_message_view, 
    add_news, 
    delete_news,
    messages_view, 
    start_chat, 
    send_private_message,
    set_user_role,       
    delete_user_view,
    mark_as_helpful 
)

urlpatterns = [
    # 1. Служебные пути
    path('admin/', admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),

    # 2. Главная страница
    path('', home_view, name='home'),

    # 3. Форум: Категории и Темы
    path('catalog/', catalog_view, name='catalog'),
    path('category/<int:category_id>/', category_detail_view, name='category_detail'),
    path('topic/create/', create_topic_view, name='create_topic'), 
    path('topic/<int:topic_id>/', topic_view, name='topic'),
    
    # 4. Сообщения и взаимодействие
    path('message/<int:message_id>/edit/', edit_message_view, name='edit_message'),
    path('message/<int:message_id>/like/', toggle_like_message, name='toggle_like'),
    path('message/<int:message_id>/delete/', delete_message_view, name='delete_message'),
    path('message/helpful/<int:message_id>/', mark_as_helpful, name='mark_helpful'), 
    path('search/', global_search_view, name='global_search'),

    # 5. Личные сообщения (Диалоги)
    path('messages/', messages_view, name='messages'),
    path('messages/<int:dialog_id>/', messages_view, name='messages_with_id'),
    path('messages/start/<str:username>/', start_chat, name='start_chat'),
    path('messages/send/<int:dialog_id>/', send_private_message, name='send_message'),

    # 6. Профили и авторизация
    path('profile/', profile_view, name='profile'),
    path('profile/update-avatar/', update_avatar, name='update_avatar'),
    path('profile/block/<int:user_id>/', toggle_block_user, name='toggle_block_user'), 
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),

    # 7. Модерация и Админ-панель сайта
    path('dashboard/', dashboard_view, name='dashboard'),
    path('admin-panel/', admin_panel_view, name='admin_panel'),
    path('admin-panel/category/add/', add_category, name='add_category'),
    path('admin-panel/category/<int:category_id>/delete/', delete_category, name='delete_category'),
    path('admin-panel/news/add/', add_news, name='add_news'),
    path('admin-panel/news/<int:news_id>/delete/', delete_news, name='delete_news'),
    path('admin-panel/user/<int:user_id>/set-role/<str:role>/', set_user_role, name='set_role'),
    path('admin-panel/user/<int:user_id>/delete/', delete_user_view, name='delete_user'),

    # 8. Статические страницы
    path('team/', team_view, name='team'),
    path('rules/', rules_view, name='rules'),
    path('message/helpful/<int:message_id>/', mark_as_helpful, name='mark_helpful'),
    path('message/like/<int:message_id>/', toggle_like_message, name='toggle_like'),
]

# Подключение медиа-файлов (аватарок) в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)