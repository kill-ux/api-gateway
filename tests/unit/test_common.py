from app import get_env_variable
import pytest

def test_get_env_variable_success(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "123")
    assert get_env_variable("TEST_VAR", cast_type=int) == 123

def test_get_env_variable_missing(monkeypatch):
    monkeypatch.delenv("NON_EXISTENT_VAR", raising=False)
    assert get_env_variable("NON_EXISTENT_VAR") is None

def test_get_env_variable_value_error(monkeypatch):
    monkeypatch.setenv("BAD_INT", "not_a_number")
    with pytest.raises(RuntimeError):
        get_env_variable("BAD_INT", cast_type=int)
        
def test_global_exception_handler(client):
    response = client.get("/route-that-raises-exception")
    assert response.status_code == 404