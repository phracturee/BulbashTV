# BulbashTV

**BulbashTV** — веб-приложение для поиска и просмотра фильмов и сериалов с интеграцией торрент-трекеров. Использует TMDB API для метаданных и выполняет поиск на нескольких торрент-трекерах.

**Языки:** [English](README.md) | [Русский](README.ru.md)

## Содержание

- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Установка](#установка)
- [Настройка](#настройка)
- [Использование](#использование)
- [API Endpoints](#api-endpoints)
- [Структура проекта](#структура-проекта)
- [Требования](#требования)
- [Кэширование](#кэширование)
- [Диагностика](#диагностика)
- [Troubleshooting](#troubleshooting)
- [Вклад в проект](#вклад-в-проект)

---

## Возможности

- **Каталог фильмов и сериалов** — интеграция с TMDB с поддержкой русского языка
- **Страница сезонов и серий** — удобный выбор серий с описаниями, рейтингами и датами выхода
- **Поиск торрентов** — интеграция с несколькими трекерами:
  - **RuTracker** — прямая интеграция, до 500 результатов (требуются cookies, до 10 страниц)
  - **Rutor** — не требует авторизации, до 125 результатов (5 страниц)
  - **LostFilm** — HD фильмы и сериалы с озвучкой (автоматическая загрузка torrent)
- **Воспроизведение сериалов** — умный поиск по сезону с фильтрацией по маске SXXEYY
- **Пагинация результатов** — постепенная загрузка торрентов (30 результатов на страницу с кнопкой "Загрузить ещё")
- **Избранное** — организация контента по папкам
- **История просмотров** — отслеживание просмотренных фильмов и серий
- **История поиска** — сохранение поисковых запросов
- **Стриминг торрентов** — воспроизведение через server.js + mpv
- **Кэширование изображений** — локальное кэширование постеров
- **Приоритизация торрентов** — запоминание выбранных раздач
- **Чистый интерфейс** — современный дизайн с закруглёнными элементами и фоновыми изображениями

---

## Архитектура

Приложение следует принципу **разделения ответственности** с использованием ООП:

```
BulbashTVApp (Flask application factory)
├── TMDBClient (TMDB API communication)
├── FavoritesManager (Persistent favorites storage)
├── HistoryManager (Search/watch history)
├── MediaFormatter + ImageCache (Data formatting, image caching)
└── TorrentManager (Search, caching, streaming)
    └── TorrentSearcher (Multi-tracker search)
```

### Основные классы

| Класс | Файл | Описание |
|-------|------|----------|
| `BulbashTVApp` | `app.py` | Фабрика Flask приложения, регистрация маршрутов |
| `TMDBClient` | `services/tmdb_client.py` | TMDB API клиент с retry логикой |
| `TorrentManager` | `services/torrent_manager.py` | Поиск торрентов, кэш, стриминг |
| `TorrentSearcher` | `torrent_search.py` | Реализация поиска по нескольким трекерам |
| `FavoritesManager` | `services/data_manager.py` | Управление папками избранного |
| `MediaFormatter` | `services/media_formatter.py` | Форматирование данных TMDB для шаблонов |

---

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/phracturee/BulbashTV.git
cd BulbashTV
```

### 2. Установка Python зависимостей

```bash
pip install -r requirements.txt
```

### 3. Установка Node.js зависимостей

```bash
npm install
```

Это установит `webtorrent` и `webtorrent-cli` необходимые для стриминга.

### 4. Установка mpv (для воспроизведения)

```bash
# Ubuntu/Debian
sudo apt install mpv

# macOS
brew install mpv

# Windows
# Скачайте с https://mpv.io/installation/
```

### 5. Настройка конфигурации

```bash
cp config.py.example config.py
```

Отредактируйте `config.py` и добавьте ваш TMDB API ключ.

---

## Настройка

```python
# TMDB API Configuration
# Получите ваш API ключ на: https://www.themoviedb.org/settings/api
TMDB_API_KEY = "your_api_key_here"

# Custom DNS (опционально)
# Рекомендуется: "8.8.8.8" (Google), "1.1.1.1" (Cloudflare), "9.9.9.9" (Quad9)
CUSTOM_DNS = ""

# TMDB API Base URL
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Torrent download directory (опционально)
# Оставьте пустым для использования системной временной директории
TORRENT_DOWNLOAD_DIR = ""
```

### Настройка cookies для RuTracker

RuTracker требует авторизации. Вместо логина/пароля используются cookies:

1. Войдите на rutracker.org через браузер
2. Экспортируйте cookies (например, через расширение "EditThisCookie")
3. Сохраните в файл `cookies/rutracker_cookies.json`

**Формат cookies файла:**
```json
[
  {"name": "bb_data", "value": "...", "domain": ".rutracker.org"},
  {"name": "bb_session", "value": "...", "domain": ".rutracker.org"}
]
```

**Rutor** не требует авторизации и работает сразу.

---

## Использование

### Запуск приложения

```bash
python app.py
```

Приложение будет доступно по адресу: **http://localhost:5000**

### Поиск торрентов

1. Откройте страницу фильма/сериала
2. Нажмите кнопку поиска торрентов
3. Выберите подходящий торрент из списка
4. Нажмите "Смотреть" для начала стриминга

### Управление избранным

- Создавайте папки для организации контента
- Добавляйте фильмы/сериалы в избранное
- Быстрый доступ через меню "Избранное"

### Просмотр сериалов

1. Откройте страницу сериала
2. Нажмите "Смотреть" для перехода к сезонам
3. Выберите сезон из списка слева
4. Выберите серию для просмотра информации
5. Нажмите "Смотреть" для запуска

---

## API Endpoints

### Контент

| Endpoint | Описание |
|----------|----------|
| `GET /api/movies` | Получить список фильмов |
| `GET /api/tv-shows` | Получить список сериалов |
| `GET /api/trending` | Получить тренды |
| `GET /api/search?q=query` | Поиск контента |

### Избранное

| Endpoint | Описание |
|----------|----------|
| `GET /api/favorites/folders` | Получить все папки |
| `POST /api/favorites/folders` | Создать папку |
| `PUT /api/favorites/folders/<id>` | Переименовать папку |
| `DELETE /api/favorites/folders/<id>` | Удалить папку |
| `POST /api/favorites/add` | Добавить в избранное |
| `DELETE /api/favorites/remove/<id>` | Удалить из избранного |

### Торренты

| Endpoint | Описание |
|----------|----------|
| `GET /api/torrents/search?q=query` | Поиск по всем трекерам (RuTracker + Rutor) |
| `GET /api/torrents/search/rutracker?q=query` | Поиск RuTracker |
| `GET /api/torrents/search/rutor?q=query` | Поиск Rutor |
| `POST /api/torrent/start` | Начать стриминг |
| `GET /api/torrent/status` | Получить статус |
| `POST /api/torrent/stop` | Остановить стриминг |
| `DELETE /api/torrent/cache/clear` | Очистить кэш торрентов |

### Диагностика

| Endpoint | Описание |
|----------|----------|
| `GET /api/diagnostics` | Проверка подключения к TMDB |

---

## Структура проекта

```
BulbashTV/
├── app.py                      # Основной файл приложения
├── config.py                   # Конфигурация (не хранить в git)
├── config.py.example           # Шаблон конфигурации
├── torrent_search.py           # Поиск торрентов
├── server.js                   # Стриминг торрентов через MPV
├── requirements.txt            # Python зависимости
├── package.json                # Node.js зависимости
├── models/
│   └── __init__.py            # Модели данных
├── services/
│   ├── __init__.py
│   ├── tmdb_client.py         # TMDB API клиент
│   ├── data_manager.py        # Управление данными
│   ├── media_formatter.py     # Форматирование медиа
│   └── torrent_manager.py     # Управление торрентами
├── parsers/
│   ├── __init__.py            # Базовый класс Spider
│   ├── rutor.py               # Парсер Rutor
│   └── rutracker.py           # Парсер RuTracker (многостраничный)
├── utils/
│   └── http.py                # HTTP утилиты
├── templates/                  # HTML шаблоны
│   ├── index.html             # Главная страница
│   ├── movie.html             # Страница фильма/сериала
│   ├── tv_episodes.html       # Страница серий сериала
│   ├── category.html          # Каталог
│   ├── search.html            # Поиск
│   ├── favorites.html         # Избранное
│   └── folder_items.html      # Элементы папки
├── static/                     # Статические файлы
│   ├── css/style.css          # Основные стили
│   └── img/                   # Кэшированные изображения (не хранить в git)
│       └── .gitkeep           # Пустой файл для сохранения структуры
├── data/                       # Данные приложения (не хранить в git)
│   ├── favorites.json         # Избранное пользователя
│   ├── search_history.json    # История поиска
│   ├── selected_torrents.json # Выбранные торренты
│   ├── torrent_cache.json     # Кэш поиска торрентов
│   └── playback_progress.json # Прогресс воспроизведения
├── logs/                       # Логи (не хранить в git)
│   └── app.log                # Лог приложения
├── downloads/                  # Загрузки (не хранить в git)
└── cookies/                    # Cookies трекеров (не хранить в git)
    └── .gitkeep               # Пустой файл для сохранения структуры
```

---

## Требования

### Обязательные

- **Python 3.9+**
- **Node.js 16+** (для webtorrent-cli)
- **TMDB API ключ** (получить на https://www.themoviedb.org/settings/api)
- **mpv** (для воспроизведения видео)

### Опциональные

- **Tor** — для анонимного поиска
- **Git** — для клонирования репозитория

### Python зависимости

```
flask>=3.0.0
flask-wtf>=1.2.0
requests>=2.32.0
urllib3>=2.6.0
certifi>=2026.1.4
PySocks>=1.7.1
beautifulsoup4>=4.12.0
lxml>=5.0.0
bencodepy>=5.1.0
cryptography>=44.0.0
python-dotenv>=1.0.0
```

### Node.js зависимости

```
webtorrent
webtorrent-cli
```

---

## Кэширование

### Как работает

При поиске торрентов результаты сохраняются в кэш на **1 час**.

**Файлы:**
- `data/torrent_cache.json` — кэш результатов поиска
- `data/selected_torrents.json` — выбранные пользователем раздачи
- `data/torrent_history.json` — история просмотров
- `data/playback_progress.json` — прогресс воспроизведения

**Логика:**
```
1. Пользователь ищет "фильм"
   ↓
2. Проверка кэша:
   - Есть валидный кэш (< 1 часа)? → Вернуть из кэша
   - Кэш устарел или нет? → Искать заново
   ↓
3. Сохранить результаты в кэш
   ↓
4. Вернуть результаты пользователю
```

### Настройка кэширования

В `services/torrent_manager.py`:
```python
CACHE_DURATION = 3600  # 1 час (в секундах)
```

Измените на нужное значение:
- `1800` = 30 минут
- `7200` = 2 часа
- `86400` = 24 часа

### Очистка кэша

**Через API:**
```bash
curl -X DELETE http://localhost:5000/api/torrent/cache/clear
```

**Вручную:**
```bash
rm data/torrent_cache.json
```

### Преимущества

1. **Быстрый поиск** — результаты возвращаются мгновенно из кэша
2. **Меньше нагрузки** — не нужно каждый раз опрашивать трекеры
3. **Экономия трафика** — меньше запросов к внешним API

---

## Диагностика

### Проверка подключения к TMDB

```bash
curl http://localhost:5000/api/diagnostics
```

**Успешный ответ:**
```json
{
  "overall_status": "ok",
  "tests": {
    "dns": {"status": "ok", "ip": "xxx.xxx.xxx.xxx"},
    "tmdb": {"status": "ok", "response_time": 0.5}
  }
}
```

### Проверка доступности трекеров

```bash
curl "http://localhost:5000/api/torrents/search?q=test"
```

### Проверка логов

```bash
# Логи приложения
tail -f logs/app.log

# Логи стриминга
tail -f logs/streaming.log
```

---

## Troubleshooting

### Ошибка подключения к TMDB

**Проблема:** `Connection refused`

**Решения:**
1. Проверьте DNS: `nslookup api.themoviedb.org`
2. Используйте VPN или Tor
3. Смените DNS на `8.8.8.8` или `1.1.1.1`
4. Проверьте API ключ в `config.py`

### Не работают русские трекеры

**Проблема:** Поиск не находит контент

**Решение:**
1. RuTracker и Rutor интегрированы напрямую
2. Для RuTracker требуются cookies (см. [Настройка cookies](#настройка-cookies-для-rutracker))
3. Проверьте логи: `cat logs/app.log`

### Ошибки при стриминге

**Проблема:** Видео не воспроизводится

**Решения:**
1. Убедитесь, что установлен `mpv`: `sudo apt install mpv`
2. Проверьте логи стриминга: `cat logs/streaming.log`
3. Проверьте логи приложения: `cat logs/app.log`
4. Обновите зависимости: `npm update`

### Проблемы с производительностью

**Проблема:** Медленная загрузка торрентов

**Решения:**
1. Уменьшите `max_pages` для RuTracker в `torrent_search.py`
2. Используйте кэширование поиска (включено по умолчанию)
3. Настройте прокси или VPN для ускорения

### Ошибка "No module named ..."

**Проблема:** Не установлены Python зависимости

**Решение:**
```bash
pip install -r requirements.txt
```

### Ошибка "Cannot find module ..."

**Проблема:** Не установлены Node.js зависимости

**Решение:**
```bash
npm install
```

### JSON Serialization Error

**Проблема:** `Object of type TorrentResult is not JSON serializable`

**Решение:** Обновите `app.py` и `services/torrent_manager.py` до актуальной версии (конвертация в словари)

---

## Вклад в проект

1. Fork репозиторий
2. Создайте ветку (`git checkout -b feature/new-feature`)
3. Закоммитьте изменения (`git commit -m 'Add new feature'`)
4. Отправьте (`git push origin feature/new-feature`)
5. Откройте Pull Request

См. [CONTRIBUTING.md](CONTRIBUTING.md) для подробных инструкций.

---

## Контакты

- **Email:** phracture266@gmail.com
- **Issues:** GitHub Issues
- **Репозиторий:** https://github.com/phracturee/BulbashTV

---

## Лицензия

Проект создан в образовательных целях.

---

## История изменений

См. [CHANGELOG.md](CHANGELOG.md) для полной истории изменений.

---

**BulbashTV** © 2026
