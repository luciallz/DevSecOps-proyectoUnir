import pytest
from app import app
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def client():
    """
    Cliente de prueba para la app Flask.
    """
    with app.test_client() as client:
        yield client

def test_home(client):
    """
    Test para la ruta principal.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "¡Hola desde Flask!" in response.data.decode("utf-8")

def test_suma(client):
    """
    Test para el endpoint /suma.
    """
    response = client.post("/suma", json={"a": 3, "b": 4})
    json_data = response.get_json()
    assert response.status_code == 200
    assert json_data["resultado"] == 7

    # Prueba error con datos no numéricos
    response = client.post("/suma", json={"a": "x", "b": 4})
    assert response.status_code == 400

def test_resta(client):
    """
    Test para el endpoint /resta.
    """
    response = client.post("/resta", json={"a": 10, "b": 4})
    json_data = response.get_json()
    assert response.status_code == 200
    assert json_data["resultado"] == 6

    # Prueba error con datos no numéricos
    response = client.post("/resta", json={"a": 5, "b": "y"})
    assert response.status_code == 400
