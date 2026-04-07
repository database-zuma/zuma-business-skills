#!/usr/bin/env bash
# plano_heartbeat.sh — Planogram Agent entry point
# Reads inbox, generates planogram, uploads GDrive, sends WA, writes DB
set -euo pipefail

# ── Paths ──
export PATH="$HOME/homebrew/bin:$HOME/.local/bin:$HOME/homebrew/opt/node/bin:/usr/local/bin:/usr/bin:/bin"
AGENT_HOME="$HOME/.paperclip/instances/default/workspaces/35f69382-704f-4980-8822-33954e15db44"
INBOX="$AGENT_HOME/inbox"
OUTBOX="$AGENT_HOME/outbox"
SCRIPTS="$HOME/.claude/skills/zuma-plano-ro-skills/planogram-agent"
REQUEST_FILE="$INBOX/plano_request.json"
AP_PHONE="+628983539659"  # Wayan — Allocations Planner

# ── DB credentials ──
export PGHOST="76.13.194.120"
export PGPORT="5432"
export PGDATABASE="openclaw_ops"
export PGUSER="openclaw_app"
export PGPASSWORD='Zuma-0psCl4w-2026!'

DATE=$(date +%Y%m%d)

# ============================================================
# HELPERS
# ============================================================
log() { echo "[plano-hb $(date +%H:%M:%S)] $*"; }

send_wa_single() {
  local PHONE="$1" MSG="$2"
  local OK
  OK=$(openclaw message send --channel whatsapp --target "$PHONE" --message "$MSG" --json 2>/dev/null | grep -c '"ok"' || true)
  if [[ "$OK" -lt 1 ]]; then
    log "WA send failed to $PHONE, restarting gateway..."
    openclaw gateway restart 2>/dev/null || true
    sleep 5
    openclaw message send --channel whatsapp --target "$PHONE" --message "$MSG" --json 2>/dev/null || log "WA retry failed to $PHONE"
  fi
}

send_wa() {
  local MSG="$1"
  # Send to requester
  if [[ -n "$REQ_PHONE" && "$REQ_PHONE" != "$AP_PHONE" ]]; then
    send_wa_single "$REQ_PHONE" "$MSG"
  fi
  # Always send to AP
  send_wa_single "$AP_PHONE" "$MSG"
}

upload_gsheet() {
  local FILE="$1" FOLDER="$2"
  python3 "$HOME/.claude/skills/zuma-plano-ro-skills/step3-zuma-ro-surplus-skills/upload_gsheet.py" \
    --file "$FILE" --folder "$FOLDER" 2>&1 | tail -1 | sed 's/GSHEET_LINK=//'
}

# ============================================================
# CHECK INBOX
# ============================================================
if [[ ! -f "$REQUEST_FILE" ]]; then
  log "No request file found at $REQUEST_FILE — nothing to do."
  exit 0
fi

log "Reading request: $REQUEST_FILE"
FLOW=$(python3 -c "import json; d=json.load(open('$REQUEST_FILE')); print(d.get('flow','planogram'))")
STORE=$(python3 -c "import json; d=json.load(open('$REQUEST_FILE')); print(d.get('store','ALL'))")
AREA=$(python3 -c "import json; d=json.load(open('$REQUEST_FILE')); print(d.get('area','Jatim'))")
REQ_PHONE=$(python3 -c "import json; d=json.load(open('$REQUEST_FILE')); print(d.get('requester_phone',''))")
REQ_NAME=$(python3 -c "import json; d=json.load(open('$REQUEST_FILE')); print(d.get('requester_name',''))")

log "Flow=$FLOW Store=$STORE Area=$AREA Requester=$REQ_NAME"

# ============================================================
# STORE CODE MAPPING (bash 3.2 compatible)
# ============================================================
get_store_full() {
  case "$1" in
    GM)      echo "Zuma Galaxy Mall" ;;
    PTC)     echo "ZUMA PTC" ;;
    TP)      echo "Zuma Tunjungan Plaza" ;;
    ROYAL)   echo "Zuma Royal Plaza" ;;
    SDA)     echo "Zuma Lippo Sidoarjo" ;;
    CITO)    echo "Zuma City Of Tomorrow Mall" ;;
    BATU)    echo "Zuma Lippo Batu" ;;
    MOG)     echo "Zuma Mall Olympic Garden" ;;
    MATOS)   echo "Zuma Matos" ;;
    ICON)    echo "Zuma Icon Gresik" ;;
    SUNRISE) echo "Zuma Sunrise Mall" ;;
    *)       echo "$1" ;;
  esac
}

get_store_db() {
  case "$1" in
    GM)      echo "zuma galaxy mall" ;;
    PTC)     echo "zuma ptc" ;;
    TP)      echo "zuma tunjungan plaza" ;;
    ROYAL)   echo "zuma royal plaza" ;;
    SDA)     echo "zuma lippo sidoarjo" ;;
    CITO)    echo "zuma city of tomorrow mall" ;;
    BATU)    echo "zuma lippo batu" ;;
    MOG)     echo "zuma mall olympic garden" ;;
    MATOS)   echo "zuma matos" ;;
    ICON)    echo "zuma icon gresik" ;;
    SUNRISE) echo "zuma sunrise mall" ;;
    *)       echo "$1" ;;
  esac
}

# ============================================================
# GENERATE PLANOGRAM
# ============================================================
run_planogram() {
  local SCODE="$1"
  local STORE_FULL="$(get_store_full "$SCODE")"
  local STORE_DB="$(get_store_db "$SCODE")"

  log "Generating planogram for $STORE_FULL (db=$STORE_DB)..."

  # Run the generator
  local OUTFILE="$OUTBOX/Planogram-${DATE}-${SCODE}.xlsx"
  python3 "$SCRIPTS/generate_planogram_agent.py" \
    --store-code "$SCODE" \
    --store-name "$STORE_FULL" \
    --store-db "$STORE_DB" \
    --area "$AREA" \
    --output "$OUTFILE" \
    2>&1 | while read -r line; do log "  $line"; done

  if [[ ! -f "$OUTFILE" ]]; then
    log "ERROR: Output file not created for $SCODE"
    send_wa "Planogram $STORE_FULL GAGAL. Output file not generated. Hubungi admin."
    return 1
  fi

  # Upload to GDrive
  log "Uploading to GDrive..."
  local GLINK
  GLINK=$(upload_gsheet "$OUTFILE" "Planogram/$AREA/$DATE")
  log "GSheet link: $GLINK"

  # Send WA
  local MSG="Planogram *${STORE_FULL}* sudah selesai.

Link: $GLINK

Output:
- Sheet 'Layout Visual': Denah planogram visual (format v4)
- Sheet 'Summary': Tabel per SKU, subtotal per zone

Data juga sudah di-update di database (portal.planogram_paperclip).

_Generated by Plano-Agent (Paperclip) — $(date '+%d %B %Y %H:%M WIB')_"

  send_wa "$MSG"
  log "Done: $SCODE"
}

# ============================================================
# DISPATCH
# ============================================================
if [[ "$STORE" == "ALL" ]]; then
  log "Running ALL stores in $AREA..."
  STORES_LIST=("GM" "PTC" "TP" "ROYAL" "SDA" "CITO" "BATU" "MOG" "MATOS" "ICON" "SUNRISE")
  SUCCESS=0
  FAIL=0
  for S in "${STORES_LIST[@]}"; do
    if run_planogram "$S"; then
      ((SUCCESS++))
    else
      ((FAIL++))
    fi
  done
  send_wa "Planogram batch selesai: $SUCCESS berhasil, $FAIL gagal dari ${#STORES_LIST[@]} toko."
else
  run_planogram "$STORE"
fi

# ============================================================
# CLEANUP
# ============================================================
mv "$REQUEST_FILE" "$REQUEST_FILE.done.$(date +%s)" 2>/dev/null || true
log "Request archived. Heartbeat complete."
