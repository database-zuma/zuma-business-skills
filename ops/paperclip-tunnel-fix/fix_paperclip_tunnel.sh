#!/usr/bin/env bash
# fix_paperclip_tunnel.sh — One-command Paperclip tunnel + server fix
# Handles: tunnel URL change after Mac Mini restart, "failed to fetch", 502 errors
set -eo pipefail

export PATH="$HOME/homebrew/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"

PAPERCLIP_PORT=3100
PAPERCLIP_HOME="$HOME/.paperclip/instances/default"
CONFIG="$PAPERCLIP_HOME/config.json"
TUNNEL_LOG="/tmp/cf_tunnel_paperclip.log"

log() { echo "[paperclip-fix $(date +%H:%M:%S)] $*"; }

# ── 1. Kill old Cloudflare tunnel for port 3100 ──
log "Stopping old tunnel..."
pkill -f "cloudflared.*localhost:$PAPERCLIP_PORT" 2>/dev/null || true
sleep 2

# ── 2. Start new tunnel ──
log "Starting new Cloudflare tunnel..."
cloudflared tunnel --url http://localhost:$PAPERCLIP_PORT --no-autoupdate > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

# Wait for URL to appear (max 15s)
NEW_URL=""
for i in $(seq 1 15); do
  NEW_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | tail -1)
  if [[ -n "$NEW_URL" ]]; then
    break
  fi
  sleep 1
done

if [[ -z "$NEW_URL" ]]; then
  log "ERROR: Could not get tunnel URL after 15s"
  cat "$TUNNEL_LOG"
  exit 1
fi

NEW_HOST=$(echo "$NEW_URL" | sed 's|https://||')
log "New tunnel URL: $NEW_URL"

# ── 3. Register hostname in Paperclip ──
log "Registering hostname: $NEW_HOST"
npx paperclipai@2026.403.0 allowed-hostname "$NEW_HOST" 2>/dev/null || {
  # Fallback: update config directly with python
  python3 -c "
import json
with open('$CONFIG') as f:
    cfg = json.load(f)
hosts = cfg.get('server',{}).get('allowedHostnames',[])
if '$NEW_HOST' not in hosts:
    hosts.append('$NEW_HOST')
    cfg['server']['allowedHostnames'] = hosts
cfg['auth']['publicBaseUrl'] = '$NEW_URL'
cfg['\$meta']['updatedAt'] = '$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'
with open('$CONFIG','w') as f:
    json.dump(cfg, f, indent=2)
print('Config updated via python fallback')
"
}

# Update publicBaseUrl
python3 -c "
import json
with open('$CONFIG') as f:
    cfg = json.load(f)
if cfg.get('auth',{}).get('publicBaseUrl') != '$NEW_URL':
    cfg['auth']['publicBaseUrl'] = '$NEW_URL'
    with open('$CONFIG','w') as f:
        json.dump(cfg, f, indent=2)
    print('publicBaseUrl updated to $NEW_URL')
else:
    print('publicBaseUrl already correct')
"

# ── 4. Restart Paperclip server ──
log "Restarting Paperclip server..."
# Kill existing server
pkill -f "paperclipai.*run\|node.*paperclip.*server" 2>/dev/null || true
sleep 3

# Start server
npx paperclipai@2026.403.0 run > /tmp/paperclip-serve.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready (max 30s)
for i in $(seq 1 30); do
  if curl -s --max-time 2 http://localhost:$PAPERCLIP_PORT/api/health 2>/dev/null | grep -q '"ok"'; then
    break
  fi
  sleep 1
done

# ── 5. Verify ──
HEALTH=$(curl -s --max-time 5 http://localhost:$PAPERCLIP_PORT/api/health 2>/dev/null)
TUNNEL_HEALTH=$(curl -s --max-time 5 "$NEW_URL/api/health" 2>/dev/null)

if echo "$HEALTH" | grep -q '"ok"' && echo "$TUNNEL_HEALTH" | grep -q '"ok"'; then
  log "SUCCESS! Paperclip ready."
  log ""
  log "Dashboard: $NEW_URL"
  log "Local:     http://localhost:$PAPERCLIP_PORT"
  log ""
  echo "PAPERCLIP_URL=$NEW_URL"
else
  log "WARNING: Server may still be starting up."
  log "Local health: $HEALTH"
  log "Tunnel health: $TUNNEL_HEALTH"
  log "Dashboard: $NEW_URL"
  echo "PAPERCLIP_URL=$NEW_URL"
fi
