from __future__ import annotations

import csv
import io
from datetime import datetime, time, timedelta
from functools import wraps
from typing import Callable, List, Optional
from zoneinfo import ZoneInfo

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
from sqlalchemy import func

from app.admin import admin
from app.emails import enviar_email
from app.extensions import db
from app.models import Empleado, Reserva, Servicio, Usuario
from app.security import MENSAJE_429, controlar_intentos
from app.whatsapp import enviar_whatsapp_simulado

LIMA_TZ = ZoneInfo("America/Lima")


def _ahora_lima() -> datetime:
    return datetime.now(LIMA_TZ)


def admin_required(view: Callable) -> Callable:
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is None:
            return redirect(url_for("admin.login"))
        usuario = db.session.get(Usuario, user_id)
        if usuario is None or not usuario.es_admin:
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


def _parse_hora(value: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return time(9, 0)


def _count_reservas(estado: Optional[str], dia_inicio: datetime, dia_fin: datetime) -> int:
    query = db.select(func.count()).select_from(Reserva).where(
        Reserva.fecha_hora_inicio >= dia_inicio,
        Reserva.fecha_hora_inicio <= dia_fin,
    )
    if estado is not None:
        query = query.where(Reserva.estado == estado)
    return db.session.execute(query).scalar() or 0


@admin.get("/login")
def login() -> Response:
    return render_template("admin/login.html")


@admin.post("/login")
def login_post() -> Response:
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    ip = request.remote_addr or "desconocida"
    if not controlar_intentos(ip, "login"):
        return (
            render_template(
                "admin/login.html",
                error=MENSAJE_429,
                username=username,
            ),
            429,
        )
    usuario = db.session.execute(
        db.select(Usuario).where(Usuario.username == username)
    ).scalar_one_or_none()
    if (
        usuario is None
        or not usuario.es_admin
        or not usuario.verificar_password(password)
    ):
        return (
            render_template(
                "admin/login.html",
                error="Usuario o contraseña incorrectos.",
                username=username,
            ),
            401,
        )
    session.clear()
    session["user_id"] = usuario.id
    return redirect(url_for("admin.dashboard"))


@admin.get("/logout")
def logout() -> Response:
    session.clear()
    return redirect(url_for("admin.login"))


@admin.get("/")
@admin_required
def dashboard() -> Response:
    hoy = datetime.now()
    dia_inicio = datetime.combine(hoy.date(), time.min)
    dia_fin = datetime.combine(hoy.date(), time.max)
    stats = {
        "total_hoy": _count_reservas(None, dia_inicio, dia_fin),
        "pendientes": _count_reservas("pendiente", dia_inicio, dia_fin),
        "confirmadas": _count_reservas("confirmada", dia_inicio, dia_fin),
        "canceladas": _count_reservas("cancelada", dia_inicio, dia_fin),
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin.get("/reportes")
@admin_required
def reportes() -> Response:
    hoy = _ahora_lima().date()
    inicio_ventana = datetime.combine(hoy - timedelta(days=29), time.min)
    fin_ventana = datetime.combine(hoy, time.max)

    por_dia_raw = db.session.execute(
        db.select(
            func.date(Reserva.fecha_hora_inicio).label("dia"),
            func.count(Reserva.id).label("total"),
        )
        .where(
            Reserva.fecha_hora_inicio >= inicio_ventana,
            Reserva.fecha_hora_inicio <= fin_ventana,
        )
        .group_by(func.date(Reserva.fecha_hora_inicio))
        .order_by(func.date(Reserva.fecha_hora_inicio))
    ).all()
    por_dia = {fila.dia: fila.total for fila in por_dia_raw}

    labels_dias: List[str] = []
    data_dias: List[int] = []
    for i in range(29, -1, -1):
        dia = hoy - timedelta(days=i)
        labels_dias.append(dia.strftime("%d/%m"))
        data_dias.append(por_dia.get(dia.isoformat(), 0))

    top_raw = db.session.execute(
        db.select(Servicio.nombre, func.count(Reserva.id).label("total"))
        .join(Reserva, Reserva.servicio_id == Servicio.id)
        .where(Reserva.estado != "cancelada")
        .group_by(Servicio.nombre)
        .order_by(func.count(Reserva.id).desc())
        .limit(5)
    ).all()
    labels_servicios = [fila.nombre for fila in top_raw]
    data_servicios = [fila.total for fila in top_raw]

    primer_dia_mes = datetime.combine(hoy.replace(day=1), time.min)
    primer_dia_siguiente = datetime.combine(
        (hoy.replace(day=1) + timedelta(days=32)).replace(day=1), time.min
    )
    ingresos_mes = (
        db.session.execute(
            db.select(func.sum(Servicio.precio))
            .join(Reserva, Reserva.servicio_id == Servicio.id)
            .where(
                Reserva.estado.in_(["confirmada", "completada"]),
                Reserva.fecha_hora_inicio >= primer_dia_mes,
                Reserva.fecha_hora_inicio < primer_dia_siguiente,
            )
        ).scalar()
        or 0
    )
    total_mes = (
        db.session.execute(
            db.select(func.count(Reserva.id)).where(
                Reserva.fecha_hora_inicio >= primer_dia_mes,
                Reserva.fecha_hora_inicio < primer_dia_siguiente,
            )
        ).scalar()
        or 0
    )
    canceladas_mes = (
        db.session.execute(
            db.select(func.count(Reserva.id)).where(
                Reserva.estado == "cancelada",
                Reserva.fecha_hora_inicio >= primer_dia_mes,
                Reserva.fecha_hora_inicio < primer_dia_siguiente,
            )
        ).scalar()
        or 0
    )
    tasa_cancelacion = (canceladas_mes / total_mes) if total_mes else 0.0

    chart_datos = {
        "por_dia": {"labels": labels_dias, "data": data_dias},
        "top_servicios": {"labels": labels_servicios, "data": data_servicios},
    }
    return render_template(
        "admin/reportes.html",
        ingresos_mes=ingresos_mes,
        tasa_cancelacion=tasa_cancelacion,
        total_mes=total_mes,
        chart_datos=chart_datos,
    )


@admin.get("/reportes/reservas.csv")
@admin_required
def reportes_csv() -> Response:
    query = (
        db.select(Reserva)
        .join(Usuario, Reserva.usuario_id == Usuario.id)
        .join(Servicio, Reserva.servicio_id == Servicio.id)
        .join(Empleado, Reserva.empleado_id == Empleado.id)
        .order_by(Reserva.fecha_hora_inicio.desc())
    )

    estado = request.args.get("estado", "").strip()
    desde = request.args.get("desde", "").strip()
    hasta = request.args.get("hasta", "").strip()

    if estado:
        query = query.where(Reserva.estado == estado)
    if desde:
        try:
            fecha_desde = datetime.strptime(desde, "%Y-%m-%d").date()
        except ValueError:
            abort(400)
        query = query.where(
            Reserva.fecha_hora_inicio >= datetime.combine(fecha_desde, time.min)
        )
    if hasta:
        try:
            fecha_hasta = datetime.strptime(hasta, "%Y-%m-%d").date()
        except ValueError:
            abort(400)
        query = query.where(
            Reserva.fecha_hora_inicio <= datetime.combine(fecha_hasta, time.max)
        )

    reservas = db.session.execute(query).scalars().all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "codigo",
            "cliente_nombre",
            "cliente_email",
            "servicio",
            "empleado",
            "inicio",
            "fin",
            "estado",
            "precio",
        ]
    )
    for r in reservas:
        writer.writerow(
            [
                r.codigo,
                r.usuario.nombre or r.usuario.username,
                r.usuario.email,
                r.servicio.nombre,
                r.empleado.nombre,
                r.fecha_hora_inicio.strftime("%Y-%m-%d %H:%M"),
                r.fecha_hora_fin.strftime("%Y-%m-%d %H:%M"),
                r.estado,
                f"{r.servicio.precio:.2f}",
            ]
        )

    fecha_archivo = _ahora_lima().strftime("%Y%m%d")
    contenido = "\ufeff" + buffer.getvalue()
    return Response(
        contenido,
        mimetype="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="reservafacil_reservas_{fecha_archivo}.csv"'
            )
        },
    )


@admin.get("/servicios")
@admin_required
def servicios_lista() -> Response:
    servicios = db.session.execute(
        db.select(Servicio).order_by(Servicio.id)
    ).scalars().all()
    return render_template("admin/servicios_lista.html", servicios=servicios)


@admin.route("/servicios/nuevo", methods=["GET", "POST"])
@admin_required
def servicios_nuevo() -> Response:
    if request.method == "POST":
        error = _procesar_servicio_form(None)
        if error is None:
            flash("Servicio creado correctamente.")
            return redirect(url_for("admin.servicios_lista"))
        return (
            render_template("admin/servicios_form.html", servicio=None, error=error),
            400,
        )
    return render_template("admin/servicios_form.html", servicio=None)


@admin.route("/servicios/<int:servicio_id>/editar", methods=["GET", "POST"])
@admin_required
def servicios_editar(servicio_id: int) -> Response:
    servicio = db.session.get(Servicio, servicio_id)
    if servicio is None:
        abort(404)
    if request.method == "POST":
        error = _procesar_servicio_form(servicio)
        if error is None:
            flash("Servicio actualizado correctamente.")
            return redirect(url_for("admin.servicios_lista"))
        return (
            render_template("admin/servicios_form.html", servicio=servicio, error=error),
            400,
        )
    return render_template("admin/servicios_form.html", servicio=servicio)


def _procesar_servicio_form(servicio: Optional[Servicio]) -> Optional[str]:
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    try:
        duracion_minutos = int(request.form.get("duracion_minutos", "30"))
        precio = float(request.form.get("precio", "0"))
    except ValueError:
        return "La duración y el precio deben ser números."
    if not nombre:
        return "El nombre es obligatorio."
    if duracion_minutos <= 0 or precio < 0:
        return "La duración debe ser mayor a 0 y el precio no puede ser negativo."
    activo = "activo" in request.form
    if servicio is None:
        servicio = Servicio(
            nombre=nombre,
            descripcion=descripcion or None,
            duracion_minutos=duracion_minutos,
            precio=precio,
            activo=activo,
        )
        db.session.add(servicio)
    else:
        servicio.nombre = nombre
        servicio.descripcion = descripcion or None
        servicio.duracion_minutos = duracion_minutos
        servicio.precio = precio
        servicio.activo = activo
    db.session.commit()
    return None


@admin.post("/servicios/<int:servicio_id>/eliminar")
@admin_required
def servicios_eliminar(servicio_id: int) -> Response:
    servicio = db.session.get(Servicio, servicio_id)
    if servicio is None:
        abort(404)
    servicio.activo = False
    db.session.commit()
    flash("Servicio desactivado (soft delete).")
    return redirect(url_for("admin.servicios_lista"))


@admin.get("/empleados")
@admin_required
def empleados_lista() -> Response:
    empleados = db.session.execute(
        db.select(Empleado).order_by(Empleado.id)
    ).scalars().all()
    return render_template("admin/empleados_lista.html", empleados=empleados)


@admin.route("/empleados/nuevo", methods=["GET", "POST"])
@admin_required
def empleados_nuevo() -> Response:
    servicios = db.session.execute(db.select(Servicio).order_by(Servicio.id)).scalars().all()
    if request.method == "POST":
        error = _procesar_empleado_form(None, servicios)
        if error is None:
            flash("Empleado creado correctamente.")
            return redirect(url_for("admin.empleados_lista"))
        return (
            render_template(
                "admin/empleados_form.html", empleado=None, servicios=servicios, error=error
            ),
            400,
        )
    return render_template("admin/empleados_form.html", empleado=None, servicios=servicios)


@admin.route("/empleados/<int:empleado_id>/editar", methods=["GET", "POST"])
@admin_required
def empleados_editar(empleado_id: int) -> Response:
    empleado = db.session.get(Empleado, empleado_id)
    if empleado is None:
        abort(404)
    servicios = db.session.execute(db.select(Servicio).order_by(Servicio.id)).scalars().all()
    if request.method == "POST":
        error = _procesar_empleado_form(empleado, servicios)
        if error is None:
            flash("Empleado actualizado correctamente.")
            return redirect(url_for("admin.empleados_lista"))
        return (
            render_template(
                "admin/empleados_form.html",
                empleado=empleado,
                servicios=servicios,
                error=error,
            ),
            400,
        )
    return render_template(
        "admin/empleados_form.html", empleado=empleado, servicios=servicios
    )


def _procesar_empleado_form(
    empleado: Optional[Empleado], servicios: List[Servicio]
) -> Optional[str]:
    nombre = request.form.get("nombre", "").strip()
    if not nombre:
        return "El nombre es obligatorio."
    email = request.form.get("email", "").strip() or None
    telefono = request.form.get("telefono", "").strip() or None
    horario_inicio = _parse_hora(request.form.get("horario_inicio", "09:00"))
    horario_fin = _parse_hora(request.form.get("horario_fin", "18:00"))
    servicio_ids = {int(sid) for sid in request.form.getlist("servicios") if sid.isdigit()}

    if empleado is None:
        empleado = Empleado(
            nombre=nombre,
            email=email,
            telefono=telefono,
            horario_inicio=horario_inicio,
            horario_fin=horario_fin,
        )
        db.session.add(empleado)
    else:
        empleado.nombre = nombre
        empleado.email = email
        empleado.telefono = telefono
        empleado.horario_inicio = horario_inicio
        empleado.horario_fin = horario_fin
        empleado.servicios.clear()

    for sid in servicio_ids:
        servicio = db.session.get(Servicio, sid)
        if servicio is not None:
            empleado.servicios.append(servicio)

    db.session.commit()
    return None


@admin.post("/empleados/<int:empleado_id>/eliminar")
@admin_required
def empleados_eliminar(empleado_id: int) -> Response:
    empleado = db.session.get(Empleado, empleado_id)
    if empleado is None:
        abort(404)
    empleado.activo = False
    db.session.commit()
    flash("Empleado desactivado (soft delete).")
    return redirect(url_for("admin.empleados_lista"))


@admin.get("/reservas")
@admin_required
def reservas_lista() -> Response:
    estado = request.args.get("estado", "").strip()
    fecha = request.args.get("fecha", "").strip()
    query = db.select(Reserva).order_by(Reserva.fecha_hora_inicio)
    if estado:
        query = query.where(Reserva.estado == estado)
    if fecha:
        try:
            fecha_dt = datetime.fromisoformat(fecha).date()
        except ValueError:
            fecha_dt = None
        if fecha_dt is not None:
            dia_inicio = datetime.combine(fecha_dt, time.min)
            dia_fin = datetime.combine(fecha_dt, time.max)
            query = query.where(
                Reserva.fecha_hora_inicio >= dia_inicio,
                Reserva.fecha_hora_inicio <= dia_fin,
            )
    reservas = db.session.execute(query).scalars().all()
    return render_template(
        "admin/reservas_lista.html",
        reservas=reservas,
        estado_filtro=estado,
        fecha_filtro=fecha,
    )


def _cambiar_estado(reserva_id: int, nuevo_estado: str) -> Response:
    reserva = db.session.get(Reserva, reserva_id)
    if reserva is None:
        abort(404)
    if reserva.estado != nuevo_estado:
        reserva.estado = nuevo_estado
        db.session.commit()
        flash(f"Reserva {reserva.codigo} marcada como '{nuevo_estado}'.")
        _notificar_cambio_estado(reserva, nuevo_estado)
    return redirect(url_for("admin.reservas_lista"))


def _notificar_cambio_estado(reserva: Reserva, estado: str) -> None:
    nombre_cliente = reserva.usuario.nombre or reserva.usuario.username
    if estado == "confirmada":
        cuerpo = (
            f"Hola {nombre_cliente},\n\n"
            f"Tu reserva {reserva.codigo} fue confirmada.\n"
            f"Servicio: {reserva.servicio.nombre}\n"
            f"Empleado: {reserva.empleado.nombre}\n"
            f"Fecha y hora: {reserva.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')}\n\n"
            "¡Te esperamos!"
        )
        enviar_email(
            reserva.usuario.email,
            f"Tu reserva fue confirmada · {reserva.codigo}",
            cuerpo,
        )
        if reserva.usuario.telefono:
            enviar_whatsapp_simulado(
                reserva.usuario.telefono,
                f"Hola {nombre_cliente}, tu reserva {reserva.codigo} fue confirmada.\n¡Te esperamos!",
            )
    elif estado == "completada":
        cuerpo = (
            f"Hola {nombre_cliente},\n\n"
            "¡Gracias por tu visita! Esperamos que hayas quedado feliz.\n"
            f"Tu reserva {reserva.codigo} fue completada. ¡Vuelve pronto!"
        )
        enviar_email(
            reserva.usuario.email,
            f"Gracias por tu visita · {reserva.codigo}",
            cuerpo,
        )
        if reserva.usuario.telefono:
            enviar_whatsapp_simulado(
                reserva.usuario.telefono,
                f"Hola {nombre_cliente}, ¡gracias por tu visita! Tu reserva {reserva.codigo} fue completada. ¡Vuelve pronto!",
            )


@admin.post("/reservas/<int:reserva_id>/confirmar")
@admin_required
def reservas_confirmar(reserva_id: int) -> Response:
    return _cambiar_estado(reserva_id, "confirmada")


@admin.post("/reservas/<int:reserva_id>/cancelar")
@admin_required
def reservas_cancelar(reserva_id: int) -> Response:
    return _cambiar_estado(reserva_id, "cancelada")


@admin.post("/reservas/<int:reserva_id>/completar")
@admin_required
def reservas_completar(reserva_id: int) -> Response:
    return _cambiar_estado(reserva_id, "completada")