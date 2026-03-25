import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b'Hola' in res.data

def test_health(client):
    res = client.get('/health')
    assert res.status_code == 200

def test_suma(client):
    res = client.get('/suma/3/4')
    data = res.get_json()
    assert data['resultado'] == 7