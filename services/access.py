from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.core import Organizations

def authorization(db: Session, token: str):
  if not token:
    raise HTTPException(status_code=403, detail="Ошибка авторизации")
  ############
  query = db.query(Organizations)
  query = query.filter(Organizations.active == True)
  query = query.filter(Organizations.token == token)
  query_result = query.first()
  ############
  if query_result == None:
    raise HTTPException(status_code=403, detail="Ошибка авторизации")
  elif not query_result == None:
    return query_result
  ############

def login(db: Session, login: str, password: str):
  query = db.query(Organizations)
  query = query.filter(Organizations.login == login)
  query = query.filter(Organizations.active == True)
  query = query.filter(Organizations.password == password)
  query_result = query.first()
  ############
  if query_result == None:
    raise HTTPException(status_code=403, detail="Ошибка авторизации")
  elif not query_result == None:    
    return query_result
  ############