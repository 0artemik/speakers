## Speaker Recognition (FastAPI + Streamlit)

Проект представляет простую систему распознавания спикеров по голосовым записям:
- Backend: `FastAPI` (эндпоинты для регистрации/логина и операций со спикерами)
- Frontend: `Streamlit` (интерфейс для enroll/identify)
- Database: PostgreSQL (в `docker-compose.yml` используется образ `pgvector/pgvector:pg16`)

Модель/эмбеддинги извлекаются через `resemblyzer` (в `routers.py` используется `VoiceEncoder`).

## Требования

1. Python 3.10
2. Docker Desktop (для `docker-compose.yml`) или уже запущенный PostgreSQL

## Запуск через Docker

1. Поднимите БД:
```bash
cd /Users/mac/Desktop/qwe/projects/speakers
docker compose up -d
```

2. Убедитесь, что PostgreSQL доступен по `localhost:5433`.

3. Запустите backend:
```bash
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

4. Запустите frontend:
```bash
streamlit run streamlit_app.py
```

После запуска:
- Backend: `http://127.0.0.1:8000`
- Frontend: обычно `http://localhost:8501`

## Переменные окружения

Backend читает `DATABASE_URL` из переменных окружения. Если переменная не задана, используется значение по умолчанию:

`postgresql://admin:admin@localhost:5433/speakersdb`

Параметры для БД в `docker-compose.yml`:
- `POSTGRES_USER: admin`
- `POSTGRES_PASSWORD: admin`
- `POSTGRES_DB: speakersdb`
- Проброс портов: `5433:5432` (в контейнере PostgreSQL слушает `5432`)

## API (FastAPI)

Все эндпоинты принимают `multipart/form-data` с аудио-файлом где это нужно.

### Авторизация

1. Регистрация:
`POST /auth/register`

Поля формы:
- `username` (строка)
- `password` (строка)

2. Логин:
`POST /auth/login`

Поля формы:
- `username` (строка)
- `password` (строка)

Возвращает:
- `id`
- `username`
- `is_admin`

### Спикеры

1. Регистрация спикера (enroll):
`POST /speakers/enroll`

Поля:
- `name` (строка)
- `file` (аудиофайл)

Ожидаемые форматы аудио на стороне UI: `wav`, `mp3`, `ogg`.

2. Идентификация спикера (identify):
`POST /speakers/identify`

Поля:
- `file` (аудиофайл)

Возвращает:
- `match` (имя спикера или `null`)
- `score` (число от 0 до 1)

3. Список спикеров:
`GET /speakers`

Возвращает список объектов с `id`, `name`, `embedding`, `created_at`.
`embedding` хранится в PostgreSQL в типе `vector(256)` (расширение pgvector).

## UI (Streamlit)

`streamlit_app.py` ходит на backend по адресу:
- `API_URL = "http://localhost:8000"`

В интерфейсе доступны вкладки:
- `Регистрация (Enroll)`
- `Идентификация (Identify)`
- `Админ: спикеры` (появляется для пользователя с `username=admin`)

## Частые проблемы

### `connection to server at "localhost" port 5433 failed: Connection refused`

Это означает, что PostgreSQL не запущен или не слушает порт `5433`.

Проверьте:
- выполнен ли `docker compose up -d`
- не изменился ли порт в `docker-compose.yml` и `DATABASE_URL`

## Примечание про `resemblyzer`

Если зависимость `resemblyzer` не установлена или не смогла загрузиться, в эндпоинтах `enroll/identify` будет ошибка:
`Voice encoder not available. Install resemblyzer and dependencies`

