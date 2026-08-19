from app.extensions import db
from app.models import Reserva, Usuario


def _registrar(
    client,
    nombre="Cliente Uno",
    email="uno@example.com",
    telefono="999111222",
    password="clave-secreta",
):
    return client.post(
        "/registrarse",
        data={
            "nombre": nombre,
            "email": email,
            "telefono": telefono,
            "password": password,
            "confirmacion": password,
        },
    )


def _reserva_anonima(client, servicio, empleado, nombre, email, fecha):
    return client.post(
        "/api/v1/reservas",
        json={
            "servicio_id": servicio.id,
            "empleado_id": empleado.id,
            "fecha_hora_inicio": fecha,
            "nombre": nombre,
            "email": email,
        },
    )


def test_registro_crea_usuario_y_loguea(client):
    rv = _registrar(client)
    assert rv.status_code == 302
    assert "/mis-reservas" in rv.headers["Location"]
    with client.session_transaction() as sess:
        assert sess["rol"] == "cliente"
        assert "user_id" in sess
    with client.application.app_context():
        usuario = db.session.execute(
            db.select(Usuario).where(Usuario.email == "uno@example.com")
        ).scalar_one()
        assert usuario.es_admin is False


def test_registro_adopta_usuario_anonimo(client, seed):
    _, servicio, empleado = seed()
    anon_email = "anon@example.com"
    rv = client.post(
        "/api/v1/reservas",
        json={
            "servicio_id": servicio.id,
            "empleado_id": empleado.id,
            "fecha_hora_inicio": "2026-08-25T11:00",
            "nombre": "Cliente Anónimo",
            "email": anon_email,
            "telefono": "999333444",
        },
    )
    assert rv.status_code == 201
    reserva_id = rv.get_json()["id"]

    reg = client.post(
        "/registrarse",
        data={
            "nombre": "Cliente Adoptado",
            "email": anon_email,
            "telefono": "999333444",
            "password": "nueva-clave",
            "confirmacion": "nueva-clave",
        },
    )
    assert reg.status_code == 302
    assert "/mis-reservas" in reg.headers["Location"]
    with client.session_transaction() as sess:
        assert sess["rol"] == "cliente"

    with client.application.app_context():
        usuario = db.session.execute(
            db.select(Usuario).where(Usuario.email == anon_email)
        ).scalar_one()
        assert usuario.es_admin is False
        reserva = db.session.get(Reserva, reserva_id)
        assert reserva.usuario_id == usuario.id


def test_login_incorrecto_error_sin_sesion(client):
    _registrar(client, email="log@example.com", password="clave-ok")
    client.get("/logout-cliente")
    rv = client.post(
        "/login-cliente",
        data={"email": "log@example.com", "password": "clave-mala"},
    )
    assert rv.status_code == 401
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_mis_reservas_sin_sesion_redirige(client):
    rv = client.get("/mis-reservas")
    assert rv.status_code == 302
    assert "/login-cliente" in rv.headers["Location"]


def test_mis_reservas_solo_del_usuario(client, seed):
    _registrar(client, email="a@example.com")
    _, servicio, empleado = seed()
    rv_a = _reserva_anonima(
        client, servicio, empleado, "A", "a@example.com", "2026-08-25T12:00"
    )
    rv_b = _reserva_anonima(
        client, servicio, empleado, "B", "b@example.com", "2026-08-25T13:00"
    )
    assert rv_a.status_code == 201
    assert rv_b.status_code == 201
    codigo_a = rv_a.get_json()["codigo"]
    codigo_b = rv_b.get_json()["codigo"]

    rv = client.get("/mis-reservas")
    assert rv.status_code == 200
    body = rv.get_data(as_text=True)
    assert codigo_a in body
    assert codigo_b not in body


def test_cancelar_reserva_propia_pendiente(client, seed):
    _registrar(client, email="dueno@example.com")
    _, servicio, empleado = seed()
    rv = _reserva_anonima(
        client, servicio, empleado, "Dueño", "dueno@example.com", "2026-08-25T14:00"
    )
    reserva_id = rv.get_json()["id"]

    rv2 = client.post(f"/mis-reservas/{reserva_id}/cancelar")
    assert rv2.status_code == 302
    with client.application.app_context():
        reserva = db.session.get(Reserva, reserva_id)
        assert reserva.estado == "cancelada"


def test_cancelar_reserva_ajena_403(client, seed):
    _registrar(client, email="victima@example.com")
    _, servicio, empleado = seed()
    rv_b = _reserva_anonima(
        client, servicio, empleado, "B", "b@example.com", "2026-08-25T15:00"
    )
    reserva_b_id = rv_b.get_json()["id"]

    rv = client.post(f"/mis-reservas/{reserva_b_id}/cancelar")
    assert rv.status_code == 403
    with client.application.app_context():
        reserva = db.session.get(Reserva, reserva_b_id)
        assert reserva.estado != "cancelada"


def test_post_reservas_anonimo_sigue_funcionando(client, seed):
    _, servicio, empleado = seed()
    rv = client.post(
        "/api/v1/reservas",
        json={
            "servicio_id": servicio.id,
            "empleado_id": empleado.id,
            "fecha_hora_inicio": "2026-08-25T16:00",
            "nombre": "Anónimo",
            "email": "anonimo@example.com",
        },
    )
    assert rv.status_code == 201
    assert rv.get_json()["estado"] == "pendiente"


def test_login_anonimo_con_sentinel_rechazado(client, seed):
    from app.cliente.routes import PASSWORD_ANONIMO

    _, servicio, empleado = seed()
    anon_email = "anonx@example.com"
    rv = client.post(
        "/api/v1/reservas",
        json={
            "servicio_id": servicio.id,
            "empleado_id": empleado.id,
            "fecha_hora_inicio": "2026-08-25T17:30",
            "nombre": "Anónimo X",
            "email": anon_email,
        },
    )
    assert rv.status_code == 201

    login = client.post(
        "/login-cliente",
        data={"email": anon_email, "password": PASSWORD_ANONIMO},
    )
    assert login.status_code == 401
    with client.session_transaction() as sess:
        assert "user_id" not in sess

    mis = client.get("/mis-reservas")
    assert mis.status_code == 302