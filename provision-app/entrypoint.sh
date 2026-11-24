#!/usr/bin/env bash
set -euo pipefail

DB_FILE="${DB_FILE:-./expenses.db}"
BLOB_CONTAINER="${BLOB_CONTAINER:-dbcontainer}"
BLOB_NAME="${BLOB_NAME:-expenses.db}"

upload_db() {
    if [ -z "${AZURE_STORAGE_CONNECTION_STRING:-}" ]; then
        echo "[sync] AZURE_STORAGE_CONNECTION_STRING not set; skipping upload."
        return 0
    fi

    if [ ! -f "$DB_FILE" ]; then
        echo "[sync] Local DB file '$DB_FILE' not found; skipping upload."
        return 0
    fi

    echo "[sync] Checkpointing SQLite and uploading '$DB_FILE' to '$BLOB_CONTAINER/$BLOB_NAME'..."
    python3 - <<'PY'
import os
import sqlite3
from azure.storage.blob import BlobServiceClient

db_file = os.environ.get("DB_FILE", "./expenses.db")
container_name = os.environ.get("BLOB_CONTAINER", "dbcontainer")
blob_name = os.environ.get("BLOB_NAME", "expenses.db")
conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]

# Flush any WAL frames into the main DB file before uploading
try:
    con = sqlite3.connect(db_file, timeout=10)
    con.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    con.commit()
    con.close()
except sqlite3.Error as exc:
    print(f"[sync] SQLite checkpoint warning: {exc}")

service_client = BlobServiceClient.from_connection_string(conn_str)
blob_client = service_client.get_blob_client(container=container_name, blob=blob_name)
with open(db_file, "rb") as f:
    blob_client.upload_blob(f, overwrite=True)

print("[sync] Upload complete.")
PY
}

download_db() {
    if [ -z "${AZURE_STORAGE_CONNECTION_STRING:-}" ]; then
        echo "[sync] AZURE_STORAGE_CONNECTION_STRING not set; starting with fresh/local DB."
        return 0
    fi

    echo "[sync] Checking for existing '$BLOB_CONTAINER/$BLOB_NAME'..."
    python3 - <<'PY'
import os
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

db_file = os.environ.get("DB_FILE", "./expenses.db")
container_name = os.environ.get("BLOB_CONTAINER", "dbcontainer")
blob_name = os.environ.get("BLOB_NAME", "expenses.db")
conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]

parent = os.path.dirname(os.path.abspath(db_file))
if parent:
    os.makedirs(parent, exist_ok=True)

service_client = BlobServiceClient.from_connection_string(conn_str)
blob_client = service_client.get_blob_client(container=container_name, blob=blob_name)

try:
    stream = blob_client.download_blob()
    with open(db_file, "wb") as f:
        f.write(stream.readall())
    print(f"[sync] Downloaded '{blob_name}' to '{db_file}'.")
except ResourceNotFoundError:
    print(f"[sync] Blob '{blob_name}' not found yet; starting fresh.")
PY
}

APP_PID=""
UPLOADED=0

cleanup() {
    trap - TERM INT EXIT
    if [ -n "$APP_PID" ] && kill -0 "$APP_PID" 2>/dev/null; then
        echo "[entrypoint] Forwarding SIGTERM to app (PID $APP_PID)..."
        kill -TERM "$APP_PID" 2>/dev/null || true
        wait "$APP_PID" 2>/dev/null || true
    fi
    if [ "$UPLOADED" -eq 0 ]; then
        UPLOADED=1
        upload_db || true
    fi
}

trap cleanup TERM INT EXIT

download_db

echo "[entrypoint] Starting application: $*"
"$@" &
APP_PID=$!

wait "$APP_PID"
EXIT_CODE=$?
APP_PID=""

if [ "$UPLOADED" -eq 0 ]; then
    UPLOADED=1
    upload_db || true
fi

exit "$EXIT_CODE"