from __future__ import annotations

import secrets
from datetime import datetime, time
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

empleado_servicio = Table(
    "empleado_servicio",
    db.metadata,
    Column("empleado_id", ForeignKey("empleado.id"), primary_key=True),
    Column("servicio_id", ForeignKey("servicio.id"), primary_key=True),
)


class Usuario(db.Model):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    nombre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    es_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    reservas: Mapped[List["Reserva"]] = relationship(back_populates="usuario")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def verificar_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "nombre": self.nombre,
            "email": self.email,
            "telefono": self.telefono,
            "es_admin": self.es_admin,
            "created_at": self.created_at.isoformat(timespec="minutes"),
        }


class Servicio(db.Model):
    __tablename__ = "servicio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duracion_minutos: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    precio: Mapped[float] = mapped_column(Float, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    empleados: Mapped[List["Empleado"]] = relationship(
        secondary=empleado_servicio, back_populates="servicios"
    )
    reservas: Mapped[List["Reserva"]] = relationship(back_populates="servicio")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "duracion_minutos": self.duracion_minutos,
            "precio": self.precio,
            "activo": self.activo,
        }


class Empleado(db.Model):
    __tablename__ = "empleado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    horario_inicio: Mapped[time] = mapped_column(Time, default=time(9, 0), nullable=False)
    horario_fin: Mapped[time] = mapped_column(Time, default=time(18, 0), nullable=False)

    servicios: Mapped[List["Servicio"]] = relationship(
        secondary=empleado_servicio, back_populates="empleados"
    )
    reservas: Mapped[List["Reserva"]] = relationship(back_populates="empleado")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "telefono": self.telefono,
            "activo": self.activo,
            "horario_inicio": self.horario_inicio.strftime("%H:%M"),
            "horario_fin": self.horario_fin.strftime("%H:%M"),
            "servicios": [s.id for s in self.servicios],
        }


class Reserva(db.Model):
    __tablename__ = "reserva"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(9), unique=True, nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicio.id"), nullable=False)
    empleado_id: Mapped[int] = mapped_column(ForeignKey("empleado.id"), nullable=False)
    fecha_hora_inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fecha_hora_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente", nullable=False)
    notas: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="reservas")
    servicio: Mapped["Servicio"] = relationship(back_populates="reservas")
    empleado: Mapped["Empleado"] = relationship(back_populates="reservas")

    @classmethod
    def generate_codigo(cls) -> str:
        return "RF-" + secrets.token_hex(3).upper()

    @staticmethod
    def hay_conflicto(
        empleado_id: int,
        fecha_hora_inicio: datetime,
        fecha_hora_fin: datetime,
        excluir_reserva_id: Optional[int] = None,
    ) -> bool:
        query = db.select(Reserva).where(
            Reserva.empleado_id == empleado_id,
            Reserva.estado.in_(["pendiente", "confirmada"]),
            Reserva.fecha_hora_inicio < fecha_hora_fin,
            Reserva.fecha_hora_fin > fecha_hora_inicio,
        )
        if excluir_reserva_id is not None:
            query = query.where(Reserva.id != excluir_reserva_id)
        return db.session.execute(query).scalars().first() is not None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "codigo": self.codigo,
            "usuario_id": self.usuario_id,
            "servicio_id": self.servicio_id,
            "empleado_id": self.empleado_id,
            "fecha_hora_inicio": self.fecha_hora_inicio.isoformat(timespec="minutes"),
            "fecha_hora_fin": self.fecha_hora_fin.isoformat(timespec="minutes"),
            "estado": self.estado,
            "notas": self.notas,
            "created_at": self.created_at.isoformat(timespec="minutes"),
        }