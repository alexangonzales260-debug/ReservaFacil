"""WhatsApp simulado: se imprime en consola y se registra en instance/whatsapp.log.

No se usa Twilio ni APIs de mensajería reales (CONSTRAINTS): simulación vía
logger + archivo, mismo patrón que app/emails.py.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("reservafacil.whatsapp")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WHATSAPP_LOG_PATH = PROJECT_ROOT / "instance" / "whatsapp.log"


def enviar_whatsapp_simulado(destinatario: str, mensaje: str) -> None:
    """Imprime un WhatsApp simulado y lo anexa a instance/whatsapp.log."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    texto = (
        "=" * 50
        + f"\nPara: {destinatario}"
        + f"\nMensaje: {mensaje}"
        + f"\n[{timestamp}]"
        + "\n"
        + "=" * 50
    )
    logger.info("\n%s", texto)

    WHATSAPP_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WHATSAPP_LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(texto + "\n\n")