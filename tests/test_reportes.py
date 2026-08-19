import pytest

from app.extensions import db
from app.models import Usuario


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


def _crear_reserva_api(client, datos_seed, fecha="2026-08-25T10:00"):
    _, servicio, empleado = datos_seed
    rv = client.post(
        "/api/v1/reservas",
        json={
            "servicio_id": servicio.id,
            "empleado_id": empleado.id,
            "fecha_hora_inicio": fecha,
            "nombre": "Cliente Reporte",
            "email": "reporte@example.com",
        },
    )
    assert rv.status_code == 201
    return rv.get_json()


def test_reportes_sin_sesion_redirige(client, admin_user):
    rv = client.get("/admin/reportes")
    assert rv.status_code == 302
    assert "/admin/login" in rv.headers["Location"]


def test_reportes_con_admin_muestra_canvas(client, admin_user):
    _login(client)
    rv = client.get("/admin/reportes")
    assert rv.status_code == 200
    body = rv.get_data(as_text=True)
    assert 'id="grafico-dias"' in body
    assert 'id="grafico-servicios"' in body
    assert "Descargar CSV" in body


def test_csv_con_admin_contiene_codigo(client, admin_user, seed):
    _login(client)
    datos = _crear_reserva_api(client, seed())
    rv = client.get("/admin/reportes/reservas.csv")
    assert rv.status_code == 200
    assert rv.headers["Content-Type"].startswith("text/csv")
    assert rv.get_data()[:3] == b"\xef\xbb\xbf"
    body = rv.get_data(as_text=True)
    assert "codigo" in body
    assert datos["codigo"] in body


def test_csv_sin_sesion_redirige(client, admin_user):
    rv = client.get("/admin/reportes/reservas.csv")
    assert rv.status_code == 302
    assert "/admin/login" in rv.headers["Location"]


def test_csv_filtro_estado_cancelada(client, admin_user, seed):
    _login(client)
    datos_seed = seed()
    d1 = _crear_reserva_api(client, datos_seed, "2026-08-25T10:00")
    d2 = _crear_reserva_api(client, datos_seed, "2026-08-25T11:00")
    rv = client.patch(f"/api/v1/reservas/{d1['id']}/cancelar")
    assert rv.status_code == 200

    rv = client.get("/admin/reportes/reservas.csv?estado=cancelada")
    body = rv.get_data(as_text=True)
    assert d1["codigo"] in body
    assert d2["codigo"] not in body