def test_index(client):
    rv = client.get("/")
    assert rv.status_code == 200
    assert "ReservaFácil" in rv.get_data(as_text=True)


def test_reserva_detalle(client, seed):
    usuario, servicio, empleado = seed()
    rv = client.post(
        "/api/v1/reservas",
        json={
            "usuario_id": usuario.id,
            "servicio_id": servicio.id,
            "empleado_id": empleado.id,
            "fecha_hora_inicio": "2026-08-20T11:00",
        },
    )
    codigo = rv.get_json()["codigo"]

    rv2 = client.get(f"/reservas/{codigo}")
    assert rv2.status_code == 200
    html = rv2.get_data(as_text=True)
    assert codigo in html
    assert "Corte de cabello" in html
    assert "Ana Gomez" in html


def test_reserva_detalle_inexistente(client):
    rv = client.get("/reservas/RF-000000")
    assert rv.status_code == 404