import requests
from os import environ
from dotenv import load_dotenv

from db import get_db
from json import dumps

from os import path
from sys import exc_info
from celery_app import celery
from contextlib import contextmanager

from oslash import Right, Left
from models.regions import Regions

from tasks.task import db_add_task
from tasks.task import db_update_task

from models.core import Pharmacies
from models.core import PharmaciesScheme

load_dotenv()

class UtekaPharmacies():
  timeout = 15
  site_url = 'https://uteka.ru/rpc/?method='
  headers = {'Content-Type': 'application/json'}

  def __init__(self, proxy=environ["PROXY"]):
    self.http = requests.Session()
    self.http.proxies = {'https': proxy}

  def get_pharmacies_from_uteka(self, count: int, city_id: int) -> 'list[PharmaciesScheme]':
    body = {
      "id": 48,
      "jsonrpc": "2.0",
      "method": "pharmacies.Get",
      "params": {
          "search": {
              "partnerIds": [],
              "cityId": city_id,
              "pickupOnly": False,
              "discountPriceOnly": False
          },
          "page": 0,
          "pageSize": count
      }
    }

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
      if data['result']:
        result = []
        list = data['result']
        
        for pharmacy in list:
          model = PharmaciesScheme(
            region_id=city_id,
            guid=pharmacy['id'],
            title=pharmacy['title'],
            address=pharmacy['address'],
            latitude=pharmacy['latitude'],
            longitude=pharmacy['longitude']
          )
          result.append(model)
        
        return Right(result)

  def get_pharmacies_count(self, city_id: int) -> int:
    body = {
      "id":49,
      "jsonrpc": "2.0",
      "method": "pharmacies.Count",
      "params": {
          "search": {
            "partnerIds": [],
            "cityId": city_id,
            "pickupOnly": False,
            "discountPriceOnly": False
          }
      }
    }
    
    try:
      response = self.http.post(
        headers=self.headers, timeout=self.timeout,
        url=f'{self.site_url}pharmacies.Count', data=dumps(body),
      )
    except Exception:
      self.http = requests.Session()
      self.http.proxies = {'https': environ["PROXY"]}
      response = self.http.post(
        headers=self.headers, timeout=self.timeout,
        url=f'{self.site_url}pharmacies.Count', data=dumps(body),
      )
    
    if response.ok:
      data = response.json()
      if data['result']:
        return data['result']
  
  def set_context(self, region_id: int, pharmacy_id: int) -> bool:
    body = {
      "id": "1",
      "jsonrpc": "2.0",
      "method": "cart.SetContext",
      "params": {
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

  def db_delete_pharmacies(self, region_id: int) -> None:
    with contextmanager(get_db)() as session:
      session.query(Pharmacies).filter(Pharmacies.region_id == region_id).delete()
      session.commit()

  def db_add_pharmacies(self, region_id: int, result: 'list[PharmaciesScheme]') -> None:
    
    self.db_delete_pharmacies(region_id)
    with contextmanager(get_db)() as session:
      for pharma in result:
        record = Pharmacies(**pharma.dict())
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
  
  def pharmacies(self) -> None:
    try:
      city_ids = self.db_get_city_ids()
      for id in city_ids:
        task = db_add_task('GET PHARMACIES')
        count = self.get_pharmacies_count(id)
        result = self.get_pharmacies_from_uteka(count, id)
        if isinstance(result, Right):
          pharma_list = []
          for i in result.value:
            is_available = self.set_context(id, i.guid)
            if isinstance(is_available, Right):
              pharma_list.append(i)
            else:
              continue
          record_pharmacies = self.db_add_pharmacies(id, pharma_list)
        if isinstance(record_pharmacies, Right):
          task.status = 'COMPLETE'
          db_update_task(task)
    except Exception as error:
      traceback = exc_info()[2]
      fname = path.split(traceback.tb_frame.f_code.co_filename)[1]
      error_status = f'File: {fname}; Line: {traceback.tb_lineno}; Error: {error}'
      task.error_status = error_status
      task.status = 'ERROR'
      db_update_task(task)

@celery.task(bind=True, soft_time_limit=15*60, default_retry_delay=30, max_retries=2)
def get_pharmacies_task(self):
  try:
    uteka = UtekaPharmacies()
    uteka.pharmacies()
  except Exception as err:
    raise self.retry(exc=err)