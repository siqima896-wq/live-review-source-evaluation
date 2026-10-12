#!/usr/bin/env bash
set -euo pipefail

PSQL_BIN="${PSQL_BIN:-psql}"
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5433}"
PGUSER="${PGUSER:-$(id -un)}"
DATABASE_NAME="${DATABASE_NAME:-sciencia_google_play}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "$DATABASE_NAME" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "DATABASE_NAME must be a simple PostgreSQL identifier" >&2
    exit 2
fi

if ! "$PSQL_BIN" -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres \
    -Atqc "SELECT 1 FROM pg_database WHERE datname = '$DATABASE_NAME'" | grep -qx 1; then
    "$PSQL_BIN" -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres \
        -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"$DATABASE_NAME\""
fi

if ! "$PSQL_BIN" -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$DATABASE_NAME" \
    -Atqc "SELECT to_regclass('public.apps') IS NOT NULL" | grep -qx t; then
    "$PSQL_BIN" -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$DATABASE_NAME" \
        -v ON_ERROR_STOP=1 -f "$PROJECT_DIR/docs/google-play/google_play_schema.sql"
else
    echo "Schema already exists; leaving existing tables and data unchanged."
fi

echo "Database ready: postgresql://$PGUSER@$PGHOST:$PGPORT/$DATABASE_NAME"
