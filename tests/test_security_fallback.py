import importlib.util
import os
import sys

def test_import_fallback(monkeypatch):
    """Simula que security_constants no está disponible"""
    monkeypatch.setitem(sys.modules, 'src.security_constants', None)

    # Forzamos recarga del módulo app
    import importlib
    import src.app as app_module
    importlib.reload(app_module)

    assert app_module.SELF == "'self'"
    assert app_module.NONE == "'none'"
    assert app_module.UNSAFE_INLINE == "'unsafe-inline'"
    assert app_module.DATA_SRC == "data:"
