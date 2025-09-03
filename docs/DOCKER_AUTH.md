# Docker: Авторизация Telegram и запуск

Ниже — проверенный поток для продоподобного запуска в Docker c хранением сессии в томе.

## 1) Подготовка окружения

- Создайте `.env` из шаблона и заполните:
  - `TELEGRAM_API_ID`
  - `TELEGRAM_API_HASH`
  - `TELEGRAM_PHONE` (номер тех‑аккаунта)
  - (опционально) `TELEGRAM_2FA_PASSWORD` — пароль 2FA, чтобы не вводить его вручную при ре‑логине
- Соберите контейнеры:

```
docker compose build
```

## 2) Первичная авторизация внутри контейнера

Один раз интерактивно авторизуем тех‑аккаунт; Telethon сохранит сессию в `/app/data/dooms_deal_session.session` (том `app_data`).

```
# через Makefile
make docker-auth

# напрямую через docker compose
# docker compose run --rm dooms-deal-clock python scripts/telegram_auth.py
```

В терминале появится запрос кода из Telegram. Если включена двухфакторная аутентификация:

- Можно задать пароль 2FA через переменную окружения `TELEGRAM_2FA_PASSWORD` (в `.env`), или
- Оставить её пустой — тогда скрипт интерактивно спросит пароль 2FA (без эха).

После успешного входа сессия сохранится в томе и переживёт перезапуски контейнера.

Проверить, что авторизовано:

```
make tg-status
# или: docker compose run --rm dooms-deal-clock python scripts/telegram_status.py
```

## 3) Запуск сервиса

```
docker compose up -d
# Проверка
docker compose logs -f dooms-deal-clock
```

Фронтенд доступен через Nginx на `http://localhost/` (см. `nginx.conf`), а API — на `http://localhost:8000` (если публикуется порт).

## 4) Обновление данных вручную (для проверки)

```
curl -sS -X POST http://localhost:8000/api/clock/fetch
curl -sS http://localhost:8000/api/clock/latest | jq .
```

## 5) Ротация/переавторизация

Если сессия слетела (смена пароля/2FA или отзыв всех сессий):

```
docker compose stop dooms-deal-clock
# по необходимости удалить/переименовать файл
# docker compose run --rm dooms-deal-clock rm -f data/dooms_deal_session.session
make docker-auth
```

## Безопасность

- Файл `.session` — полноценный доступ к аккаунту. Хранится только в Docker‑томе `app_data` с правами `600`.
- `TELEGRAM_2FA_PASSWORD` — секрет; держите его в секрет‑хранилище (Docker/K8s secrets), не логируйте.
- В случае компрометации: отозвать все сессии в Telegram, сменить пароль/2FA, заново пройти авторизацию.

***

Подготовка отдельного тех‑аккаунта вынесена в общий TODO и выполняется перед публичным деплоем.
