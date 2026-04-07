#!/usr/bin/env bash
# trigger_planogram_agent.sh — Write inbox + clear state + trigger Paperclip Plano-Agent
# Usage: bash trigger_planogram_agent.sh STORE_CODE PHONE NAME [AREA]
# Examples:
#   bash trigger_planogram_agent.sh ROYAL +628983539659 Wayan
#   bash trigger_planogram_agent.sh ALL +628983539659 Wayan Jatim
set -euo pipefail

STORE="${1:-}"
PHONE="${2:-}"
NAME="${3:-}"
AREA="${4:-Jatim}"

if [[ -z "$STORE" || -z "$PHONE" || -z "$NAME" ]]; then
  echo "Usage: $0 STORE_CODE PHONE NAME [AREA]"
  echo "  STORE: GM|PTC|TP|ROYAL|SDA|CITO|BATU|MOG|MATOS|ICON|SUNRISE|ALL"
  echo "  AREA: Jatim (default), Jakarta, Bali, etc."
  exit 1
fi

# ── Paths ──
INBOX="$HOME/.paperclip/instances/default/workspaces/35f69382-704f-4980-8822-33954e15db44/inbox"
ROUTINE="a5d55c55-8947-4f16-a037-0f17e59b9673"
API_KEY="pcp_plano_b02d92586af29db103cec56f35b6f52b6ed12c774064fd70"
API_URL="http://localhost:3100"

# ── 1. Write inbox JSON ──
cat > "$INBOX/plano_request.json" <<ENDJSON
{
  "flow": "planogram",
  "store": "$STORE",
  "area": "$AREA",
  "requester_phone": "$PHONE",
  "requester_name": "$NAME",
  "requested_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
ENDJSON
echo "[plano-trigger] Inbox written: store=$STORE area=$AREA requester=$NAME"

# ── 2. Clear agent state (prevent "already ran" skip) ──
PGPASSWORD=paperclip psql -h 127.0.0.1 -p 54329 -U paperclip -d paperclip -q -c \
  "UPDATE agents SET status='idle', adapter_config=adapter_config-'last_run_summary'-'last_run_result' WHERE name='Plano-Agent';" 2>/dev/null || true
echo "[plano-trigger] Agent state cleared"

# ── 3. Trigger routine via API ──
# Try routine trigger first, fallback to direct agent run
if [[ -n "$ROUTINE" ]]; then
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/routines/$ROUTINE/run" \
    -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" -d '{}')
  echo "[plano-trigger] Routine trigger HTTP=$HTTP"
else
  # Fallback: trigger agent directly
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/agents/35f69382-704f-4980-8822-33954e15db44/run" \
    -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" -d '{}')
  echo "[plano-trigger] Agent direct trigger HTTP=$HTTP"
fi

echo "[plano-trigger] Done. Plano-Agent will process and send results via WA."
