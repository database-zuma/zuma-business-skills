# Changelog

All notable changes to this skill library will be documented here.

---

## [1.1.0] — 10 Feb 2026

### Repo Reorganization + Planogram & RO Request Pipeline

**Folder restructure:**
- Merged `ops/zuma-planogram/` + `ops/zuma-distribution-flow/` → `ops/zuma-plano-and-ro/`
- Sub-folders: `step1-planogram/`, `step2-visualizations/`, `step3-ro-request/`
- Prompt templates promoted to `ops/zuma-plano-and-ro/` root

**New skills & files:**
- **SKILL_planogram_zuma_v3** (1400+ lines) — Full planogram generation skill: tier assignment, capacity allocation, size-level targets, assortment rules, DB queries, Excel output format
- **SKILL_visualized-plano_zuma_v1** (700+ lines) — Planogram visualization skill: heatmap per tier, stock vs target comparison, color coding, openpyxl styling
- **zuma-distribution-flow SKILL.md** (400+ lines) — Updated with complete RO Request generation docs: output format (5-sheet Excel), script reference, WH source rules, surplus detection logic, styling reference, example output
- **section-for-planogram.md** — Updated with RO Request output section (1.11.7)
- **PROMPT_ro_request.md** (172 lines) — NEW: Prompt template for weekly RO Request generation (single store, multi-store, custom protol-only/box-only/surplus-only)
- **PROMPT_new_planogram.md** — Prompt template for generating new planogram
- **build_ro_royal_plaza.py** (1460+ lines) — NEW: RO Request generator script for Royal Plaza (official form format, 5-sheet Excel output)
- **build_royal_planogram.py** — Planogram generator for Royal Plaza
- **build_tunjungan_planogram.py** — Planogram generator for Tunjungan Plaza
- **visualize_planogram.py** — Visual planogram for Royal Plaza
- **visualize_tunjungan_planogram.py** — Visual planogram for Tunjungan Plaza

**README updates:**
- Badge: 5 → 8 skills
- Added planogram & RO pipeline skill table
- Added Python prerequisites (`openpyxl`, `psycopg2-binary`) with install instructions
- Updated repo structure tree with full `zuma-plano-and-ro/` breakdown
- Added pipeline flow diagram

---

## [1.0.0] — 9 Feb 2026

### Initial Release

**5 skills across 2 departments:**

#### General (Cross-Department)
- **zuma-company-context** — Brand identity (witty/casual/confident tone), 4 business entities (DDD, MBB, UBB, LJBB), data source mapping (Accurate, iSeller, Ginee, Supabase)
- **brand-guidelines.md** — Visual identity reference: Zuma Teal `#002A3A`, Zuma Green `#00E273`, Japandi aesthetic, GT Walsheim typography

#### Operations
- **zuma-sku-context** — Product hierarchy (Type > Gender > Series > Article > Size), Kode Mix versioning system (V0-V4 unification), assortment patterns (12 pairs/box), 6-tier classification
- **zuma-branch** — 6 branches (Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali), store categories (RETAIL/NON-RETAIL/EVENT), Area Supervisors, store stock management, replenishment process
- **zuma-warehouse-and-stocks** — 3 physical warehouses (WHS/WHJ/WHB), stock formula & stages, full RO workflow (QUEUE > APPROVED > PICKING > ... > COMPLETED), variance tracking
- **zuma-data-ops** — PostgreSQL VPS connection (76.13.194.120:5432), 5 schemas (raw/portal/core/mart/public), complete table/view documentation, 6 critical SQL rules, 9 query templates, analysis methodology, ETL schedule (02:00 backup, 03:00 stock, 05:00 sales)
