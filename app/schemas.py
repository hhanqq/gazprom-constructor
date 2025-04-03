from typing import List, Optional
from pydantic import BaseModel, EmailStr, validator
from enum import Enum

class RoleEnum(str, Enum):
    HR = "HR"
    DEVELOPER = "Developer"
    ADMIN = "Admin"

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str
    surname: Optional[str] = None
    rating: float = 0.0
    education: str
    job_title: str
    work_experience: str
    hard_skills: List[str] = []
    soft_skills: List[str] = []
    hobby: Optional[List[str]] = None
    tg_id: str
    role: RoleEnum
    tags: List[str] = []
    group_id: Optional[int] = None
    disabled: bool = False

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class UserOut(UserBase):
    user_id: int
    surname: Optional[str]
    rating: float
    education: str
    job_title: str
    work_experience: str
    hard_skills: List[str]
    soft_skills: List[str]
    hobby: Optional[List[str]]
    tg_id: str
    role: RoleEnum
    tags: List[str]
    group_id: Optional[int]
    disabled: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


class ServiceSchema(BaseModel):
    service_id: int
    name: str

    class Config:
        orm_mode = True

class DepartmentSchema(BaseModel):
    depart_id: int
    name: str
    service_id: int

    class Config:
        orm_mode = True

class GroupSchema(BaseModel):
    group_id: int
    name: str
    depart_id: int

    class Config:
        orm_mode = True



class ServiceCreate(BaseModel):
    name: str

class DepartmentCreate(BaseModel):
    name: str
    service_id: int

class GroupCreate(BaseModel):
    name: str
    depart_id: int