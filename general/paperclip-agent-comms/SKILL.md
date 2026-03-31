---
name: paperclip-agent-comms
description: Communicate with Paperclip agents (CEO, RO-Agent, Iris). Trigger agent tasks, check status, send inter-agent messages via Paperclip API. Use when user says 'tell RO Agent to...', 'trigger RO heartbeat', 'check agent status', or when Iris needs to delegate to other agents.
user-invocable: true
---

# Paperclip Agent Communication Skill

## API Configuration
```
BASE_URL: http://100.96.41.20:3100/api/companies/a110fd08-96af-4cb5-8375-ce08a2a2cc8e
AUTH: Authorization: Bearer pcp_4b469136118bada6b2255799a25d4b917589d6cc8aee474a
```

## Agents
| Name | ID | Role |
|------|-----|------|
| CEO | 1283d81a-8dde-4aeb-8849-06c195967fae | ceo (orchestrator) |
| Iris (OpenClaw) | 5b5349e8-89a3-4692-a073-d46c303c0d76 | communications (WA/Telegram) |
| RO-Agent | b1b9ff7c-0b4b-44cd-a012-21e77d02edc2 | analyst (RO generation) |

## Actions

### 1. List Agents
```bash
curl -s "$BASE_URL/agents" -H "Authorization: Bearer $API_KEY"
```

### 2. Create Issue (Trigger Agent Task)
```bash
curl -s -X POST "$BASE_URL/issues" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Task title",
    "description": "Detailed task description",
    "assignee_agent_id": "AGENT_UUID",
    "project_id": "71049fc4-b3cb-4f6b-a2b1-273d2e0128e4",
    "priority": "high"
  }'
```

### 3. Trigger RO HEARTBEAT
When user says "buatkan RO", "trigger RO", "run heartbeat", or similar:

```bash
# Step 1: Run analysis + generate xlsx per store
python3 ~/.claude/skills/zuma-plano-ro-skills/step3-zuma-ro-surplus-skills/generate_daily_ro.py

# Step 2: Upload each file to GSheet + send via WA
bash ~/.claude/skills/zuma-plano-ro-skills/step3-zuma-ro-surplus-skills/send_ro_via_iris.sh --all
```

Or for a specific store:
```bash
python3 ~/.claude/skills/zuma-plano-ro-skills/step3-zuma-ro-surplus-skills/generate_daily_ro.py --store ROYAL
bash ~/.claude/skills/zuma-plano-ro-skills/step3-zuma-ro-surplus-skills/send_ro_via_iris.sh \
  ~/.paperclip/instances/default/workspaces/b1b9ff7c-0b4b-44cd-a012-21e77d02edc2/outbox/ROBOX-*.xlsx
```

### 4. Check Agent Status
```bash
curl -s "$BASE_URL/agents" -H "Authorization: Bearer $API_KEY" | \
  python3 -c "import sys,json; [print(f'{a[\"name\"]}: {a[\"status\"]}') for a in json.loads(sys.stdin.read())]"
```

### 5. Check Issues
```bash
curl -s "$BASE_URL/issues?status=todo,in_progress" -H "Authorization: Bearer $API_KEY"
```

### 6. Send Message Between Agents
To send from Iris → RO-Agent (or vice versa), create an issue comment:
```bash
curl -s -X POST "$BASE_URL/issues/ISSUE_ID/comments" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"body": "Message content", "author_agent_id": "SENDER_AGENT_ID"}'
```

## RO-Agent Scripts
| Script | Purpose |
|--------|---------|
| `generate_daily_ro.py` | Refresh DB + generate per-store xlsx (ROBOX-YYYYMMDD-STORE-SEQ.xlsx) |
| `upload_gsheet.py` | Upload xlsx as GSheet (personal OAuth → harveywayan@gmail.com) |
| `send_ro_via_iris.sh` | Upload + send GSheet link via OpenClaw WA |

## Store Codes (Jatim)
GM, PTC, TP, ROYAL, SDA, CITO, BATU, MOG, MATOS, ICON, SUNRISE

## Output Columns (xlsx/GSheet)
Kode Kecil | Artikel | Tier | Stock WHS | Stock LJBB | Stock Total | On-Hand | Planogram | Recomms RO

All values in **Box** format (1 box = 12 pairs).

## Dashboard
Paperclip dashboard: http://100.96.41.20:3100 (Tailscale) or http://localhost:3100 (local)
