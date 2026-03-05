# Настройка парсеров русских трекеров

Теперь поиск работает с русскими фильмами через парсеры Rutracker, Rutor и NnmClub.

## Работающие парсеры

### 1. Rutor (работает без логина) ✅
- **URL:** http://rutor.info или Tor: http://rutorc6mqdinc4cz.onion
- **Логин:** Не требуется
- **Статус:** Работает сразу

### 2. Rutracker (требует логин) ⚠️
- **URL:** https://rutracker.org
- **Логин:** Требуется
- **Статус:** Нужно добавить логин в config.py

### 3. NnmClub (требует логин) ⚠️
- **URL:** https://nnmclub.to или Tor
- **Логин:** Требуется
- **Статус:** Нужно добавить логин в config.py

## Настройка

Отредактируйте `config.py`:

```python
# Russian Tracker Credentials (optional)
# Leave empty to use without login (only Rutor will work)
RUTRACKER_LOGIN = "ваш_логин"
RUTRACKER_PASS = "ваш_пароль"
NNMCLUB_LOGIN = "ваш_логин"
NNMCLUB_PASS = "ваш_пароль"

# Tor Proxy Configuration (optional)
# Format: "socks5h://127.0.0.1:9050"
# Leave empty if Tor is not installed
TOR_PROXY = ""
```

## API Endpoints

Добавлены новые endpoints:

```
GET /api/torrents/search?q=query              # Все трекеры (включая русские)
GET /api/torrents/search/rutor?q=query        # Только Rutor
GET /api/torrents/search/rutracker?q=query    # Только Rutracker
GET /api/torrents/search/nnmclub?q=query      # Только NnmClub
```

## Результаты тестирования

✅ **Марти Великолепный:**
- Rutor: 6 результатов (до 785 сидов)
- Качество: WEB-DL 1080p, 720p

✅ **Кин-дза-дза:**
- Rutor: 52 результата
- Качество: BDRip 1080p, BDRip-AVC, BDRemux

✅ **Ирония судьбы:**
- Rutor: 54 результата
- Качество: DVDRip, BDRip-AVC, HDTVRip

## Без логина

Без логина работает только **Rutor**, но этого достаточно для поиска большинства русских фильмов.

## Установка Tor (опционально)

Если хотите использовать Tor для Rutracker/NnmClub:

```bash
# Ubuntu/Debian
sudo apt install tor
sudo service tor start

# В config.py добавьте:
TOR_PROXY = "socks5h://127.0.0.1:9050"
```

## Примечания

- Rutor работает быстро и без авторизации
- Rutracker и NnmClub требуют логин для поиска
- Парсеры сохраняют cookies между запросами
- При ошибках парсинга, ошибки выводятся в консоль
