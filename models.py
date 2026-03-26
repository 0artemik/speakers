from pydantic import BaseModel
from datetime import datetime
from typing import List
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean

Base = declarative_base()


class Speaker(Base):
	__tablename__ = "speakers"

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, nullable=False)
	embedding = Column(JSON, nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	username = Column(String, unique=True, nullable=False, index=True)
	password_hash = Column(String, nullable=False)
	is_admin = Column(Boolean, default=False, nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)


class SpeakerOut(BaseModel):
	id: int
	name: str
	embedding: List[float]
	created_at: datetime

	class Config:
		from_attributes = True


class UserOut(BaseModel):
	id: int
	username: str
	is_admin: bool
	created_at: datetime

	class Config:
		from_attributes = True

