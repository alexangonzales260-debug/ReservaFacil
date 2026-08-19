# PLAN.md — ReservaFácil

6 fases atómicas. Cada fase tiene criterio de cierre verificable antes de pasar a la siguiente.
Regla: NO avanzar de fase sin que su criterio de cierre pase.

---

## FASE 1 — Bootstrap (fábrica)

- **Descripción:** crear los archivos de la fábrica (SPEC, CONSTRAINTS, ARCHITECTURE, PLAN, validate.sh) y el esqueleto del proyecto. Sin código de aplicación funcional aún.
- **Archivos:** `SPEC.md`, `CONSTRAINTS.md`, `ARCHITECTURE.md`, `PLAN.md`, `validate.sh`, `requirements.txt`.
- **Criterio de cierre:** la fábrica existe y `./validate.sh` retorna código 0.
- **Verificación:** `./validate.sh`.

## FASE 2 — Modelos + API base  ✅ COMPLETADA (2026-08-18)

- **Descripción:** implementar `app/__init__.py` (factory), `extensions.py`, `models.py` (Usuario, Servicio, Empleado, Reserva) y el blueprint `api` con endpoints JSON básicos (listar servicios, crear/consultar reservas).
- **Archivos:** `app/*`, `app/api/*`, `tests/conftest.py`, `tests/test_models.py`, `tests/test_api.py`, `run.py`.
- **Criterio de cierre:** pytest pasa (modelos + endpoints básicos) y `./validate.sh` es verde.
- **Verificación:** `pytest -q` + `./validate.sh`.
- **Resultado:** 19 tests PASADOS (14 API + 5 modelos); `./validate.sh` verde; curl `/api/v1/servicios` → `{"servicios": []}` HTTP 200.

## FASE 3 — Frontend cliente (formulario de reserva)  ✅ COMPLETADA (2026-08-18)

- **Descripción:** templates Jinja2 + Tailwind (CDN) para el flujo cliente: home con catálogo, formulario de reserva con selector de servicio/empleado/fecha, confirmación y "mis reservas".
- **Archivos:** `templates/*`, `static/*`, `app/cliente/*`.
- **Criterio de cierre:** un cliente puede crear una reserva desde el navegador (formulario funcional con CSRF y validación).
- **Verificación:** `pytest -q` + prueba manual en navegador.
- **Resultado:** 26 tests PASADOS; `./validate.sh` verde; flujo completo verificado por HTTP (catálogo → slots → POST anónimo con CSRF → detalle → cancelación). Seed con 3 servicios + 2 empleados.

## FASE 4 — Lógica de conflictos (solapamientos, no-overbooking)  ✅ COMPLETADA (2026-08-18)

- **Descripción:** implementar y endurecer la lógica de negocio: validación de solapamientos (RF-SYS-01), no-overbooking (RF-SYS-02/03), horario de atención (RF-SYS-04), ID único por reserva (RF-SYS-05).
- **Archivos:** `app/models.py`, `app/api/*`, `tests/test_models.py`, `tests/test_api.py`.
- **Criterio de cierre:** pytest con tests de conflicto pasa (reservas solapadas rechazadas, slots bloqueados, IDs únicos).
- **Verificación:** `pytest -q tests/test_models.py tests/test_api.py -k "conflict"` + `./validate.sh`.
- **Resultado:** 32 tests PASADOS (6 nuevos de conflictos). `Reserva.hay_conflicto` en models; POST `/reservas` retorna 409 en solapamiento; disponibilidad filtra slots ocupados y excluye canceladas. Curl real: 201 → 409 → disponibilidad sin `10:00`. `./validate.sh` verde con nuevo grep.

## FASE 5 — Panel administrador  ✅ COMPLETADA (2026-08-18)

- **Descripción:** blueprint `admin` con CRUD de servicios y empleados, gestión de horarios de atención y listado de todas las reservas con filtros (RF-ADM-*).
- **Archivos:** `app/admin/*`, `templates/admin/*`, `app/models.py`, `tests/*`.
- **Criterio de cierre:** CRUD de servicios/empleados/reservas funciona desde el panel (verificado por pytest + navegador).
- **Verificación:** `pytest -q` + prueba manual en navegador + `./validate.sh`.
- **Resultado:** 38 tests PASADOS (6 nuevos de admin). Login con `flask.session` + `@admin_required`; soft delete en servicios/empleados; gestión de estados de reserva (confirmar/cancelar/completar); seed crea admin `admin/admin123`.

## FASE 6 — Emails simulados + pulido  ✅ COMPLETADA (2026-08-18) — PROYECTO CERRADO

- **Descripción:** emitir emails simulados por `logger`/consola al crear/cancelar reservas (RF-SYS-06) y pulido general de UX/errores.
- **Archivos:** `app/*`, `templates/*`, `tests/*`.
- **Criterio de cierre:** las confirmaciones aparecen en logs al crear/cancelar reservas.
- **Verificación:** `pytest -q` + revisar logs + `./validate.sh`.
- **Resultado:** 40 tests PASADOS con **0 warnings de deprecación** (se eliminó `utcnow()`). Emails simulados en consola + `instance/emails.log` (confirmación/cancelación en API, confirmación/agradecimiento en admin). Manejo de errores 409/red en el frontend. README.md final. Nuevos gates en `validate.sh` (sin `utcnow()`, uso de `enviar_email`).

---

## Resumen de verificación global

Cada fase finaliza ejecutando `./validate.sh`. La secuencia completa (FASE 1 → 6) es el roadmap del proyecto.

## F0 Retrofit v2  ✅ COMPLETADA

- **Descripción:** retrofit de la fábrica a la v2 + limpieza de artefactos del repositorio (retirados de tracking sin borrar del disco).
- **Archivos:** `.gitignore`, `DECISIONS.md`, `METRICAS.md`, `PLAN.md`.
- **Verificación:** `./validate.sh` + `git ls-files` sin `venv/`, `instance/`, `__pycache__/`, `*.pyc`.

## F7 Hardening threat-light  ✅ COMPLETADA

- **Descripción:** credenciales y secretos vía variables de entorno (`config.py`); candado en producción; README sin credenciales; gates threat-light en `validate.sh`.
- **Archivos:** `config.py`, `seed.py`, `run.py`, `.gitignore`, `.env.example`, `README.md`, `validate.sh`, `tests/test_hardening.py`.
- **Verificación:** `./validate.sh` + `pytest -q` (42 tests, 0 warnings) + `APP_ENV=production python -c "import config"` falla sin `SECRET_KEY`.

## FASE 9 — Autenticación de cliente + portal "Mis reservas"  ✅ COMPLETADA

- **Descripción:** registro/login de cliente (flask.session + Werkzeug), portal "Mis reservas" con cancelación propia y adopción de cuentas anónimas.
- **Archivos:** `app/cliente/routes.py`, `app/api/routes.py`, `templates/registrarse.html`, `templates/login_cliente.html`, `templates/mis_reservas.html`, `templates/base.html`, `tests/test_auth_cliente.py`.
- **Verificación:** `./validate.sh` + `pytest -q` (53 tests, 0 warnings) + flujo curl registro → mis-reservas → cancelar.

## F10 Reportes  ✅ COMPLETADA

- **Descripción:** inteligencia de negocio para el dueño: dashboard de reportes (métricas del mes + gráficos Chart.js de reservas por día y top servicios) y exportación CSV de reservas con filtros.
- **Archivos:** `app/admin/routes.py`, `templates/admin/reportes.html`, `templates/admin/base_admin.html`, `tests/test_reportes.py`, `validate.sh`, `SPEC.md`, `DECISIONS.md`.
- **Verificación:** `./validate.sh` + `pytest -q` + flujo curl reportes/CSV con y sin sesión admin.