# 🍿 Popcorn-MPV Integration

## Обзор

Интеграция **popcorn-mpv** в BulbashTV для стриминга торрентов с сохранением прогресса воспроизведения.

## Компоненты

### Backend (Python)

**services/torrent_manager.py:**
- `start_streaming()` - запуск popcorn-mpv
- `save_playback_progress()` - сохранение позиции
- `get_playback_progress()` - получение позиции
- `PLAYBACK_PROGRESS_FILE` - файл прогресса (`data/playback_progress.json`)

**API Endpoints:**
- `POST /api/torrent/start` - запуск стрима
- `POST /api/torrent/progress/save` - сохранить прогресс
- `GET /api/torrent/progress?magnet=...` - получить прогресс

### Frontend (JavaScript)

**movie.html:**
- `selectTorrent()` - выбор раздачи
- `startStatusPolling()` - опрос статуса
- `saveProgress()` - сохранение позиции
- `getPlaybackProgress()` - получение прогресса

## Как работает

### 1. Выбор торрента

```
Пользователь → Выбрать раздачу
    ↓
Frontend → POST /api/torrent/start {magnet, title, query}
    ↓
Backend → Запуск popcorn-mpv/server.js
    ↓
popcorn-mpv → HTTP сервер на :8888 + MPV
    ↓
Frontend → Открыть http://localhost:8888/0
```

### 2. Сохранение прогресса

```
Каждые 10 секунд:
    ↓
Frontend → POST /api/torrent/progress/save {magnet, position, duration}
    ↓
Backend → Сохранить в data/playback_progress.json
```

### 3. Отображение прогресса

```
При загрузке списка торрентов:
    ↓
Frontend → GET /api/torrent/progress?magnet=...
    ↓
Отобразить ⏰ 15:30 рядом с названием
```

## Структура данных

**playback_progress.json:**
```json
{
  "abc123...": {
    "position": 925,
    "duration": 7200,
    "timestamp": 1708300000,
    "formatted": "15:25"
  }
}
```

## Статистика в реальном времени

Отображается в плеере:
- **Прогресс загрузки** - % скачанного
- **Скорость** - MB/s
- **Пиры** - количество подключений

## Файлы

| Файл | Описание |
|------|----------|
| `popcorn-mpv/server.js` | Стриминг сервер |
| `services/torrent_manager.py` | Управление стримингом |
| `data/playback_progress.json` | Прогресс воспроизведения |
| `templates/movie.html` | UI плеера |

## Использование

### Запуск

```bash
python app.py
```

### API Примеры

**Запуск стрима:**
```bash
curl -X POST http://localhost:5000/api/torrent/start \
  -H "Content-Type: application/json" \
  -d '{"magnet": "magnet:?xt=urn:btih:...", "title": "Movie", "query": "Movie"}'
```

**Сохранить прогресс:**
```bash
curl -X POST http://localhost:5000/api/torrent/progress/save \
  -H "Content-Type: application/json" \
  -d '{"magnet": "...", "position": 925, "duration": 7200}'
```

**Получить прогресс:**
```bash
curl "http://localhost:5000/api/torrent/progress?magnet=..."
```

## Преимущества

✅ **Стриминг без полной загрузки** - начало через 10 секунд
✅ **Сохранение прогресса** - продолжение с места остановки
✅ **Статистика** - скорость, пиры, прогресс загрузки
✅ **Поддержка перемотки** - HTTP Range Requests
✅ **Автоматический выбор видео** - поиск видеофайлов

## Troubleshooting

**popcorn-mpv не запускается:**
```bash
cd popcorn-mpv
npm install
node server.js "magnet:..."
```

**Прогресс не сохраняется:**
- Проверьте `data/playback_progress.json`
- Проверьте консоль браузера на ошибки

**Видео не открывается:**
- Проверьте что порт 8888 свободен
- Установите MPV: `sudo apt install mpv`
