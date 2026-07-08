#!/usr/bin/env bash
set -euo pipefail

: "${SCRIPT_DIR:=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
CONFIG="${1:-$SCRIPT_DIR/config.yaml}"
ENV_FILE="${2:-$SCRIPT_DIR/.env}"

IMAGE_NAME="ghcr.io/jmc000/onlyoffice-backup"
TAG="$(grep -m1 '^TAG=' "$ENV_FILE" | cut -d '=' -f2-)"
TAG="${TAG:?set TAG in $ENV_FILE, e.g. TAG=<commit-sha>}"

# Reuse the venv to use PyYAML
mapfile -t TARGETS < <("$SCRIPT_DIR/venv/bin/python" -c "
import yaml
with open('$CONFIG') as f:
    cfg = yaml.safe_load(f) or {}
for p in cfg.get('files', []) + cfg.get('dirs', []):
    print(p)
")

VOLUME_ARGS=()
for p in "${TARGETS[@]}"; do
  abs="$(readlink -f "$p")"
  VOLUME_ARGS+=(-v "${abs}:${abs}:ro,z")
done

podman run --rm --env-file "$ENV_FILE" \
  -v "$SCRIPT_DIR/config.yaml:/app/config.yaml:ro,z" \
  -v "$SCRIPT_DIR/output.log:/app/output.log:z" \
  "${VOLUME_ARGS[@]}" \
  "${IMAGE_NAME}:${TAG}"


