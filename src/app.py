from flask import Flask, jsonify, request
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_talisman import Talisman
from flask_cors import CORS
import sys

app = Flask(__name__)

# Configuración básica de seguridad
app.config['JSON_SORT_KEYS'] = False  # Mejor para APIs

# Configuración CSRF deshabilitada (para API stateless)
app.config['WTF_CSRF_ENABLED'] = False

# Configuración de entorno
is_testing = os.environ.get('FLASK_ENV') == 'test' or 'pytest' in sys.modules
is_development = os.environ.get('FLASK_ENV') == 'development'

if is_testing:
    # Configuración menos estricta para testing
    app.logger.info("Modo testing - seguridad reducida")
    Talisman(app, force_https=False, strict_transport_security=False)
else:
    # Configuración de producción/desarrollo
    allowed_origins = [o.strip() for o in os.environ.get('ALLOWED_ORIGINS', '').split(',') if o.strip()]
    
    # Validación de origenes permitidos
    if not all(o.startswith(('http://localhost', 'https://')) for o in allowed_origins) and not is_development:
        raise ValueError("Orígenes permitidos deben usar HTTPS excepto en desarrollo")
    
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "supports_credentials": False,  # No se necesitan cookies
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })
    
    # Configuración de seguridad reforzada sin CSRF
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'"],
        'style-src': ["'self'"],
        'img-src': ["'self'", "data:"],
        'connect-src': ["'self'"] + allowed_origins,
        'frame-ancestors': "'none'",
        'form-action': "'self'"
    }
    
    Talisman(
        app,
        force_https=not is_development,
        force_https_permanent=True,
        strict_transport_security=not is_development,
        strict_transport_security_max_age=31536000,
        strict_transport_security_include_subdomains=True,
        content_security_policy=csp,
        session_cookie_secure=not is_development
    )

# Configuración de logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

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

@app.route('/suma', methods=['POST'])
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

@app.route('/resta', methods=['POST'])
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