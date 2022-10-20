from db import Base

from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID as pydantic_UUID

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from lib.sqlalchemy import uuid, timestamp, token
from sqlalchemy import Boolean, Column, String, DateTime

class Organizations(Base):
  __tablename__ = 'organizations'
  
  id = Column(UUID(as_uuid=True), primary_key=True, server_default=uuid(), index=True)
  created_at = Column(DateTime(timezone=False), server_default=timestamp(), index=True)
  updated_at = Column(DateTime(timezone=False), server_default=timestamp(), onupdate=timestamp(), index=True)
  
  password = Column(String(100), nullable=False)
  login = Column(String(100), nullable=False, unique=True)
  
  name = Column(String(250))
  email = Column(String(250))
  admin = Column(Boolean, server_default='false')
  active = Column(Boolean, server_default='true')
  token = Column(String(50), server_default=token(50), unique=True)
  
  tasks = relationship('Tasks', lazy='select', foreign_keys='[Tasks.created_by]')
  @property
  def label(self):
    return self.name

class OrganizationsScheme(BaseModel):
  id: Optional[pydantic_UUID] = None
  name: Optional[str] = None
  token: Optional[str] = None
  email: Optional[str] = None
  active: Optional[bool] = True
  created_at: Optional[Any] = None
  login: Optional[str] = None
  token: Optional[str] = None
  admin: Optional[bool] = False
  password: Optional[str] = None
  class Config: orm_mode = True