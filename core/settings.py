import os  # Добавь этот импорт в самое начало
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- 1. СЕКРЕТЫ ИЗ ОКРУЖЕНИЯ ---
# Мы не храним ключи прямо в коде. Docker будет передавать их из файла .env
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# В Docker ALLOWED_HOSTS должен включать 'localhost' и имя сервиса
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost 127.0.0.1 web').split()

# --- 2. ПРИЛОЖЕНИЯ ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Твои инструменты
    'tailwind',
    'theme',  # Твоя папка с Tailwind
    'django_browser_reload', # Для автообновления страницы при разработке
    
    # Будущие приложения форума (когда создашь их в папке apps)
    'forum',
    'users',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_browser_reload.middleware.BrowserReloadMiddleware', # Добавь это
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# --- 3. ПЕРЕЕЗД НА POSTGRESQL ---
# Теперь Django будет искать базу данных внутри Docker-контейнера 'db'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'postgres'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'db'), # 'db' - это имя сервиса в docker-compose
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# --- 4. НАСТРОЙКИ TAILWIND ---
TAILWIND_APP_NAME = 'theme'
INTERNAL_IPS = ["127.0.0.1"]
# Важно для Docker: указываем, где лежит npm
NPM_BIN_PATH = '/usr/bin/npm' 

# Остальные настройки (Static, Media, Auth)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

# --- 5. АВТОРИЗАЦИЯ ---
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

TIME_ZONE = 'Europe/Tallinn' 
USE_TZ = True