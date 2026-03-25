#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PIPELINE_ROOT="${REPO_ROOT}/agents/tools/opencode_session_pipeline"
PROJECT_LABEL="$(basename "${REPO_ROOT}")"

MODE="${1:-incremental}"
if [[ "${MODE}" != "incremental" && "${MODE}" != "backfill" ]]; then
  echo "Usage: $(basename "$0") [incremental|backfill]" >&2
  exit 2
fi

RAW_ROOT="${REPO_ROOT}/archive/raw/opencode"
EVENTS_ROOT="${REPO_ROOT}/archive/derived/events/opencode"
MANIFEST_ROOT="${REPO_ROOT}/archive/manifests/opencode"
INDEX_ROOT="${REPO_ROOT}/archive/index"
CHECKPOINT_INGEST="${REPO_ROOT}/archive/checkpoints/opencode_ingest_state.json"
CHECKPOINT_EVENTS="${REPO_ROOT}/archive/checkpoints/opencode_events_state.json"

echo "[1/3] Ingest raw sessions (${MODE})"
python3 "${PIPELINE_ROOT}/bin/ingest_raw.py" \
  --mode "${MODE}" \
  --project-worktree "${REPO_ROOT}" \
  --archive-root "${RAW_ROOT}" \
  --manifest-root "${MANIFEST_ROOT}" \
  --index-root "${INDEX_ROOT}" \
  --checkpoint-path "${CHECKPOINT_INGEST}"

echo "[2/3] Normalize canonical events (${MODE})"
python3 "${PIPELINE_ROOT}/bin/normalize_events.py" \
  --mode "${MODE}" \
  --project-worktree "${REPO_ROOT}" \
  --raw-root "${RAW_ROOT}" \
  --events-root "${EVENTS_ROOT}" \
  --manifest-root "${MANIFEST_ROOT}" \
  --index-root "${INDEX_ROOT}" \
  --checkpoint-path "${CHECKPOINT_EVENTS}"

echo "[3/3] Validate event coverage"
python3 "${PIPELINE_ROOT}/bin/validate_events.py" \
  --project "${PROJECT_LABEL}" \
  --raw-root "${RAW_ROOT}" \
  --events-root "${EVENTS_ROOT}" \
  --index-root "${INDEX_ROOT}"

echo "Done. Project=${PROJECT_LABEL} archive_root=${REPO_ROOT}/archive"
