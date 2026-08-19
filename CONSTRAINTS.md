# CONSTRAINTS.md — ReservaFácil

Restricciones técnicas y convenciones del proyecto. **Reglas no negociables.**

---

## 1. Entorno

| Ítem | Valor |
|---|---|
| SO | Linux Mint XFCE (base Ubuntu 24.04) |
| Python | 3.12 |
| Virtualenv | `venv/` (opcional pero recomendado) |
| Zona horaria | America/Lima |

## 2. Stack exacto

- **Flask** 3.x
- **Flask-SQLAlchemy** (SQLAlchemy 2.x)
- **pytest** para pruebas
- **TailwindCSS** vía CDN (no compilado, no build step)
- **SQLite** en archivo único: `instance/reservafacil.db`
- **Jinja2** para templates (bundled con Flask)

## 3. APIs y dependencias PROHIBIDAS

- SQLAlchemy 1.x (deprecated APIs)
- Raw SQL sin ORM (todo acceso a datos vía SQLAlchemy ORM)
- Dependencias externas de pago
- APIs de email reales (solo `logger`/consola)

## 4. Seguridad

- Sin `eval()`, `exec()`, `os.system()` ni shell injection.
- Validar TODOS los inputs (server-side).
- Contraseñas hasheadas con **Werkzeug** (`generate_password_hash` / `check_password_hash`).
- **CSRF** habilitado en todos los formularios (Flask-WTF).
- No exponer secretos en código ni en logs.
- `PASSWORD_ANONIMO` es un sentinel de detección/adoptación (solo `/registrarse`); jamás se acepta como credencial en `/login-cliente`.

## 5. Convenciones

- **UI en español**, **código en inglés** (nombres de variables, funciones, clases).
- **URLs RESTful**: recursos en plural, jerárquicas.
- **Fechas en ISO 8601** (`YYYY-MM-DD`, `HH:MM` en hora local America/Lima).
- Horarios almacenados como minutos desde medianoche o `HH:MM`.

## 6. Estructura de código

- Blueprint por actor:
  - `app/admin/` → panel administrador
  - `app/cliente/` → flujo cliente
  - `app/api/` → endpoints JSON
- Application factory en `app/__init__.py` (`create_app()`).
- Modelos en `app/models.py`; extensiones en `app/extensions.py`.
- Tests en `tests/` con `conftest.py` compartido.
- Toda fecha/hora se procesa en America/Lima.

## 7. Git y control de versiones

- **Regla Git Push:** El ejecutor NUNCA ejecutará `git push` a remotos (HTTPS/SSH). El push a repositorios remotos lo realiza exclusivamente el humano desde su terminal local para gestionar credenciales (tokens/SSH) de forma segura.
- **Regla Registro de Hashes:** El hash registrado en `METRICAS.md` para una fase es el del commit que contiene los cambios funcionales de dicha fase. Si es necesario actualizar `METRICAS.md` tras cerrar la fase, se hace un commit posterior de mantenimiento (ej. "chore: sync metrics") pero la tabla SIEMPRE registra el hash del commit principal de la fase. Nunca se usará `git commit --amend` para incluir el propio archivo de métricas.
