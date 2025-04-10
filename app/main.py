from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, Optional
from datetime import timedelta
import uvicorn
import re
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

from app.models import User, Base, Service, Departament, Group
from app.models import Request as RequestModel
from app.database import engine
from app.schemas import UserCreate, UserOut, Token, ServiceSchema, \
    GroupSchema, DepartmentSchema, UserGroupUpdate, GroupWithUsers, DepartmentCreate, ServiceCreate, GroupCreate, \
    GroupUpdate, DepartmentUpdate, ServiceUpdate, UserDisabledUpdate
from app.auth import (
    get_db,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash,
    get_current_active_user
)

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Настройки
BOT_TOKEN = "7978079024:AAEMjRp68zWXbLtV5W4zjqcXQfEyQCzTAwI"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://d80vzq-188-162-12-160.ru.tuna.am" + WEBHOOK_PATH
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = 8000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def parse_application(text: str) -> Optional[dict]:
    try:
        # Используем регулярные выражения для извлечения данных
        title_match = re.search(r'title:\s*(.+?)(?=\n|$)', text, re.IGNORECASE)
        desc_match = re.search(r'description:\s*(.+?)(?=\n|$)', text, re.IGNORECASE)
        tags_match = re.search(r'tags:\s*(.+?)(?=\n|$)', text, re.IGNORECASE)

        if not all([title_match, desc_match, tags_match]):
            return None

        # Очистка и обработка тегов
        tags = [tag.strip() for tag in tags_match.group(1).split(',') if tag.strip()]

        return {
            'title': title_match.group(1).strip(),
            'description': desc_match.group(1).strip(),
            'tags': tags
        }
    except Exception as e:
        logger.error(f"Parse error: {e}")
        return None


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    help_text = (
        "📝 Отправьте заявку в формате:\n\n"
        "title: Ваш заголовок\n"
        "description: Ваше описание\n"
        "tags: тег1, тег2\n\n"
        "Пример:\n"
        "title: Проблема с доступом\n"
        "description: Не могу зайти в систему\n"
        "tags: доступ, авторизация"
    )
    await message.answer(help_text)


@dp.message(F.text)
async def handle_application(
        message: types.Message,
        db: Session = Depends(get_db)
):
    user_input = message.text
    parsed_data = parse_application(user_input)

    if not parsed_data:
        await message.answer(
            "❌ Неверный формат заявки. Используйте:\n\n"
            "title: ...\ndescription: ...\ntags: ..."
        )
        return

    try:
        # Сохранение в базу
        db_request = RequestModel(
            title=parsed_data['title'],
            description=parsed_data['description'],
            tags=parsed_data['tags'],
            user_id=message.from_user.id,
            raw_text=user_input,
            status="new"
        )

        db.add(db_request)
        db.commit()

        await message.answer(
            "✅ Заявка принята!\n\n"
            f"Заголовок: {parsed_data['title']}\n"
            f"Описание: {parsed_data['description']}\n"
            f"Теги: {', '.join(parsed_data['tags'])}"
        )
    except Exception as e:
        logger.error(f"Database error: {e}")
        await message.answer("⚠️ Ошибка при сохранении заявки")


@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    yield
    await bot.session.close()



@app.post("/register", response_model=UserOut)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    if user_data.tg_id:
        db_user_tg = db.query(User).filter(User.tg_id == user_data.tg_id).first()
        if db_user_tg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram ID already registered"
            )

    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        surname=user_data.surname,
        hashed_password=hashed_password,
        rating=user_data.rating,
        education=user_data.education,
        job_title=user_data.job_title,
        work_experience=user_data.work_experience,
        hard_skills=user_data.hard_skills,
        soft_skills=user_data.soft_skills,
        hobby=user_data.hobby,
        tg_id=user_data.tg_id,
        role=user_data.role.value,
        tags=user_data.tags,
        group_id=user_data.group_id,
        disabled=user_data.disabled
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": user.email},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=UserOut)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


@app.get("/users/", response_model=list[UserOut])
async def get_users(
        db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users


@app.post("/services/", response_model=ServiceSchema)
async def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["ADMIN", "HR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN or HR can change user groups"
        )

    db_service = Service(name=service.name)
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


@app.post("/departments/", response_model=DepartmentSchema)
async def create_department(
        department: DepartmentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):

    if current_user.role not in ["ADMIN", "HR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN or HR can change user groups"
        )

    db_service = db.query(Service).filter(Service.service_id == department.service_id).first()
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")

    db_department = Departament(
        name=department.name,
        service_id=department.service_id
    )
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department


@app.post("/groups/", response_model=GroupSchema)
async def create_group(
        group: GroupCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["ADMIN", "HR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN or HR can change user groups"
        )

    db_department = db.query(Departament).filter(Departament.depart_id == group.depart_id).first()
    if not db_department:
        raise HTTPException(status_code=404, detail="Department not found")

    db_group = Group(
        name=group.name,
        depart_id=group.depart_id
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


@app.get("/services/", response_model=list[ServiceSchema])
async def read_services(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    services = db.query(Service).offset(skip).limit(limit).all()
    return services

@app.get("/departments/", response_model=list[DepartmentSchema])
async def read_departments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    departments = db.query(Departament).offset(skip).limit(limit).all()
    return departments

@app.get("/groups/", response_model=list[GroupSchema])
async def read_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    groups = db.query(Group).offset(skip).limit(limit).all()
    return groups


@app.get("/groups/{group_id}/users", response_model=GroupWithUsers)
async def get_group_with_users(
        group_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    db_group = db.query(Group).filter(Group.group_id == group_id).first()
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    users = db.query(User).filter(User.group_id == group_id).all()

    group_data = {
        "group_id": db_group.group_id,
        "name": db_group.name,
        "depart_id": db_group.depart_id,
        "users": users
    }

    return group_data


@app.put("/users/{user_id}/disabled", response_model=UserOut)
async def update_user_disabled(
        user_id: int,
        disabled_update: UserDisabledUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Обновить статус активности пользователя

    - **user_id**: ID пользователя
    - **disabled**: True - деактивировать, False - активировать
    """
    if current_user.role not in ["ADMIN", "HR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN or HR can change user status"
        )

    # Находим пользователя
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Обновляем статус
    db_user.disabled = disabled_update.disabled
    db.commit()
    db.refresh(db_user)

    return db_user


@app.put("/users/{user_id}/group", response_model=UserOut)
async def update_user_group(
        user_id: int,
        group_update: UserGroupUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["ADMIN", "HR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN or HR can change user groups"
        )

    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if group_update.group_id is not None:
        db_group = db.query(Group).filter(Group.group_id == group_update.group_id).first()
        if not db_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group not found"
            )

    db_user.group_id = group_update.group_id
    db.commit()
    db.refresh(db_user)
    return db_user


@app.put("/services/{service_id}", response_model=ServiceSchema)
async def update_service(
        service_id: int,
        service_update: ServiceUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):

    if current_user.role not in ["ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can update services"
        )

    db_service = db.query(Service).filter(Service.service_id == service_id).first()
    if not db_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    db_service.name = service_update.name
    db.commit()
    db.refresh(db_service)
    return db_service


@app.put("/departments/{department_id}", response_model=DepartmentSchema)
async def update_department(
        department_id: int,
        department_update: DepartmentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):

    if current_user.role not in ["ADMIN", "HR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN or HR can update departments"
        )

    db_department = db.query(Departament).filter(Departament.depart_id == department_id).first()
    if not db_department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    db_department.name = department_update.name
    db.commit()
    db.refresh(db_department)
    return db_department


@app.put("/groups/{group_id}", response_model=GroupSchema)
async def update_group(
        group_id: int,
        group_update: GroupUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Обновить название группы

    - **group_id**: ID группы для обновления
    - **name**: Новое название группы
    """
    if current_user.role not in ["ADMIN", "HR", "MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN, HR or MANAGER can update groups"
        )

    db_group = db.query(Group).filter(Group.group_id == group_id).first()
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    db_group.name = group_update.name
    db.commit()
    db.refresh(db_group)
    return db_group


@app.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Удаление сервиса
    - Только для ADMIN
    - Проверка на существование связанных департаментов
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can delete services"
        )

    db_service = db.query(Service).filter(Service.service_id == service_id).first()
    if not db_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    # Проверяем есть ли связанные департаменты
    if db.query(Departament).filter(Departament.service_id == service_id).count() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete service with linked departments"
        )

    db.delete(db_service)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Удаление департамента
    - Для ADMIN и HR
    - Проверка на существование связанных групп
    """
    if current_user.role not in ["ADMIN", "HR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN or HR can delete departments"
        )

    db_department = db.query(Departament).filter(Departament.depart_id == department_id).first()
    if not db_department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Проверяем есть ли связанные группы
    if db.query(Group).filter(Group.depart_id == department_id).count() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete department with linked groups"
        )

    db.delete(db_department)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Удаление группы
    - Для ADMIN, HR и MANAGER
    - Проверка на существование связанных пользователей
    """
    if current_user.role not in ["ADMIN", "HR", "MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN, HR or MANAGER can delete groups"
        )

    db_group = db.query(Group).filter(Group.group_id == group_id).first()
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    if db.query(User).filter(User.group_id == group_id).count() > 0:
        user = db.query(User).filter(User.group_id == group_id).first()
        user.group_id = None
        db.commit()
        # raise HTTPException(
        #     status_code=status.HTTP_400_BAD_REQUEST,
        #     detail="Cannot delete group with assigned users"
        # )

    db.delete(db_group)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        reload=True
    )