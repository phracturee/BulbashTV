# Cookie файлы для авторизации на трекерах

## Как получить cookies

### Способ 1: Через браузер (рекомендуется)

1. **Войдите в аккаунт** на rutracker.org или nnmclub.to
2. **Откройте DevTools** (F12 или Ctrl+Shift+I)
3. Перейдите во вкладку **Application** (Приложение)
4. В левом меню выберите **Storage** → **Cookies** → сайт
5. **Скопируйте нужные cookies** (см. список ниже)
6. **Вставьте в JSON файл** в папку `cookies/`

### Способ 2: Через расширение

1. Установите расширение **"Cookie-Editor"** или **"EditThisCookie"**
2. Войдите в аккаунт на трекере
3. Нажмите на иконку расширения
4. Нажмите **Export** (Экспорт)
5. Сохраните в файл `cookies/[tracker]_cookies.json`

## Необходимые cookies

### Для Rutracker (rutracker_cookies.json):
```json
[
  {
    "name": "bb_session",
    "value": "ваш_токен",
    "domain": ".rutracker.org"
  },
  {
    "name": "bb_uid",
    "value": "ваш_id",
    "domain": ".rutracker.org"
  },
  {
    "name": "bb_hash",
    "value": "ваш_hash",
    "domain": ".rutracker.org"
  }
]
```

### Для NnmClub (nnmclub_cookies.json):
```json
[
  {
    "name": "phpbb2mysql_4_sid",
    "value": "ваш_session_id",
    "domain": "nnmclub.to"
  },
  {
    "name": "opt_js_user_id",
    "value": "ваш_id",
    "domain": "nnmclub.to"
  },
  {
    "name": "opt_js_user_pass",
    "value": "ваш_pass_hash",
    "domain": "nnmclub.to"
  }
]
```

## Важно!

- Cookies действуют **ограниченное время** (обычно несколько месяцев)
- При выходе из аккаунта в браузере cookies станут **недействительными**
- **Не коммитьте cookies в git!** Добавьте в `.gitignore`:
  ```
  cookies/*_cookies.json
  ```

## Как работает автоматическая авторизация

1. Парсер **сначала пытается загрузить cookies** из файла
2. Если cookies загружены, проверяет их **валидность** (ищет ссылку "Выход")
3. Если cookies **валидны** → использует их для поиска
4. Если cookies **невалидны или отсутствуют** → пытается войти по логину/паролю
5. Если нет ни cookies ни логина → выводит сообщение об ошибке

## Проверка

После добавления cookies запустите тест:
```bash
python -c "from parsers.rutracker import RutrackerSpider; s = RutrackerSpider(); print('Cookies loaded:', len(s.session.cookies))"
```

### Если видите: "[Rutracker] No login credentials provided and no valid cookies"

Это значит:
- ❌ Cookies не загружены (файл отсутствует)
- ❌ Cookies загружены но **невалидны** (устарели)
- ❌ Нет логина/пароля в config.py

**Решение:** Обновите cookies через браузер (см. инструкцию выше)

### Если видите: "[Rutracker] Cookies are valid, already logged in"

✅ Всё работает! Поиск будет использовать cookies.
