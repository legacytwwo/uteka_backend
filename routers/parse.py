import requests
from os import environ
from dotenv import load_dotenv

from os import path
from sys import exc_info

from json import dumps
from uuid import UUID, uuid4

from app import app
from db import get_db
from celery_app import celery
from sqlalchemy.orm import Session
from fastapi import Depends, Header

from tasks.task import db_add_task
from tasks.task import db_update_task
from tasks.task import db_get_tasks_by_id

from pydantic import BaseModel
from oslash import Right, Left
from typing import List, Optional
from datetime import datetime, timedelta
from services.access import authorization

import smtplib
import ssl, csv
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

load_dotenv()

class ProductModel(BaseModel):
  guid: int
  name: str
  price: int
  country: Optional[str]
  GRLSUrl: Optional[str]
  producer: Optional[str]
  reviewCount: Optional[int]
  reviewRating: Optional[float]

class Uteka():
  timeout = 15
  site_url = 'https://uteka.ru/rpc/?method='
  headers = {'Content-Type': 'application/json'}

  def __init__(self, proxy=environ["PROXY"]):
    self.http = requests.Session()
    self.http.proxies = {'https': proxy}

  def set_context(self, region_id: int, pharmacy_id: int, new_uuid: str) -> bool:
    body = {
      "id": "1",
      "jsonrpc": "2.0",
      "method": "cart.SetContext",
      "params": {
        "cartId": new_uuid,
        "cityId": region_id,
        "cartContext": {
          "pharmacies": {
            "pharmacyIds": [
              pharmacy_id
            ],
            "pickupOnly": True
          }
        },
        "options": {
          "isPartial": True
        },
        "deliveryType": 11
      }
    }
    
    try:
      response = self.http.post(
        url=f'{self.site_url}cart.SetContext',
        headers=self.headers, data=dumps(body), timeout=self.timeout
      )
    except Exception:
      self.http = requests.Session()
      self.http.proxies = {'https': environ["PROXY"]}
      response = self.http.post(
        url=f'{self.site_url}cart.SetContext',
        headers=self.headers, data=dumps(body), timeout=self.timeout
      )
    
    if response.ok:
      data = response.json()
      if data['result']['result']:
        data = data['result']['cartContext']['pharmacies']
        if data['pharmacyCount'] > 0:
          return Right(True)
        else:
          return Left(True)
    
  def get_categories(self, region_id: int) -> 'list[int]':
    body = {
      "id": 211,
      "jsonrpc": "2.0",
      "method": "catalogue.Categories",
      "params": {
        "cityId": region_id
      }
    }
    
    try:
      response = self.http.post(
        url=f'{self.site_url}catalogue.Categories',
        data=dumps(body), timeout=self.timeout, headers=self.headers
      )
    except Exception:
      self.http = requests.Session()
      self.http.proxies = {'https': environ["PROXY"]}
      response = self.http.post(
        url=f'{self.site_url}catalogue.Categories',
        data=dumps(body), timeout=self.timeout, headers=self.headers
      )
    
    if response.ok:
      data = response.json()
      if data['result']:
        result = []
        data = data['result']
        for i in data:
          result.append(i['categoryId'])
        return result

  def get_products(self, region_id: int, new_uuid: str) -> 'list[ProductModel]':
    result = []
    categories = self.get_categories(region_id)
    for category in categories:
      counter = 0
      while True:
        body = [
          {
            "jsonrpc": "2.0",
            "id": 118,
            "method": "products.Get",
            "params": {
              "page": counter,
              "pageSize": 100,
              "search": {
                "cartId": new_uuid,
                "cityId": region_id,
                "showDisabled": False,
                "categoryId": int(category),
                "withChildCategories": True,
              }
            }
          }
        ]
        
        try:
          response = self.http.post(
            headers=self.headers, timeout=self.timeout,
            url=f'{self.site_url}products.Get', data=dumps(body)
          )
        except Exception:
          self.http = requests.Session()
          self.http.proxies = {'https': environ["PROXY"]}
          response = self.http.post(
            headers=self.headers, timeout=self.timeout,
            url=f'{self.site_url}products.Get', data=dumps(body)
          )
        
        if response.ok:
          data = response.json()
          if data[0]['result']:
            data = data[0]['result']
            
            for i in data:
              if i['isAvailable'] == False:
                break
              elif i['isAvailable'] == True:
                model = ProductModel(
                  guid = i["productId"],
                  name = i["fullTitle"],
                  price = i["avgPrice"],
                  country = i["country"],
                  GRLSUrl = i['GRLSUrl'],
                  producer = i["producer"],
                  reviewCount = i['reviewCount'],
                  reviewRating = i['reviewRating'],
                )
                result.append(model)
            
            if len(data) == 100:
              counter += 1
            elif len(data) < 100:
              break
          else:
            break
        else:
          break
    return Right(result)

  def get_csv(self, result: 'list[ProductModel]') -> str:
    import xlsxwriter
    row = 0
    col = 0
    utc = datetime.utcnow()
    workbook = xlsxwriter.Workbook(f'files/{str(utc + timedelta(hours=3))}.xlsx')
    worksheet = workbook.add_worksheet()
    #
    header = ['GUID', 'NAME', 'COUNTRY', 'PRODUCER', 'PRICE', 'ReviewCount', 'ReviewRating', 'GRLSUrl']
    worksheet.write_row(row, col, header)
    #
    for x in result:
      row += 1
      data_row = [x.guid, x.name, x.country, x.producer, x.price, x.reviewCount, x.reviewRating, x.GRLSUrl]
      
      worksheet.write_row(row, col, data_row)
    workbook.close()
    return Right(workbook.filename)

  def send_email(self, receiver: str, file_name: str, pharmacy_id: int) -> bool:
    receiver = receiver
    msg = MIMEMultipart()
    password = environ["EMAIL_PASSWORD"]
    sender = environ["EMAIL_USER"]
    subject = f'UTEKA PARSING FOR ID: {pharmacy_id}'
    
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject
    
    with open(file_name,'rb') as file:
      msg.attach(MIMEApplication(file.read(), Name=file_name))
    
    context = ssl.create_default_context()
    
    with smtplib.SMTP_SSL('smtp.gmail.com', port=465, context=context) as smtp:
      smtp.login(sender, password)
      smtp.sendmail(sender, receiver, msg.as_string())
    return Right(True)
  
  def products_by_pharmacy(self, region_id: int, pharmacy_id: int, email: str, org: UUID) -> None:
    try:
      task = db_add_task('GET PRODUCTS BY PHARMACY')
      
      task.email = email
      task.created_by = org
      task.service = 'UTEKA'
      task.region_id = region_id
      task.pharm_id = pharmacy_id
      
      db_update_task(task)
      
      new_uuid = str(uuid4())
      context = self.set_context(region_id, pharmacy_id, new_uuid)
      
      if isinstance(context, Right):
        products = self.get_products(region_id, new_uuid)
      
      if isinstance(products, Right):
        file = self.get_csv(products.value)
      
      if isinstance(file, Right):
        email = self.send_email(email, file.value, pharmacy_id)
      
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
  region_id: int
  pharmacy_ids: List[int]

@app.post('/api/pharmacies-products', response_model=dict)
def route_get_products_by_pharmacy(body: Query, db: Session = Depends(get_db), token = Header()):
  org = authorization(db, token)
  for id in body.pharmacy_ids:
    get_pharmacy_products.apply_async(args=[body.region_id, id, body.email, org.id])
  return {'status': True}

@app.post('/api/retry-tasks', response_model=dict)
def route_retry_tasks(body: List[UUID], db: Session = Depends(get_db), token = Header()):
  org = authorization(db, token)
  tasks = db_get_tasks_by_id(body)
  for task in tasks:
    get_pharmacy_products.apply_async(args=[task.region_id, task.pharm_id, task.email, org.id])
  return {'status': True}

@celery.task(bind=True, soft_time_limit=15*60, default_retry_delay=30, max_retries=1)
def get_pharmacy_products(self, region_id: int, pharmacy_id: int, email: str, org: UUID):
  try:
    uteka = Uteka()
    uteka.products_by_pharmacy(region_id, pharmacy_id, email, org)
  except Exception as err:
    raise self.retry(exc=err)