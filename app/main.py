from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta
import uvicorn
from sqlalchemy.orm import Session

from app.models import User, Base, Service, Departament, Group
from app.database import engine
from app.schemas import UserCreate, UserOut, Token, ServiceCreate, ServiceSchema, DepartmentCreate, GroupCreate, \
    GroupSchema, DepartmentSchema
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


@app.post("/services/", response_model=ServiceSchema)
async def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

