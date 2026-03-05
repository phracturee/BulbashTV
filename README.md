# BulbashTV

**BulbashTV** — это веб-приложение для поиска и просмотра фильмов и сериалов с интеграцией торрент-трекеров. Приложение использует TMDB API для получения информации о контенте и предоставляет возможность поиска торрентов на множестве трекеров.

## 📋 Содержание

- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Установка](#установка)
- [Настройка](#настройка)
- [Использование](#использование)
- [API Endpoints](#api-endpoints)
- [Структура проекта](#структура-проекта)
- [Требования](#требования)
- [Диагностика](#диагностика)
- [Troubleshooting](#troubleshooting)

## 🎬 Возможности

- **Каталог фильмов и сериалов** — получение данных из TMDB с поддержкой русского языка
- **Страница сезонов и серий** — удобный выбор серий для сериалов с описанием, рейтингом и датой выхода
- **Поиск торрентов** — интеграция с 15+ трекерами:
  - Международные: YTS, TPB, 1337x, SolidTorrents, Nyaa.si
  - Русские: RuTracker (прямая интеграция, до 500 результатов), Rutor, Kinozal
  - Агрегаторы: TorrentsAPI, BT4G, MagnetDL
- **Пагинация результатов** — постепенная загрузка торрентов (по 30 результатов с кнопкой "Показать ещё")
- **Избранное** — организация контента по папкам
- **Просмотренное** — отслеживание просмотренных фильмов и серий
- **История поиска** — сохранение поисковых запросов
- **Стриминг торрентов** — воспроизведение через striming-torrent-mpv + mpv
- **Кэширование изображений** — локальное кэширование постеров
- **Приоритизация торрентов** — запоминание выбранных раздач
- **Прозрачный интерфейс** — современный дизайн с закруглёнными элементами и фоновыми изображениями

## 🏗 Архитектура

Приложение построено по принципу **разделения ответственности** с использованием ООП:

```
┌─────────────────────────────────────────────────────────┐
│                    BulbashTVApp                         │
│  (Flask application factory)                            │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ TMDBClient   │  │ DataManager  │  │ TorrentMgr   │  │
│  │              │  │              │  │              │  │
│  │ - API запросы│  │ - Избранное  │  │ - Поиск      │  │
│  │ - Кэширование│  │ - История    │  │ - Стриминг   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │           MediaFormatter + ImageCache            │   │
│  │           (Форматирование и кэширование)         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  Parsers (BaseSpider + конкретные)    │
        │  - RutrackerSpider (многостраничный)  │
        │  - RutorSpider                        │
        │  - KinozalSpider                      │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  striming-torrent-mpv/                │
        │  - Стриминг торрентов через MPV       │
        └───────────────────────────────────────┘
```

### Основные классы

| Класс | Описание |
|-------|----------|
| `BulbashTVApp` | Основной класс приложения, фабрика Flask |
| `TMDBClient` | Клиент для работы с TMDB API |
| `DataManager` | Базовый класс для управления данными |
| `FavoritesManager` | Управление избранным (папки) |
| `HistoryManager` | Управление историей поиска |
| `MediaFormatter` | Форматирование данных для шаблонов |
| `ImageCache` | Кэширование изображений |
| `TorrentManager` | Управление поиском и стримингом торрентов |
| `TorrentSearcher` | Поиск по трекерам |
| `TorrentResult` | Модель результата поиска |
| `BaseSpider` | Базовый класс для парсеров |
| `RutrackerSpider` | Парсер RuTracker с поддержкой пагинации (до 10 страниц) | |

## 📦 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd BulbashTV
```

### 2. Установка Python зависимостей

**Важно:** Установите все зависимости самостоятельно:

```bash
pip install -r requirements.txt
```

### 3. Установка Node.js зависимостей

**Важно:** Установите все зависимости самостоятельно:

```bash
npm install
```

### 4. Настройка конфигурации

```bash
cp config.py.example config.py
# Отредактируйте config.py, добавив ваши API ключи
```

### 5. Настройка striming-torrent-mpv

Стриминг использует `striming-torrent-mpv` для воспроизведения:

```bash
cd striming-torrent-mpv
npm install
```

Убедитесь, что установлен `mpv`:
```bash
# Ubuntu/Debian
sudo apt install mpv

# macOS
brew install mpv
```

## ⚙️ Настройка

### Конфигурационный файл (config.py)

```python
# TMDB API Configuration
TMDB_API_KEY = "ваш_api_ключ"  # Получите на https://www.themoviedb.org/settings/api
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Jackett Configuration (опционально)
JACKETT_API_KEY = ""  # API ключ Jackett
JACKETT_URL = "http://localhost:9117"

# Russian Tracker Credentials (опционально)
RUTRACKER_LOGIN = ""
RUTRACKER_PASS = ""
NNMCLUB_LOGIN = ""
NNMCLUB_PASS = ""

# Tor Proxy (опционально)
TOR_PROXY = ""  # "socks5h://127.0.0.1:9050"
```

### Настройка Jackett (рекомендуется для русского контента)

Jackett обеспечивает доступ к русским трекерам (RuTracker, Kinozal, NnmClub).

1. Установите Jackett:
   ```bash
   # Linux
   wget https://github.com/Jackett/Jackett/releases/download/v0.21.0/Jackett.Binaries.LinuxAMD64.tar.gz
   tar -xzf Jackett.Binaries.LinuxAMD64.tar.gz
   cd Jackett && ./jackett
   ```

2. Откройте веб-интерфейс: http://localhost:9117

3. Добавьте индексеры: RuTracker, Kinozal, NnmClub

4. Скопируйте API ключ и добавьте в `config.py`

### Настройка Tor (опционально)

Для доступа к трекерам через Tor:

```bash
sudo apt install tor
sudo service tor start
```

В `config.py`:
```python
TOR_PROXY = "socks5h://127.0.0.1:9050"
```

## 🚀 Использование

### Запуск приложения

```bash
python app.py
```

Приложение будет доступно по адресу: http://localhost:5000

### Поиск торрентов

1. Откройте страницу фильма/сериала
2. Нажмите кнопку поиска торрентов
3. Выберите подходящий торрент из списка
4. Нажмите "Смотреть" для начала стриминга

### Управление избранным

- Создавайте папки для организации контента
- Добавляйте фильмы/сериалы в избранное
- Быстрый доступ через меню "Избранное"

## 🔌 API Endpoints

### Фильмы и сериалы

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
| `GET /api/torrents/search?q=query` | Поиск по всем трекерам |
| `GET /api/torrents/search/yts?q=query` | Поиск только YTS |
| `GET /api/torrents/search/tpb?q=query` | Поиск только TPB |
| `GET /api/torrents/search/rutracker?q=query` | Поиск RuTracker |
| `POST /api/torrent/start` | Начать стриминг |
| `GET /api/torrent/status` | Получить статус |
| `POST /api/torrent/stop` | Остановить стриминг |

### Диагностика

| Endpoint | Описание |
|----------|----------|
| `GET /api/diagnostics` | Проверка подключения к TMDB |

## 📁 Структура проекта

```
BulbashTV/
├── app.py                      # Основной файл приложения
├── config.py                   # Конфигурация (не хранить в git)
├── config.py.example           # Шаблон конфигурации
├── torrent_search.py           # Поиск торрентов
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
│   ├── rutracker.py           # Парсер RuTracker (многостраничный)
│   └── kinozal.py             # Парсер Kinozal
├── utils/
│   └── http.py                # HTTP утилиты
├── striming-torrent-mpv/      # Стриминг торрентов
│   ├── server.js              # Сервер стриминга
│   └── downloads/             # Загруженные торренты
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
│   └── img/                   # Кэшированные изображения
├── data/                       # Данные приложения (не хранить в git)
│   ├── favorites.json         # Избранное
│   ├── search_history.json    # История поиска
│   ├── selected_torrents.json # Выбранные торренты
│   └── torrent_cache.json     # Кэш поиска
├── logs/                       # Логи (не хранить в git)
│   └── app.log                # Лог приложения
├── downloads/                  # Загрузки (не хранить в git)
└── cookies/                    # Cookies трекеров (не хранить в git)
```

## 📋 Требования

### Обязательные

- **Python 3.9+**
- **Node.js 16+** (для striming-torrent-mpv и webtorrent-cli)
- **TMDB API ключ** (получить на https://www.themoviedb.org/settings/api)
- **mpv** (для воспроизведения видео)

### Опциональные

- **Jackett** — для доступа к дополнительным трекерам
- **Tor** — для анонимного поиска
- **Git** — для клонирования репозитория

### Python зависимости

Все зависимости указаны в `requirements.txt`:

```
flask>=3.0.0
requests[socks]>=2.31.0
PySocks>=1.7.1
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

**Установка:**
```bash
pip install -r requirements.txt
```

### Node.js зависимости

Все зависимости указаны в `package.json`:

```
webtorrent
webtorrent-cli
```

**Установка:**
```bash
npm install
```

**Важно:** Зависимости не включены в репозиторий. Пользователь должен установить их самостоятельно.

## 🔍 Диагностика

### Проверка подключения к TMDB

```bash
curl http://localhost:5000/api/diagnostics
```

Успешный ответ:
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

## 🛠 Troubleshooting

### Ошибка подключения к TMDB

**Проблема:** `Connection refused`

**Решения:**
1. Проверьте DNS: `nslookup api.themoviedb.org`
2. Используйте VPN или Tor
3. Смените DNS на `8.8.8.8` или `1.1.1.1`
4. Проверьте API ключ в `config.py`

### Не работают русские трекеры

**Проблема:** Поиск не находит русский контент

**Решение:**
1. RuTracker интегрирован напрямую (требуется авторизация)
2. Настройте Jackett для дополнительных трекеров
3. Добавьте API ключ Jackett в `config.py`

### Ошибки при стриминге

**Проблема:** Видео не воспроизводится

**Решения:**
1. Убедитесь, что установлен `mpv`: `sudo apt install mpv`
2. Проверьте логи striming-torrent-mpv: `cat /tmp/striming-torrent-mpv.log`
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

## 📝 Лицензия

Проект создан в образовательных целях.

## 🤝 Вклад в проект

1. Fork репозиторий
2. Создайте ветку (`git checkout -b feature/new-feature`)
3. Закоммитьте изменения (`git commit -m 'Add new feature'`)
4. Отправьте (`git push origin feature/new-feature`)
5. Откройте Pull Request

## 📞 Контакты

- **Issues:** GitHub Issues
- **Документация:** [JACKETT_SETUP.md](JACKETT_SETUP.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**BulbashTV** © 2024
# BulbashTV
