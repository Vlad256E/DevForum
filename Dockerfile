# Используем легкий образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости для Postgres и Node.js (для Tailwind)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    gnupg \
    && curl -sL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Открываем порт
EXPOSE 8000

# Команда для запуска (её мы переопределим в compose для разработки)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]