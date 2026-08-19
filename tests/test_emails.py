from pathlib import Path

from app.emails import EMAIL_LOG_PATH

LOG = Path("instance") / "emails.log"


def _limpiar_log():
    if LOG.exists():
        LOG.unlink()


def test_email_crear_reserva(client, seed):
    _limpiar_log()
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
    assert rv.status_code == 201
    codigo = rv.get_json()["codigo"]

    assert LOG.exists()
    contenido = LOG.read_text(encoding="utf-8")
    assert codigo in contenido
    assert usuario.email in contenido
    assert "Reserva registrada" in contenido


def test_email_cancelar_reserva(client, seed):
    _limpiar_log()
    usuario, servicio, empleado = seed()
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
    assert "Reserva cancelada" in contenido
    assert usuario.email in contenido