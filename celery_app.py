from os import environ
from celery import Celery
from dotenv import load_dotenv

load_dotenv()
celery = Celery(__name__)
celery.conf.broker_url = environ["BROKER_URL"]
celery.conf.result_backend = environ["RESULT_BACKEND"]
celery.conf.update(enable_utc=False, timezone=('Europe/Moscow'))

from celery.schedules import crontab
from tasks.regions import get_regions_task
from tasks.products import get_products_task
from tasks.pharmacies import get_pharmacies_task

celery.conf.beat_schedule = {
  'get_regions': {
    'task': 'tasks.regions.get_regions_task',
    'schedule': crontab(hour=15, minute=42),
  },
  'get_products': {
    'task': 'tasks.products.get_products_task',
    'schedule': crontab(hour=15, minute=10),
  },
  'get_pharmacies': {
    'task': 'tasks.pharmacies.get_pharmacies_task',
    'schedule': crontab(hour=14, minute=55),
  },
}

from routers.parse import *

# celery -A celery_app.celery worker -B