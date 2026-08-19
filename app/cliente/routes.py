from __future__ import annotations

import secrets
from datetime import datetime
from functools import wraps
from typing import Callable, Dict

from flask import (
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.cliente import cliente
from app.emails import enviar_email
from app.extensions import db
from app.models import Reserva, Usuario
from app.security import MENSAJE_429, controlar_intentos
from app.whatsapp import enviar_whatsapp_simulado

PASSWORD_ANONIMO = "__reservafacil_anonimo__"


def _format_fecha_hora(iso_str: str) -> str:
    return datetime.fromisoformat(iso_str).strftime("%d/%m/%Y %H:%M")


def _reserva_to_view(reserva: Reserva) -> Dict:
    data = reserva.to_dict()
    data["servicio_nombre"] = reserva.servicio.nombre
    data["empleado_nombre"] = reserva.empleado.nombre
    data["cliente_nombre"] = reserva.usuario.nombre or reserva.usuario.username
    data["fecha_inicio_display"] = _format_fecha_hora(data["fecha_hora_inicio"])
    return data


def _unique_username(email: str) -> str:
    base = email.split("@")[0][:80] or "cliente"
    username = base
    while (
        db.session.execute(db.select(Usuario).where(Usuario.username == username))
        .scalar_one_or_none()
        is not None
    ):
        username = f"{base}_{secrets.token_hex(2).lower()}"
    return username


def cliente_required(view: Callable) -> Callable:
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("rol") != "cliente":
            return redirect(url_for("cliente.login_cliente"))
        usuario = db.session.get(Usuario, session.get("user_id"))
        if usuario is None or usuario.es_admin:
            session.clear()
            return redirect(url_for("cliente.login_cliente"))
        return view(*args, **kwargs)

    return wrapped


def _iniciar_sesion_cliente(usuario: Usuario) -> Response:
    session.clear()
    session["user_id"] = usuario.id
    session["rol"] = "cliente"
    return redirect(url_for("cliente.mis_reservas"))


@cliente.get("/")
def index() -> Response:
    return render_template("index.html")


@cliente.get("/reservas/<codigo>")
def reserva_detalle(codigo: str) -> Response:
    reserva = db.session.execute(
        db.select(Reserva).where(Reserva.codigo == codigo.upper())
    ).scalar_one_or_none()
    if reserva is None:
        abort(404)
    return render_template("reserva_detalle.html", reserva=_reserva_to_view(reserva))


@cliente.get("/registrarse")
def registrarse() -> Response:
    return render_template("registrarse.html")


@cliente.post("/registrarse")
def registrarse_post() -> Response:
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip().lower()
    telefono = request.form.get("telefono", "").strip()
    password = request.form.get("password", "")
    confirmacion = request.form.get("confirmacion", "")

    def _error(mensaje: str) -> Response:
        return (
            render_template(
                "registrarse.html",
                error=mensaje,
                nombre=nombre,
                email=email,
                telefono=telefono,
            ),
            400,
        )

    if not all([nombre, email, password, confirmacion]):
        return _error("Todos los campos son obligatorios.")
    if password != confirmacion:
        return _error("Las contraseñas no coinciden.")

    usuario = db.session.execute(
        db.select(Usuario).where(Usuario.email == email)
    ).scalar_one_or_none()

    if usuario is not None:
        if usuario.es_admin:
            return _error("Ese email pertenece a una cuenta de administrador.")
        if not usuario.verificar_password(PASSWORD_ANONIMO):
            return _error("Ya existe una cuenta con ese email, inicia sesión.")
        usuario.nombre = nombre
        if telefono:
            usuario.telefono = telefono
        usuario.set_password(password)
        db.session.commit()
        return _iniciar_sesion_cliente(usuario)

    nuevo = Usuario(
        username=_unique_username(email),
        nombre=nombre,
        email=email,
        telefono=telefono or None,
        es_admin=False,
    )
    nuevo.set_password(password)
    db.session.add(nuevo)
    db.session.commit()
    return _iniciar_sesion_cliente(nuevo)


@cliente.get("/login-cliente")
def login_cliente() -> Response:
    return render_template("login_cliente.html")


@cliente.post("/login-cliente")
def login_cliente_post() -> Response:
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    ip = request.remote_addr or "desconocida"
    if not controlar_intentos(ip, "login"):
        return (
            render_template(
                "login_cliente.html",
                error=MENSAJE_429,
                email=email,
            ),
            429,
        )
    usuario = db.session.execute(
        db.select(Usuario).where(Usuario.email == email)
    ).scalar_one_or_none()
    if (
        usuario is not None
        and not usuario.es_admin
        and usuario.verificar_password(PASSWORD_ANONIMO)
    ):
        return (
            render_template(
                "login_cliente.html",
                error=(
                    "Esta cuenta se creó con una reserva anónima. "
                    "Regístrate con ese email para activarla."
                ),
                email=email,
            ),
            401,
        )
    if (
        usuario is None
        or usuario.es_admin
        or not usuario.verificar_password(password)
    ):
        return (
            render_template(
                "login_cliente.html",
                error="Email o contraseña incorrectos.",
                email=email,
            ),
            401,
        )
    return _iniciar_sesion_cliente(usuario)


@cliente.get("/logout-cliente")
def logout_cliente() -> Response:
    session.clear()
    return redirect(url_for("cliente.index"))


@cliente.get("/mis-reservas")
@cliente_required
def mis_reservas() -> Response:
    reservas = db.session.execute(
        db.select(Reserva)
        .where(Reserva.usuario_id == session["user_id"])
        .order_by(Reserva.fecha_hora_inicio.desc())
    ).scalars().all()
    return render_template(
        "mis_reservas.html", reservas=[_reserva_to_view(r) for r in reservas]
    )


@cliente.post("/mis-reservas/<int:reserva_id>/cancelar")
@cliente_required
def mis_reservas_cancelar(reserva_id: int) -> Response:
    reserva = db.session.get(Reserva, reserva_id)
    if reserva is None or reserva.usuario_id != session["user_id"]:
        abort(403)
    if reserva.estado not in ("pendiente", "confirmada"):
        abort(403)
    reserva.estado = "cancelada"
    db.session.commit()

    usuario = reserva.usuario
    nombre_cliente = usuario.nombre or usuario.username
    cuerpo = (
        f"Hola {nombre_cliente},\n\n"
        f"Tu reserva {reserva.codigo} fue cancelada.\n"
        f"Servicio: {reserva.servicio.nombre}\n"
        f"Empleado: {reserva.empleado.nombre}\n"
        f"Fecha y hora: {reserva.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')}\n\n"
        "Si quieres reagendar, visítanos en nuestra página. ¡Gracias!"
    )
    enviar_email(usuario.email, f"Reserva cancelada · {reserva.codigo}", cuerpo)
    if usuario.telefono:
        mensaje_whatsapp = (
            f"Hola {nombre_cliente}, tu reserva {reserva.codigo} fue cancelada.\n"
            f"Servicio: {reserva.servicio.nombre}\n"
            f"Empleado: {reserva.empleado.nombre}\n"
            "Si quieres reagendar, visítanos en nuestra página. ¡Gracias!"
        )
        enviar_whatsapp_simulado(usuario.telefono, mensaje_whatsapp)
    flash("Reserva cancelada.")
    return redirect(url_for("cliente.mis_reservas"))