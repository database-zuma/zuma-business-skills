---
name: planogram-delegate
description: >
  MANDATORY for ALL planogram requests. Iris runs ONE command only.
  trigger_planogram_agent.sh handles everything — inbox, state clear, API trigger.
globs:
  - "**/*planogram*"
  - "**/*plano*"
  - "**/*layout toko*"
  - "**/*display*"
---

# Planogram Delegate — Run ONE Command

Iris is a receptionist. Run the trigger script. Nothing else.

## Usage

```bash
bash ~/.openclaw/skills/planogram-delegate/trigger_planogram_agent.sh STORE_CODE PHONE NAME [AREA]
```

## Store Codes (Jatim):
| Code | Store |
|------|-------|
| GM | Zuma Galaxy Mall |
| PTC | Zuma PTC |
| TP | Zuma Tunjungan Plaza |
| ROYAL | Zuma Royal Plaza |
| SDA | Zuma Lippo Sidoarjo |
| CITO | Zuma City Of Tomorrow |
| BATU | Zuma Lippo Batu |
| MOG | Zuma Mall Olympic Garden |
| MATOS | Zuma Matos |
| ICON | Zuma Icon Gresik |
| SUNRISE | Zuma Sunrise Mall |
| ALL | Semua toko di area |

## Examples

Single store:
```bash
bash ~/.openclaw/skills/planogram-delegate/trigger_planogram_agent.sh ROYAL +628983539659 Wayan
```

All stores in Jatim:
```bash
bash ~/.openclaw/skills/planogram-delegate/trigger_planogram_agent.sh ALL +628983539659 Wayan Jatim
```

## After running:
Reply: "Planogram [STORE] sedang diproses oleh Plano-Agent. Hasilnya dikirim via WA."

## Reference Data (jika user mau update):
- Store Layout Jatim: https://docs.google.com/spreadsheets/d/1rQCC93t6f7HY1Dnoliplu2Mg61i-nnAupErn_U0fPhw/edit
- Data Option (Backwall Config): https://docs.google.com/spreadsheets/d/1FweMqoNikHB7F9efH0xv5rOtpt4mxnuxqzbPqb41eCo/edit

## DILARANG
- Jangan run python3 untuk planogram
- Jangan query database
- Jangan generate xlsx
- Jangan upload GDrive
- ONLY run trigger_planogram_agent.sh
