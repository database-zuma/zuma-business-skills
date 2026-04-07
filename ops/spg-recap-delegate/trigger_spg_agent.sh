#!/usr/bin/env bash
set -eo pipefail

AREA="${1:-ALL}"
MONTH="${2:-$(date +%-m)}"
YEAR="${3:-$(date +%Y)}"
PHONE="${4:-}"
NAME="${5:-}"

if [[ -z "$PHONE" || -z "$NAME" ]]; then
  echo "Usage: $0 AREA MONTH YEAR PHONE NAME"
  exit 1
fi

INBOX="$HOME/.paperclip/instances/default/workspaces/e7a1b2c3-d4e5-f6a7-b8c9-0d1e2f3a4b5c/inbox"
ROUTINE="f8e7d6c5-b4a3-9281-7060-504030201000"
API_KEY="pcp_spg_78f4d9f6b67cd1522cec519528902b33e92b233685cae976"

cat > "$INBOX/spg_request.json" <<ENDJSON
{
  "flow": "spg_recap",
  "area": "$AREA",
  "month": "$MONTH",
  "year": "$YEAR",
  "requester_phone": "$PHONE",
  "requester_name": "$NAME",
  "requested_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
ENDJSON
echo "[spg-trigger] Inbox written: area=$AREA month=$MONTH/$YEAR requester=$NAME"

PGPASSWORD=paperclip psql -h 127.0.0.1 -p 54329 -U paperclip -d paperclip -q -c \
  "UPDATE agents SET status='idle', adapter_config=adapter_config-'last_run_summary'-'last_run_result' WHERE name='SPG-Recap-Agent';" 2>/dev/null || true

HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:3100/api/routines/$ROUTINE/run" \
  -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" -d '{}')
echo "[spg-trigger] Routine trigger HTTP=$HTTP"
