from db import Base

from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from uuid import UUID as pydantic_UUID
from lib.sqlalchemy import uuid, timestamp
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey

class Pharmacies(Base):
  __tablename__ = 'pharmacies'
  
  id = Column(UUID(as_uuid=True), server_default=uuid(), index=True)
  created_at = Column(DateTime(timezone=False), server_default=timestamp(), index=True)
  updated_at = Column(DateTime(timezone=False), server_default=timestamp(), onupdate=timestamp(), index=True)
  
  title = Column(String(100), nullable=False)
  latitude = Column(Numeric(), nullable=False)
  longitude = Column(Numeric(), nullable=False)
  address = Column(String(250), nullable=False)
  guid = Column(Integer, nullable=False, unique=True, index=True, primary_key=True)
  
  ts_search = Column(TSVectorType('title', 'address'), index=True)
  
  region_id = Column(Integer, ForeignKey('regions.guid', onupdate='CASCADE', ondelete='CASCADE'))

class PharmaciesScheme(BaseModel):
  guid: Optional[int] = None
  title: Optional[str] = None
  address: Optional[str] = None
  region_id: Optional[int] = None
  latitude: Optional[float] = None
  longitude: Optional[float] = None
  id: Optional[pydantic_UUID] = None
  class Config: orm_mode = True