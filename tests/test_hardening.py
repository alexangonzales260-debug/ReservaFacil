import importlib
import sys

from app.extensions import db
from app.models import Usuario


def _recargar_config():
    sys.modules.pop("config", None)
    import config

    return config


def test_login_admin_password_desde_env(monkeypatch, app, client):
    monkeypatch.setenv("ADMIN_PASSWORD", "secret99")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.delenv("APP_ENV", raising=False)
    cfg = _recargar_config()

    with app.app_context():
        admin = Usuario(
            username=cfg.ADMIN_USERNAME,
            email="admin@test.pe",
            es_admin=True,
        )
        admin.set_password(cfg.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()

    ok = client.post(
        "/admin/login",
        data={"username": "admin", "password": "secret99"},
    )
    assert ok.status_code == 302

    fail = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
    )
    assert fail.status_code == 401


def test_secret_key_desde_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "clave-super-secreta")
    monkeypatch.delenv("APP_ENV", raising=False)
    cfg = _recargar_config()
    assert cfg.SECRET_KEY == "clave-super-secreta"