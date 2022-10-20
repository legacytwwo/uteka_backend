from oslash import Right
from celery_app import celery

from tasks.regions import UtekaRegions
from tasks.products import UtekaProducts
from tasks.pharmacies import UtekaPharmacies

def test_task_regions():
  uteka = UtekaRegions()
  regions = uteka.get_regions_from_uteka()
  assert isinstance(regions, Right) == True

def test_task_products(city_id):
  categories = [3043]
  uteka = UtekaProducts()
  products = uteka.get_products_from_uteka(categories=categories, city_id=city_id)
  assert isinstance(products, Right) == True

def test_task_pharmacies(city_id):
  uteka = UtekaPharmacies()
  count = uteka.get_pharmacies_count(city_id=city_id)
  pharmacies = uteka.get_pharmacies_from_uteka(count=count, city_id=city_id)
  assert isinstance(pharmacies, Right) == True