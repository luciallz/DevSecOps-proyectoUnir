import pytest
from app import app
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def client():
    """Cliente de prueba para la app Flask."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    """Test para la ruta principal."""
    response = client.get("/")
    assert response.status_code == 200
    # Solución 1: Decodificar la respuesta a UTF-8
    assert "¡Hola desde Flask!" in response.data.decode('utf-8')
    # O Solución 2: Usar string normal si no necesitas bytes
    assert "¡Hola desde Flask!" in response.get_data(as_text=True)

def test_suma(client):
    """Test exhaustivo para el endpoint /suma."""
    # Caso normal
    response = client.post("/suma", json={"a": 3, "b": 4})
    assert response.status_code == 200
    assert response.get_json()["resultado"] == 7

    # Caso con decimales
    response = client.post("/suma", json={"a": 3.5, "b": 4.2})
    assert response.status_code == 200
    assert pytest.approx(response.get_json()["resultado"]) == 7.7

    # Caso con un parámetro faltante
    response = client.post("/suma", json={"a": 3})
    assert response.status_code == 400

    # Caso con datos no numéricos
    response = client.post("/suma", json={"a": "x", "b": 4})
    assert response.status_code == 400
    assert "error" in response.get_json()

    # Caso sin datos JSON
    response = client.post("/suma", data="not json", headers={"Content-Type": "text/plain"})
    assert response.status_code == 400

def test_resta(client):
    """Test exhaustivo para el endpoint /resta."""
    # Caso normal
    response = client.post("/resta", json={"a": 10, "b": 4})
    assert response.status_code == 200
    assert response.get_json()["resultado"] == 6

    # Caso con resultado negativo
    response = client.post("/resta", json={"a": 4, "b": 10})
    assert response.status_code == 200
    assert response.get_json()["resultado"] == -6

    # Caso con un parámetro faltante
    response = client.post("/resta", json={"b": 4})
    assert response.status_code == 400

    # Caso con datos no numéricos
    response = client.post("/resta", json={"a": 5, "b": "y"})
    assert response.status_code == 400
    assert "error" in response.get_json()