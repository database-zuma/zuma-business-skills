# Zuma RO Agent — Automated Replenishment Order System

## Overview
Daily automated RO (Replenishment Order) analysis for Jatim branch stores.
Compares planogram targets vs actual store stock, recommends RO Box when ≥50% sizes empty.

## Agent Hierarchy (Pencil/Paperclip)
```
CEO (Claude Code Opus 4.6)
├── Iris (OpenClaw Gateway) — WA/Telegram comms
└── RO-Agent (Claude Local) — analysis + xlsx generation
```

## Components

### Database
- **Table**: `public.ro_daily_analysis` — daily analysis output per store per article
- **Function**: `public.refresh_ro_daily_analysis()` — populates table for 11 Jatim stores
- **Tracker**: `public.ro_file_tracker` — sequential file numbering

### Scripts
| Script | Purpose |
|--------|---------|
| `generate_daily_ro.py` | Refresh DB analysis + generate per-store xlsx files |
| `upload_gsheet.py` | Upload xlsx to GDrive as Google Sheet (personal OAuth) |
| `send_ro_via_iris.sh` | Upload + send GSheet link via Iris WA to Wayan |

### File Naming
```
ROBOX-{YYYYMMDD}-{STORE_SHORT}-{SEQ:05d}.xlsx
Example: ROBOX-20260331-ROYAL-00001.xlsx
```

### Output Location
```
~/.paperclip/instances/default/workspaces/{RO_AGENT_ID}/outbox/
```

## Jatim Stores (11)
GM, PTC, TP, ROYAL, SDA, CITO, BATU, MOG, MATOS, ICON, SUNRISE

## HEARTBEAT Cron
- Schedule: Daily 07:00 WIB
- Routine: "RO Daily HEARTBEAT" in Pencil DB

## RO Logic (from existing planogram skill)
1. Fetch planogram targets from `portal.planogram_existing_q1_2026`
2. Fetch actual store stock from `core.stock_with_product` (join on `kode` column)
3. Fetch WHS availability from `branch_super_app_clawdbot.ro_whs_readystock`
4. Per article: count empty sizes → if ≥50% empty → RO_BOX (1 box), else RO_PROTOL
5. All quantities by Box, not Pairs

## Dependencies
- psycopg2-binary, openpyxl
- google-api-python-client, google-auth-oauthlib
- OAuth token: `~/.config/gspread/authorized_user.json`
