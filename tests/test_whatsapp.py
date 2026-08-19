from pathlib import Path

from app.extensions import db

LOG = Path("instance") / "whatsapp.log"


def _limpiar_log():
    if LOG.exists():
        LOG.unlink()


def _crear_reserva(client, seed):
    usuario, servicio, empleado = seed()
    rv = client.post(
        "/api/v1/reservas",
        json={
            "usuario_id": usuario.id,
            "servicio_id": servicio.id,
            "empleado_id": empleado.id,
            "fecha_hora_inicio": "2026-08-25T10:00",
        },
    )
    return rv, usuario


def test_whatsapp_crear_reserva_con_telefono(client, seed):
    _limpiar_log()
    usuario, servicio, empleado = seed()
    usuario.telefono = "999111222"
    db.session.add(usuario)
    db.session.commit()

    rv = client.post(
        "/api/v1/reservas",
        json={
            "usuario_id": usuario.id,
            "servicio_id": servicio.id,
            "empleado_id": empleado.id,
            "fecha_hora_inicio": "2026-08-25T10:00",
        },
    )
    assert rv.status_code == 201
    codigo = rv.get_json()["codigo"]

    assert LOG.exists()
    contenido = LOG.read_text(encoding="utf-8")
    assert codigo in contenido
    assert "999111222" in contenido


def test_whatsapp_cancelar_reserva(client, seed):
    _limpiar_log()
    usuario, servicio, empleado = seed()
    usuario.telefono = "999111222"
    db.session.add(usuario)
    db.session.commit()

    rv = client.post(
        "/api/v1/reservas",
        json={
            "usuario_id": usuario.id,
            "servicio_id": servicio.id,
            "empleado_id": empleado.id,
            "fecha_hora_inicio": "2026-08-25T11:00",
        },
    )
    reserva_id = rv.get_json()["id"]

    rv2 = client.patch(f"/api/v1/reservas/{reserva_id}/cancelar")
    assert rv2.status_code == 200

    contenido = LOG.read_text(encoding="utf-8")
    assert "fue cancelada" in contenido
    assert "999111222" in contenido


def test_whatsapp_sin_telefono_no_escribe(client, seed):
    _limpiar_log()
    rv, _ = _crear_reserva(client, seed)
    assert rv.status_code == 201
    assert not LOG.exists()