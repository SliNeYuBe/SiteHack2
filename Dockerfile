# Используем официальный Python образ
FROM python:3.10-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем все файлы проекта
COPY . /app

# Переход в нужную директорию, где находится app.py
WORKDIR /app/YoutubeMessenger-master

# Установка зависимостей
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Команда запуска
CMD ["python", "app.py"]
