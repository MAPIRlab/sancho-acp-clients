#!/usr/bin/env bash
set -eu

# Clean up Python environment variables polluted by acp-ui AppImage
unset PYTHONHOME PYTHONPATH

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

exec python3 "$ROOT_DIR/acp_tcp_stdio_adapter.py" "$@"
