from typing import List, Optional, Dict, Union
from pydantic import BaseModel, EmailStr, validator, Field, ConfigDict
from enum import Enum


class RoleEnum(str, Enum):
    HR = "HR"
    DEVELOPER = "Developer"
    ADMIN = "Admin"


class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    first_name: str = Field(..., min_length=1, max_length=50, example="John")
    last_name: str = Field(..., min_length=1, max_length=50, example="Doe")

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="SecurePass123")
    surname: Optional[str] = Field(None, max_length=50, example="Smith")
    rating: float = Field(0.0, ge=0.0, le=5.0, example=4.5)
    education: str = Field(..., example="Moscow State University")
    job_title: str = Field(..., example="Backend Developer")
    work_experience: str = Field(..., example="3 years as Python developer")
    hard_skills: List[str] = Field(default_factory=list, example=["Python", "Docker"])
    soft_skills: List[str] = Field(default_factory=list, example=["Teamwork", "Communication"])
    hobby: Optional[List[str]] = Field(None, example=["Reading", "Hiking"])
    tg_id: str = Field(..., example="123456789")
    role: RoleEnum = Field(..., example=RoleEnum.DEVELOPER)
    tags: List[str] = Field(default_factory=list, example=["Python", "FastAPI"])
    group_id: Optional[int] = Field(None, example=1)
    disabled: bool = Field(False)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserOut(UserBase):
    user_id: int = Field(..., example=1)
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


class UserGroupUpdate(BaseModel):
    group_id: Optional[int] = Field(
        None,
        description="ID группы (null для удаления из группы)",
        example=1
    )


class Token(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(..., example="bearer")


class TokenData(BaseModel):
    email: Optional[str] = None


class ServiceBase(BaseModel):
    name: str = Field(..., example="IT Services")


class ServiceCreate(ServiceBase):
    pass


class ServiceSchema(ServiceBase):
    service_id: int = Field(..., example=1)
    model_config = ConfigDict(from_attributes=True)


class DepartmentBase(BaseModel):
    name: str = Field(..., example="Backend Development")
    service_id: int = Field(..., example=1)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentSchema(DepartmentBase):
    depart_id: int = Field(..., example=1)
    model_config = ConfigDict(from_attributes=True)


class GroupBase(BaseModel):
    name: str = Field(..., example="Python Team")
    depart_id: int = Field(..., example=1)


class GroupCreate(GroupBase):
    pass


class GroupSchema(GroupBase):
    group_id: int = Field(..., example=1)
    model_config = ConfigDict(from_attributes=True)


class GroupWithUsers(GroupSchema):
    users: List[UserOut] = Field(default_factory=list)



class ServiceUpdate(BaseModel):
    name: str = Field(..., example="Updated Service Name")

class DepartmentUpdate(BaseModel):
    name: str = Field(..., example="Updated Department Name")

class GroupUpdate(BaseModel):
    name: str = Field(..., example="Updated Group Name")


class UserDisabledUpdate(BaseModel):
    disabled: bool = Field(..., example=True)