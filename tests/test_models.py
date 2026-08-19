from datetime import datetime, timedelta

from app.extensions import db
from app.models import Empleado, Reserva, Servicio, Usuario


def test_crear_usuario(app):
    with app.app_context():
        u = Usuario(username="juan", email="juan@example.com")
        u.set_password("secreto123")
        db.session.add(u)
        db.session.commit()
        assert u.id is not None
        assert u.password_hash != "secreto123"
        assert u.check_password("secreto123") is True
        assert u.es_admin is False


def test_crear_empleado(app):
    with app.app_context():
        emp = Empleado(nombre="Ana Gomez", email="ana@example.com", telefono="999111222")
        db.session.add(emp)
        db.session.commit()
        assert emp.id is not None
        assert emp.activo is True
        assert emp.horario_inicio.strftime("%H:%M") == "09:00"
        assert emp.horario_fin.strftime("%H:%M") == "18:00"


def test_crear_servicio(app):
    with app.app_context():
        s = Servicio(nombre="Tintura", precio=60.0, duracion_minutos=90)
        db.session.add(s)
        db.session.commit()
        assert s.id is not None
        assert s.duracion_minutos == 90
        assert s.activo is True


def test_many_to_many_empleado_servicio(app):
    with app.app_context():
        s1 = Servicio(nombre="Corte", precio=25.0, duracion_minutos=30)
        s2 = Servicio(nombre="Barba", precio=15.0, duracion_minutos=20)
        emp = Empleado(nombre="Luis Torres")
        emp.servicios.extend([s1, s2])
        db.session.add_all([s1, s2, emp])
        db.session.commit()
        assert s1 in emp.servicios
        assert s2 in emp.servicios
        assert emp in s1.empleados
        assert emp in s2.empleados


def test_crear_reserva(app):
    with app.app_context():
        u = Usuario(username="cliente1", email="cliente1@example.com")
        u.set_password("x")
        s = Servicio(nombre="Corte", precio=25.0, duracion_minutos=30)
        emp = Empleado(nombre="Ana")
        db.session.add_all([u, s, emp])
        db.session.commit()

        inicio = datetime(2026, 8, 20, 10, 0)
        r = Reserva(
            codigo="RF-ABCDEF",
            usuario_id=u.id,
            servicio_id=s.id,
            empleado_id=emp.id,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=s.duracion_minutos),
        )
        db.session.add(r)
        db.session.commit()
        assert r.id is not None
        assert r.estado == "pendiente"
        assert r.fecha_hora_fin == datetime(2026, 8, 20, 10, 30)
        assert r.codigo.startswith("RF-")