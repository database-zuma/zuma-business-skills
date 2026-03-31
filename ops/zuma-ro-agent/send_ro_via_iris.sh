#!/usr/bin/env bash
# Send RO files via Iris (OpenClaw WA gateway)
# Reads request context from inbox/ro_request.json to know who to send to.
#
# Usage: send_ro_via_iris.sh <file1.xlsx> [file2.xlsx] ...
# Or:    send_ro_via_iris.sh --all

set -euo pipefail

ALLOC_PLANNER_PHONE="+628983539659"  # Allocations Planner (Wayan for now)
RO_INBOX="$HOME/.paperclip/instances/default/workspaces/b1b9ff7c-0b4b-44cd-a012-21e77d02edc2/inbox"
RO_OUTBOX="$HOME/.paperclip/instances/default/workspaces/b1b9ff7c-0b4b-44cd-a012-21e77d02edc2/outbox"
TODAY=$(date +%Y-%m-%d)
UPLOAD_SCRIPT="$HOME/.claude/skills/zuma-plano-ro-skills/step3-zuma-ro-surplus-skills/upload_gsheet.py"

# Read request context (who triggered, send to whom)
REQUESTER_PHONE=""
REQUESTER_NAME=""
REQUEST_FILE="$RO_INBOX/ro_request.json"
if [ -f "$REQUEST_FILE" ]; then
    REQUESTER_PHONE=$(python3 -c "import json; d=json.load(open('$REQUEST_FILE')); print(d.get('requester_phone',''))" 2>/dev/null || true)
    REQUESTER_NAME=$(python3 -c "import json; d=json.load(open('$REQUEST_FILE')); print(d.get('requester_name',''))" 2>/dev/null || true)
    echo "Request context: ${REQUESTER_NAME} (${REQUESTER_PHONE})"
fi

send_to_wa() {
    local PHONE="$1"
    local MSG="$2"
    if [ -n "$PHONE" ]; then
        openclaw message send --channel whatsapp --account default \
            --target "$PHONE" --message "$MSG" 2>&1 || echo "  WARN: WA send failed to $PHONE"
    fi
}

send_file() {
    local XLSX_PATH="$1"
    local FILENAME
    FILENAME=$(basename "$XLSX_PATH")

    echo "--- Sending: $FILENAME ---"

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

    STORE=$(echo "$FILENAME" | sed 's/ROBOX-[0-9]*-\(.*\)-[0-9]*.xlsx/\1/')

    MSG="*ROBOX ${TODAY} — ${STORE}*

File RO: ${GDRIVE_LINK}

Silakan review & adjust. Reply *lanjut picking list* kalau sudah."

    # 1. Send to requester (AS who triggered)
    if [ -n "$REQUESTER_PHONE" ] && [ "$REQUESTER_PHONE" != "$ALLOC_PLANNER_PHONE" ]; then
        echo "  Sending to requester: ${REQUESTER_NAME} (${REQUESTER_PHONE})..."
        send_to_wa "$REQUESTER_PHONE" "$MSG"
    fi

    # 2. Always send to Allocations Planner
    echo "  Sending to AP: ${ALLOC_PLANNER_PHONE}..."
    send_to_wa "$ALLOC_PLANNER_PHONE" "$MSG"

    echo "  Done: $FILENAME → $GDRIVE_LINK"
    echo ""
}

# Main
if [ "${1:-}" = "--all" ]; then
    DATE_COMPACT=$(date +%Y%m%d)
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

# Cleanup request context after send
if [ -f "$REQUEST_FILE" ]; then
    mv "$REQUEST_FILE" "$REQUEST_FILE.done.$(date +%s)" 2>/dev/null
fi
