# ReservaFácil

Sistema web de reservas para una peluquería local en Lima, Perú. Permite a los clientes agendar citas en línea (elegir servicio, empleado y horario disponible) y al administrador gestionar servicios, empleados y todas las reservas desde un panel protegido.

## Stack tecnológico

- **Backend:** Python 3.12 + Flask 3.x
- **ORM:** Flask-SQLAlchemy / SQLAlchemy 2.x (modelos con `Mapped[]` y `mapped_column`)
- **Base de datos:** SQLite (archivo único `instance/reservafacil.db`)
- **Frontend:** Jinja2 + TailwindCSS vía CDN + JavaScript vanilla
- **Seguridad:** Flask-WTF (CSRF), contraseñas hasheadas con Werkzeug
- **Tests:** pytest

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py          # opcional: datos de ejemplo + usuario admin
```

## Ejecución

```bash
python run.py
```

Abre `http://localhost:5000`. Si la base de datos está vacía, `run.py` ejecuta el seed automáticamente.

## Credenciales de administración

- **Usuario:** `admin`
- **Contraseña:** `admin123`

Panel en `http://localhost:5000/admin`.

## Tests

```bash
pytest -v
./validate.sh
```

`validate.sh` verifica: sintaxis Python, presence de `hay_conflicto`, ausencia de `utcnow()`, uso de `enviar_email`, `pytest`, APIs prohibidas (`eval`/`exec`/`os.system`) y que la base SQLite sea creable.

## Estructura de carpetas

```
ReservaFacil/
├── app/
│   ├── __init__.py       # create_app() (factory)
│   ├── models.py         # Usuario, Servicio, Empleado, Reserva
│   ├── extensions.py     # db (SQLAlchemy), csrf (Flask-WTF)
│   ├── emails.py         # emails simulados (consola + instance/emails.log)
│   ├── admin/            # blueprint panel administrador
│   ├── cliente/          # blueprint flujo cliente
│   └── api/              # blueprint API JSON (/api/v1)
├── templates/            # Jinja2 + Tailwind (incluye templates/admin/)
├── static/               # app.js, style.css
├── tests/                # conftest.py + test_*.py
├── seed.py               # datos de ejemplo + admin
├── run.py                # punto de entrada del servidor
├── requirements.txt
├── validate.sh
└── docs de la fábrica: SPEC.md, CONSTRAINTS.md, ARCHITECTURE.md, PLAN.md
```

## Estado de fases

| Fase | Descripción | Estado |
|---|---|---|
| 1 | Bootstrap (fábrica) | ✅ Completada |
| 2 | Modelos + API base | ✅ Completada |
| 3 | Frontend cliente (formulario de reserva) | ✅ Completada |
| 4 | Lógica de conflictos (solapamientos, no-overbooking) | ✅ Completada |
| 5 | Panel administrador | ✅ Completada |
| 6 | Emails simulados + pulido | ✅ Completada |

**PROYECTO CERRADO.**