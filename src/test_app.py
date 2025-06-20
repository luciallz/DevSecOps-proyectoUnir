import pytest
from app import app

@pytest.fixture
def client():
    """Cliente de prueba para la app Flask."""
    with app.test_client() as client:
        yield client

def test_home(client):
    """Prueba que la ruta '/' devuelve el saludo esperado."""
    response = client.get("/")
    assert response.status_code == 200
    assert "¡Hola desde Flask!" in response.data.decode('utf-8')
