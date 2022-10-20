from routers.core import *

def test_route_ping(test_client):
  response = test_client.get('/api/ping')
  assert response.status_code == 418

def test_route_regions(test_client, headers):
  response = test_client.get('/api/regions', headers=headers)
  data = response.json()
  assert response.status_code == 200
  assert len(data['response']) > 0

def test_route_products(test_client, headers, city_id):
  response = test_client.get(f'/api/pharmacies?region_id={city_id}&page=1', headers=headers)
  data = response.json()
  assert len(data['response']) == 5

def test_route_pharmacies(test_client, headers, city_id):
  response = test_client.get(f'/api/products?region_id={city_id}&page=1', headers=headers)
  data = response.json()
  assert len(data['response']) == 20