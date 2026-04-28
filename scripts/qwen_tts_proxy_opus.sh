#!/usr/bin/env bash
set -euo pipefail

TEXT="${1:-}"
OUT="${2:-}"

if [[ -z "${TEXT}" || -z "${OUT}" ]]; then
  echo "usage: qwen_tts_proxy_opus.sh <text> <output_path>" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_SCRIPT="${QWEN_TTS_RUNTIME_SCRIPT:-${SCRIPT_DIR}/qwen_tts_runtime.py}"

if [[ ! -f "${RUNTIME_SCRIPT}" ]]; then
  echo "runtime script not found: ${RUNTIME_SCRIPT}" >&2
  exit 1
fi

exec python3 "${RUNTIME_SCRIPT}" "${TEXT}" "${OUT}"
