# Настройка Jackett для поиска русских торрентов

Для поиска русского контента (RuTracker, Kinozal и др.) рекомендуется установить Jackett.

## Установка Jackett

### Linux:
```bash
# Скачайте последнюю версию с https://github.com/Jackett/Jackett/releases
# Для x64:
wget https://github.com/Jackett/Jackett/releases/download/v0.21.0/Jackett.Binaries.LinuxAMD64.tar.gz
tar -xzf Jackett.Binaries.LinuxAMD64.tar.gz
cd Jackett
./jackett
```

### Windows:
Скачайте установщик с https://github.com/Jackett/Jackett/releases

### Docker:
```bash
docker run -d \
  --name=jackett \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/Moscow \
  -p 9117:9117 \
  -v /path/to/jackett/config:/config \
  --restart unless-stopped \
  lscr.io/linuxserver/jackett:latest
```

## Настройка

1. Откройте Jackett web UI: http://localhost:9117
2. Добавьте индексеры:
   - **RuTracker** - крупнейший русский трекер
   - **Kinozal** - русские фильмы и сериалы
   - **NoNaMe-Club** - русский контент
   - **TorLook** - агрегатор
   - ** Rutor** - открытый русский трекер

3. Скопируйте API Key (вверху страницы)

4. Отредактируйте `config.py`:
```python
JACKETT_API_KEY = "ваш_api_ключ_здесь"
JACKETT_URL = "http://localhost:9117"  # или ваш URL
```

5. Перезапустите приложение

## Примечания

- Без Jackett поиск работает только через публичные API (YTS, TPB, EZTV и др.)
- Эти API не индексируют русский контент
- Для русских фильмов/сериалов Jackett **обязателен**
- Если Jackett не настроен, поиск будет работать только для англоязычного контента

## Альтернативные методы

Если Jackett не подходит, можно:
1. Найти magnet-ссылку вручную на RuTracker/Kinozal
2. Вставить её напрямую через интерфейс
3. Или использовать API endpoint: `POST /api/torrents/start` с magnet ссылкой
