#!/usr/bin/env bash
# validate.sh — Verificación de salud de la fábrica ReservaFácil.
# Código 0 = todo OK; != 0 = algo falló.
set -u
# NOTA: no usamos `set -e` a propósito: ejecutamos TODAS las comprobaciones
# y reportamos al final con un único código de salida.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

FAIL=0

echo "=== [1/5] Activando virtualenv (si existe) ==="
if [ -d "venv" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
  echo "venv/ activado."
else
  echo "venv/ no encontrado; usando el entorno actual."
fi

echo ""
echo "=== [2/5] Instalando requirements.txt (silencioso) ==="
if [ -f requirements.txt ]; then
  if pip install -q -r requirements.txt; then
    echo "Dependencias instaladas."
  else
    echo "ERROR: fallo al instalar dependencias."
    FAIL=1
  fi
else
  echo "requirements.txt no existe; omitiendo."
fi

echo ""
echo "=== [3/5] Verificando sintaxis de Python (py_compile) ==="
shopt -s globstar nullglob
ALL_PY=(app/*.py app/**/*.py run.py tests/*.py tests/**/*.py)
PY_FILES=()
for f in "${ALL_PY[@]}"; do
  [ -f "$f" ] && PY_FILES+=("$f")
done
if [ "${#PY_FILES[@]}" -gt 0 ]; then
  if python -m py_compile "${PY_FILES[@]}"; then
    echo "Sintaxis OK (${#PY_FILES[@]} archivo(s))."
  else
    echo "ERROR: py_compile falló."
    FAIL=1
  fi
else
  echo "Sin archivos .py aún (fase bootstrap). OK."
fi

echo ""
echo "=== Verificando uso de hay_conflicto (FASE 4) ==="
grep -n "hay_conflicto" app/models.py app/api/routes.py || exit 1

echo ""
echo "=== [4/5] Ejecutando pytest ==="
if compgen -G "tests/test_*.py" >/dev/null 2>&1; then
  if python -m pytest -q; then
    echo "pytest OK."
  else
    echo "ERROR: pytest falló."
    FAIL=1
  fi
else
  echo "Sin tests aún (fase bootstrap). OK."
fi

echo ""
echo "=== [5/6] Verificando APIs prohibidas (eval/exec/os.system) ==="
FORBIDDEN=$(grep -rn -E "\beval\s*\(|\bexec\s*\(|os\.system\s*\(" app tests run.py 2>/dev/null || true)
if [ -n "$FORBIDDEN" ]; then
  echo "ERROR: APIs prohibidas encontradas:"
  echo "$FORBIDDEN"
  FAIL=1
else
  echo "Sin APIs prohibidas. OK."
fi

echo ""
echo "=== [6/6] Verificando que instance/reservafacil.db sea creable/abrible ==="
if python - <<'PY'
import os, sqlite3

path = os.path.join("instance", "reservafacil.db")
try:
    os.makedirs("instance", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("SELECT 1")
    conn.close()
    print("OK: SQLite puede crear/abrir", path)
except Exception as exc:
    print("ERROR:", exc)
    raise SystemExit(1)
PY
then
  echo "Base de datos SQLite verificada (no se borró nada)."
else
  echo "ERROR: SQLite no pudo crear/abrir la base de datos."
  FAIL=1
fi

echo ""
if [ "$FAIL" -ne 0 ]; then
  echo "VALIDATE: FALLÓ (código 1)"
  exit 1
else
  echo "VALIDATE: OK (código 0)"
  exit 0
fi