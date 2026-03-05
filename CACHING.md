# Кэширование торрентов

## Как работает

При поиске торрентов результаты сохраняются в кэш на 1 час.

### Файлы

- `data/torrent_cache.json` - кэш результатов поиска
- `data/selected_torrents.json` - выбранные пользователем раздачи
- `data/torrent_history.json` - история просмотров

### Логика

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

## API

### Поиск с кэшированием

```bash
GET /api/torrents/search?q=фильм
```

Автоматически использует кэш если есть.

### Очистка кэша

```bash
DELETE /api/torrent/cache/clear
```

Очищает весь кэш.

## Настройка

В `services/torrent_manager.py`:

```python
CACHE_DURATION = 3600  # 1 час (в секундах)
```

Измените на нужное значение:
- `1800` = 30 минут
- `7200` = 2 часа
- `86400` = 24 часа

## Преимущества

1. **Быстрый поиск** - результаты возвращаются мгновенно из кэша
2. **Меньше нагрузки** - не нужно каждый раз опрашивать трекеры
3. **Экономия трафика** - меньше запросов к внешним API

## Пример кэша

```json
{
  "matrix": {
    "query": "matrix",
    "results": [...],
    "timestamp": 1708300000,
    "count": 25
  },
  "terminator": {
    "query": "terminator",
    "results": [...],
    "timestamp": 1708303600,
    "count": 18
  }
}
```

## Мониторинг

### Размер кэша

```bash
ls -lh data/torrent_cache.json
```

### Просмотр кэша

```bash
cat data/torrent_cache.json | python -m json.tool | head -50
```

### Очистка

```bash
rm data/torrent_cache.json
```

Или через API:

```bash
curl -X DELETE http://localhost:5000/api/torrent/cache/clear
```

## Статистика

В логах:

```
[Cache] Hit for query: matrix         # Кэш найден
[Cache] Expired for query: oldfilm    # Кэш устарел
[Search] Searching for: newfilm       # Поиск заново
[Cache] Saved 25 results for: film    # Сохранено в кэш
```
