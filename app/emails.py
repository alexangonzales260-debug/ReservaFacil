"""Emails simulados: se imprimen en consola y se registran en instance/emails.log.

No se usa smtplib ni servidores de correo reales (CONSTRAINTS).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("reservafacil.emails")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EMAIL_LOG_PATH = PROJECT_ROOT / "instance" / "emails.log"

REMITE = "ReservaFácil <no-responder@reservafacil.local>"


def enviar_email(destinatario: str, asunto: str, cuerpo: str) -> None:
    """Imprime un email simulado y lo anexa a instance/emails.log."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    mensaje = (
        "=" * 50
        + f"\nDe: {REMITE}"
        + f"\nPara: {destinatario}"
        + f"\nAsunto: {asunto}"
        + "\n------------------------------------------\n"
        + cuerpo
        + f"\n[{timestamp}]"
        + "\n"
        + "=" * 50
    )
    logger.info("\n%s", mensaje)

    EMAIL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EMAIL_LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(mensaje + "\n\n")