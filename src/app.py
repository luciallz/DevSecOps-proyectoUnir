from flask import Flask, jsonify, request
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_talisman import Talisman
from flask_cors import CORS
import sys
from flask_wtf.csrf import CSRFProtect  # Importar CSRFProtect explícitamente

app = Flask(__name__)

# Configuración básica de seguridad
app.config['JSON_SORT_KEYS'] = False  # Mejor para APIs

# Configuración CSRF
csrf = CSRFProtect(app)  # Inicializar CSRF protection
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hora de validez
app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken']  # Para APIs
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32))  # Clave secreta fuerte

# Configuración de entorno
is_testing = os.environ.get('FLASK_ENV') == 'test' or 'pytest' in sys.modules
is_development = os.environ.get('FLASK_ENV') == 'development'

if is_testing:
    # Documentación explícita sobre por qué se deshabilita CSRF en testing
    app.logger.info("CSRF deshabilitado para testing - solo usar en entorno controlado")
    app.config['WTF_CSRF_ENABLED'] = False
    Talisman(app, force_https=False, strict_transport_security=False)
else:
    # Configuración segura para producción/desarrollo
    allowed_origins = os.environ.get('ALLOWED_ORIGINS', '').split(',')
    
    # Validación de origenes permitidos
    if not all(o.startswith(('http://localhost', 'https://')) and not is_development:
        raise ValueError("Orígenes permitidos deben usar HTTPS excepto en desarrollo")
    
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "supports_credentials": True,
            "allow_headers": ["Content-Type", "X-CSRFToken"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })
    
    # Configuración de seguridad reforzada
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'"],
        'style-src': ["'self'", "'unsafe-inline'"],
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
        strict_transport_security_preload=True,
        content_security_policy=csp,
        session_cookie_secure=not is_development,
        session_cookie_http_only=True
    )

# Documentación de seguridad para APIs
if not is_testing:
    @app.before_request
    def csrf_protect():
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            csrf.protect()

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