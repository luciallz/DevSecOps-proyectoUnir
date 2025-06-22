import os
import pytest
from flask import Flask
from src.app import create_csp_policy, configure_talisman

def test_create_csp_policy_structure():
    """Verifica que la política CSP tenga las claves esperadas"""
    origins = ["https://example.com"]
    csp = create_csp_policy(origins)
    assert 'default-src' in csp
    assert 'script-src' in csp
    assert 'connect-src' in csp
    assert origins[0] in csp['connect-src']

def test_configure_talisman_applies(monkeypatch):
    """Verifica que configure_talisman no lanza errores"""
    app = Flask(__name__)
    csp = create_csp_policy(["https://test.com"])
    configure_talisman(app, csp)
