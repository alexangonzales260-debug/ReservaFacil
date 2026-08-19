from __future__ import annotations

import os
import sys

APP_ENV = os.environ.get("APP_ENV", "development")


def _secret_key() -> str:
    valor = os.environ.get("SECRET_KEY")
    if valor:
        return valor
    if APP_ENV == "production":
        raise RuntimeError(
            "SECRET_KEY no definida y APP_ENV=production. "
            "Define la variable SECRET_KEY antes de arrancar."
        )
    print(
        "ADVERTENCIA: SECRET_KEY no definida; usando fallback de desarrollo.",
        file=sys.stderr,
    )
    return "dev-secret-key"


def _admin_username() -> str:
    if APP_ENV == "production":
        valor = os.environ.get("ADMIN_USERNAME")
        if not valor:
            raise RuntimeError(
                "ADMIN_USERNAME no definido y APP_ENV=production. "
                "Define la variable ADMIN_USERNAME antes de arrancar."
            )
        return valor
    return os.environ.get("ADMIN_USERNAME", "admin")


def _admin_password() -> str:
    if APP_ENV == "production":
        valor = os.environ.get("ADMIN_PASSWORD")
        if not valor:
            raise RuntimeError(
                "ADMIN_PASSWORD no definida y APP_ENV=production. "
                "Define la variable ADMIN_PASSWORD antes de arrancar."
            )
        return valor
    return os.environ.get("ADMIN_PASSWORD", "admin123")


SECRET_KEY = _secret_key()
ADMIN_USERNAME = _admin_username()
ADMIN_PASSWORD = _admin_password()