from app import app
from db import get_db
from os import system
from fastapi import Depends, Header, HTTPException

from sqlalchemy.orm import Session

from services.access import login
from services.access import authorization

from typing import Optional
from pydantic import BaseModel, validator
from models.core import OrganizationsScheme

class Email(BaseModel):
  email: str 

class Login(BaseModel):
  login: Optional[str] = None
  password: Optional[str] = None

  @validator('login', 'password', pre=True)
  def model_validator(cls, value):
    if not value:
      raise HTTPException(status_code=403, detail='Заполните поле "Login" и "Password')
    return value

@app.post('/api/login', response_model=OrganizationsScheme)
def route_login(body: Login, db: Session = Depends(get_db)):
  org = login(db, body.login, body.password)
  return OrganizationsScheme.from_orm(org)

@app.post('/api/auth', response_model=OrganizationsScheme)
def route_auth(db: Session = Depends(get_db), token = Header()):
  org = authorization(db, token)
  return OrganizationsScheme.from_orm(org)

@app.post('/api/change-email', response_model=OrganizationsScheme)
def route_auth(email: Email, db: Session = Depends(get_db), token = Header()):
  org = authorization(db, token)
  org.email = email.email
  db.commit()
  return OrganizationsScheme.from_orm(org)

@app.get('/api/restart-celery', include_in_schema=False)
def restart_service_celery(db: Session = Depends(get_db), token = Header()):
  org = authorization(db, token)
  if org.admin:
    cmd = 'sudo service uteka.celery restart'
    system(cmd)
  return None

@app.get('/api/restart-fastapi', include_in_schema=False)
def restart_service_fastapi(db: Session = Depends(get_db), token = Header()):
  org = authorization(db, token)
  if org.admin:
    cmd = 'sudo service uteka.server restart'
    system(cmd)
  return None