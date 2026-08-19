# ARCHITECTURE.md — ReservaFácil

## 1. Estructura de carpetas

```
ReservaFacil/
├── app/
│   ├── __init__.py            # Application factory: create_app()
│   ├── models.py              # Usuario, Servicio, Empleado, Reserva
│   ├── extensions.py          # db (SQLAlchemy), csrf
│   ├── admin/                 # Blueprint 'admin': panel de gestión
│   │   └── __init__.py
│   ├── cliente/               # Blueprint 'cliente': flujo del cliente
│   │   └── __init__.py
│   └── api/                   # Blueprint 'api': endpoints JSON
│       └── __init__.py
├── templates/                 # Jinja2 + Tailwind (CDN)
├── static/
├── tests/
│   ├── conftest.py            # Fixtures: app de prueba, DB, client
│   ├── test_models.py         # Pruebas de modelos y validaciones
│   └── test_api.py            # Pruebas de endpoints JSON
├── requirements.txt
├── run.py                     # Punto de entrada del servidor
├── SPEC.md
├── CONSTRAINTS.md
├── ARCHITECTURE.md
├── PLAN.md
└── validate.sh                # Verificación de salud de la fábrica
```

## 2. Descripción de módulos

### app/__init__.py — Factory
`create_app()` crea y configura la instancia Flask: carga config, inicializa `db` y `csrf` desde `extensions.py`, registra los tres blueprints (`admin`, `cliente`, `api`), crea tablas al arrancar y define la zona horaria America/Lima.

### app/extensions.py — Extensiones
Instancias únicas de SQLAlchemy (`db`) y Flask-WTF (`csrf`) para evitar acoplamiento circular con los blueprints.

### app/models.py — Modelos
- **Usuario**: cliente o administrador; email único, password hasheado (Werkzeug), rol.
- **Servicio**: nombre, descripción, precio, duración (minutos).
- **Empleado**: nombre, rol, servicios que puede realizar (relación N:M con Servicio).
- **Reserva**: fecha, hora inicio, duración, estado (confirmada/cancelada), `codigo` único legible (RF-SYS-05), FK a Usuario (cliente), Empleado y Servicio. Validaciones de solapamiento viven aquí o en la capa de servicio.

### app/admin/ — Blueprint admin
Vistas de panel: CRUD de servicios y empleados, gestión de horarios de atención, listado de reservas con filtros (RF-ADM-*). Formularios con CSRF.

### app/cliente/ — Blueprint cliente
Página de inicio con catálogo, formulario de reserva, cancelación y "mis reservas" (RF-CLI-*). Consulta de disponibilidad según servicio, empleado y fecha.

### app/api/ — Blueprint api
Endpoints JSON (RESTful) para integración: listar servicios, consultar disponibilidad, crear/cancelar reservas, listar reservas. Respuestas JSON consistentes con códigos HTTP apropiados.

### tests/
- `conftest.py`: fixture de app en modo test con SQLite en memoria o temporal; cliente de prueba; datos semilla.
- `test_models.py`: modelos, validaciones y reglas de negocio (solapamientos, no-overbooking, ID único).
- `test_api.py`: endpoints JSON (200/400/404/409 según el caso).

### run.py
Arranca la app (`python run.py`). Importa `create_app()` y llama a `app.run(debug=True)`.

## 3. Flujos de datos principales

### Flujo cliente → reserva
1. Cliente ve catálogo (GET `/`) → `cliente` lee `Servicio` desde `db`.
2. Cliente consulta disponibilidad (GET `/reservar?servicio=&fecha=`) → `cliente` consulta `Reserva` confirmadas del empleado y calcula slots libres aplicando no-overbooking (RF-SYS-01..03).
3. Cliente envía formulario (POST `/reservar`) → valida inputs + CSRF → crea `Reserva` → genera `codigo` único → emite email simulado (logger) → redirige a confirmación.

### Flujo administrador → gestión
1. Admin crea/edita `Servicio`/`Empleado` (POST `/admin/...`) → valida → persiste.
2. Admin define horarios → guarda en config/modelo → afecta cálculo de disponibilidad.
3. Admin ve reservas (GET `/admin/reservas`) → filtra por fecha/estado/empleado.

### Flujo API
`GET/POST/DELETE /api/...` → validación → transacción ORM → JSON (estado 200/201/400/404/409).

## 4. Reglas de negocio (núcleo del sistema)

- **Solapamiento** (RF-SYS-01): dos reservas del mismo empleado no pueden compartir intervalo de tiempo.
- **No-overbooking** (RF-SYS-02): un empleado atiende 1 cliente a la vez.
- **Horario de atención** (RF-SYS-04): la reserva debe caber dentro del horario del día.
- **ID único** (RF-SYS-05): `codigo` legible único por reserva.
- **Email simulado** (RF-SYS-06): logger/consola, nunca email real.