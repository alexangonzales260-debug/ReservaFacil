from __future__ import annotations

from datetime import datetime
from typing import Dict

from flask import Response, abort, render_template

from app.cliente import cliente
from app.extensions import db
from app.models import Reserva


def _format_fecha_hora(iso_str: str) -> str:
    return datetime.fromisoformat(iso_str).strftime("%d/%m/%Y %H:%M")


def _reserva_to_view(reserva: Reserva) -> Dict:
    data = reserva.to_dict()
    data["servicio_nombre"] = reserva.servicio.nombre
    data["empleado_nombre"] = reserva.empleado.nombre
    data["cliente_nombre"] = reserva.usuario.nombre or reserva.usuario.username
    data["fecha_inicio_display"] = _format_fecha_hora(data["fecha_hora_inicio"])
    return data


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