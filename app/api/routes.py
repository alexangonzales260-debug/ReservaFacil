from __future__ import annotations

import secrets
from datetime import datetime, time, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo

from flask import Response, jsonify, make_response, request

from app.api import api
from app.emails import enviar_email
from app.extensions import db
from app.models import Empleado, Reserva, Servicio, Usuario
from app.whatsapp import enviar_whatsapp_simulado

LIMA_TZ = ZoneInfo("America/Lima")


def _parse_local_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is not None:
        dt = dt.astimezone(LIMA_TZ).replace(tzinfo=None)
    return dt


def _generate_slots(start: time, end: time) -> List[str]:
    slots: List[str] = []
    current = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)
    while current < end_dt:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=30)
    return slots


def _generate_unique_codigo() -> str:
    while True:
        codigo = Reserva.generate_codigo()
        existing = db.session.execute(
            db.select(Reserva).where(Reserva.codigo == codigo)
        ).scalar_one_or_none()
        if existing is None:
            return codigo


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


def _get_or_create_cliente(
    nombre: str, email: str, telefono: Optional[str] = None
) -> Usuario:
    usuario = db.session.execute(
        db.select(Usuario).where(Usuario.email == email)
    ).scalar_one_or_none()
    if usuario is not None:
        if nombre:
            usuario.nombre = nombre
        if telefono:
            usuario.telefono = telefono
        return usuario
    usuario = Usuario(
        username=_unique_username(email),
        nombre=nombre,
        email=email,
        telefono=telefono,
    )
    usuario.set_password(secrets.token_urlsafe(12))
    db.session.add(usuario)
    return usuario


@api.get("/servicios")
def list_servicios() -> Response:
    servicios = db.session.execute(
        db.select(Servicio).where(Servicio.activo.is_(True)).order_by(Servicio.id)
    ).scalars().all()
    return make_response(
        jsonify({"servicios": [s.to_dict() for s in servicios]}), 200
    )


@api.get("/empleados")
def list_empleados() -> Response:
    empleados = db.session.execute(
        db.select(Empleado).where(Empleado.activo.is_(True)).order_by(Empleado.id)
    ).scalars().all()
    return make_response(
        jsonify({"empleados": [e.to_dict() for e in empleados]}), 200
    )


@api.get("/empleados/<int:empleado_id>/disponibilidad")
def get_disponibilidad(empleado_id: int) -> Response:
    empleado = db.session.get(Empleado, empleado_id)
    if empleado is None:
        return make_response(jsonify({"error": "empleado no encontrado"}), 404)

    fecha = request.args.get("fecha")
    if not fecha:
        return make_response(
            jsonify({"error": "parametro 'fecha' requerido (formato YYYY-MM-DD)"}),
            400,
        )
    try:
        fecha_dt = datetime.fromisoformat(fecha).date()
    except ValueError:
        return make_response(
            jsonify({"error": "fecha invalida (formato YYYY-MM-DD)"}), 400
        )

    dia_inicio = datetime.combine(fecha_dt, time.min)
    dia_fin = datetime.combine(fecha_dt, time.max)
    reservas = db.session.execute(
        db.select(Reserva).where(
            Reserva.empleado_id == empleado_id,
            Reserva.estado.in_(["pendiente", "confirmada"]),
            Reserva.fecha_hora_inicio < dia_fin,
            Reserva.fecha_hora_fin > dia_inicio,
        )
    ).scalars().all()

    slots_disponibles: List[str] = []
    for slot in _generate_slots(empleado.horario_inicio, empleado.horario_fin):
        slot_inicio = datetime.combine(
            fecha_dt, datetime.strptime(slot, "%H:%M").time()
        )
        slot_fin = slot_inicio + timedelta(minutes=30)
        ocupado = any(
            r.fecha_hora_inicio < slot_fin and r.fecha_hora_fin > slot_inicio
            for r in reservas
        )
        if not ocupado:
            slots_disponibles.append(slot)

    return make_response(
        jsonify(
            {
                "empleado_id": empleado_id,
                "fecha": fecha,
                "slots": slots_disponibles,
            }
        ),
        200,
    )


@api.post("/reservas")
def crear_reserva() -> Response:
    data = request.get_json(silent=True) or {}
    usuario_id = data.get("usuario_id")
    servicio_id = data.get("servicio_id")
    empleado_id = data.get("empleado_id")
    fecha_hora_inicio = data.get("fecha_hora_inicio")
    notas = data.get("notas")

    if not all([servicio_id, empleado_id, fecha_hora_inicio]):
        return make_response(
            jsonify(
                {
                    "error": (
                        "campos requeridos: servicio_id, empleado_id, "
                        "fecha_hora_inicio y (usuario_id o nombre+email)"
                    )
                }
            ),
            400,
        )

    servicio = db.session.get(Servicio, servicio_id)
    empleado = db.session.get(Empleado, empleado_id)
    if servicio is None or empleado is None:
        return make_response(
            jsonify({"error": "servicio o empleado no encontrado"}), 404
        )

    if usuario_id:
        usuario = db.session.get(Usuario, usuario_id)
        if usuario is None:
            return make_response(jsonify({"error": "usuario no encontrado"}), 404)
    else:
        nombre = data.get("nombre")
        email = data.get("email")
        if not nombre or not email:
            return make_response(
                jsonify({"error": "se requiere usuario_id o (nombre y email)"}), 400
            )
        usuario = _get_or_create_cliente(str(nombre), str(email), data.get("telefono"))
        db.session.flush()

    try:
        inicio = _parse_local_datetime(str(fecha_hora_inicio))
    except ValueError:
        return make_response(
            jsonify({"error": "fecha_hora_inicio invalida (formato ISO 8601)"}), 400
        )

    fin = inicio + timedelta(minutes=servicio.duracion_minutos)

    if Reserva.hay_conflicto(
        empleado_id=empleado.id,
        fecha_hora_inicio=inicio,
        fecha_hora_fin=fin,
    ):
        return make_response(
            jsonify({"error": "El empleado ya tiene una reserva en ese horario"}), 409
        )

    reserva = Reserva(
        codigo=_generate_unique_codigo(),
        usuario_id=usuario.id,
        servicio_id=servicio.id,
        empleado_id=empleado.id,
        fecha_hora_inicio=inicio,
        fecha_hora_fin=fin,
        notas=notas or None,
    )
    db.session.add(reserva)
    db.session.commit()

    nombre_cliente = usuario.nombre or usuario.username
    cuerpo = (
        f"Hola {nombre_cliente},\n\n"
        f"Tu reserva fue registrada con el código {reserva.codigo}.\n"
        f"Servicio: {servicio.nombre}\n"
        f"Empleado: {empleado.nombre}\n"
        f"Fecha y hora: {reserva.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')}\n\n"
        "¡Te esperamos en la peluquería!"
    )
    enviar_email(
        usuario.email,
        f"Reserva registrada · {reserva.codigo}",
        cuerpo,
    )

    if usuario.telefono:
        mensaje_whatsapp = (
            f"Hola {nombre_cliente}, tu reserva {reserva.codigo} quedó registrada.\n"
            f"Servicio: {servicio.nombre}\n"
            f"Empleado: {empleado.nombre}\n"
            f"Fecha y hora: {reserva.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')}\n"
            "¡Te esperamos!"
        )
        enviar_whatsapp_simulado(usuario.telefono, mensaje_whatsapp)

    return make_response(jsonify(reserva.to_dict()), 201)


@api.get("/reservas/codigo/<codigo>")
def get_reserva_por_codigo(codigo: str) -> Response:
    reserva = db.session.execute(
        db.select(Reserva).where(Reserva.codigo == codigo.upper())
    ).scalar_one_or_none()
    if reserva is None:
        return make_response(jsonify({"error": "reserva no encontrada"}), 404)
    return make_response(jsonify(reserva.to_dict()), 200)


@api.get("/reservas/<int:reserva_id>")
def get_reserva(reserva_id: int) -> Response:
    reserva = db.session.get(Reserva, reserva_id)
    if reserva is None:
        return make_response(jsonify({"error": "reserva no encontrada"}), 404)
    return make_response(jsonify(reserva.to_dict()), 200)


@api.patch("/reservas/<int:reserva_id>/cancelar")
def cancelar_reserva(reserva_id: int) -> Response:
    reserva = db.session.get(Reserva, reserva_id)
    if reserva is None:
        return make_response(jsonify({"error": "reserva no encontrada"}), 404)
    reserva.estado = "cancelada"
    db.session.commit()

    nombre_cliente = reserva.usuario.nombre or reserva.usuario.username
    cuerpo = (
        f"Hola {nombre_cliente},\n\n"
        f"Tu reserva {reserva.codigo} fue cancelada.\n"
        f"Servicio: {reserva.servicio.nombre}\n"
        f"Empleado: {reserva.empleado.nombre}\n"
        f"Fecha y hora: {reserva.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')}\n\n"
        "Si quieres reagendar, visítanos en nuestra página. ¡Gracias!"
    )
    enviar_email(
        reserva.usuario.email,
        f"Reserva cancelada · {reserva.codigo}",
        cuerpo,
    )

    if reserva.usuario.telefono:
        mensaje_whatsapp = (
            f"Hola {nombre_cliente}, tu reserva {reserva.codigo} fue cancelada.\n"
            f"Servicio: {reserva.servicio.nombre}\n"
            f"Empleado: {reserva.empleado.nombre}\n"
            "Si quieres reagendar, visítanos en nuestra página. ¡Gracias!"
        )
        enviar_whatsapp_simulado(reserva.usuario.telefono, mensaje_whatsapp)

    return make_response(jsonify(reserva.to_dict()), 200)