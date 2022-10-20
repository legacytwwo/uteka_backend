from db import Base

from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID as pydantic_UUID

from sqlalchemy.orm import relationship
from lib.sqlalchemy import uuid, timestamp
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey

class Tasks(Base):
  __tablename__ = 'tasks'
  
  id = Column(UUID(as_uuid=True), primary_key=True, server_default=uuid(), index=True)
  created_at = Column(DateTime(timezone=False), server_default=timestamp(), index=True)
  updated_at = Column(DateTime(timezone=False), server_default=timestamp(), onupdate=timestamp(), index=True)
  
  pharm_id = Column(Integer)
  email = Column(String(250))
  region_id = Column(Integer)
  service = Column(String(150))
  task_name = Column(String(500))
  error_status = Column(String(500))
  status = Column(String(100), nullable=False)
  
  created_by = Column(UUID(as_uuid=True), ForeignKey('organizations.id', onupdate='CASCADE', ondelete='CASCADE'))
  @property
  def label(self):
    return self.task_name

class TasksScheme(BaseModel):
  email: Optional[str] = None
  service: Optional[str] = None
  pharm_id: Optional[int] = None
  region_id: Optional[int] = None
  task_name: Optional[str] = None
  status: Optional[str] = 'WAITING'
  id: Optional[pydantic_UUID] = None
  error_status: Optional[str] = None
  created_at: Optional[datetime] = None
  created_by: Optional[pydantic_UUID] = None
  class Config: orm_mode = True