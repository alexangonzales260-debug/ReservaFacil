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

## D10 | WhatsApp simulado (sin Twilio)

- **Contexto:** Twilio real exige cuenta de pago y API keys, violando la restricción todo-local y "sin dependencias de pago".
- **Decisión:** Simular WhatsApp con logger + `instance/whatsapp.log`, mismo patrón que `emails.py`.
- **Consecuencia:** Sin costo ni claves; para producción real basta sustituir el cuerpo de `app/whatsapp.py` por la llamada a Twilio.

## D11 | Cuenta de cliente opcional (convive con anónimo)

- **Contexto:** Cliente anónimo (D1); el Usuario anónimo se crea sin contraseña propia.
- **Decisión:** Registrarse con un email anónimo activa la cuenta y hereda sus reservas.
- **Consecuencia:** Sin verificación de email, aceptable en threat-light.

## D12 | BI sin tooling de build ni dependencias de servidor

- **Contexto:** El dueño necesita inteligencia de negocio (métricas y gráficos) sin tooling de build ni dependencias de servidor.
- **Decisión:** Chart.js vía CDN (coherente con Tailwind, D7) + exportación CSV con stdlib (`csv`).
- **Consecuencia:** Cero dependencias nuevas en `requirements.txt`; Chart.js requiere internet en el cliente, aceptable.

## D13 | Rate limiter en memoria y CSP omitida

- **Contexto:** Login sin límite de intentos y respuestas sin cabeceras de seguridad; prohibido añadir dependencias externas.
- **Decisión:** Rate limiter en memoria (máx 5 intentos/60 s por IP) + cabeceras `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y `Cache-Control: no-store` en `/admin`; CSP omitida a propósito.
- **Consecuencia:** Cero dependencias; el limiter es por proceso (aceptable single-process) y no hay CSP porque Tailwind y Chart.js se sirven por CDN.