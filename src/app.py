from flask import Flask, jsonify, request
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_cors import CORS
import secrets
# Constantes de seguridad básicas (eliminamos la dependencia de security_constants.py)
SELF = "'self'"
NONE = "'none'"
UNSAFE_INLINE = "'unsafe-inline'"
DATA_SRC = "data:"
flask_env = os.environ.get("FLASK_ENV", "development")
is_testing = flask_env == "testing"
is_development = flask_env == "development"
is_production = not (is_testing or is_development)
app = Flask(__name__)
app.url_map.strict_slashes = False

# Configuración básica
app.config['JSON_SORT_KEYS'] = False
# La SECRET_KEY no está hardcodeada, se obtiene de las variables de entorno en producción
if is_production:
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError("En producción SECRET_KEY debe estar definido en las variables de entorno")
    app.config['SECRET_KEY'] = secret_key

# Configuración de logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# CORS permisivo para desarrollo
CORS(app)

# Middleware de seguridad básico sin HTTPS
@app.after_request
def add_security_headers(response):
    headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY'
    }
    response.headers.update(headers)
    return response

def validate_json_content(f):
    """Decorador para validar contenido JSON"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            app.logger.warning('Intento de acceso sin JSON')
            return jsonify({"error": "Content-Type debe ser application/json"}), 400
        return f(*args, **kwargs)
    return decorated_function

def validate_numbers_input(f):
    """Decorador para validar entrada numérica"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        if not data or 'a' not in data or 'b' not in data:
            app.logger.warning('Parámetros faltantes')
            return jsonify({"error": "Se requieren los parámetros 'a' y 'b'"}), 400
        
        try:
            a = float(data['a'])
            b = float(data['b'])
        except (ValueError, TypeError):
            app.logger.warning('Valores no numéricos recibidos')
            return jsonify({"error": "Los valores deben ser números válidos"}), 400
            
        return f(a, b, *args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    """Ruta principal que devuelve un saludo."""
    app.logger.info('Acceso a ruta principal')
    return "¡Hola desde Flask!"

@app.route('/suma/', methods=['POST'])
@validate_json_content
@validate_numbers_input
def suma(a, b):
    """
    Suma dos números enviados en formato JSON.
    
    JSON esperado: {"a": número, "b": número}
    Devuelve: {"resultado": suma de a y b}
    """
    try:
        resultado = a + b
        app.logger.info(f'Operación suma exitosa: {a} + {b} = {resultado}')
        return jsonify({
            "operacion": "suma",
            "resultado": resultado,
            "status": "exito"
        })
    except Exception as e:
        app.logger.error(f'Error en suma: {str(e)}')
        return jsonify({"error": "Error interno procesando la solicitud"}), 500

@app.route('/resta/', methods=['POST'])
@validate_json_content
@validate_numbers_input
def resta(a, b):
    """
    Resta dos números enviados en formato JSON.
    
    JSON esperado: {"a": número, "b": número}
    Devuelve: {"resultado": resta de a menos b}
    """
    try:
        resultado = a - b
        app.logger.info(f'Operación resta exitosa: {a} - {b} = {resultado}')
        return jsonify({
            "operacion": "resta",
            "resultado": resultado,
            "status": "exito"
        })
    except Exception as e:
        app.logger.error(f'Error en resta: {str(e)}')
        return jsonify({"error": "Error interno procesando la solicitud"}), 500

@app.errorhandler(404)
def page_not_found(e):
    app.logger.warning(f'Intento de acceso a ruta no existente: {request.path}')
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    app.logger.warning(f'Método no permitido: {request.method} en {request.path}')
    return jsonify({"error": "Método no permitido"}), 405

if __name__ == "__main__":
    # Configuración para entorno de desarrollo
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False  # Siempre False en producción!
    )