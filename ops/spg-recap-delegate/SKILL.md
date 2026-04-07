---
name: spg-recap-delegate
description: >
  MANDATORY for ALL SPG achievement/leaderboard/recap requests.
  Iris runs ONE command only. trigger_spg_agent.sh handles everything.
globs:
  - "**/*spg*"
  - "**/*leaderboard*"
  - "**/*achievement*"
  - "**/*recap spg*"
  - "**/*ranking spg*"
  - "**/*capaian spg*"
---

# SPG Recap Delegate — Run ONE Command

Iris is a receptionist. Run the trigger script. Nothing else.

## Usage

```bash
bash ~/.openclaw/skills/spg-recap-delegate/trigger_spg_agent.sh AREA MONTH YEAR PHONE NAME
```

## Parameters
- AREA: Jatim, Jakarta, Bali, Lombok, Sumatera, Sulawesi, Batam, ALL
- MONTH: 1-12 (default: current month)
- YEAR: 2026 (default: current year)

## Examples

```bash
# Current month, all areas
bash ~/.openclaw/skills/spg-recap-delegate/trigger_spg_agent.sh ALL "" "" +628983539659 Wayan

# Jatim March 2026
bash ~/.openclaw/skills/spg-recap-delegate/trigger_spg_agent.sh Jatim 3 2026 +628983539659 Wayan
```

## After running:
Reply: "SPG Achievement Recap [AREA] [BULAN] sedang diproses oleh SPG-Recap-Agent. Hasilnya dikirim via WA."

## DILARANG
- Jangan query database
- Jangan generate xlsx
- ONLY run trigger_spg_agent.sh
