# ReservaFácil — Sistema de reservas que elimina el overbooking y reduce no-shows para salones.

Los salones y barberías gestionan sus citas a mano: agenda en papel, WhatsApp y llamadas. El resultado es overbooking de empleados, clientes que no llegan (no-shows) y cero historial para tomar decisiones.

## La solución

- **El cliente reserva en línea:** elige servicio, empleado y horario disponible real, sin llamadas.
- **El dueño administra todo:** panel con servicios, empleados, reservas y reportes de negocio.
- **El sistema bloquea solapamientos automáticamente:** valida que ningún empleado quede con dos reservas a la vez y que el horario esté dentro del negocio.

## 📸 Capturas

- `[CAPTURA: formulario de reserva]`
- `[CAPTURA: panel admin]`
- `[CAPTURA: reportes con gráficos]`
- `[CAPTURA: mis reservas del cliente]`

## Stack

- **Python 3.12 + Flask 3.x** — microframework simple y ampliamente conocido.
- **Flask-SQLAlchemy / SQLAlchemy 2.x** — ORM maduro con modelos tipados.
- **SQLite** — base de datos de archivo único, sin servidor extra (ideal para un despliegue local y simple).
- **Jinja2 + TailwindCSS (CDN) + JavaScript vanilla** — UI limpia sin tooling de build.
- **Flask-WTF (CSRF) + Werkzeug** — formularios seguros y contraseñas hasheadas.
- **pytest** — 63 tests automatizados que validan la lógica de negocio.

## Cómo correr en local

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py          # datos de ejemplo + usuario admin
python run.py
```

Abre `http://localhost:5000`. Panel administrador en `http://localhost:5000/admin`.

Las credenciales se leen de variables de entorno (nunca del código). Copia `.env.example` a `.env` y exporta las variables:

```bash
cp .env.example .env
set -a; source .env; set +a
python run.py
```

## Decisiones técnicas destacadas

- **Validación de conflictos a nivel de aplicación:** la lógica `hay_conflicto` impide reservas solapadas y respeta el horario del negocio (sin depender de transacciones complejas de base de datos).
- **Soft delete:** los servicios y empleados nunca se borran; se desactivan, preservando el historial de reservas.
- **Hardening de secretos:** credenciales vía variables de entorno; en producción el arranque falla si faltan, y el login está protegido contra fuerza bruta (5 intentos/60 s).

## Métricas

- **63 tests, 0 warnings.**
- **12 fases** de desarrollo incremental, cada una con criterio de cierre verificado.

Más detalles técnicos en `SPEC.md`, `DECISIONS.md` y `PLAN.md`.