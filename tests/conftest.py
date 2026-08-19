import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from app.extensions import db


@pytest.fixture(autouse=True)
def _reset_limites():
    from app.security import reset_limites

    reset_limites()
    yield
    reset_limites()


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False},
            },
            "WTF_CSRF_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def seed(app):
    def _seed():
        from app.models import Empleado, Servicio, Usuario

        usuario = Usuario(username="cliente1", email="cliente1@example.com")
        usuario.set_password("secreto123")
        servicio = Servicio(nombre="Corte de cabello", precio=25.0, duracion_minutos=30)
        empleado = Empleado(nombre="Ana Gomez", email="ana@example.com")
        empleado.servicios.append(servicio)
        db.session.add_all([usuario, servicio, empleado])
        db.session.commit()
        return usuario, servicio, empleado

    return _seed