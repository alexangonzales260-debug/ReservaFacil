"""Siembra la base de datos con datos de ejemplo.

Uso: python seed.py
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from app import create_app
from app.extensions import db
from app.models import Empleado, Servicio

SERVICIOS = [
    {
        "nombre": "Corte de cabello",
        "descripcion": "Corte clásico o moderno",
        "duracion_minutos": 30,
        "precio": 25.0,
    },
    {
        "nombre": "Tinte",
        "descripcion": "Coloración completa del cabello",
        "duracion_minutos": 90,
        "precio": 80.0,
    },
    {
        "nombre": "Peinado",
        "descripcion": "Peinado para ocasiones especiales",
        "duracion_minutos": 45,
        "precio": 40.0,
    },
]

EMPLEADOS = [
    {
        "nombre": "María",
        "email": "maria@reservafacil.pe",
        "telefono": "999000111",
        "horario_inicio": "09:00",
        "horario_fin": "18:00",
    },
    {
        "nombre": "Carlos",
        "email": "carlos@reservafacil.pe",
        "telefono": "999000222",
        "horario_inicio": "10:00",
        "horario_fin": "19:00",
    },
]


def seed() -> None:
    servicios: List[Servicio] = []
    for data in SERVICIOS:
        obj = db.session.execute(
            db.select(Servicio).where(Servicio.nombre == data["nombre"])
        ).scalar_one_or_none()
        if obj is None:
            obj = Servicio(**data)
            db.session.add(obj)
        servicios.append(obj)

    for data in EMPLEADOS:
        emp = db.session.execute(
            db.select(Empleado).where(Empleado.nombre == data["nombre"])
        ).scalar_one_or_none()
        if emp is None:
            emp = Empleado(
                nombre=data["nombre"],
                email=data["email"],
                telefono=data["telefono"],
                horario_inicio=datetime.strptime(data["horario_inicio"], "%H:%M").time(),
                horario_fin=datetime.strptime(data["horario_fin"], "%H:%M").time(),
            )
            db.session.add(emp)
        for servicio in servicios:
            if servicio not in emp.servicios:
                emp.servicios.append(servicio)

    db.session.commit()
    empleados = db.session.execute(db.select(Empleado)).scalars().all()
    print("Seed completado.")
    print("  Servicios:", ", ".join(s.nombre for s in servicios))
    print("  Empleados:", ", ".join(e.nombre for e in empleados))


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        seed()