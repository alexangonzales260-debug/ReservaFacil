# DECISIONS.md — Registro de decisiones de arquitectura (ADR)

Formato: 3 líneas por entrada — **Contexto** / **Decisión** / **Consecuencia**.

## D1 | Flujo de reserva sin fricción

- **Contexto:** Peluquería local, reserva sin fricción.
- **Decisión:** Cliente anónimo: `POST /reservas` crea/encuentra Usuario por email.
- **Consecuencia:** Sin historial por cliente hasta añadir auth (F7).

## D2 | Preservar historial y poder reactivar

- **Contexto:** Preservar historial y poder reactivar.
- **Decisión:** Soft delete: flag `activo=False`, nunca borrar filas.
- **Consecuencia:** Todos los listados filtran por `activo`.

## D3 | Un solo admin, stack mínimo

- **Contexto:** Un solo admin, stack mínimo.
- **Decisión:** `flask.session` + `@admin_required`, sin Flask-Login.
- **Consecuencia:** Sesión manual; sin recuperación de contraseña.

## D4 | Despliegue local sin servicio de email

- **Contexto:** Despliegue local sin servicio de email.
- **Decisión:** Hashes con Werkzeug; emails simulados en `instance/emails.log`.
- **Consecuencia:** Sin SMTP; email real queda para fase futura.

## D5 | Deprecación de `datetime.utcnow()`

- **Contexto:** Deprecación de `datetime.utcnow()`.
- **Decisión:** TZ America/Lima + `datetime.now(timezone.utc)`.
- **Consecuencia:** `validate.sh` bloquea `utcnow()`.

## D6 | SQLite + volumen bajo

- **Contexto:** SQLite + volumen bajo.
- **Decisión:** Conflictos a nivel de aplicación (`Reserva.hay_conflicto`), no transacciones DB.
- **Consecuencia:** Si la concurrencia crece, revisar esta decisión.

## D7 | Sin tooling de build

- **Contexto:** Sin tooling de build.
- **Decisión:** Tailwind vía CDN + JS vanilla.
- **Consecuencia:** Sin paso de compilación.

## D8 | Despliegue local en una máquina

- **Contexto:** Despliegue local en una máquina.
- **Decisión:** SQLite archivo único (`instance/`).
- **Consecuencia:** Migrar a Postgres si llega multi-sucursal (F10).

## D9 | Secretos vía variables de entorno

- **Contexto:** Repo público en GitHub; credenciales hardcodeadas en código y README.
- **Decisión:** Secretos vía variables de entorno (`os.environ.get`); defaults de desarrollo solo fuera de producción.
- **Consecuencia:** README sin credenciales; `APP_ENV=production` exige secretos explícitos.