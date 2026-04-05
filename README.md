## Speaker Recognition (FastAPI + Streamlit)

Проект представляет простую систему распознавания спикеров по голосовым записям:
- Backend: `FastAPI` (эндпоинты для регистрации/логина и операций со спикерами)
- Frontend: `Streamlit` (интерфейс для enroll/identify)
- Database: PostgreSQL (в `docker-compose.yml` используется образ `pgvector/pgvector:pg16`)

Модель/эмбеддинги извлекаются через `resemblyzer` (в `routers.py` используется `VoiceEncoder`).

## Требования

1. Python 3.10
2. Docker Desktop (для `docker-compose.yml`) или уже запущенный PostgreSQL

## Запуск через Docker (всё в контейнерах)

Собирает и поднимает PostgreSQL, FastAPI (`Dockerfile`) и Streamlit.

```bash
cd /Users/mac/Desktop/qwe/projects/speakers
docker compose up --build -d
```

### Сборка «висит» и в терминале пусто

1. **Не вешайте вывод на `tail` во время сборки.** Команда вида `docker compose build ... 2>&1 | tail -60` почти всегда **ничего не покажет**, пока сборка целиком не закончится: `tail` ждёт конца потока. Смотрите лог напрямую:
   ```bash
   docker compose build --progress=plain streamlit
   ```
   или без pipe вообще:
   ```bash
   docker compose build streamlit
   ```

2. **Первая сборка долгая:** в `requirements.txt` есть `torch`, `streamlit`, `scipy` и др. Шаг `pip install` внутри образа часто занимает **10–30+ минут** (скачивание колёс), при этом вывод может редко обновляться — это не обязательно зависание.

3. **Долго на «Sending build context»:** если в каталоге проекта лежит тяжёлый `venv/` или датасеты, убедитесь, что они перечислены в `.dockerignore` (у нас `venv/` уже исключён).

После запуска:
- API: `http://127.0.0.1:8000`
- Streamlit: `http://127.0.0.1:8501` (в контейнере задано `API_URL=http://api:8000`)

Только API (без UI), например:

```bash
docker compose up --build -d postgres api
```

Образ собирается из `Dockerfile` (Python 3.10, зависимости из `requirements.txt`).

`requirements.txt` должен быть в **UTF-8**. Если редактор сохранил файл как **UTF-16**, локальный `pip install -r requirements.txt` и сборка Docker падали бы с ошибкой вида `Invalid requirement: 'a\x00l\x00t...'`. В `Dockerfile` перед `pip install` вызывается `docker/normalize_requirements.py`, который приводит файл к UTF-8 внутри образа.

## Локальная разработка (только БД в Docker)

1. Поднимите PostgreSQL:
```bash
cd /Users/mac/Desktop/qwe/projects/speakers
docker compose up -d postgres
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

`streamlit_app.py` ходит на backend по адресу из переменной окружения `API_URL` (по умолчанию `http://localhost:8000`). В `docker-compose` для сервиса `streamlit` задано `API_URL=http://api:8000`.

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

