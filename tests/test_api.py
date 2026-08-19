def test_get_servicios_vacio(client):
    rv = client.get("/api/v1/servicios")
    assert rv.status_code == 200
    assert rv.get_json() == {"servicios": []}


def test_get_empleados_vacio(client):
    rv = client.get("/api/v1/empleados")
    assert rv.status_code == 200
    assert rv.get_json() == {"empleados": []}


def test_get_servicios_con_seed(client, seed):
    _, servicio, _ = seed()
    rv = client.get("/api/v1/servicios")
    data = rv.get_json()
    assert rv.status_code == 200
    assert len(data["servicios"]) == 1
    assert data["servicios"][0]["nombre"] == "Corte de cabello"
    assert data["servicios"][0]["precio"] == 25.0


def test_get_empleados_con_seed(client, seed):
    _, _, empleado = seed()
    rv = client.get("/api/v1/empleados")
    data = rv.get_json()
    assert rv.status_code == 200
    assert len(data["empleados"]) == 1
    assert data["empleados"][0]["nombre"] == "Ana Gomez"
    assert data["empleados"][0]["horario_inicio"] == "09:00"
    assert 1 in data["empleados"][0]["servicios"]


def test_get_disponibilidad(client, seed):
    _, _, empleado = seed()
    rv = client.get(f"/api/v1/empleados/{empleado.id}/disponibilidad?fecha=2026-08-20")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["fecha"] == "2026-08-20"
    assert data["slots"][0] == "09:00"
    assert "18:00" not in data["slots"]
    assert len(data["slots"]) == 18


def test_get_disponibilidad_sin_fecha(client, seed):
    _, _, empleado = seed()
    rv = client.get(f"/api/v1/empleados/{empleado.id}/disponibilidad")
    assert rv.status_code == 400


def test_get_disponibilidad_empleado_inexistente(client):
    rv = client.get("/api/v1/empleados/9999/disponibilidad?fecha=2026-08-20")
    assert rv.status_code == 404


def test_post_reserva(client, seed):
    usuario, servicio, empleado = seed()
    payload = {
        "usuario_id": usuario.id,
        "servicio_id": servicio.id,
        "empleado_id": empleado.id,
        "fecha_hora_inicio": "2026-08-20T10:00",
        "notas": "preferencia silla junto a ventana",
    }
    rv = client.post("/api/v1/reservas", json=payload)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["codigo"].startswith("RF-")
    assert len(data["codigo"]) == 9
    assert data["estado"] == "pendiente"
    assert data["fecha_hora_inicio"] == "2026-08-20T10:00"
    assert data["fecha_hora_fin"] == "2026-08-20T10:30"


def test_post_reserva_anonimo(client, seed):
    _, servicio, empleado = seed()
    payload = {
        "servicio_id": servicio.id,
        "empleado_id": empleado.id,
        "fecha_hora_inicio": "2026-08-20T15:00",
        "nombre": "Pedro Rojas",
        "email": "pedro@example.com",
        "telefono": "999888777",
        "notas": "primer corte",
    }
    rv = client.post("/api/v1/reservas", json=payload)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["codigo"].startswith("RF-")
    assert data["estado"] == "pendiente"


def test_post_reserva_anonimo_sin_datos(client, seed):
    _, servicio, empleado = seed()
    rv = client.post(
        "/api/v1/reservas",
        json={
            "servicio_id": servicio.id,
            "empleado_id": empleado.id,
            "fecha_hora_inicio": "2026-08-20T15:00",
        },
    )
    assert rv.status_code == 400


def test_get_reserva_por_codigo(client, seed):
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
    rv2 = client.get(f"/api/v1/reservas/codigo/{codigo}")
    assert rv2.status_code == 200
    assert rv2.get_json()["codigo"] == codigo


def test_get_reserva_por_codigo_inexistente(client):
    rv = client.get("/api/v1/reservas/codigo/RF-ZZZZZZ")
    assert rv.status_code == 404


def test_post_reserva_datos_invalidos(client):
    rv = client.post("/api/v1/reservas", json={})
    assert rv.status_code == 400


def test_post_reserva_referencias_inexistentes(client):
    payload = {
        "usuario_id": 999,
        "servicio_id": 999,
        "empleado_id": 999,
        "fecha_hora_inicio": "2026-08-20T10:00",
    }
    rv = client.post("/api/v1/reservas", json=payload)
    assert rv.status_code == 404


def test_get_reserva_detalle(client, seed):
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
    reserva_id = rv.get_json()["id"]
    rv2 = client.get(f"/api/v1/reservas/{reserva_id}")
    assert rv2.status_code == 200
    assert rv2.get_json()["codigo"].startswith("RF-")


def test_get_reserva_inexistente(client):
    rv = client.get("/api/v1/reservas/9999")
    assert rv.status_code == 404


def test_cancelar_reserva(client, seed):
    usuario, servicio, empleado = seed()
    rv = client.post(
        "/api/v1/reservas",
        json={
            "usuario_id": usuario.id,
            "servicio_id": servicio.id,
            "empleado_id": empleado.id,
            "fecha_hora_inicio": "2026-08-20T12:00",
        },
    )
    reserva_id = rv.get_json()["id"]
    rv2 = client.patch(f"/api/v1/reservas/{reserva_id}/cancelar")
    assert rv2.status_code == 200
    assert rv2.get_json()["estado"] == "cancelada"


def test_cancelar_reserva_inexistente(client):
    rv = client.patch("/api/v1/reservas/9999/cancelar")
    assert rv.status_code == 404