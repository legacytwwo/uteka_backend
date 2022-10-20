from app import app
from db import get_db
from fastapi import Depends, Header
from services.access import authorization

from sqlalchemy import func
from sqlalchemy.orm import Session

from typing import List
from pydantic import BaseModel
from models.core import Pharmacies, Pagination
from models.core import PharmaciesScheme, PaginationScheme

class Query(BaseModel):
  page: int = 1
  region_id: str
  search: str = None

class ResponsePharmacies(BaseModel):
  response: List[PharmaciesScheme]
  pagination: PaginationScheme = None

@app.get('/api/pharmacies', response_model=ResponsePharmacies)
def route_get_pharmacies(query: Query = Depends(), db: Session = Depends(get_db), token = Header()):
  page = query.page
  search = query.search
  region_id = query.region_id
  
  org = authorization(db, token)
  
  page = page if page > 0 else 1
  
  limit = 5
  result = []
  offset = (page - 1) * limit
  
  query = db.query(Pharmacies)
  query = query.filter(Pharmacies.region_id == region_id)
  
  if search and len(search) >= 3:
    ts_search = Pharmacies.ts_search
    parse = func.parse_websearch(search)
    query = query.filter(ts_search.op('@@')(parse))
  
  query_count = func.count(Pharmacies.created_at)
  query_count = query.with_entities(query_count)
  count = query_count.scalar()
  query = query.limit(limit).offset(offset)
  
  for x in query.all():
    scheme = PharmaciesScheme
    result.append(scheme.from_orm(x).dict())
  
  pagination = Pagination(
    itemCount=count,
    page=page, pageSize=limit
  )
  
  return ResponsePharmacies(
    response=result, pagination=pagination
  )