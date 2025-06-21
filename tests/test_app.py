import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.app import app
@pytest.fixture
def client():
    """Cliente de prueba para la app Flask."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    response = client.get("/", follow_redirects=True)  # ¡Añade este parámetro!
    assert response.status_code == 200

def test_suma(client):
    response = client.post("/suma", json={"a": 3, "b": 4}, follow_redirects=True)
    assert response.status_code == 200

def test_resta(client):
    response = client.post("/resta", json={"a": 10, "b": 4}, follow_redirects=True)
    assert response.status_code == 200

def test_suma_datos_invalidos(client):
    response = client.post("/suma", 
                         json={"a": "texto", "b": 4},
                         follow_redirects=True)
    assert response.status_code == 400
    assert "error" in response.json