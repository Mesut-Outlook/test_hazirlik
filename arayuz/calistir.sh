#!/usr/bin/env bash
# arayuz/calistir.sh — FAZ 4 yerel web arayüzünü kurar/başlatır.
# Kullanım: bash arayuz/calistir.sh
set -euo pipefail

BURASI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$BURASI/backend"
VENV_DIR="$BACKEND_DIR/venv"
PORT=8756

if [ ! -x "$VENV_DIR/bin/python3" ]; then
  echo "[arayuz] venv bulunamadı, kuruluyor: $VENV_DIR"
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --upgrade pip -q
  "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt" -q
else
  # requirements.txt değişmişse eksik paketleri tamamla (hızlı, kuruluysa no-op'a yakın)
  "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt" -q || true
fi

echo "[arayuz] uvicorn başlatılıyor: http://127.0.0.1:$PORT"
(
  sleep 1.5
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://127.0.0.1:$PORT" >/dev/null 2>&1 || true
  fi
) &

exec "$VENV_DIR/bin/uvicorn" main:app --app-dir "$BACKEND_DIR" --host 127.0.0.1 --port "$PORT"
