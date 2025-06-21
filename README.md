Проект реализован в рамках интенсива от компании Газпром Трансгаз Томск.
---

# 🧩 Проект: Телеграм-бот + FastAPI Backend

## 📌 Описание
Проект состоит из двух частей:
- **Telegram-бот** (на Aiogram 3.x), принимающий заявки от пользователей.
- **FastAPI backend**, предоставляющий API для регистрации, аутентификации, управления пользователями, группами, департаментами и заявками.
- Используется **PostgreSQL** как основная БД.
- Поддержка **микросервисной архитектуры** через Docker и Docker Compose.

---

## 🛠 Стек технологий

| Категория       | Используемые технологии |
|----------------|-------------------------|
| **Backend**     | Python 3.12, FastAPI    |
| **Telegram Bot**| Aiogram 3.x             |
| **База данных** | PostgreSQL              |
| **ORM**         | SQLAlchemy ORM          |
| **Миграции**    | Alembic                 |
| **Аутентификация** | JWT, Bcrypt           |
| **Веб-фреймворк** | FastAPI                |
| **Контейнеризация** | Docker, Docker Compose |
| **Логирование** | logging                 |

---

## 🧠 Архитектура backend

### 1. **FastAPI**
- Создан REST API для:
  - Регистрации и авторизации (`/register`, `/login`)
  - Управления пользователями (`/users/me`, `/users/{id}/group`)
  - Управления департаментами, группами, сервисами
  - Обработки заявок (`/requests`)

### 2. **JWT Аутентификация**
- Реализовано токенное аутентификационное окружение:
  - Логин через OAuth2 (`/login`)
  - Защита эндпоинтов через `Depends(get_current_user)`
  - Токены живут 30 минут

### 3. **Пользователи и роли**
- Поддерживаются следующие роли:
  - `ADMIN`
  - `HR`
  - `MANAGER`
  - `DEVELOPER`
- Доступ к функционалу зависит от роли (RBAC)
- Пример: только `ADMIN` может удалять сервисы

### 4. **Сервисы / Департаменты / Группы**
- Иерархическая структура:
  - Сервис → Департамент → Группа → Пользователь
- Возможность создания, обновления и удаления элементов

### 5. **Telegram-бот**
- Прием заявок от пользователей в формате:
  ```
  title: ...
  description: ...
  tags: ...
  ```
- Заявки сохраняются в базу данных
- Поддержка вебхуков

---

## 🗃️ Структура базы данных

```python
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    role = Column(String)
    group_id = Column(Integer, ForeignKey("groups.group_id"))
    disabled = Column(Boolean, default=False)

class Service(Base):
    __tablename__ = "services"
    service_id = Column(Integer, primary_key=True)
    name = Column(String)

class Departament(Base):
    __tablename__ = "departaments"
    depart_id = Column(Integer, primary_key=True)
    name = Column(String)
    service_id = Column(Integer, ForeignKey("services.service_id"))

class Group(Base):
    __tablename__ = "groups"
    group_id = Column(Integer, primary_key=True)
    name = Column(String)
    depart_id = Column(Integer, ForeignKey("departaments.depart_id"))
```

---

## 🐳 Инфраструктура (Docker)

### `docker-compose.yml` содержит:
- `app`: FastAPI приложение
- `db`: PostgreSQL 15
- `pgadmin`: Для удобного просмотра БД
- `bot`: (закомментирован) для запуска бота отдельно

### `Dockerfile`:
- Основан на `python:3.12-slim`
- Установка зависимостей через `requirements.txt`
- Выполнение миграций перед запуском приложения:
  ```bash
  python -m alembic upgrade head
  ```

---

## 🔁 Миграции (Alembic)

- Автоматическое управление версиями БД
- Пример миграции:
  ```bash
  alembic revision --autogenerate -m "Add requests table"
  alembic upgrade head
  ```
- Поддержка downgrade/upgrade

---

## 🚀 Установка и запуск

### 1. Установите зависимости:
```bash
pip install -r requirements.txt
```

### 2. Настройте `.env` или измените `config.py`:
```python
DATABASE_URL=postgresql://root:12345@db:5432/test_postg-db-1
BOT_TOKEN=your_bot_token
```

### 3. Запустите проект через Docker:
```bash
docker-compose up --build
```

---

## ✅ Возможности для доработки

- Реализовать очередь задач (например, Celery).
- Добавить тесты (pytest).
- Улучшить систему уведомлений (email, push).
- Внедрить RBAC на уровне БД.
- Добавить документацию Swagger / ReDoc.
- Подключить CI/CD (GitHub Actions / GitLab CI).

---

## 📌 Лицензия

MIT License — см. [LICENSE](LICENSE)

---

