from db import Base

from typing import Optional
from pydantic import BaseModel
from uuid import UUID as pydantic_UUID
from lib.sqlalchemy import uuid, timestamp
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey

class Products(Base):
  __tablename__ = 'products'
  
  id = Column(UUID(as_uuid=True), primary_key=True, server_default=uuid(), index=True)
  created_at = Column(DateTime(timezone=False), server_default=timestamp(), index=True)
  updated_at = Column(DateTime(timezone=False), server_default=timestamp(), onupdate=timestamp(), index=True)
  
  guid = Column(Integer, nullable=False)
  min_price = Column(Integer, nullable=False)
  max_price = Column(Integer, nullable=False)
  avg_price = Column(Integer, nullable=False)
  name = Column(String(250), nullable=False, index=True)
  producer = Column(String(250), nullable=False, index=True)
  
  ts_search = Column(TSVectorType('name', 'producer'), index=True)
  
  region_id = Column(Integer, ForeignKey('regions.guid', onupdate='CASCADE', ondelete='CASCADE'))

class ProductsScheme(BaseModel):
  guid: Optional[int] = None
  name: Optional[str] = None
  producer: Optional[str] = None
  region_id: Optional[int] = None
  min_price: Optional[int] = None
  max_price: Optional[int] = None
  avg_price: Optional[int] = None
  id: Optional[pydantic_UUID] = None
  class Config: orm_mode = True