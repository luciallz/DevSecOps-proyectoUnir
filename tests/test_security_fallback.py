from src.app import SELF, NONE, UNSAFE_INLINE, DATA_SRC

def test_security_constants():
    assert SELF == "'self'"
    assert NONE == "'none'"
    assert UNSAFE_INLINE == "'unsafe-inline'"
    assert DATA_SRC == "data:"