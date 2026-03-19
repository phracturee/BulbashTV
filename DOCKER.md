# BulbashTV - Docker запуск

## Быстрый старт

### 1. Подготовка

Убедитесь, что у вас установлены:
- Docker
- Docker Compose

### 2. Настройка

Создайте файл конфигурации:

```bash
cp config.py.example config.py
```

Отредактируйте `config.py` и укажите ваш TMDB API ключ:

```python
TMDB_API_KEY = "ваш_api_ключ"
```

### 3. Запуск через Docker Compose (рекомендуется)

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### 4. Запуск через Docker

```bash
# Сборка образа
docker build -t bulbashtv .

# Запуск контейнера
docker run -d \
  --name bulbashtv \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/cookies:/app/cookies \
  -v $(pwd)/config.py:/app/config.py:ro \
  bulbashtv

# Просмотр логов
docker logs -f bulbashtv

# Остановка
docker stop bulbashtv
docker rm bulbashtv
```

## Доступ

После запуска откройте в браузере:
```
http://localhost:5000
```

## Структура томов

| Том | Описание |
|-----|----------|
| `./data` | Базы данных (избранное, история, кэш) |
| `./logs` | Логи приложения |
| `./downloads` | Загруженные торренты |
| `./cookies` | Cookies для трекеров |
| `./static/img` | Кэшированные изображения |
| `./config.py` | Файл конфигурации |

## Управление

```bash
# Перезапуск
docker-compose restart

# Пересборка
docker-compose up -d --build

# Остановка и удаление
docker-compose down

# Полное удаление с данными
docker-compose down -v
```

## Диагностика

```bash
# Проверка состояния
docker-compose ps

# Логи
docker-compose logs -f

# Выполнение команд в контейнере
docker-compose exec bulbashtv bash

# Проверка API
curl http://localhost:5000/api/diagnostics
```

## Примечания

- **Воспроизведение видео**: Для работы streaming через webtorrent требуется, чтобы в системе был установлен mpv. В Docker контейнере mpv уже установлен.
- **Порты**: По умолчанию приложение доступно на порту 5000. Можно изменить в `docker-compose.yml`.
- **Данные**: Все данные сохраняются в томах и не теряются при пересоздании контейнера.
