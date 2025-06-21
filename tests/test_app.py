import pytest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_home_page(client):
    """Test para la ruta principal"""
    response = client.get('/')
    assert response.status_code == 200
    assert "¡Hola desde Flask!" in response.get_data(as_text=True)

def test_suma_success(client):
    """Test para la operación suma con datos válidos"""
    data = {'a': 5, 'b': 3}
    response = client.post(
        '/suma',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 200
    response_data = json.loads(response.get_data(as_text=True))
    assert response_data['operacion'] == 'suma'
    assert response_data['resultado'] == 8
    assert response_data['status'] == 'exito'

def test_resta_success(client):
    """Test para la operación resta con datos válidos"""
    data = {'a': 10, 'b': 4}
    response = client.post(
        '/resta',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 200
    response_data = json.loads(response.get_data(as_text=True))
    assert response_data['operacion'] == 'resta'
    assert response_data['resultado'] == 6
    assert response_data['status'] == 'exito'

def test_suma_missing_parameters(client):
    """Test para suma con parámetros faltantes"""
    data = {'a': 5}  # Falta 'b'
    response = client.post(
        '/suma',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 400
    response_data = json.loads(response.get_data(as_text=True))
    assert 'error' in response_data

def test_resta_invalid_content_type(client):
    """Test para resta con Content-Type incorrecto"""
    data = {'a': 5, 'b': 3}
    response = client.post(
        '/resta',
        data=json.dumps(data),
        content_type='text/plain'  # Incorrecto
    )
    assert response.status_code == 400
    response_data = json.loads(response.get_data(as_text=True))
    assert 'error' in response_data

def test_suma_non_numeric(client):
    """Test para suma con valores no numéricos"""
    data = {'a': 'cinco', 'b': 'tres'}  # No son números
    response = client.post(
        '/suma',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 400
    response_data = json.loads(response.get_data(as_text=True))
    assert 'error' in response_data

def test_404_not_found(client):
    """Test para ruta no existente"""
    response = client.get('/ruta-inexistente')
    assert response.status_code == 404
    response_data = json.loads(response.get_data(as_text=True))
    assert 'error' in response_data

def test_405_method_not_allowed(client):
    """Test para método no permitido"""
    response = client.get('/suma')  # GET no está permitido, solo POST
    assert response.status_code == 405
    response_data = json.loads(response.get_data(as_text=True))
    assert 'error' in response_data