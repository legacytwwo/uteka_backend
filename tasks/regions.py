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

from models.core import Regions
from models.core import RegionsScheme

load_dotenv()

class UtekaRegions():
  timeout = 15
  site_url = 'https://uteka.ru/rpc/?method='
  headers = {'Content-Type': 'application/json'}

  def __init__(self, proxy=environ["PROXY"]):
    self.http = requests.Session()
    self.http.proxies = {'https': proxy}

  def get_regions_from_uteka(self) -> 'list[RegionsScheme]':
    body = {
      "id": 28,
      "jsonrpc": "2.0",
      "method": "catalogue.Cities"
    }

    try:
      response = self.http.post(
        headers=self.headers, timeout=self.timeout,
        url=f'{self.site_url}catalogue.Cities', data=dumps(body),
      )
    except Exception:
      self.http = requests.Session()
      self.http.proxies = {'https': environ["PROXY"]}
      response = self.http.post(
        headers=self.headers, timeout=self.timeout,
        url=f'{self.site_url}catalogue.Cities', data=dumps(body),
      )

    if response.ok:
      result = []
      data = response.json()
      if data['result']:
        regions = data['result']

        for region in regions:
          model = RegionsScheme(
            guid=region['cityId'],
            title=region['title'],
          )
          result.append(model)

        return Right(result)

  def db_delete_regions(self) -> None:
    with contextmanager(get_db)() as session:
      session.query(Regions).delete()
      session.commit()

  def db_add_regions(self, result: 'list[RegionsScheme]') -> bool:
    self.db_delete_regions()
    with contextmanager(get_db)() as session:
      for region in result:
        record = Regions(**region.dict())
        record = session.merge(record)
      session.commit()
    return Right(True)

  def regions(self) -> None:
    task = db_add_task('GET REGIONS')
    try:
      result = self.get_regions_from_uteka()
      if isinstance(result, Right):
        record_regions = self.db_add_regions(result.value)
      if isinstance(record_regions, Right):
        task.status = 'COMPLETE'
        db_update_task(task)
    except Exception as error:
      traceback = exc_info()[2]
      fname = path.split(traceback.tb_frame.f_code.co_filename)[1]
      error_status = f'File: {fname}; Line: {traceback.tb_lineno}; Error: {error}'
      task.error_status = error_status
      task.status = 'ERROR'
      db_update_task(task)

@celery.task(bind=True, soft_time_limit=1*60, default_retry_delay=30, max_retries=2)
def get_regions_task(self) -> None:
  try:
    uteka = UtekaRegions()
    uteka.regions()
  except Exception as err:
    raise self.retry(exc=err)