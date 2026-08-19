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

## Configuración

Los secretos y credenciales se leen de variables de entorno (`os.environ`), nunca del código.

| Variable | Uso | Default (solo fuera de producción) |
|---|---|---|
| `APP_ENV` | Entorno de ejecución (`development` o `production`) | `development` |
| `SECRET_KEY` | Clave secreta de sesiones de Flask | `dev-secret-key` (avisa por consola si no se define) |
| `ADMIN_USERNAME` | Usuario administrador creado por el seed | `admin` |
| `ADMIN_PASSWORD` | Contraseña del administrador (seed) | default de desarrollo (ver `.env.example`) |

En `APP_ENV=production` es obligatorio definir `SECRET_KEY`, `ADMIN_USERNAME` y `ADMIN_PASSWORD`; si faltan, el arranque falla con `RuntimeError`.

Usa `.env.example` como plantilla: cópialo a `.env` (ignorado por git) y exporta las variables antes de ejecutar:

```bash
cp .env.example .env
set -a; source .env; set +a
python run.py
```

Panel administrador en `http://localhost:5000/admin`.

## Tests

```bash
pytest -v
./validate.sh
```

`validate.sh` verifica: sintaxis Python, presence de `hay_conflicto`, ausencia de `utcnow()`, uso de `enviar_email`, gates threat-light (`shell=True`, `debug=True`, contraseñas hardcodeadas), `pytest`, APIs prohibidas (`eval`/`exec`/`os.system`) y que la base SQLite sea creable.

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
| 7 | Hardening (secretos vía variables de entorno) | ✅ Completada |