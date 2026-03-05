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
- **Поиск торрентов** — интеграция с 15+ трекерами:
  - Международные: YTS, TPB, 1337x, SolidTorrents, Nyaa.si
  - Русские: RuTracker, Rutor, Kinozal (требуется Jackett или прямая интеграция)
  - Агрегаторы: TorrentsAPI, BT4G, MagnetDL
- **Избранное** — организация контента по папкам
- **История просмотра** — отслеживание просмотренного контента
- **История поиска** — сохранение поисковых запросов
- **Стриминг торрентов** — воспроизведение через webtorrent-cli + mpv
- **Кэширование изображений** — локальное кэширование постеров
- **Приоритизация торрентов** — запоминание выбранных раздач

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
        │  - RutrackerSpider                    │
        │  - RutorSpider                        │
        │  - KinozalSpider                      │
        └───────────────────────────────────────┘
```

### Основные классы

| Класс | Описание |
|-------|----------|
| `BulbashTVApp` | Основной класс приложения, фабрика Flask |
| `TMDBClient` | Клиент для работы с TMDB API |
| `DataManager` | Базовый класс для управления данными |
| `FavoritesManager` | Управление избранным |
| `HistoryManager` | Управление историей |
| `MediaFormatter` | Форматирование данных для шаблонов |
| `ImageCache` | Кэширование изображений |
| `TorrentManager` | Управление поиском и стримингом торрентов |
| `TorrentSearcher` | Поиск по трекерам |
| `TorrentResult` | Модель результата поиска |
| `BaseSpider` | Базовый класс для парсеров |

## 📦 Установка

### 1. Клонирование репозитория

```bash
cd /path/to/project
```

### 2. Установка Python зависимостей

```bash
pip install -r requirements.txt
```

### 3. Установка Node.js зависимостей

```bash
npm install
```

### 4. Настройка конфигурации

```bash
cp config.py.example config.py
# Отредактируйте config.py, добавив ваши API ключи
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
├── config.py                   # Конфигурация
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
│   ├── rutracker.py           # Парсер Rutracker
│   └── kinozal.py             # Парсер Kinozal
├── utils/
│   └── http.py                # HTTP утилиты
├── templates/                  # HTML шаблоны
├── static/                     # Статические файлы
├── data/                       # Данные приложения
└── cookies/                    # Cookies трекеров
```

## 📋 Требования

### Обязательные

- **Python 3.9+**
- **Node.js 16+** (для webtorrent-cli)
- **TMDB API ключ**

### Опциональные

- **Jackett** — для доступа к русским трекерам
- **Tor** — для анонимного поиска
- **mpv** — для воспроизведения видео

### Python зависимости

```
flask>=3.0.0
requests[socks]>=2.31.0
PySocks>=1.7.1
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

### Node.js зависимости

```
webtorrent
webtorrent-cli
```

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

### Не работают русские трекеры

**Проблема:** Поиск не находит русский контент

**Решение:**
1. Установите и настройте Jackett
2. Добавьте RuTracker, Kinozal в Jackett
3. Укажите API ключ в `config.py`

### Ошибки при стриминге

**Проблема:** Видео не воспроизводится

**Решения:**
1. Убедитесь, что установлен `mpv`: `sudo apt install mpv`
2. Проверьте логи: `cat /tmp/webtorrent.log`
3. Обновите webtorrent-cli: `npm update webtorrent-cli`

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
