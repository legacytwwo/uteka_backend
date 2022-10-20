import pytest
from app import app
from os import environ
from dotenv import load_dotenv
from fastapi.testclient import TestClient

@pytest.fixture()
def city_id():
  return 26

@pytest.fixture()
def test_client():
  client = TestClient(app)
  return client

@pytest.fixture()
def headers():
  load_dotenv()
  return {'Token': environ["TEST_TOKEN"]}