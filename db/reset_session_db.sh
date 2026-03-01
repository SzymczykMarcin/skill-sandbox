#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="${SQLITE_RUNTIME_DIR:-${ROOT_DIR}/.runtime/sqlite}"
BASE_DB="${SQLITE_BASE_DB_PATH:-${RUNTIME_DIR}/base_snapshot.sqlite}"
TARGET_DB="${1:-${RUNTIME_DIR}/session.sqlite}"

mkdir -p "$(dirname "${BASE_DB}")"
mkdir -p "$(dirname "${TARGET_DB}")"

if [[ ! -f "${BASE_DB}" ]]; then
  echo "Base snapshot not found. Building ${BASE_DB} from schema + seed..."
  sqlite3 "${BASE_DB}" < "${ROOT_DIR}/db/schema.sql"
  sqlite3 "${BASE_DB}" < "${ROOT_DIR}/db/seed.sql"
fi

cp "${BASE_DB}" "${TARGET_DB}"
echo "Session DB reset at ${TARGET_DB}"
