from os import path
from time import sleep
import requests as http
from sys import exc_info

from app import app
from db import get_db
from celery_app import celery
from sqlalchemy.orm import Session
from fastapi import Depends, Header

from services.csv import get_csv
from services.email import send_email

from tasks.task import db_add_task
from tasks.task import db_update_task

from uuid import UUID
from pydantic import BaseModel
from oslash import Right, Left
from services.access import authorization

class AptekaRu:
  timeout = 15
  scrapyd_url = 'http://10.42.0.109:6800/'

  def __init__(self, service: str) -> None:
    self.service = service
  
  def send_request_scrapyd(self, region: str):
    url = f'{self.scrapyd_url}schedule.json?project={self.service}&spider={self.service}&city={region}'
    response = http.post(url, timeout=self.timeout)
    if response.ok:
      data = response.json()
      if data['status'] == 'ok':
        return Right(data['jobid'])
  
  def scheck_jobid(self, jobid: str):
    url = f'{self.scrapyd_url}listjobs.json?project={self.service}'
    response = http.get(url, timeout=self.timeout)
    if response.ok:
      data = response.json()
      if data['status'] == 'ok':
        for i in data['finished']:
          if i['id'] == jobid:
            return Right(True)
        return Left(False)
  
  def get_products(self, jobid: str):
    url = f'{self.scrapyd_url}items/{self.service}/{self.service}/{jobid}.json'
    response = http.get(url, timeout=self.timeout)
    if response.ok:
      data = response.json()
      return Right(data)
  
  def get_products(self, region: str, service: str, email: str, org: UUID):
    try:
      task = db_add_task(f'GET PRODUCTS BY {service}')
      
      task.email = email
      task.created_by = org
      task.service = service
      
      db_update_task(task)
      jobid = self.send_request_scrapyd(region)
      if isinstance(jobid, Right):
        finished = self.scheck_jobid(jobid.value)
        while not isinstance(finished, Right):
          sleep(30)
          finished = self.scheck_jobid(jobid.value)
      if isinstance(finished, Right):
        products = self.get_products(jobid.value)
      if isinstance(products, Right):
        file = get_csv(products.value)
      if isinstance(file, Right):
        email = send_email(email, file.value)
      if isinstance(email, Right):
        task.status = 'COMPLETE'
        db_update_task(task)
    except Exception as error:
      traceback = exc_info()[2]
      fname = path.split(traceback.tb_frame.f_code.co_filename)[1]
      error_status = f'File: {fname}; Line: {traceback.tb_lineno}; Error: {error}'
      task.error_status = error_status
      task.status = 'ERROR'
      db_update_task(task)

class Query(BaseModel):
  email: str
  region: str
  service: str

@app.post('/api/products-by-service', response_model=dict)
def route_get_products_from_service(body: Query, db: Session = Depends(get_db), token = Header()):
  org = authorization(db, token)
  get_products_from_service.apply_async(args=[body.region, body.service, body.email, org.id])
  return {'status': True}

@celery.task(bind=True, soft_time_limit=15*60, default_retry_delay=30, max_retries=1)
def get_products_from_service(self, region: str, service: str, email: str, org: UUID):
  try:
    aptekaru = AptekaRu(service)
    aptekaru.get_products(region, service, email, org)
  except Exception as err:
    raise self.retry(exc=err)