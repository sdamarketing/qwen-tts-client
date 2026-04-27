#!/usr/bin/env bash
set -euo pipefail

TEXT="${1:-}"
OUT="${2:-}"

if [[ -z "${TEXT}" || -z "${OUT}" ]]; then
  echo "usage: qwen_tts_proxy_opus.sh <text> <output_path>" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${QWEN_TTS_CLIENT_ENV:-${ROOT_DIR}/.env}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "env file not found: ${ENV_FILE}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

if [[ -z "${CENTRAL_TTS_BASE_URL:-}" || -z "${CENTRAL_TTS_API_KEY:-}" ]]; then
  echo "CENTRAL_TTS_BASE_URL or CENTRAL_TTS_API_KEY is missing in ${ENV_FILE}" >&2
  exit 1
fi

JSON_PAYLOAD="$(python3 -c 'import json,sys; print(json.dumps({"text": sys.argv[1]}, ensure_ascii=False))' "${TEXT}")"

/usr/bin/curl -sS -X POST "${CENTRAL_TTS_BASE_URL%/}/tts" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${CENTRAL_TTS_API_KEY}" \
  --data "${JSON_PAYLOAD}" \
  --output "${OUT}"
