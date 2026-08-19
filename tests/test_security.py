import pytest

from app.extensions import db
from app.models import Usuario
from app.security import reset_limites


@pytest.fixture(autouse=True)
def _limites_limpios():
    reset_limites()
    yield
    reset_limites()


@pytest.fixture()
def admin_user(app):
    u = Usuario(username="admin", email="admin@reservafacil.pe", es_admin=True)
    u.set_password("admin123")
    db.session.add(u)
    db.session.commit()
    return u


def _login(client, password="incorrecta"):
    return client.post(
        "/admin/login",
        data={"username": "admin", "password": password},
    )


def test_login_admin_bloqueado_tras_5_intentos(client, admin_user):
    for _ in range(5):
        assert _login(client).status_code == 401
    rv = _login(client)
    assert rv.status_code == 429
    assert "Demasiados intentos" in rv.get_data(as_text=True)


def test_reset_limites_restaura_login(client, admin_user):
    for _ in range(6):
        _login(client)
    reset_limites()
    rv = _login(client, password="admin123")
    assert rv.status_code == 302


def test_cabeceras_seguridad_en_respuesta_normal(client):
    rv = client.get("/")
    assert rv.headers["X-Content-Type-Options"] == "nosniff"
    assert rv.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert rv.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_admin_responde_cache_control_no_store(client):
    rv = client.get("/admin/login")
    assert rv.headers["Cache-Control"] == "no-store"