from app import app
from db import get_db
from fastapi import Depends, Header
from services.access import authorization

from typing import List
from pydantic import BaseModel
from models.core import Regions
from sqlalchemy.orm import Session
from models.core import RegionsScheme

available_regions = (
  {'label': 'Курск', 'value': 'kursk'},
  {'label': 'Брянск', 'value': 'bryansk'},
  {'label': 'Белгород', 'value': 'belgorod'}
)

class ResponseRegions(BaseModel):
  response: List[RegionsScheme]

@app.get('/api/regions', response_model=ResponseRegions)
def get_regions(db: Session = Depends(get_db), token = Header()):
  result = []
  org = authorization(db, token)
  query = db.query(Regions).order_by(Regions.active.desc())
  query = query.filter(Regions.active == True)
  for x in query.all():
    scheme = RegionsScheme
    result.append(scheme.from_orm(x).dict())
  return ResponseRegions(response=result)

@app.get('/api/available-regions', response_model=List[dict])
def get_available_regions(db: Session = Depends(get_db), token = Header()):
  org = authorization(db, token)
  return available_regions