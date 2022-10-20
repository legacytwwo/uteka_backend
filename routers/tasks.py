from app import app
from db import get_db
from fastapi import Depends, Header
from services.access import authorization

from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.core import Tasks
from models.pharmacies import Pharmacies
from models.core import PaginationScheme, Pagination

class Query(BaseModel):
  page: int = 1

class TasksScheme(BaseModel):
  id: Optional[UUID]
  email: Optional[str]
  status: Optional[str]
  address: Optional[str]
  service: Optional[str]
  pharm_id: Optional[int]
  region_id: Optional[int]
  created_at: Optional[datetime]
  class Config: orm_mode = True

class ResponseTasks(BaseModel):
  response: List[TasksScheme]
  pagination: PaginationScheme = None

@app.get('/api/tasks', response_model=ResponseTasks)
def get_tasks(query: Query = Depends(), db: Session = Depends(get_db), token = Header()) -> ResponseTasks:
  page = query.page
  
  org = authorization(db, token)
  
  page = page if page > 0 else 1
  
  limit = 16
  result = []
  offset = (page - 1) * limit
  
  query = db.query(Tasks)
  query = query.filter(Tasks.created_by == org.id)
  
  query_count = func.count(Tasks.created_at)
  query_count = query.with_entities(query_count)
  count = query_count.scalar()
  
  query = query.order_by(Tasks.created_at.desc())
  query = query.limit(limit).offset(offset)
  for x in query.all():
    x.created_at += timedelta(hours=3)
    scheme = TasksScheme.from_orm(x).dict()
    pharm = db.query(Pharmacies)
    pharm = pharm.filter(Pharmacies.guid == x.pharm_id).first()
    if pharm:
      scheme['address'] = pharm.address
    else:
      scheme['address'] = 'Недоступна'
    result.append(scheme)
  
  pagination = Pagination(
    itemCount=count,
    page=page, pageSize=limit
  )
  
  return ResponseTasks(
    response=result, pagination=pagination
  )