import sys
import importlib
import pytest

def test_invalid_origins_raise(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost")

    # Borrar el módulo para forzar recarga y que lea las nuevas variables
    if "src.app" in sys.modules:
        del sys.modules["src.app"]

    # La excepción debe saltar al importar el módulo, por eso va dentro de pytest.raises
    with pytest.raises(ValueError, match="todos los origenes deben usar HTTPS"):
        import src.app