from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models import Empleado, Reserva, Servicio, Usuario


@pytest.fixture()
def admin_user(app):
    u = Usuario(username="admin", email="admin@reservafacil.pe", es_admin=True)
    u.set_password("admin123")
    db.session.add(u)
    db.session.commit()
    return u


def _login(client):
    return client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
    )


def test_login_exitoso(client, admin_user):
    rv = _login(client)
    assert rv.status_code == 302
    assert "/admin/" in rv.headers["Location"]
    with client.session_transaction() as sess:
        assert sess["user_id"] == admin_user.id


def test_login_fallido(client, admin_user):
    rv = client.post(
        "/admin/login",
        data={"username": "admin", "password": "clave-incorrecta"},
    )
    assert rv.status_code == 401
    assert "incorrectos" in rv.get_data(as_text=True)


def test_acceso_protegido_sin_login(client):
    rv = client.get("/admin/")
    assert rv.status_code == 302
    assert "/admin/login" in rv.headers["Location"]


def test_crud_servicios(client, admin_user):
    _login(client)
    rv = client.post(
        "/admin/servicios/nuevo",
        data={
            "nombre": "Manicure",
            "descripcion": "Uñas y cutículas",
            "duracion_minutos": "60",
            "precio": "35.5",
            "activo": "on",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "Manicure" in client.get("/admin/servicios").get_data(as_text=True)

    with db.session() as sess:
        servicio = sess.execute(
            db.select(Servicio).where(Servicio.nombre == "Manicure")
        ).scalar_one()
        servicio_id = servicio.id

    rv = client.post(
        f"/admin/servicios/{servicio_id}/editar",
        data={
            "nombre": "Manicure Premium",
            "descripcion": "Uñas y cutículas",
            "duracion_minutos": "45",
            "precio": "40",
            "activo": "on",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "Manicure Premium" in client.get("/admin/servicios").get_data(as_text=True)

    rv = client.post(f"/admin/servicios/{servicio_id}/eliminar", follow_redirects=True)
    assert rv.status_code == 200
    with db.session() as sess:
        assert sess.get(Servicio, servicio_id).activo is False


def test_crud_empleados(client, admin_user):
    _login(client)
    with db.session() as sess:
        svc = Servicio(nombre="Corte", precio=25.0, duracion_minutos=30)
        sess.add(svc)
        sess.commit()
        svc_id = svc.id

    rv = client.post(
        "/admin/empleados/nuevo",
        data={
            "nombre": "Lucía",
            "email": "lucia@example.com",
            "telefono": "999123456",
            "horario_inicio": "09:00",
            "horario_fin": "17:00",
            "servicios": str(svc_id),
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = client.get("/admin/empleados").get_data(as_text=True)
    assert "Lucía" in html
    assert "Corte" in html

    with db.session() as sess:
        empleado = sess.execute(
            db.select(Empleado).where(Empleado.nombre == "Lucía")
        ).scalar_one()
        empleado_id = empleado.id

    rv = client.post(
        f"/admin/empleados/{empleado_id}/editar",
        data={
            "nombre": "Lucía M.",
            "email": "lucia@example.com",
            "telefono": "999123456",
            "horario_inicio": "10:00",
            "horario_fin": "18:00",
            "servicios": str(svc_id),
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "Lucía M." in client.get("/admin/empleados").get_data(as_text=True)

    rv = client.post(f"/admin/empleados/{empleado_id}/eliminar", follow_redirects=True)
    assert rv.status_code == 200
    with db.session() as sess:
        assert sess.get(Empleado, empleado_id).activo is False


def test_gestion_reservas(client, admin_user):
    _login(client)
    with db.session() as sess:
        u = Usuario(username="clienteX", email="clienteX@example.com")
        u.set_password("x")
        svc = Servicio(nombre="Corte", precio=25.0, duracion_minutos=30)
        emp = Empleado(nombre="María")
        sess.add_all([u, svc, emp])
        sess.commit()
        inicio = datetime(2026, 8, 22, 10, 0)
        r = Reserva(
            codigo="RF-AAAAAA",
            usuario_id=u.id,
            servicio_id=svc.id,
            empleado_id=emp.id,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=30),
            estado="pendiente",
        )
        sess.add(r)
        sess.commit()
        reserva_id = r.id

    html = client.get("/admin/reservas").get_data(as_text=True)
    assert "RF-AAAAAA" in html

    client.post(f"/admin/reservas/{reserva_id}/confirmar")
    with db.session() as sess:
        assert sess.get(Reserva, reserva_id).estado == "confirmada"

    client.post(f"/admin/reservas/{reserva_id}/completar")
    with db.session() as sess:
        assert sess.get(Reserva, reserva_id).estado == "completada"

    client.post(f"/admin/reservas/{reserva_id}/cancelar")
    with db.session() as sess:
        assert sess.get(Reserva, reserva_id).estado == "cancelada"