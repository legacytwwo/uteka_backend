from db import Base

from typing import Optional
from pydantic import BaseModel
from uuid import UUID as pydantic_UUID
from sqlalchemy.orm import relationship
from lib.sqlalchemy import uuid, timestamp
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy import Column, String, DateTime, Integer, Boolean

class Regions(Base):
  __tablename__ = 'regions'
  
  id = Column(UUID(as_uuid=True), server_default=uuid(), index=True)
  created_at = Column(DateTime(timezone=False), server_default=timestamp(), index=True)
  updated_at = Column(DateTime(timezone=False), server_default=timestamp(), onupdate=timestamp(), index=True)
  
  title = Column(String(100), nullable=False)
  active = Column(Boolean, server_default='false')
  guid = Column(Integer, primary_key=True, nullable=False, unique=True, index=True)
  
  ts_search = Column(TSVectorType('title'), index=True)
  
  pharmacies = relationship('Pharmacies', lazy='select', foreign_keys='[Pharmacies.region_id]')
  
  products = relationship('Products', lazy='select', foreign_keys='[Products.region_id]')
  @property
  def label(self):
    return self.title

class RegionsScheme(BaseModel):
  guid: Optional[int] = None
  title: Optional[str] = None
  active: Optional[bool] = None
  id: Optional[pydantic_UUID] = None
  class Config: orm_mode = True