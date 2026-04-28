#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
CLIENT_ENV_PATH="${ROOT_DIR}/.env"
PROXY_SCRIPT_SOURCE="${ROOT_DIR}/scripts/qwen_tts_proxy_opus.sh"
PROXY_SCRIPT_TARGET="${OPENCLAW_HOME}/bin/qwen_tts_proxy_opus.sh"
RUNTIME_SCRIPT_SOURCE="${ROOT_DIR}/scripts/qwen_tts_runtime.py"
RUNTIME_SCRIPT_TARGET="${OPENCLAW_HOME}/bin/qwen_tts_runtime.py"
DEFAULT_BASE_URL="https://qwen-tts-118.tailf26c2b.ts.net"

print_step() {
  echo
  echo "==> $1"
}

env_quote() {
  python3 -c 'import shlex,sys; print(shlex.quote(sys.argv[1]))' "$1"
}

prompt_value() {
  local label="$1"
  local default_value="$2"
  local result
  read -r -p "${label} [${default_value}]: " result
  if [[ -z "${result}" ]]; then
    result="${default_value}"
  fi
  echo "${result}"
}

print_step "Qwen TTS Client setup"
echo "Root: ${ROOT_DIR}"
echo "OpenClaw home: ${OPENCLAW_HOME}"

BASE_URL="$(prompt_value "CENTRAL_TTS_BASE_URL" "${DEFAULT_BASE_URL}")"
if [[ "${BASE_URL}" != http://* && "${BASE_URL}" != https://* ]]; then
  echo "ERROR: CENTRAL_TTS_BASE_URL must start with http:// or https://" >&2
  exit 1
fi

read -r -s -p "CENTRAL_TTS_API_KEY: " API_KEY
echo
if [[ -z "${API_KEY}" ]]; then
  echo "ERROR: CENTRAL_TTS_API_KEY cannot be empty" >&2
  exit 1
fi

SMOKE_TEXT="$(prompt_value "Smoke test text" "Проверка удаленного TTS клиента.")"
DEFAULT_TARGET="$(prompt_value "CENTRAL_TTS_TARGET (voice-note|audio-file|telephony)" "voice-note")"
DEFAULT_TIMEOUT_SEC="$(prompt_value "CENTRAL_TTS_TIMEOUT_SEC" "120")"
DEFAULT_RETRIES="$(prompt_value "CENTRAL_TTS_RETRIES" "2")"
DEFAULT_BACKOFF_MS="$(prompt_value "CENTRAL_TTS_RETRY_BACKOFF_MS" "350")"

print_step "Writing ${CLIENT_ENV_PATH}"
cat > "${CLIENT_ENV_PATH}" <<EOF
CENTRAL_TTS_BASE_URL=$(env_quote "${BASE_URL}")
CENTRAL_TTS_API_KEY=$(env_quote "${API_KEY}")
SMOKE_TEXT=$(env_quote "${SMOKE_TEXT}")
CENTRAL_TTS_TARGET=$(env_quote "${DEFAULT_TARGET}")
CENTRAL_TTS_TIMEOUT_SEC=$(env_quote "${DEFAULT_TIMEOUT_SEC}")
CENTRAL_TTS_RETRIES=$(env_quote "${DEFAULT_RETRIES}")
CENTRAL_TTS_RETRY_BACKOFF_MS=$(env_quote "${DEFAULT_BACKOFF_MS}")
# Optional hints for OpenClaw 2026.4.25+ flow
CENTRAL_TTS_VOICE=
CENTRAL_TTS_MODEL=
CENTRAL_TTS_PERSONA=
CENTRAL_TTS_SESSION_HINTS_JSON=
EOF
chmod 600 "${CLIENT_ENV_PATH}"

print_step "Installing runtime scripts"
mkdir -p "${OPENCLAW_HOME}/bin"
cp "${PROXY_SCRIPT_SOURCE}" "${PROXY_SCRIPT_TARGET}"
cp "${RUNTIME_SCRIPT_SOURCE}" "${RUNTIME_SCRIPT_TARGET}"
chmod +x "${PROXY_SCRIPT_TARGET}"
chmod +x "${RUNTIME_SCRIPT_TARGET}"

print_step "Configuring OpenClaw TTS provider"
python3 - "${OPENCLAW_HOME}" "${PROXY_SCRIPT_TARGET}" "${RUNTIME_SCRIPT_TARGET}" <<'PY'
import json
import pathlib
import sys

openclaw_home = pathlib.Path(sys.argv[1])
proxy_script = sys.argv[2]
runtime_script = sys.argv[3]
config_path = openclaw_home / "openclaw.json"

if not config_path.exists():
    print(f"ERROR: {config_path} not found. Run OpenClaw at least once first.", file=sys.stderr)
    sys.exit(1)

data = json.loads(config_path.read_text())
messages = data.setdefault("messages", {})
tts = messages.setdefault("tts", {})
providers = tts.setdefault("providers", {})

providers["tts-local-cli"] = {
    "enabled": True,
    "command": proxy_script,
    "args": ["{{Text}}", "{{OutputPath}}"],
    "outputFormat": "opus",
    "timeoutMs": 120000,
    "env": {
        "QWEN_TTS_RUNTIME_SCRIPT": runtime_script,
    },
}

tts["enabled"] = True
tts["provider"] = "tts-local-cli"
tts.setdefault("auto", "off")
tts.setdefault("persona", "")
tts.setdefault("personas", {})
tts["maxTextLength"] = 600
tts.pop("audioAsVoice", None)
tts.pop("textLimit", None)

config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
print(f"updated {config_path}")
PY

print_step "Restarting gateway service (if available)"
if command -v systemctl >/dev/null 2>&1 && systemctl --user list-unit-files | awk '{print $1}' | grep -qx "openclaw-gateway.service"; then
  systemctl --user restart openclaw-gateway.service || true
  systemctl --user is-active openclaw-gateway.service || true
elif command -v launchctl >/dev/null 2>&1; then
  launchctl kickstart -k "gui/$(id -u)/ai.openclaw.gateway" || true
fi

print_step "Running smoke test"
TMP_OUT="/tmp/qwen-tts-client-smoke.ogg"
QWEN_TTS_CLIENT_ENV="${CLIENT_ENV_PATH}" "${PROXY_SCRIPT_TARGET}" "${SMOKE_TEXT}" "${TMP_OUT}"
ls -lh "${TMP_OUT}"
file "${TMP_OUT}" || true

echo
echo "Done."
echo "Client env: ${CLIENT_ENV_PATH}"
echo "Proxy script: ${PROXY_SCRIPT_TARGET}"
echo "Next: /tts status"
