---
name: paperclip-delegate
description: >
  General-purpose Paperclip delegation skill. Check agent status, delegate tasks
  to any Paperclip agent (CEO, RO-Agent, future agents). Iris only writes inbox
  + triggers routine. Never executes tasks herself.
globs:
  - "**/*delegate*"
  - "**/*paperclip*"
  - "**/*agent*"
---

# Paperclip Delegate — General Agent Orchestration

Iris is a mediator between users and Paperclip agents. She delegates, never executes.

---

## Step 0: Check Paperclip Status

Before any delegation, verify Paperclip is running:
```bash
curl -s -o /dev/null -w '%{http_code}' http://localhost:3100/api/companies/a110fd08-96af-4cb5-8375-ce08a2a2cc8e/agents -H "Authorization: Bearer pcp_4b469136118bada6b2255799a25d4b917589d6cc8aee474a"
```
- `200` = OK
- Anything else = Paperclip down. Tell user: "Paperclip server sedang down. Coba restart."

---

## Step 1: List Available Agents

```bash
curl -s http://localhost:3100/api/companies/a110fd08-96af-4cb5-8375-ce08a2a2cc8e/agents \
  -H "Authorization: Bearer pcp_4b469136118bada6b2255799a25d4b917589d6cc8aee474a" | \
  python3 -c "import sys,json; [print(f'{a[\"name\"]}: {a[\"status\"]} — {a[\"title\"]}') for a in json.loads(sys.stdin.read())]"
```

### Current Agents

| Agent | Role | Routine ID | API Key | Trigger |
|-------|------|-----------|---------|---------|
| CEO | Orchestrator | — | — | — |
| Iris (OpenClaw) | Communications | — | — | (this is you) |
| RO-Agent | RO Analysis + Picking + SOPB | `66c05c3a-0901-4fef-9697-82a0a6d90160` (single) / `38549cf0-76f0-44d2-85a0-5d19752205c2` (all stores) | `pcp_ro_4dc96dfb9fb884342e2b1c5485cc11777a648fcc8c225dfe` | See ro-delegate skill |

---

## Step 2: Delegate to Agent

### General Pattern (same for ALL agents)

```bash
# 1. Write inbox JSON to agent workspace
echo '{TASK_JSON}' > ~/.paperclip/instances/default/workspaces/{AGENT_ID}/inbox/request.json

# 2. Clear agent stale state
PGPASSWORD=paperclip psql -h 127.0.0.1 -p 54329 -U paperclip -d paperclip -c \
  "UPDATE agents SET status='idle', adapter_config=adapter_config-'last_run_summary'-'last_run_result' WHERE id='{AGENT_ID}';"

# 3. Trigger routine
curl -s -X POST "http://localhost:3100/api/routines/{ROUTINE_ID}/run" \
  -H "Authorization: Bearer {AGENT_API_KEY}" \
  -H "Content-Type: application/json" -d '{}'
```

### Agent-Specific Details

#### RO-Agent (`b1b9ff7c-0b4b-44cd-a012-21e77d02edc2`)

**Workspace:** `~/.paperclip/instances/default/workspaces/b1b9ff7c-0b4b-44cd-a012-21e77d02edc2/`
**Inbox file:** `inbox/ro_request.json`
**Trigger script:** `bash ~/.openclaw/skills/ro-delegate/trigger_ro_agent.sh {FLOW} {ARGS...}`

Or manual:
```bash
# RO Form
echo '{"flow":"ro","store":"STORE","requester_phone":"PHONE","requester_name":"NAME"}' > ~/.paperclip/instances/default/workspaces/b1b9ff7c-0b4b-44cd-a012-21e77d02edc2/inbox/ro_request.json

# Picking List
echo '{"flow":"picking","stores":"GM,ROYAL","requester_phone":"PHONE","requester_name":"NAME"}' > ~/.paperclip/instances/default/workspaces/b1b9ff7c-0b4b-44cd-a012-21e77d02edc2/inbox/ro_request.json

# SOPB (ask entity + SOPB number + tanggal first)
echo '{"flow":"sopb","store":"ROYAL","entity":"DDD","sopb_number":"SOPB/DDD/WHS/2026/IV/001","tanggal_diminta":"2026-04-07","requester_phone":"PHONE","requester_name":"NAME"}' > ~/.paperclip/instances/default/workspaces/b1b9ff7c-0b4b-44cd-a012-21e77d02edc2/inbox/ro_request.json
```

Then clear state + trigger:
```bash
PGPASSWORD=paperclip psql -h 127.0.0.1 -p 54329 -U paperclip -d paperclip -c "UPDATE agents SET status='idle', adapter_config=adapter_config-'last_run_summary'-'last_run_result' WHERE name='RO-Agent';"

curl -s -X POST "http://localhost:3100/api/routines/66c05c3a-0901-4fef-9697-82a0a6d90160/run" -H "Authorization: Bearer pcp_ro_4dc96dfb9fb884342e2b1c5485cc11777a648fcc8c225dfe" -H "Content-Type: application/json" -d '{}'
```

Store codes: GM PTC TP ROYAL SDA CITO BATU MOG MATOS ICON SUNRISE

#### Future Agents

When new agents are added, register them in this skill with:
- Agent ID + name
- Workspace path
- Inbox file format
- Routine ID + API key
- Trigger command

---

## Step 3: After Delegation

Reply to user: "[Task] sudah di-delegasikan ke [Agent]. Hasilnya dikirim via WA."

Do NOT wait for result. Do NOT check status. Agent handles everything autonomously.

---

## Monitoring (if user asks "status agent X")

```bash
# Agent status
curl -s http://localhost:3100/api/companies/a110fd08-96af-4cb5-8375-ce08a2a2cc8e/agents \
  -H "Authorization: Bearer pcp_4b469136118bada6b2255799a25d4b917589d6cc8aee474a" | \
  python3 -c "import sys,json; [print(f'{a[\"name\"]}: {a[\"status\"]}') for a in json.loads(sys.stdin.read())]"
```

```bash
# Latest run for specific agent
PGPASSWORD=paperclip psql -h 127.0.0.1 -p 54329 -U paperclip -d paperclip -c \
  "SELECT status, exit_code, started_at, finished_at FROM heartbeat_runs WHERE agent_id='AGENT_ID' ORDER BY created_at DESC LIMIT 1;"
```

---

## Troubleshooting

### Agent doesn't pick up task
**Symptoms:** Issue created in dashboard but agent stays "idle", no heartbeat_run created.
**Cause:** Agent status not 'idle' or stale `last_run_summary` makes agent skip.
**Fix:**
```bash
PGPASSWORD=paperclip psql -h 127.0.0.1 -p 54329 -U paperclip -d paperclip -c \
  "UPDATE agents SET status='idle', adapter_config=adapter_config-'last_run_summary'-'last_run_result' WHERE name='AGENT_NAME';"
```

### Agent "thinks" instead of executing script
**Symptoms:** Agent runs 3+ minutes, no file generated, lots of output tokens but no bash commands.
**Cause:** CLAUDE.md missing from working directory.
**Fix:** Ensure this file exists:
```
~/.paperclip/instances/default/projects/a110fd08-96af-4cb5-8375-ce08a2a2cc8e/71049fc4-b3cb-4f6b-a2b1-273d2e0128e4/_default/CLAUDE.md
```
Content must say: "Run bash command IMMEDIATELY as first action."

### Agent fails with "Invalid API key"
**Symptoms:** Heartbeat run status = "failed", error mentions API key.
**Cause:** `ANTHROPIC_API_KEY` env var (invalid) overrides subscription auth.
**Fix:** Set empty key in agent adapter_config:
```bash
PGPASSWORD=paperclip psql -h 127.0.0.1 -p 54329 -U paperclip -d paperclip -c \
  "UPDATE agents SET adapter_config = jsonb_set(adapter_config, '{env,ANTHROPIC_API_KEY}', '\"\"') WHERE name='AGENT_NAME';"
```

### WA "unsupported channel: whatsapp"
**Symptoms:** Script runs, file generated, but WA send fails.
**Cause:** Gateway WA plugin not loaded (happens after tunnel restart or config change).
**Fix:**
```bash
openclaw gateway restart
# Wait 5-8 seconds before sending
```

### GSheet "This operation is not supported for this document" (400)
**Symptoms:** Flow 2/3 fails when reading GSheet.
**Cause:** File is xlsx upload (not native GSheet). Sheets API only reads native GSheets.
**Fix:** Auto-detect now handles this — script searches GDrive for latest native GSheet matching store code. If still failing, check that Flow 1 used `upload_gsheet.py` (converts to native).

### Iris generates files herself instead of delegating
**Symptoms:** File output is xlsx (not native GSheet), no Paperclip issue created, file naming different from ROBOX pattern.
**Cause:** Iris model fallback to MiniMax/Gemini (rate limited on primary). These models don't follow ro-delegate skill.
**Fix:** Check which model Iris is using:
```bash
openclaw sessions --json 2>&1 | python3 -c "
import sys,json
raw=sys.stdin.read()
for i in range(len(raw)):
    if raw[i] in '[{': break
d=json.loads(raw[i:])
for s in (d.get('sessions',[]) if isinstance(d,dict) else d):
    if '628983539659' in s.get('key',''):
        print(f'Model: {s.get(\"model\")}')
"
```
If model is MiniMax or Gemini → Anthropic key rate-limited. Update key:
```bash
OLD_KEY="sk-ant-oat01-OLD..."
NEW_KEY="sk-ant-oat01-NEW..."
for f in $(grep -rl "$OLD_KEY" ~/.openclaw/ --include="*.json" 2>/dev/null | grep -v node_modules); do
    sed -i '' "s|$OLD_KEY|$NEW_KEY|g" "$f"
done
openclaw gateway restart
```

### Paperclip dashboard 403
**Symptoms:** Can't access dashboard via cloudflare tunnel URL.
**Cause:** New tunnel URL not in `allowedHostnames`.
**Fix:**
```bash
cd ~/Projects/paperclip && pnpm paperclipai allowed-hostname NEW_HOSTNAME
touch ~/Projects/paperclip/server/src/index.ts  # hot reload
```

### Paperclip MCP not loading in Claude Code
**Symptoms:** `mcp__paperclip__*` tools not available.
**Fix:** Run `/mcp` in Claude Code to reload. Or check `~/.mcp.json` has paperclip entry.

---

## Architecture Reference

```
User (WA/Telegram)
  → OpenClaw Gateway (:18789)
    → Iris (claude-sonnet-4-6)
      → writes inbox + curl Paperclip API
        → Paperclip Runtime (:3100)
          → creates issue + wakes agent
            → Claude Code CLI (--dangerously-skip-permissions)
              → reads CLAUDE.md → runs bash script
                → generates file → uploads GSheet → sends WA
```

## Key Paths
| Path | Purpose |
|------|---------|
| `~/.paperclip/instances/default/workspaces/{ID}/inbox/` | Agent inbox (task context) |
| `~/.paperclip/instances/default/workspaces/{ID}/outbox/` | Agent output files |
| `~/.paperclip/instances/default/projects/.../CLAUDE.md` | Forces agent to run bash first |
| `~/.openclaw/skills/` | Gateway-level skills (strongest Iris instructions) |
| `~/.openclaw/workspace/SOUL.md` | Iris identity + prohibitions |
| `~/.openclaw/openclaw.json` | Auth profiles, agent config, model config |

## Company & API
```
Company ID: a110fd08-96af-4cb5-8375-ce08a2a2cc8e
Iris API Key: pcp_4b469136118bada6b2255799a25d4b917589d6cc8aee474a
Paperclip API: http://localhost:3100
Paperclip DB: localhost:54329 (user: paperclip, pw: paperclip)
Zuma VPS DB: 76.13.194.120:5432 (user: openclaw_app, pw: Zuma-0psCl4w-2026!)
```
