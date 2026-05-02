#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="/opt/anaconda3/envs/lightfm_env/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "LightFM env python bulunamadi: $PYTHON_BIN" >&2
  exit 1
fi

cd "$PROJECT_ROOT"
"$PYTHON_BIN" scripts/export_lightfm_artifacts.py
echo "LightFM artifact yenilendi. Backend restart gerekmiyorsa yeni isteklerde otomatik okunur."
