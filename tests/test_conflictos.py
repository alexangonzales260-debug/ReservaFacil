from datetime import time

from app.extensions import db
from app.models import Empleado, Servicio


def _crear_base(
    app,
    horario_inicio: time = time(9, 0),
    horario_fin: time = time(18, 0),
) -> tuple:
    servicio = Servicio(nombre="Corte", precio=25.0, duracion_minutos=30)
    empleado = Empleado(
        nombre="Maria",
        horario_inicio=horario_inicio,
        horario_fin=horario_fin,
    )
    db.session.add_all([servicio, empleado])
    db.session.commit()
    return servicio.id, empleado.id


def _post_reserva(client, servicio_id, empleado_id, inicio, email):
    return client.post(
        "/api/v1/reservas",
        json={
            "servicio_id": servicio_id,
            "empleado_id": empleado_id,
            "fecha_hora_inicio": inicio,
            "nombre": "Cliente Test",
            "email": email,
        },
    )


def test_crear_reserva_sin_conflicto(app, client):
    servicio_id, empleado_id = _crear_base(app)
    rv = _post_reserva(
        client, servicio_id, empleado_id, "2026-08-21T10:00", "cliente1@example.com"
    )
    assert rv.status_code == 201


def test_crear_reserva_solapamiento_directo(app, client):
    servicio_id, empleado_id = _crear_base(app)
    assert (
        _post_reserva(
            client, servicio_id, empleado_id, "2026-08-21T10:00", "a@example.com"
        ).status_code
        == 201
    )
    rv = _post_reserva(
        client, servicio_id, empleado_id, "2026-08-21T10:15", "b@example.com"
    )
    assert rv.status_code == 409
    assert "ya tiene una reserva" in rv.get_json()["error"]


def test_crear_reserva_solapamiento_parcial(app, client):
    servicio_id, empleado_id = _crear_base(app)
    assert (
        _post_reserva(
            client, servicio_id, empleado_id, "2026-08-21T10:00", "a@example.com"
        ).status_code
        == 201
    )
    rv = _post_reserva(
        client, servicio_id, empleado_id, "2026-08-21T10:20", "b@example.com"
    )
    assert rv.status_code == 409


def test_crear_reserva_adyacente(app, client):
    servicio_id, empleado_id = _crear_base(app)
    assert (
        _post_reserva(
            client, servicio_id, empleado_id, "2026-08-21T10:00", "a@example.com"
        ).status_code
        == 201
    )
    rv = _post_reserva(
        client, servicio_id, empleado_id, "2026-08-21T10:30", "b@example.com"
    )
    assert rv.status_code == 201


def test_disponibilidad_excluye_slots_ocupados(app, client):
    servicio_id, empleado_id = _crear_base(app, time(9, 0), time(12, 0))
    assert (
        _post_reserva(
            client, servicio_id, empleado_id, "2026-08-21T10:00", "a@example.com"
        ).status_code
        == 201
    )
    rv = client.get(f"/api/v1/empleados/{empleado_id}/disponibilidad?fecha=2026-08-21")
    assert rv.status_code == 200
    slots = rv.get_json()["slots"]
    assert "10:00" not in slots
    for slot in ["09:00", "09:30", "10:30", "11:00", "11:30"]:
        assert slot in slots


def test_disponibilidad_reservas_canceladas_no_bloquean(app, client):
    servicio_id, empleado_id = _crear_base(app, time(9, 0), time(12, 0))
    rv = _post_reserva(
        client, servicio_id, empleado_id, "2026-08-21T10:00", "a@example.com"
    )
    reserva_id = rv.get_json()["id"]
    assert (
        client.patch(f"/api/v1/reservas/{reserva_id}/cancelar").status_code == 200
    )
    rv = client.get(f"/api/v1/empleados/{empleado_id}/disponibilidad?fecha=2026-08-21")
    assert rv.status_code == 200
    slots = rv.get_json()["slots"]
    assert "10:00" in slots