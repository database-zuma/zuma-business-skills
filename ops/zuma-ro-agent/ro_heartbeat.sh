#!/usr/bin/env bash
# RO Agent Heartbeat — unified entry point for ALL RO flows.
# Reads inbox/ro_request.json for context, then executes the requested flow.
#
# Usage:
#   ro_heartbeat.sh                     # reads flow from inbox, or defaults to Flow 1
#   ro_heartbeat.sh --date 2026-04-01   # override date
#
# Inbox format (written by Iris before triggering):
#
# Flow 1 (RO Form):
#   {"flow":"ro", "store":"SDA", "requester_phone":"+62...", "requester_name":"Nisa"}
#   {"flow":"ro", "store":"ALL", ...}   ← all stores
#
# Flow 2 (Picking List):
#   {"flow":"picking", "stores":"GM,ROYAL,PTC", "requester_phone":"+62...", "requester_name":"Wayan"}
#
# Flow 3 (SOPB):
#   {"flow":"sopb", "store":"ROYAL", "entity":"DDD", "sopb_number":"SOPB/DDD/WHS/2026/IV/001",
#    "tanggal_diminta":"2026-04-04", "requester_phone":"+62...", "requester_name":"Wayan"}
#   For multi-entity: "entity":"DDD,LJBB", "sopb_number":"SOPB/.../001,SOPB/.../002"

set -euo pipefail

# Ensure homebrew binaries (openclaw, python3, etc.) are in PATH
export PATH="$HOME/homebrew/bin:$HOME/homebrew/sbin:/usr/local/bin:$PATH"

AGENT_HOME="$HOME/.paperclip/instances/default/workspaces/b1b9ff7c-0b4b-44cd-a012-21e77d02edc2"
INBOX="$AGENT_HOME/inbox"
OUTBOX="$AGENT_HOME/outbox"
SCRIPTS="$HOME/.claude/skills/zuma-plano-ro-skills/step3-zuma-ro-surplus-skills"
AP_PHONE="+628983539659"  # Allocations Planner (Wayan for now)
REQUEST_FILE="$INBOX/ro_request.json"

# Parse --date flag
DATE="$(date +%Y-%m-%d)"
while [ $# -gt 0 ]; do
    case "$1" in
        --date) DATE="$2"; shift 2;;
        *) shift;;
    esac
done
DATE_COMPACT=$(echo "$DATE" | tr -d '-')

# ─── Read inbox ─────────────────────────────────────────────
FLOW="ro"
STORE=""
STORES=""
ENTITY=""
SOPB_NUMBER=""
TANGGAL=""
REQUESTER_PHONE=""
REQUESTER_NAME=""
GSHEET_ID=""          # ROBOX GSheet ID (for Flow 2 to read Actual RO)
PICKING_GSHEET_ID=""  # Picking List GSheet ID (for Flow 3 to read adjusted qty)

if [ -f "$REQUEST_FILE" ]; then
    read_json() { python3 -c "import json; print(json.load(open('$REQUEST_FILE')).get('$1',''))" 2>/dev/null || true; }
    FLOW=$(read_json flow)
    STORE=$(read_json store)
    STORES=$(read_json stores)
    ENTITY=$(read_json entity)
    SOPB_NUMBER=$(read_json sopb_number)
    TANGGAL=$(read_json tanggal_diminta)
    REQUESTER_PHONE=$(read_json requester_phone)
    REQUESTER_NAME=$(read_json requester_name)
    GSHEET_ID=$(read_json gsheet_id)
    PICKING_GSHEET_ID=$(read_json picking_gsheet_id)
    [ -z "$FLOW" ] && FLOW="ro"
    echo "Inbox: flow=$FLOW store=$STORE stores=$STORES gsheet=$GSHEET_ID requester=$REQUESTER_NAME"
else
    echo "No inbox file — running Flow 1 (all stores)"
fi

# ─── Helper: send WA to requester + AP ──────────────────────
send_wa() {
    local MSG="$1"
    # Send to requester (if different from AP)
    if [ -n "$REQUESTER_PHONE" ] && [ "$REQUESTER_PHONE" != "$AP_PHONE" ]; then
        echo "  WA → $REQUESTER_NAME ($REQUESTER_PHONE)"
        openclaw message send --channel whatsapp --account default --target "$REQUESTER_PHONE" -m "$MSG" 2>&1 || true
    fi
    # Always send to AP
    echo "  WA → AP ($AP_PHONE)"
    openclaw message send --channel whatsapp --account default --target "$AP_PHONE" -m "$MSG" 2>&1 || true
}

# ─── Helper: upload file as GSheet, return link ─────────────
upload_gsheet() {
    local FILE="$1"
    local FOLDER="$2"
    python3 "$SCRIPTS/upload_gsheet.py" --file "$FILE" --folder "$FOLDER" 2>&1 | grep "GSHEET_LINK=" | cut -d'=' -f2-
}

# ═══════════════════════════════════════════════════════════
#  FLOW 1: RO FORM (Generate ROBOX → upload → send)
# ═══════════════════════════════════════════════════════════
run_flow_ro() {
    echo "=== FLOW 1: RO FORM — $DATE ==="

    # Clean old files for this run
    if [ -n "$STORE" ] && [ "$STORE" != "ALL" ]; then
        rm -f "$OUTBOX"/ROBOX-${DATE_COMPACT}-${STORE}-*.xlsx 2>/dev/null || true
        python3 "$SCRIPTS/generate_ro.py" --store "$STORE" --date "$DATE"
    else
        rm -f "$OUTBOX"/ROBOX-${DATE_COMPACT}-*.xlsx 2>/dev/null || true
        python3 "$SCRIPTS/generate_ro.py" --date "$DATE"
    fi

    # Upload + send (only files for requested store, not all)
    local FILES
    if [ -n "$STORE" ] && [ "$STORE" != "ALL" ]; then
        FILES=$(find "$OUTBOX" -name "ROBOX-${DATE_COMPACT}-${STORE}-*.xlsx" 2>/dev/null | sort)
    else
        FILES=$(find "$OUTBOX" -name "ROBOX-${DATE_COMPACT}-*.xlsx" 2>/dev/null | sort)
    fi
    [ -z "$FILES" ] && { echo "No RO files generated."; return; }

    local COUNT=0
    while IFS= read -r f; do
        local FN STORE_CODE LINK
        FN=$(basename "$f")
        STORE_CODE=$(echo "$FN" | sed 's/ROBOX-[0-9]*-\(.*\)-[0-9]*.xlsx/\1/')
        echo "  Uploading $FN..."
        LINK=$(upload_gsheet "$f" "ROBOX/$DATE")
        [ -z "$LINK" ] && { echo "  WARN: Upload failed"; continue; }
        send_wa "*ROBOX $DATE — $STORE_CODE*
File RO: $LINK
Silakan review & adjust. Reply *lanjut picking list [store]* kalau sudah."
        COUNT=$((COUNT + 1))
    done <<< "$FILES"
    echo "=== FLOW 1 DONE: $COUNT files sent ==="
}

# ═══════════════════════════════════════════════════════════
#  FLOW 2: PICKING LIST (for AP-approved stores only)
# ═══════════════════════════════════════════════════════════
run_flow_picking() {
    echo "=== FLOW 2: PICKING LIST — $DATE ==="

    if [ -z "$STORES" ]; then
        echo "ERROR: No stores specified. Inbox must have 'stores' field (e.g. 'GM,ROYAL,PTC')."
        return 1
    fi

    echo "  Approved stores: $STORES"

    # Auto-detect ROBOX GSheet ID if not provided or invalid
    local RESOLVED_GSHEET="$GSHEET_ID"
    if [ -z "$RESOLVED_GSHEET" ] || echo "$RESOLVED_GSHEET" | grep -q "^1[a-zA-Z0-9_-]\{10,\}$" 2>/dev/null; then
        # Try to find latest native GSheet for this store in GDrive
        local FIRST_STORE
        FIRST_STORE=$(echo "$STORES" | cut -d',' -f1)
        echo "  Auto-detecting ROBOX GSheet for $FIRST_STORE..."
        RESOLVED_GSHEET=$(python3 -c "
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
with open('$HOME/.config/gspread/authorized_user.json') as f:
    td = json.load(f)
creds = Credentials(token=td.get('token'), refresh_token=td.get('refresh_token'),
    token_uri='https://oauth2.googleapis.com/token', client_id=td.get('client_id'), client_secret=td.get('client_secret'))
if creds.expired: creds.refresh(Request())
drive = build('drive', 'v3', credentials=creds)
r = drive.files().list(
    q=\"name contains 'ROBOX-' and name contains '$FIRST_STORE' and mimeType='application/vnd.google-apps.spreadsheet'\",
    fields='files(id)', orderBy='createdTime desc', pageSize=1).execute()
files = r.get('files',[])
print(files[0]['id'] if files else '')
" 2>/dev/null)
        if [ -n "$RESOLVED_GSHEET" ]; then
            echo "  Found: $RESOLVED_GSHEET"
        else
            echo "  No native GSheet found — falling back to DB"
        fi
    fi

    local GSHEET_ARG=""
    if [ -n "$RESOLVED_GSHEET" ]; then
        GSHEET_ARG="--gsheet-id $RESOLVED_GSHEET"
    fi
    python3 "$SCRIPTS/generate_picking_list.py" --stores "$STORES" --date "$DATE" $GSHEET_ARG

    # Find the generated file
    local PL_FILE
    PL_FILE=$(find "$OUTBOX" -name "PickingList-${DATE_COMPACT}-*.xlsx" -newer "$REQUEST_FILE" 2>/dev/null | sort | tail -1)
    [ -z "$PL_FILE" ] && { echo "ERROR: Picking list not generated."; return 1; }

    echo "  Uploading $(basename "$PL_FILE")..."
    local LINK
    LINK=$(upload_gsheet "$PL_FILE" "PickingList/$DATE")
    [ -z "$LINK" ] && { echo "WARN: Upload failed"; return 1; }

    send_wa "*PICKING LIST $DATE — $STORES*
File: $LINK
Untuk WHS: print dan mulai picking. Reply *lanjut SOPB [store]* + SOPB number + tanggal diminta setelah picking selesai."
    echo "=== FLOW 2 DONE ==="
}

# ═══════════════════════════════════════════════════════════
#  FLOW 3: SOPB (needs SOPB number + entity + tanggal)
# ═══════════════════════════════════════════════════════════
run_flow_sopb() {
    echo "=== FLOW 3: SOPB — $DATE ==="

    if [ -z "$STORE" ] || [ -z "$ENTITY" ] || [ -z "$SOPB_NUMBER" ] || [ -z "$TANGGAL" ]; then
        echo "ERROR: Missing required fields."
        echo "  store=$STORE entity=$ENTITY sopb_number=$SOPB_NUMBER tanggal=$TANGGAL"
        echo "  All 4 fields are required for SOPB generation."
        return 1
    fi

    echo "  Store: $STORE | Entity: $ENTITY | SOPB: $SOPB_NUMBER | Tanggal: $TANGGAL"

    # Auto-detect ROBOX GSheet ID if not provided
    local RESOLVED_GSHEET="$GSHEET_ID"
    if [ -z "$RESOLVED_GSHEET" ]; then
        echo "  Auto-detecting ROBOX GSheet for $STORE..."
        RESOLVED_GSHEET=$(python3 -c "
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
with open('$HOME/.config/gspread/authorized_user.json') as f:
    td = json.load(f)
creds = Credentials(token=td.get('token'), refresh_token=td.get('refresh_token'),
    token_uri='https://oauth2.googleapis.com/token', client_id=td.get('client_id'), client_secret=td.get('client_secret'))
if creds.expired: creds.refresh(Request())
drive = build('drive', 'v3', credentials=creds)
r = drive.files().list(
    q=\"name contains 'ROBOX-' and name contains '$STORE' and mimeType='application/vnd.google-apps.spreadsheet'\",
    fields='files(id)', orderBy='createdTime desc', pageSize=1).execute()
files = r.get('files',[])
print(files[0]['id'] if files else '')
" 2>/dev/null)
        [ -n "$RESOLVED_GSHEET" ] && echo "  Found: $RESOLVED_GSHEET" || echo "  Not found — falling back to DB"
    fi

    local SOPB_GSHEET_ARG=""
    if [ -n "$RESOLVED_GSHEET" ]; then
        SOPB_GSHEET_ARG="--gsheet-id $RESOLVED_GSHEET"
    fi
    python3 "$SCRIPTS/generate_sopb.py" \
        --store "$STORE" \
        --entity "$ENTITY" \
        --sopb-number "$SOPB_NUMBER" \
        --tanggal-diminta "$TANGGAL" \
        --date "$DATE" $SOPB_GSHEET_ARG

    # Find generated file(s)
    local SOPB_FILES
    SOPB_FILES=$(find "$OUTBOX" -name "SOPB-${DATE_COMPACT}-${STORE}-*.xlsx" -newer "$REQUEST_FILE" 2>/dev/null | sort)
    [ -z "$SOPB_FILES" ] && { echo "ERROR: SOPB not generated."; return 1; }

    while IFS= read -r f; do
        local FN LINK
        FN=$(basename "$f")
        echo "  Uploading $FN..."
        LINK=$(upload_gsheet "$f" "SOPB/$DATE")
        [ -z "$LINK" ] && { echo "WARN: Upload failed for $FN"; continue; }
        send_wa "*SOPB $DATE — $STORE ($ENTITY)*
File: $LINK
SOPB Number: $SOPB_NUMBER
Upload file ini ke Accurate Online → Permintaan Barang.
Setelah dapat DNPB number, input di Branch Super App."
    done <<< "$SOPB_FILES"
    echo "=== FLOW 3 DONE ==="
}

# ─── Auto-clear stale agent state ────────────────────────
# This ensures agent never skips because of previous run summary
PGPASSWORD=paperclip psql -h 127.0.0.1 -p 54329 -U paperclip -d paperclip -c \
  "UPDATE agents SET adapter_config = adapter_config - 'last_run_summary' - 'last_run_result' WHERE name = 'RO-Agent';" 2>/dev/null || true

# ═══════════════════════════════════════════════════════════
#  MAIN — dispatch based on flow
# ═══════════════════════════════════════════════════════════
case "$FLOW" in
    ro|RO|"")       run_flow_ro ;;
    picking|PICKING) run_flow_picking ;;
    sopb|SOPB)       run_flow_sopb ;;
    *)               echo "Unknown flow: $FLOW (valid: ro, picking, sopb)"; exit 1 ;;
esac

# Cleanup inbox
if [ -f "$REQUEST_FILE" ]; then
    mv "$REQUEST_FILE" "$REQUEST_FILE.done.$(date +%s)" 2>/dev/null || true
fi
