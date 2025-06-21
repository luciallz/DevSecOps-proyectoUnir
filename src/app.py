from flask import Flask
from flask_talisman import Talisman
from flask_cors import CORS
import os
import sys

app = Flask(__name__)

# Configuración básica de seguridad
app.config['JSON_SORT_KEYS'] = False  # Mejor para APIs
app.config['WTF_CSRF_ENABLED'] = False

# Seguridad
# Seguridad
is_testing = os.environ.get('FLASK_ENV') == 'test' or 'pytest' in sys.modules

if is_testing:
    Talisman(app, force_https=False, strict_transport_security=False)
else:
    CORS(app, resources={r"/*": {"origins": os.environ.get('ALLOWED_ORIGINS', '').split(',')}})
    Talisman(app, force_https=True, strict_transport_security=True)

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