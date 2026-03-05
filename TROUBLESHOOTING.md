# Troubleshooting: Ошибки подключения к TMDB

## Ошибка: "Connection refused"

```
HTTPSConnectionPool(host='api.themoviedb.org', port=443): Max retries exceeded with url:...
Failed to establish a new connection: [Errno 111] Connection refused
```

## Причины и решения

### 1. **Проблемы с DNS**

Проверьте разрешение имени:
```bash
nslookup api.themoviedb.org
```

**Решение:** В `config.py` оставьте `CUSTOM_DNS = ""` для использования системного DNS, или используйте:
- `"8.8.8.8"` (Google DNS)
- `"1.1.1.1"` (Cloudflare DNS)

### 2. **Блокировка провайдером**

Некоторые провайдеры блокируют TMDB.

**Проверка:**
```bash
curl -I https://api.themoviedb.org/3/movie/550?api_key=bd04b0e5de7a0424a60f9bc2abf99515
```

**Решения:**
- Используйте VPN
- Используйте Tor прокси (установите Tor и настройте `TOR_PROXY`)
- Смените DNS на 1.1.1.1 или 8.8.8.8

### 3. **Проблемы с сетью**

**Проверка соединения:**
Откройте в браузере: http://localhost:5000/api/diagnostics

Или через curl:
```bash
curl http://localhost:5000/api/diagnostics
```

### 4. **Неверный API ключ**

Если видите ошибку 401 - ключ невалидный.
Получите новый ключ на https://www.themoviedb.org/settings/api

## Диагностика

### Проверка через API:
```bash
# Запустите сервер и проверьте:
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

**Ошибка:**
```json
{
  "overall_status": "error",
  "tests": {
    "dns": {"status": "error", "error": "..."},
    "tmdb": {"status": "error", "error": "..."}
  }
}
```

## Временное решение

При ошибках подключения:
1. Фильмы показываются с заглушкой "Фильм недоступен"
2. Поиск торрентов продолжает работать
3. Можно добавить фильм вручную через поиск

## Настройка Tor (если TMDB заблокирован)

1. Установите Tor:
```bash
sudo apt install tor
sudo service tor start
```

2. В `config.py` добавьте:
```python
TOR_PROXY = "socks5h://127.0.0.1:9050"
```

3. Перезапустите приложение

## Проверка cookies трекеров

Если не работают парсеры:
1. Проверьте файлы в `cookies/`
2. Убедитесь что cookies актуальны
3. При необходимости обновите cookies через браузер
