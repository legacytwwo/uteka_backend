from db import Base

from typing import Optional
from pydantic import BaseModel

from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import UUID

class Pagination(Base):
  __tablename__ = 'pagination'
  __table_args__ = {'prefixes': ['TEMPORARY']}
  id = Column(UUID(as_uuid=True), primary_key=True)
  page = Column(Integer, default=1)
  pageSize = Column(Integer, default=50)
  itemCount = Column(Integer, default=0)
  @property
  def pageCount(self):
    if not self.itemCount:
      return 1
    elif self.itemCount > 0:
      return self.itemCount / self.pageSize


class PaginationScheme(BaseModel):
  page: Optional[int] = 1
  pageSize: Optional[int] = None
  itemCount: Optional[int] = None
  class Config: orm_mode = True