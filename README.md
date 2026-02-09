<p align="center">
  <img src="https://img.shields.io/badge/ZUMA-Business_Skills-00E273?style=for-the-badge&labelColor=002A3A" alt="Zuma Business Skills"/>
  <br/>
  <img src="https://img.shields.io/badge/Claude_Code-Skills_Library-7C3AED?style=flat-square" alt="Claude Code"/>
  <img src="https://img.shields.io/badge/Status-Active-00E273?style=flat-square" alt="Active"/>
  <img src="https://img.shields.io/badge/Skills-5_Installed-FF6B35?style=flat-square" alt="5 Skills"/>
  <img src="https://img.shields.io/badge/Updated-Feb_2026-blue?style=flat-square" alt="Updated"/>
</p>

<h1 align="center">Zuma Business Skills</h1>

<p align="center">
  <strong>AI Skills Library for Zuma Indonesia</strong>
  <br/>
  Plug-and-play knowledge modules that give Claude Code (and other AI agents) deep understanding of Zuma's business — products, stores, warehouses, data, and operations.
  <br/><br/>
  <em>New skills are always being added. Existing skills are always being upgraded.<br/>Always pull the latest version.</em>
</p>

---

## What Is This?

This repo contains **Claude Code skill files** (`.md` files with YAML frontmatter) that teach AI assistants everything about Zuma Indonesia's business context. When installed, any Claude Code session automatically loads relevant skills based on what you're working on.

**Think of it as:** Zuma's institutional knowledge, packaged for AI consumption.

```
You:     "Analyze Classic Jet Black sales in Bali for the last 3 months
          and check current stock in each store"

Claude:  *automatically loads zuma-data-ops + zuma-sku-context + zuma-branch*
         *knows the DB connection, correct SQL joins, Kode Mix versioning,
          Bali's 3 sub-areas, and presents business-accurate results*
```

---

## How It Works

```
                         YOUR QUESTION
                              |
                              v
                   +--------------------+
                   |   Claude Code CLI  |
                   |  detects context   |
                   +--------------------+
                              |
                    auto-loads matching skills
                              |
          +-------+-------+-------+-------+-------+
          |       |       |       |       |       |
          v       v       v       v       v       v
      +-------+-------+-------+-------+-------+-------+
      |COMPANY|  SKU  |BRANCH |WARE-  | DATA  |FUTURE |
      |CONTEXT|CONTEXT|       |HOUSE  |  OPS  |SKILLS |
      +-------+-------+-------+-------+-------+-------+
      |Brand  |Kode   |6      |WHS/   |Postgre|Finance|
      |tone,  |Mix,   |branch-|WHJ/   |SQL VPS|HRGA,  |
      |colors,|tiers, |es,    |WHB,   |5 sche-|Market-|
      |4 PTs  |assort-|stores,|RO     |mas,   |place, |
      |       |ment   |areas  |system |SQL    |etc.   |
      +-------+-------+-------+-------+-------+-------+
          |       |       |       |       |
          +-------+-------+-------+-------+
                          |
                          v
              +------------------------+
              |   AI writes correct    |
              |   SQL, understands     |
              |   business context,    |
              |   returns accurate     |
              |   analysis             |
              +------------------------+
                          |
                          v
              ACCURATE, CONTEXTUAL ANSWER
```

---

## Repository Structure

```
zuma-business-skills/
|
|-- general/                              CROSS-DEPARTMENT (brand, identity)
|   +-- zuma-company-context/
|       |-- SKILL.md                        Brand identity, 4 entities, data sources
|       +-- brand-guidelines.md             Colors, typography, Japandi aesthetic
|
|-- ops/                                  OPERATIONS DEPARTMENT
|   |-- zuma-sku-context/
|   |   +-- SKILL.md                        Product hierarchy, Kode Mix, tiers, assortment
|   |-- zuma-branch/
|   |   +-- SKILL.md                        6 branches, store network, retail operations
|   |-- zuma-warehouse-and-stocks/
|   |   +-- SKILL.md                        3 warehouses, stock stages, RO system
|   +-- zuma-data-ops/
|       +-- SKILL.md                        PostgreSQL VPS, schemas, SQL cookbook, analysis
|
|-- finance/                              FINANCE DEPARTMENT (coming soon)
|   +-- README.md
|
|-- hrga/                                 HR & GA DEPARTMENT (coming soon)
|   +-- README.md
|
|-- README.md                             This file
+-- CHANGELOG.md                          Version history
```

### Why This Structure?

| Folder | Purpose | Who Uses It |
|--------|---------|-------------|
| `general/` | Knowledge that applies across ALL departments — brand, entity structure | Everyone |
| `ops/` | Operational knowledge — products, stores, warehouses, data analytics | Ops team, data analysts, AI agents |
| `finance/` | Financial knowledge — P&L, margins, COGS, tax structure | Finance team (planned) |
| `hrga/` | HR & GA knowledge — org structure, policies, facilities | HR team (planned) |

New department folders will be added as Zuma's AI automation expands.

---

## Skill Overview

### General (Cross-Department)

| Skill | Lines | What It Knows |
|-------|-------|---------------|
| **zuma-company-context** | 137 | Brand tonality (witty/casual/confident), visual identity (Japandi, Zuma Teal `#002A3A`, Zuma Green `#00E273`), 4 business entities (DDD, MBB, UBB, LJBB), data sources (Accurate, iSeller, Ginee) |

### Operations

| Skill | Lines | What It Knows |
|-------|-------|---------------|
| **zuma-sku-context** | 376 | Product hierarchy (Type > Gender > Series > Article > Size), Kode Mix versioning system, assortment patterns (12 pairs/box), 6-tier classification (T1-T5 + T8), naming conventions |
| **zuma-branch** | 575 | 6 branches (Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali), store categories (RETAIL/NON-RETAIL/EVENT), mall vs Ruko formats, Area Supervisors, stock capacity, replenishment from store POV |
| **zuma-warehouse-and-stocks** | 385 | 3 physical warehouses (WHS/WHJ/WHB), stock formula (ready = whs - queue - picked - ...), full RO status flow (QUEUE > APPROVED > PICKING > ... > COMPLETED), variance tracking |
| **zuma-data-ops** | 708 | PostgreSQL VPS connection details, 5 schemas (raw/portal/core/mart/public), all table/view column definitions, 6 critical SQL rules, 9 ready-to-use query templates, analysis methodology, ETL schedule, common pitfalls |

---

## Installation

### Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- Git access to this private repo

### Option 1: Quick Install (Recommended)

Clone this repo, then copy skills into Claude's skills directory:

**Windows (PowerShell):**
```powershell
# Clone the repo
git clone https://github.com/database-zuma/zuma-business-skills.git "$env:USERPROFILE\.claude\skills-repo"

# Copy general skills
Copy-Item -Recurse "$env:USERPROFILE\.claude\skills-repo\general\*" "$env:USERPROFILE\.claude\skills\" -Force

# Copy ops skills
Copy-Item -Recurse "$env:USERPROFILE\.claude\skills-repo\ops\*" "$env:USERPROFILE\.claude\skills\" -Force
```

**macOS / Linux:**
```bash
# Clone the repo
git clone https://github.com/database-zuma/zuma-business-skills.git ~/.claude/skills-repo

# Copy all skills (general + ops + future departments)
cp -r ~/.claude/skills-repo/general/* ~/.claude/skills/
cp -r ~/.claude/skills-repo/ops/* ~/.claude/skills/
```

### Option 2: Selective Install

Only install skills you need:

```bash
# Example: Only install data-ops and sku-context
cp -r ~/.claude/skills-repo/ops/zuma-data-ops ~/.claude/skills/
cp -r ~/.claude/skills-repo/ops/zuma-sku-context ~/.claude/skills/
```

### After Installation

Your `~/.claude/skills/` directory should look like:

```
~/.claude/skills/
|-- zuma-company-context/
|   |-- SKILL.md
|   +-- brand-guidelines.md
|-- zuma-sku-context/
|   +-- SKILL.md
|-- zuma-branch/
|   +-- SKILL.md
|-- zuma-warehouse-and-stocks/
|   +-- SKILL.md
+-- zuma-data-ops/
    +-- SKILL.md
```

Restart Claude Code. Skills are loaded automatically based on context — no manual invocation needed.

### Verify Installation

In any Claude Code session:
```
/zuma-data-ops
```
If the skill loads and shows database info, you're good.

---

## Keeping Skills Updated

> **Skills in this repo are actively maintained and improved.**
> Existing skills get upgraded with new columns, better query patterns, and corrected business rules.
> New skills are added as Zuma's AI automation scope expands.
> **Always pull the latest version.**

### Quick Update

**Windows (PowerShell):**
```powershell
cd "$env:USERPROFILE\.claude\skills-repo"
git pull origin main
Copy-Item -Recurse .\general\* "$env:USERPROFILE\.claude\skills\" -Force
Copy-Item -Recurse .\ops\* "$env:USERPROFILE\.claude\skills\" -Force
# Add future departments as they become available:
# Copy-Item -Recurse .\finance\* "$env:USERPROFILE\.claude\skills\" -Force
# Copy-Item -Recurse .\hrga\* "$env:USERPROFILE\.claude\skills\" -Force
```

**macOS / Linux:**
```bash
cd ~/.claude/skills-repo && git pull origin main
cp -r general/* ~/.claude/skills/
cp -r ops/* ~/.claude/skills/
```

### What Gets Updated?

| Update Type | Frequency | Examples |
|-------------|-----------|---------|
| Schema changes | When DB structure changes | New tables, columns, views added |
| Business rules | When operations evolve | New branches, changed tier criteria |
| Query patterns | As common analyses emerge | New cookbook queries, optimized joins |
| Bug fixes | As issues are found | Corrected column names, updated match rates |
| **New skills** | **As automation scope expands** | **Finance, HRGA, Marketplace, Creative** |

---

## Roadmap

### Planned Skills (New Departments)

| Department | Skill | What It Will Cover | Status |
|------------|-------|--------------------|--------|
| **Finance** | `zuma-financial-analysis` | P&L structure, margin analysis, BPP/COGS calculations, entity-level reporting | Planned |
| **HRGA** | `zuma-org-structure` | Organization chart, roles, decision hierarchy, policies | Planned |
| **Ops** | `zuma-marketplace-ops` | Shopee/Tokopedia/TikTok Shop operations, listing management | Planned |
| **Ops** | `zuma-supply-chain` | Supplier relationships (HJS/Ando), PO management, production planning | Planned |
| **General** | `zuma-customer-insights` | Customer segmentation, purchase patterns, retention analysis | Planned |
| **Creative** | `zuma-creative-hub` | AI creative workflows — product photography, VM design | Planned |

### Existing Skills — Upgrade Roadmap

| Skill | Planned Improvements |
|-------|---------------------|
| `zuma-data-ops` | iSeller integration docs, mart table templates, automated report queries |
| `zuma-sku-context` | Complete assortment patterns for all series, seasonal launch calendar |
| `zuma-branch` | Individual store profiles, performance benchmarks, staffing structure |
| `zuma-warehouse-and-stocks` | Inter-warehouse transfer rules, stock count reconciliation workflows |
| `zuma-company-context` | Org chart, decision-making hierarchy, vendor contacts |

---

## The Vision

```
  TODAY (v1.0)                              FUTURE
  ============                              ======

  +----------+                    +----------+----------+----------+
  | general/ |                    | general/ | finance/ |  hrga/   |
  |   1 skill|                    |   2+     |   2+     |   2+     |
  +----------+                    +----------+----------+----------+
  |  ops/    |                    |  ops/    |creative/ |  sales/  |
  |   4 skill|                    |   8+     |   3+     |   3+     |
  +----------+                    +----------+----------+----------+

  5 skills                        20+ skills across all departments
  covering ops                    covering the entire business
  & brand context                 = Complete Zuma AI Brain
```

Every new skill makes every AI agent smarter about Zuma's business.
Every upgrade makes existing analysis more accurate.

**This repo is the single source of truth for Zuma's AI knowledge.**

---

## Contributing

To add or update skills:

1. Create a branch: `feat/skill-name` or `update/skill-name`
2. Add/edit `SKILL.md` in the appropriate department folder
3. Follow the frontmatter format:
   ```yaml
   ---
   name: skill-name-here
   description: One-line description. Use when [trigger conditions].
   user-invocable: false
   ---
   ```
4. Update `CHANGELOG.md`
5. Open a PR for review

---

<p align="center">
  <sub>Built by Zuma Indonesia's AI team</sub>
  <br/>
  <sub>Skills that make AI actually understand the business.</sub>
</p>
