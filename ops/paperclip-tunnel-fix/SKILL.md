---
name: paperclip-tunnel-fix
description: >
  Fix Paperclip "failed to fetch" / tunnel URL mismatch.
  Restarts Cloudflare tunnel, updates Paperclip config with new URL, restarts server.
  Use when Paperclip dashboard can't connect or after Mac Mini restart.
globs:
  - "**/*paperclip*gagal*"
  - "**/*paperclip*error*"
  - "**/*paperclip*failed*"
  - "**/*paperclip*fetch*"
  - "**/*paperclip*connect*"
  - "**/*paperclip*tunnel*"
  - "**/*paperclip*down*"
  - "**/*paperclip*mati*"
---

# Paperclip Tunnel Fix

Run ONE command:

```bash
bash ~/.openclaw/skills/paperclip-tunnel-fix/fix_paperclip_tunnel.sh
```

Script will:
1. Kill old Cloudflare tunnel
2. Start new tunnel → get new URL
3. Register hostname in Paperclip config
4. Restart Paperclip server
5. Print new dashboard URL

Reply with the new URL to user.

## DILARANG
- Jangan edit config manual
- Jangan restart tunnel manual
- ONLY run fix_paperclip_tunnel.sh
