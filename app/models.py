from sqlalchemy import Boolean, Column, String, Integer, Float, ARRAY, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Service(Base):
    __tablename__ = "services"

    service_id = Column(Integer, primary_key=True, unique=True)
    name = Column(String, nullable=False)

    departments = relationship("Departament", back_populates="service")


class Departament(Base):
    __tablename__ = "departaments"

    depart_id = Column(Integer, primary_key=True, unique=True)
    name = Column(String, nullable=False)
    service_id = Column(Integer, ForeignKey("services.service_id"), nullable=False)

    service = relationship("Service", back_populates="departments")
    groups = relationship("Group", back_populates="department")


class Group(Base):
    __tablename__ = "groups"

    group_id = Column(Integer, primary_key=True, unique=True)
    name = Column(String, nullable=False)
    depart_id = Column(Integer, ForeignKey("departaments.depart_id"), nullable=False)

    department = relationship("Departament", back_populates="groups")
    users = relationship("User", back_populates="group")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    surname = Column(String)
    hashed_password = Column(String)
    rating = Column(Float, index=True, nullable=False)
    education = Column(String, nullable=False)
    job_title = Column(String, index=True)
    work_experience = Column(String)
    hard_skills = Column(ARRAY(String), index=True)
    soft_skills = Column(ARRAY(String), index=True)
    hobby = Column(ARRAY(String), index=True, nullable=True)
    email = Column(String, nullable=False, index=True, unique=True)
    tg_id = Column(String, unique=True)
    role = Column(String)
    tags = Column(ARRAY(String), index=True)
    group_id = Column(Integer, ForeignKey("groups.group_id"), nullable=True)
    disabled = Column(Boolean, default=False)

    group = relationship("Group", back_populates="users")


