---
name: paperclip-agent-creator
description: >
  Create a new Paperclip agent with full infrastructure: DB entry, workspace, 
  CLAUDE.md, heartbeat, Iris delegate, routine, API key. Agent auto-placed under CEO.
  Use when user asks to create/add a new agent in Paperclip.
globs:
  - "**/*create agent*"
  - "**/*new agent*"
  - "**/*bikin agent*"
  - "**/*tambah agent*"
---

# Paperclip Agent Creator

Create a new Paperclip agent with the complete infrastructure stack.
Every agent follows the same pattern: Iris delegate → trigger script → Paperclip routine → heartbeat → generator.

## Pre-requisites

- Paperclip server running on localhost:3100
- Paperclip embedded Postgres on localhost:54329
- OpenClaw gateway running (for Iris delegate + WA)

## Step-by-step Creation Process

### 1. Generate IDs

```bash
# Generate a UUID for the agent
AGENT_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
PROJECT_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
ROUTINE_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
COMPANY_ID="a110fd08-96af-4cb5-8375-ce08a2a2cc8e"
CEO_ID="1283d81a-8dde-4aeb-8849-06c195967fae"
```

### 2. Create Agent in Paperclip DB

```sql
-- Agent (MUST set reports_to = CEO)
INSERT INTO agents (id, company_id, name, role, title, icon, status, adapter_type, adapter_config, reports_to, capabilities)
VALUES (
  '{AGENT_ID}',
  '{COMPANY_ID}',
  '{AGENT_NAME}',
  'specialist',
  '{AGENT_TITLE}',
  '{EMOJI}',
  'idle',
  'claude_local',
  '{"model":"claude-opus-4-6","dangerouslySkipPermissions":true,"env":{"ANTHROPIC_API_KEY":""}}',
  '{CEO_ID}',  -- CRITICAL: always under CEO
  '{CAPABILITIES_TEXT}'
);

-- Project
INSERT INTO projects (id, company_id, name, description, status)
VALUES ('{PROJECT_ID}', '{COMPANY_ID}', '{PROJECT_NAME}', '{DESCRIPTION}', 'in_progress');

-- Routine
INSERT INTO routines (id, company_id, project_id, title, description, assignee_agent_id, priority, status)
VALUES ('{ROUTINE_ID}', '{COMPANY_ID}', '{PROJECT_ID}', '{ROUTINE_TITLE}', '{DESCRIPTION}', '{AGENT_ID}', 'medium', 'active');

-- API Key
-- Generate: API_KEY="pcp_{prefix}_$(openssl rand -hex 24)"
-- Hash:    KEY_HASH=$(echo -n "$API_KEY" | shasum -a 256 | cut -d' ' -f1)
INSERT INTO agent_api_keys (agent_id, company_id, name, key_hash)
VALUES ('{AGENT_ID}', '{COMPANY_ID}', '{key_name}', '{KEY_HASH}');
```

### 3. Create Workspace Directories

```bash
# Workspace (inbox/outbox)
mkdir -p ~/.paperclip/instances/default/workspaces/{AGENT_ID}/inbox
mkdir -p ~/.paperclip/instances/default/workspaces/{AGENT_ID}/outbox

# CLAUDE.md project dir
mkdir -p ~/.paperclip/instances/default/projects/{COMPANY_ID}/{PROJECT_ID}/_default
```

### 4. Create CLAUDE.md (Force Heartbeat Execution)

File: `~/.paperclip/instances/default/projects/{COMPANY_ID}/{PROJECT_ID}/_default/CLAUDE.md`

```markdown
# MANDATORY FIRST ACTION

You are {AGENT_NAME}. Your ONLY job is to run ONE bash command:

\```bash
bash ~/.claude/skills/{skill-dir}/{heartbeat_script}.sh
\```

Run this command IMMEDIATELY as your FIRST action.

DO NOT:
- Run other agents' heartbeat scripts
- Use mcp__paperclip__run_sql
- Query any database directly
- Write Python code manually
```

### 5. Create Iris Delegate Skill

Dir: `~/.openclaw/skills/{delegate-name}/`

**SKILL.md** — defines globs for keyword matching + usage example
**trigger_{agent}.sh** — writes inbox JSON + clears agent state + triggers routine via API

Trigger script template:
```bash
#!/usr/bin/env bash
set -eo pipefail

# ... parse args ...

INBOX="$HOME/.paperclip/instances/default/workspaces/{AGENT_ID}/inbox"
ROUTINE="{ROUTINE_ID}"
API_KEY="{AGENT_API_KEY}"

# 1. Write inbox JSON
cat > "$INBOX/{request_file}.json" <<ENDJSON
{json payload}
ENDJSON

# 2. Clear agent state
PGPASSWORD=paperclip psql -h 127.0.0.1 -p 54329 -U paperclip -d paperclip -q -c \
  "UPDATE agents SET status='idle', adapter_config=adapter_config-'last_run_summary'-'last_run_result' WHERE name='{AGENT_NAME}';" 2>/dev/null || true

# 3. Trigger routine
curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:3100/api/routines/$ROUTINE/run" \
  -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" -d '{}'
```

### 6. Create Heartbeat Script

Dir: `~/.claude/skills/{skill-dir}/`

Heartbeat reads inbox, calls generator, uploads GDrive, sends WA:
```bash
#!/usr/bin/env bash
set -eo pipefail
export PATH="$HOME/homebrew/bin:$HOME/.local/bin:$HOME/homebrew/opt/node/bin:/usr/local/bin:/usr/bin:/bin"

AGENT_HOME="$HOME/.paperclip/instances/default/workspaces/{AGENT_ID}"
INBOX="$AGENT_HOME/inbox"
OUTBOX="$AGENT_HOME/outbox"

# Read inbox → run generator → upload → send WA → archive inbox
```

Key patterns:
- WA send: `openclaw message send --channel whatsapp --target "$PHONE" --message "$MSG"`
- GDrive upload: `python3 ~/.claude/skills/zuma-plano-ro-skills/step3-zuma-ro-surplus-skills/upload_gsheet.py --file "$FILE" --folder "$FOLDER"`
- Bash 3.2 compat: NO `declare -A`, use `case` functions instead
- No `merge_cells` in openpyxl if uploading to GDrive

### 7. Update Iris SOUL.md

Add prohibition + delegate instruction to `~/.openclaw/workspace/SOUL.md`:
```markdown
# 🚫 ABSOLUTE PROHIBITION — {FEATURE}

**IRIS DILARANG KERAS {action} dalam bentuk apapun.**

**SATU-SATUNYA cara — LANGSUNG RUN:**
\```bash
bash ~/.openclaw/skills/{delegate}/trigger_{agent}.sh ARGS
\```
Reply: "{Feature} sedang diproses oleh {AGENT_NAME}. Hasil dikirim via WA."
```

### 8. Push to GitHub

```bash
# Copy to repo
mkdir -p ~/zuma-business-skills/ops/{skill-dir}
cp ~/.claude/skills/{skill-dir}/* ~/zuma-business-skills/ops/{skill-dir}/
cp -r ~/.openclaw/skills/{delegate} ~/zuma-business-skills/ops/

cd ~/zuma-business-skills && git add -A && git commit -m "Add {AGENT_NAME}" && git push origin main
```

## Existing Agents Reference

| Agent | ID | Project ID | Routine ID | API Key Prefix |
|-------|-----|------------|------------|----------------|
| RO-Agent | b1b9ff7c-0b4b-44cd-a012-21e77d02edc2 | 71049fc4-b3cb-4f6b-a2b1-273d2e0128e4 | 66c05c3a-0901-4fef-9697-82a0a6d90160 | pcp_ro_ |
| Plano-Agent | 35f69382-704f-4980-8822-33954e15db44 | c4a0e1f2-9b3d-4e5f-8a6c-7d8e9f0a1b2c | a5d55c55-8947-4f16-a037-0f17e59b9673 | pcp_plano_ |
| SPG-Recap-Agent | e7a1b2c3-d4e5-f6a7-b8c9-0d1e2f3a4b5c | d5e6f7a8-b9c0-d1e2-f3a4-b5c6d7e8f9a0 | f8e7d6c5-b4a3-9281-7060-504030201000 | pcp_spg_ |

## Constants

| Key | Value |
|-----|-------|
| Company ID | a110fd08-96af-4cb5-8375-ce08a2a2cc8e |
| CEO Agent ID | 1283d81a-8dde-4aeb-8849-06c195967fae |
| Paperclip DB | localhost:54329, user=paperclip, db=paperclip |
| Ops DB | 76.13.194.120:5432, user=openclaw_app, db=openclaw_ops |
| GDrive upload script | ~/.claude/skills/zuma-plano-ro-skills/step3-zuma-ro-surplus-skills/upload_gsheet.py |
| GitHub repo | github.com/database-zuma/zuma-business-skills (ops/ folder) |

## Checklist

Before declaring agent "done":
- [ ] Agent in DB with `reports_to = CEO_ID`
- [ ] Workspace dirs created (inbox + outbox)
- [ ] CLAUDE.md points to correct heartbeat script
- [ ] Heartbeat uses `--channel whatsapp` for WA
- [ ] Heartbeat uses bash 3.2 compat (no `declare -A`)
- [ ] Generator uses no `merge_cells` (GDrive compat)
- [ ] Iris delegate SKILL.md with correct globs
- [ ] Trigger script writes inbox + clears state + triggers routine
- [ ] SOUL.md updated with prohibition + delegate instruction
- [ ] API key created and used in trigger script
- [ ] Tested locally: generator produces correct output
- [ ] Tested via Iris: end-to-end trigger works
- [ ] Pushed to GitHub
