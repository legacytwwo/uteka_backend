from app import app
from db import get_db
from fastapi import Depends, Header
from services.access import authorization

from sqlalchemy import func
from sqlalchemy.orm import Session

from typing import List
from pydantic import BaseModel
from models.core import Pagination, Products
from models.core import PaginationScheme, ProductsScheme

class Query(BaseModel):
  page: int = 1
  region_id: str
  search: str = None

class ResponseProducts(BaseModel):
  response: List[ProductsScheme]
  pagination: PaginationScheme = None

@app.get('/api/products', response_model=ResponseProducts)
def route_get_products(query: Query = Depends(), db: Session = Depends(get_db), token = Header()):
  page = query.page
  search = query.search
  region_id = query.region_id

  org = authorization(db, token)
  
  page = page if page > 0 else 1
  
  limit = 20
  result = []
  offset = (page - 1) * limit
  
  query = db.query(Products)
  query = query.filter(Products.region_id == region_id)
  
  if search and len(search) >= 3:
    ts_search = Products.ts_search
    parse = func.parse_websearch(search)
    query = query.filter(ts_search.op('@@')(parse))
  
  query_count = func.count(Products.created_at)
  query_count = query.with_entities(query_count)
  count = query_count.scalar()
  query = query.order_by(Products.name.asc())
  query = query.limit(limit).offset(offset)
  
  for x in query.all():
    scheme = ProductsScheme
    result.append(scheme.from_orm(x).dict())
  
  pagination = Pagination(
    itemCount=count,
    page=page, pageSize=limit
  )
  
  return ResponseProducts(
    response=result, pagination=pagination
  )