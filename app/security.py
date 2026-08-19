from __future__ import annotations

import time
from collections import defaultdict
from typing import DefaultDict, List

INTENTOS_MAX = 5
VENTANA_SEGUNDOS = 60.0
MENSAJE_429 = "Demasiados intentos. Espera un minuto y vuelve a probar."

_intentos: DefaultDict[str, List[float]] = defaultdict(list)


def controlar_intentos(ip: str, clave: str) -> bool:
    ahora = time.monotonic()
    llave = f"{ip}|{clave}"
    registros = _intentos[llave]
    registros[:] = [t for t in registros if ahora - t <= VENTANA_SEGUNDOS]
    if len(registros) >= INTENTOS_MAX:
        return False
    registros.append(ahora)
    return True


def reset_limites() -> None:
    _intentos.clear()