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

## FASE 4 — Lógica de conflictos (solapamientos, no-overbooking)

- **Descripción:** implementar y endurecer la lógica de negocio: validación de solapamientos (RF-SYS-01), no-overbooking (RF-SYS-02/03), horario de atención (RF-SYS-04), ID único por reserva (RF-SYS-05).
- **Archivos:** `app/models.py`, `app/api/*`, `tests/test_models.py`, `tests/test_api.py`.
- **Criterio de cierre:** pytest con tests de conflicto pasa (reservas solapadas rechazadas, slots bloqueados, IDs únicos).
- **Verificación:** `pytest -q tests/test_models.py tests/test_api.py -k "conflict"` + `./validate.sh`.

## FASE 5 — Panel administrador

- **Descripción:** blueprint `admin` con CRUD de servicios y empleados, gestión de horarios de atención y listado de todas las reservas con filtros (RF-ADM-*).
- **Archivos:** `app/admin/*`, `templates/admin/*`, `app/models.py`, `tests/*`.
- **Criterio de cierre:** CRUD de servicios/empleados/reservas funciona desde el panel (verificado por pytest + navegador).
- **Verificación:** `pytest -q` + prueba manual en navegador + `./validate.sh`.

## FASE 6 — Emails simulados + pulido

- **Descripción:** emitir emails simulados por `logger`/consola al crear/cancelar reservas (RF-SYS-06) y pulido general de UX/errores.
- **Archivos:** `app/*`, `templates/*`, `tests/*`.
- **Criterio de cierre:** las confirmaciones aparecen en logs al crear/cancelar reservas.
- **Verificación:** `pytest -q` + revisar logs + `./validate.sh`.

---

## Resumen de verificación global

Cada fase finaliza ejecutando `./validate.sh`. La secuencia completa (FASE 1 → 6) es el roadmap del proyecto.