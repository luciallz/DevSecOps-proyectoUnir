from flask import Flask, jsonify, request
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_talisman import Talisman
from flask_cors import CORS
import sys
import secrets

app = Flask(__name__)

# Configuración básica de seguridad
app.config['JSON_SORT_KEYS'] = False  # Mejor para APIs
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Configuración de entorno
is_testing = os.environ.get('FLASK_ENV') == 'test' or 'pytest' in sys.modules
is_development = os.environ.get('FLASK_ENV') == 'development'
is_production = not (is_testing or is_development)

# Configuración de logging seguro
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# Deshabilitar el modo debug en producción
if is_production:
    app.debug = False
    app.config['PROPAGATE_EXCEPTIONS'] = True

# Configuración de seguridad por entorno
if is_testing:
    # Configuración para testing (con logging explícito)
    app.logger.warning("Modo testing - configuracion de seguridad reducida")
    Talisman(app, 
             force_https=False, 
             strict_transport_security=False,
             content_security_policy=None)
else:
    # Configuración CORS segura
    allowed_origins = [o.strip() for o in os.environ.get('ALLOWED_ORIGINS', '').split(',') if o.strip()]
    
    # Validación estricta de origenes permitidos
    if is_production:
        if not all(o.startswith('https://') for o in allowed_origins):
            raise ValueError("En producción, todos los origenes deben usar HTTPS")
    
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "supports_credentials": False,
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "expose_headers": [],
            "max_age": 86400
        }
    })
    
    SELF = "'self'"
    NONE = "'none'"
    UNSAFE_INLINE = "'unsafe-inline'"
    DATA_SRC = "data:"

    # Política de seguridad de contenido (CSP) estricta
    csp = {
        'default-src': SELF,
        'script-src': [SELF],
        'style-src': [SELF, UNSAFE_INLINE],  # Idealmente eliminar unsafe-inline
        'img-src': [SELF, DATA_SRC],
        'connect-src': [SELF] + allowed_origins,
        'frame-ancestors': NONE,
        'form-action': SELF,
        'base-uri': SELF,
        'object-src': NONE,
        'font-src': [SELF],  # Added for completeness
        'media-src': [SELF]  # Added for completeness
    }

    # Configuración Talisman reforzada
    Talisman(
        app,
        force_https=is_production,
        force_https_permanent=is_production,
        strict_transport_security=is_production,
        strict_transport_security_max_age=31536000,
        strict_transport_security_include_subdomains=True,
        strict_transport_security_preload=is_production,
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src'],
        referrer_policy='strict-origin-when-cross-origin',
        session_cookie_secure=is_production,
        session_cookie_http_only=True,
        session_cookie_samesite='Lax'
    )


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