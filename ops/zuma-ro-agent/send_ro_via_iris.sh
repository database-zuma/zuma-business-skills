#!/usr/bin/env bash
# Send RO files via Iris (OpenClaw WA gateway)
# Usage: send_ro_via_iris.sh <file1.xlsx> [file2.xlsx] [file3.xlsx] ...
# Or:    send_ro_via_iris.sh --all  (sends all files from today's generation)

set -euo pipefail

WAYAN_PHONE="+628983539659"  # AS (Wayan)
# ALLOC_PHONE="TBD"          # Allocations Planner
TODAY=$(date +%Y-%m-%d)
UPLOAD_SCRIPT="$HOME/.claude/skills/zuma-plano-ro-skills/step3-zuma-ro-surplus-skills/upload_gsheet.py"

send_file() {
    local XLSX_PATH="$1"
    local FILENAME
    FILENAME=$(basename "$XLSX_PATH")

    echo "--- Sending: $FILENAME ---"

    # Upload to dedicated GDrive folder: ROBOX/YYYY-MM-DD
    GDRIVE_FOLDER="ROBOX/${TODAY}"
    echo "  Uploading to GDrive (${GDRIVE_FOLDER})..."
    UPLOAD_OUTPUT=$(python3 "$UPLOAD_SCRIPT" --file "$XLSX_PATH" --folder "$GDRIVE_FOLDER" 2>&1) || {
        echo "  WARN: GSheet upload failed for $FILENAME"
        echo "$UPLOAD_OUTPUT"
        return 1
    }
    GDRIVE_LINK=$(echo "$UPLOAD_OUTPUT" | grep "GSHEET_LINK=" | cut -d'=' -f2-)

    if [ -z "$GDRIVE_LINK" ]; then
        echo "  ERROR: No GDrive link for $FILENAME"
        return 1
    fi
    echo "  Link: $GDRIVE_LINK"

    # Extract store name from filename: ROBOX-20260331-GM-00001.xlsx → GM
    STORE=$(echo "$FILENAME" | sed 's/ROBOX-[0-9]*-\(.*\)-[0-9]*.xlsx/\1/')

    # Send to Wayan
    MSG="*ROBOX ${TODAY} — ${STORE}*

File RO: ${GDRIVE_LINK}

Silakan review & adjust. Reply *lanjut picking list* kalau sudah."

    echo "  Sending to Wayan..."
    openclaw message send --channel whatsapp \
        --target "$WAYAN_PHONE" \
        --message "$MSG" 2>&1 || echo "  WARN: WA send failed — check listener"

    echo "  Done: $FILENAME → $GDRIVE_LINK"
    echo ""
}

# Main
if [ "${1:-}" = "--all" ]; then
    DATE_COMPACT=$(date +%Y%m%d)
    RO_OUTBOX="$HOME/.paperclip/instances/default/workspaces/b1b9ff7c-0b4b-44cd-a012-21e77d02edc2/outbox"
    FILES=$(find "$RO_OUTBOX" -name "ROBOX-${DATE_COMPACT}-*.xlsx" 2>/dev/null | sort)
    if [ -z "$FILES" ]; then
        echo "No ROBOX files found for today ($DATE_COMPACT)."
        exit 0
    fi
    COUNT=0
    while IFS= read -r f; do
        send_file "$f"
        COUNT=$((COUNT + 1))
    done <<< "$FILES"
    echo "Sent $COUNT files."
else
    for f in "$@"; do
        send_file "$f"
    done
fi
