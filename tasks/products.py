import requests
from os import environ
from dotenv import load_dotenv

from db import get_db
from json import dumps

from os import path
from oslash import Right
from sys import exc_info
from celery_app import celery
from contextlib import contextmanager

from tasks.task import db_add_task
from tasks.task import db_update_task

from pydantic import BaseModel
from models.core import Regions
from models.core import Products
from models.core import ProductsScheme

load_dotenv()

class ProductModel(BaseModel):
  guid: int
  name: str
  producer: str
  min_price: int
  max_price: int
  avg_price: int
  region_id: int

class UtekaProducts():
  timeout = 15
  site_url = 'https://uteka.ru/rpc/?method='
  headers = {'Content-Type': 'application/json'}

  def __init__(self, proxy=environ["PROXY"]):
    self.http = requests.Session()
    self.http.proxies = {'https': proxy}

  def get_products_from_uteka(self, categories: 'list[int]', city_id: int) -> 'list[ProductModel]':
    result = []
    for category in categories:
      counter = 0
      while True:
        body = [{
          "jsonrpc": "2.0",
          "id": 118,
          "method": "products.Get",
          "params": {
            "page": counter,
            "pageSize": 100,
            "search": {
              "cityId": city_id,
              "categoryId": int(category),
              "withChildCategories": True,
            }
          }
        }]

        try:
          response = self.http.post(
            headers=self.headers, timeout=self.timeout,
            url=f'{self.site_url}pharmacies.Get', data=dumps(body),
          )
        except Exception:
          self.http = requests.Session()
          self.http.proxies = {'https': environ["PROXY"]}
          response = self.http.post(
            headers=self.headers, timeout=self.timeout,
            url=f'{self.site_url}pharmacies.Get', data=dumps(body),
          )

        if response.ok:
          data = response.json()
          if data[0]['result']:
            data = data[0]['result']
            for i in data:
              model = ProductModel(
                region_id=city_id,
                guid = i["productId"],
                name = i["fullTitle"],
                min_price = i["minPrice"],
                max_price = i["maxPrice"],
                avg_price = i["avgPrice"],
                producer = i["fullProducer"],
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

  def get_categories(self, city_id: int) -> 'list[int]':
    body = {
      "id": 211,
      "jsonrpc": "2.0",
      "method": "catalogue.Categories",
      "params": {
        "cityId": city_id
      }
    }
    try:
      response = self.http.post(
        headers=self.headers, timeout=self.timeout,
        url=f'{self.site_url}catalogue.Categories', data=dumps(body),
      )
    except Exception:
      self.http = requests.Session()
      self.http.proxies = {'https': environ["PROXY"]}
      response = self.http.post(
        headers=self.headers, timeout=self.timeout,
        url=f'{self.site_url}catalogue.Categories', data=dumps(body),
      )
    if response.ok:
      data = response.json()
      if data['result']:
        result = []
        data = data['result']
        for i in data:
          result.append(i['categoryId'])
        return result

  def db_delete_products(self, region_id: int) -> None:
    with contextmanager(get_db)() as session:
      session.query(Products).filter(Products.region_id == region_id).delete()
      session.commit()

  def db_add_products(self, region_id: int, result: 'list[ProductsScheme]') -> None:
    self.db_delete_products(region_id)
    with contextmanager(get_db)() as session:
      for products in result:
        record = Products(**products.dict())
        record = session.merge(record)
      session.commit()
    return Right(True)
  
  def db_get_city_ids(self) -> None:
    ids = []
    with contextmanager(get_db)() as session:
      query = session.query(Regions)
      query = query.filter(Regions.active == True)
      for region in query.all():
        ids.append(region.guid)
    return ids
  
  def products(self) -> None:
    try:
      city_ids = self.db_get_city_ids()
      for id in city_ids:
        task = db_add_task('GET PRODUCTS')
        categories = self.get_categories(id)
        result = self.get_products_from_uteka(categories, id)
        if isinstance(result, Right):
          record_products = self.db_add_products(id, result.value)
        if isinstance(record_products, Right):
          task.status = 'COMPLETE'
          db_update_task(task)
    except Exception as error:
      traceback = exc_info()[2]
      fname = path.split(traceback.tb_frame.f_code.co_filename)[1]
      error_status = f'File: {fname}; Line: {traceback.tb_lineno}; Error: {error}'
      task.error_status = error_status
      task.status = 'ERROR'
      db_update_task(task)

@celery.task(bind=True, soft_time_limit=30*60, default_retry_delay=30, max_retries=2)
def get_products_task(self):
  try:
    uteka = UtekaProducts()
    uteka.products()
  except Exception as err:
    raise self.retry(exc=err)