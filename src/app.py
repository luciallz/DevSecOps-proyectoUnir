from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    """
    Ruta principal que devuelve un saludo.
    """
    return "¡Hola desde Flask!"

@app.route("/suma", methods=["POST"])
def suma():
    """
    Suma dos números enviados en formato JSON.
    
    JSON esperado:
    {
        "a": número,
        "b": número
    }

    Devuelve:
    {
        "resultado": suma de a y b
    }
    """
    data = request.get_json()
    a = data.get("a")
    b = data.get("b")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return jsonify({"error": "Los valores deben ser números"}), 400

    resultado = a + b
    return jsonify({"resultado": resultado})

@app.route("/resta", methods=["POST"])
def resta():
    """
    Resta dos números enviados en formato JSON.
    
    JSON esperado:
    {
        "a": número,
        "b": número
    }

    Devuelve:
    {
        "resultado": resta de a menos b
    }
    """
    data = request.get_json()
    a = data.get("a")
    b = data.get("b")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return jsonify({"error": "Los valores deben ser números"}), 400

    resultado = a - b
    return jsonify({"resultado": resultado})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
