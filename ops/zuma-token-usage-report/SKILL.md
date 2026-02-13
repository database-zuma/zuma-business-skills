---
name: zuma-token-usage-report
description: Cross-cutting skill for reporting token usage and model info after completing any task. Load alongside any other skill. Agent appends a standard footer showing model, tokens consumed, and estimated cost after producing output.
user-invocable: false
---

# Token Usage Report

After completing a task that produces output, append a **token usage footer** so the user sees how many tokens were consumed and which model was used.

---

## 1. When to Report

**ALWAYS report after:**
- Generating RO Request / Surplus Pull
- Generating Planogram output
- Completing data analysis queries
- Running database health checks
- Any substantial task the user explicitly requested

**SKIP for:**
- Simple conversational replies (greetings, short yes/no answers)
- Clarifying questions back to the user
- Error messages or "I can't do that" responses

---

## 2. How to Get Token Data

### OpenClaw Agents (Iris, Atlas, Apollo)

Run this at the **end of your task**, before composing the footer:

```bash
openclaw sessions --json 2>/dev/null | jq '.sessions[] | select(.key | contains("REPLACE_WITH_YOUR_SESSION_KEY")) | {model, totalTokens, inputTokens, outputTokens, contextTokens}'
```

If you cannot determine your session key, use:

```bash
openclaw sessions --json 2>/dev/null | jq '.sessions[0] | {model, totalTokens, inputTokens, outputTokens, contextTokens}'
```

This returns your most recently updated session.

**For per-task detail in long-lived sessions** (e.g., WhatsApp), sum recent assistant messages:

```bash
AGENT_ID="main"  # or "ops" for Atlas
SESSION_ID="YOUR_SESSION_ID"
jq -s '[.[] | select(.message.role == "assistant" and .message.usage.totalTokens > 0)] | last(5) | {
  model: .[0].message.model,
  total_tokens: ([.[].message.usage.totalTokens] | add),
  total_cost_usd: ([.[].message.usage.cost.total] | add)
}' ~/.openclaw/agents/$AGENT_ID/sessions/$SESSION_ID.jsonl
```

### OpenCode Agents (Coding sessions)

Token data is tracked per-message in `~/.local/share/opencode/storage/message/`. You know your model from the system prompt. Report the model name and note that exact token counts are logged automatically.

---

## 3. Footer Format

Add this block at the **very end** of your output, after all work content:

```
---
📊 Token Usage
• Model: [model_name]
• Tokens: [totalTokens] (in: [inputTokens] | out: [outputTokens])
• Est. Cost: $[cost_total_usd]
• Context: [totalTokens]/[contextTokens] ([percentage]%)
```

### Rules

| Field | Source | Notes |
|-------|--------|-------|
| Model | `model` field from session data | Always report. E.g. `claude-sonnet-4-5` |
| Tokens | `totalTokens` | For isolated sessions (cron) = task tokens. For interactive = session cumulative. |
| In/Out | `inputTokens` / `outputTokens` | Approximate — these are session-level totals |
| Est. Cost | `cost.total` from session JSONL | Already calculated in USD by OpenClaw. If unavailable, write `N/A` |
| Context | `totalTokens / contextTokens` | Shows how much of the context window was used |

### Example Footers

**Cron task (Atlas daily health check):**
```
---
📊 Token Usage
• Model: claude-sonnet-4-5
• Tokens: 18,420 (in: 12 | out: 892)
• Est. Cost: $0.028
• Context: 18,420/200,000 (9%)
```

**Interactive task (Iris RO Request via WhatsApp):**
```
---
📊 Token Usage
• Model: claude-sonnet-4-5
• Tokens: 45,200 (in: 35 | out: 1,240)
• Est. Cost: $0.042
• Context: 45,200/200,000 (23%)
```

**OpenCode coding session:**
```
---
📊 Token Usage
• Model: claude-opus-4-6
• Tokens: 131,898
• Est. Cost: N/A
• Context: 131,898/200,000 (66%)
```

---

## 4. On-Demand Usage Query

When the user asks about token usage (e.g., "berapa token tadi?", "how much did that cost?"), provide a more detailed breakdown:

```bash
# All sessions summary
openclaw sessions --json 2>/dev/null | jq '.sessions[] | {key, model, totalTokens, inputTokens, outputTokens}'

# Specific session cost breakdown
SESSION_ID="YOUR_SESSION_ID"
AGENT_ID="main"
jq -s '{
  messages: length,
  assistant_turns: [.[] | select(.message.role == "assistant")] | length,
  models_used: [.[] | select(.message.role == "assistant") | .message.model] | unique,
  total_tokens: [.[] | select(.message.role == "assistant") | .message.usage.totalTokens // 0] | add,
  total_cost_usd: [.[] | select(.message.role == "assistant") | .message.usage.cost.total // 0] | add
}' ~/.openclaw/agents/$AGENT_ID/sessions/$SESSION_ID.jsonl
```

---

## 5. Notes

- **Cron/isolated sessions**: `totalTokens` = exact tokens for that task
- **Interactive sessions (WhatsApp)**: `totalTokens` = cumulative session total (not just this task). Mention this to the user if relevant.
- **Cost**: Pre-calculated by OpenClaw runtime (USD). Accounts for cache read/write pricing.
- **Cache efficiency**: High `cacheRead` vs `cacheWrite` = good (reusing cached context). Typical ratios: 10-30x cache read vs write is healthy.
- **This skill stacks with other skills** — load it alongside `zuma-distribution-flow`, `zuma-data-analyst-skill`, `planogram-zuma`, etc.
