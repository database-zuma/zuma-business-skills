---
description: "Zuma FF/FA/FS (Fill Factor, Fill Accuracy, Fill Score) metrics calculation and analysis. Use when calculating planogram compliance, fill rates, display accuracy, or analyzing how well stores follow planogram recommendations."
globs:
  - "**/*ff*"
  - "**/*fill*factor*"
  - "**/*fill*score*"
---

# SKILL: FF / FA / FS — Store Fill Rate Metrics

> **Version**: 2.0  
> **Created**: 2026-02-11  
> **Updated**: 2026-02-14  
> **Domain**: Store performance measurement — planogram fill rate tracking  
> **Dependencies**: `zuma-data-analyst-skill` (DB connection & query rules)  
> **Output**: Daily fill rate metrics stored in `mart.ff_fa_fs_daily` table

---

## 1. Concept Overview

### What Are FF / FA / FS?

Three metrics that measure **how well each retail store is stocked relative to its planogram** (target display plan). Each measures the same thing — "are we filling the planogram?" — but at different granularity.

| Metric | Full Name | Granularity | Formula | What It Answers |
|--------|-----------|-------------|---------|-----------------|
| **FF** | Fill Factor | SIZE-level | `Count(Plan>0 AND Stock>0) / Count(Plan>0)` | "What % of planned sizes actually have stock on the shelf?" |
| **FA** | Fill Article | ARTICLE-level | `Count(Articles_with_any_stock) / Count(Articles_in_plan)` | "What % of planned articles have at least 1 size available?" |
| **FS** | Fill Stock | QUANTITY | `Sum(Actual_Stock) / Sum(Planned_Stock)` | "How deep is our stock compared to the plan? Enough depth per size?" |

### How They Relate

```
Store has 100 planned sizes across 20 articles. Planogram says total 300 pairs.
Actual: 75 sizes have stock, 18 articles have at least 1 size, total 250 pairs on hand.

FF = 75/100 = 75%    →  25 empty size slots on the shelf
FA = 18/20  = 90%    →  2 articles completely missing
FS = 250/300 = 83%   →  stock depth is light but not critical
```

- **FF < FA always** (or equal). If an article is missing (FA drops), all its sizes are missing too (FF drops more).
- **FS can exceed 100%**. More stock than plan = overstocked. This is normal for NOS (Never Out of Stock) items.
- **FF is the most important metric** for customer experience — a customer who finds the right article but not their size still walks away empty-handed.

### What About ST (Sell-Through)?

ST measures sales velocity: `Keluar / (Saldo_Awal + Masuk)` — what percentage of available stock was actually sold.

**ST is NOT included in this SKILL** because it requires **Ringkasan Mutasi Gudang** (warehouse mutation report) data from Accurate Online, which provides the `Saldo Awal`, `Masuk`, `Keluar`, and `Saldo Akhir` columns. This data is:

- Not available in VPS PostgreSQL database
- Not yet automated via Accurate Online API (the `reportId` and `planId` for Ringkasan Mutasi are still being investigated)
- Currently only obtainable via manual Excel download from Accurate Online

> **When Ringkasan Mutasi data becomes available** (either via API automation or manual file input),  
> this SKILL will be extended with ST calculation. The formula, data format, and join keys  
> are already documented in `ff-fa-fs-history.md` (Future: ST Metric section) for when that time comes.
>
> **DO NOT use Sales/(Stock+Sales) as a "fallback" for ST.** This approximation ignores  
> inter-warehouse transfers (RO Box, RO Protol), returns, and stock adjustments — making it  
> unreliable enough to produce misleading results. Better to have no ST than a wrong ST.

---

## 2. Pipeline Architecture

### Daily Automated Flow

```
DB VPS (76.13.194.120) crontab: 03:00 WIB
└─ cron_stock_pull.sh (sequential)
   ├─ pull_accurate_stock.py ddd
   ├─ pull_accurate_stock.py ljbb
   ├─ pull_accurate_stock.py mbb
   ├─ pull_accurate_stock.py ubb
   ├─ writes /opt/openclaw/logs/stock_latest_status.json
   └─ calculate_ff_fa_fs.py (runs AFTER all stock is fresh)
      ├─ sync_store_map() — auto-matches new planogram stores
      ├─ load planogram from portal.temp_portal_plannogram
      ├─ load stock from core.stock_with_product
      ├─ calculate FF/FA/FS per store
      ├─ upsert into mart.ff_fa_fs_daily
      └─ writes /opt/openclaw/logs/ff_fa_fs_latest_status.json

Atlas VPS (76.13.194.103) cron: 05:30 WIB
└─ atlas-daily-db-health job
   ├─ SSH to DB VPS → reads stock_latest_status.json
   ├─ SSH to DB VPS → reads sales_latest_status.json
   ├─ SSH to DB VPS → reads ff_fa_fs_latest_status.json
   ├─ checks backup, data freshness
   └─ writes {date}_health_report.json

Mac Mini (Iris) cron: 06:00 WIB
└─ reads Atlas health report → sends daily summary to Wayan via WhatsApp
```

### Script Locations

| Component | VPS Path | Local Path |
|-----------|----------|------------|
| Main script | `/opt/openclaw/scripts/calculate_ff_fa_fs.py` | `/Users/database-zuma/zuma-ff-fa-fs/calculate_ff_fa_fs.py` |
| Python venv | `/opt/openclaw/venv/bin/python3` | — |
| Cron wrapper | `/opt/openclaw/scripts/cron_stock_pull.sh` | — |
| Status output | `/opt/openclaw/logs/ff_fa_fs_latest_status.json` | — |
| Dated log | `/opt/openclaw/logs/ff_fa_fs_YYYYMMDD.json` | — |

### CLI Usage

```bash
# Production (VPS localhost, runs daily at 03:00 WIB)
/opt/openclaw/venv/bin/python3 /opt/openclaw/scripts/calculate_ff_fa_fs.py

# Remote run from Mac Mini
python3 calculate_ff_fa_fs.py --db-host 76.13.194.120

# Dry run (calculate + print, don't insert)
python3 calculate_ff_fa_fs.py --dry-run
```

---

## 3. Database Tables (Summary)

> Full CREATE TABLE DDL, column details, and current store mappings are in `ff-fa-fs-pipeline-details.md`.

### 3.1 `portal.store_name_map` — Auto-Evolving Store Mapping

Maps planogram store names to VPS stock `nama_gudang` values. Auto-populated by `sync_store_map()`.

- **PK:** `planogram_name`
- **Key columns:** `planogram_name`, `stock_nama_gudang`, `branch`, `match_method` (`manual`|`auto_exact`|`auto_fuzzy`)
- Manual overrides (`match_method = 'manual'`) are NEVER overwritten by auto-sync
- Currently 11 Jatim stores: 8 auto_exact + 3 auto_fuzzy matches

### 3.2 `mart.ff_fa_fs_daily` — Metric Storage

Stores daily FF/FA/FS values per store. Values are **decimals** (0.6809 = 68.09%).

- **PK:** `(report_date, store_db_name)` — upsert-safe (re-running same day overwrites)
- **Key columns:** `report_date`, `branch`, `store_label` (planogram name), `store_db_name` (VPS nama_gudang), `ff`, `fa`, `fs`, `calculated_at`
- Index: `idx_ff_fa_fs_branch_date` on `(branch, report_date DESC)`

### 3.3 `portal.temp_portal_plannogram` — Planogram Source

Defines what articles/sizes should be displayed per store, and how many pairs per size.

- **Keyed on:** `(store_name, article_mix)` — one row per combination
- **Key columns:** `store_name`, `article_mix` (= `kode_mix` join key), `gender`, `series`, `article`, `tier`, 28 size columns
- 48 columns total, all TEXT type. 2,568 rows, 11 stores, 235 articles (Jatim only)
- Size columns: `size_18_19`, `size_20_21`, ..., `size_45_46` (paired) and `size_26`, ..., `size_44` (individual)
- NULL = no plan for that size

### 3.4 `core.stock_with_product` — Stock Source

Daily stock snapshots with product attributes joined from `portal.kodemix`.

- **Keyed on:** `(nama_gudang, kode_besar, snapshot_date)`
- **Key columns:** `nama_gudang`, `gudang_area`, `kode_mix` (article join key), `size`, `quantity`, `snapshot_date`
- `quantity` can be 0 (product exists but physically out of stock)
- Product attributes available: `gender`, `series`, `article`, `tier`, `kode_besar`

---

## 9. Business Rules & Edge Cases

### 9.1 Rules

| Rule | Description |
|------|-------------|
| FF counts at SIZE-COLUMN level | Each size column in planogram is one "slot." A slot is filled if plan > 0 AND stock > 0. |
| Paired sizes are ONE slot | "18/19" is one slot — if either size 18 or 19 has stock, the slot is filled. |
| FA counts at ARTICLE level | An article is "present" if ANY of its sizes has stock > 0, regardless of how many sizes are missing. |
| FS is a ratio, not capped at 100% | FS > 100% = more stock than planned = overstocked. This is actionable (potential surplus return). |
| Zero-plan sizes are EXCLUDED | If planogram says 0 for a size column, that column is NOT counted in any denominator. |
| Stock without planogram is IGNORED | Extra stock in articles NOT in the planogram does not affect any metric. |
| Values stored as decimals | 0.6809 = 68.09%. Multiply by 100 for display. |
| FF <= FA always | If FF > FA, investigate — likely data issue. |

### 9.2 Edge Cases

| Situation | Handling |
|-----------|----------|
| No stock snapshot for today | Script fails with error (Atlas alerts) |
| Store in planogram but not in stock data | All metrics = 0.0 for that store |
| Article in planogram but zero in all size columns | Excluded (doesn't affect denominators) |
| Stock quantity = 0 in DB | Treated as "no stock" — the slot is not filled |
| Store name not in store_name_map | Auto-sync attempts to match; if fails, logged as unmapped |
| Planogram has duplicate (store, article_mix) rows | Both rows are processed — will double-count. Deduplicate planogram first. |
| Negative stock quantity | Should not exist. If encountered, treat as 0. |

### 9.3 Validation Checklist

Before trusting output:

- [ ] **Status JSON shows `success`** — check `/opt/openclaw/logs/ff_fa_fs_latest_status.json`
- [ ] **All stores mapped** — `unmapped_stores` array is empty
- [ ] **FF <= FA** in all cases — if FF > FA, investigate (could indicate data issue)
- [ ] **FS range is sane** — typically 0.5–2.0 (50%–200%) for active stores
- [ ] **Metric averages reasonable** — FF 60–80%, FA 85–95%, FS 80–150%
- [ ] **Report date is today** — check `report_date` in status JSON

---

## 14. Agent Instructions

### For AI Agents Using This SKILL

1. **ALWAYS load `zuma-data-analyst-skill`** alongside this one — it contains DB connection rules you must follow
2. **To check latest metrics:**
   - Query `mart.ff_fa_fs_daily` table (see `ff-fa-fs-sql-templates.md` Section 13.1)
   - Or read `/opt/openclaw/logs/ff_fa_fs_latest_status.json` for summary
3. **To investigate low FF stores:**
   - Query stores with FF < 0.70 (see `ff-fa-fs-sql-templates.md` Section 13.3)
   - Cross-reference with planogram to identify missing articles/sizes
4. **To add new stores:**
   - Add rows to `portal.temp_portal_plannogram` table
   - Next cron run will auto-sync store mapping
   - Check status JSON for unmapped stores
5. **To manually override store mapping:**
   - Update `portal.store_name_map` table with `match_method = 'manual'`
   - Manual mappings are never overwritten by auto-sync
6. **Do NOT calculate ST** — this SKILL covers FF/FA/FS only. ST requires Ringkasan Mutasi data that is not yet available.
7. **Database connection:** See `zuma-data-analyst-skill` for connection details (do not include passwords in this skill doc)

### User Prompt Template

```
Check FF/FA/FS metrics for [STORE NAME / BRANCH / all stores].

Show me:
- Latest metrics (today or most recent date)
- Trend over last [N] days
- Stores below target (FF < 70%)
- Branch-level summary
```

---

## Reference Files

For detailed technical documentation, see these files in the same directory:

| File | Contents |
|------|----------|
| `ff-fa-fs-calculation-logic.md` | Auto-sync store map algorithm, size column mapping, full FF/FA/FS calculation Python code |
| `ff-fa-fs-pipeline-details.md` | Full CREATE TABLE DDL, status JSON format, Atlas monitoring health checks |
| `ff-fa-fs-sql-templates.md` | SQL query templates for latest metrics, trends, stores below target, branch summaries, store mappings |
| `ff-fa-fs-history.md` | First run results (Feb 14 2026), build history, future ST metric plan, dependencies |
| `calculate_ff_fa_fs.py` | Main Python script — production pipeline (runs daily via cron on VPS) |
| `run_ff_fa_fs_jatim_v1_reference.py` | Reference implementation — Jatim region FF/FA/FS calculation (v1 baseline) |
| `AppScript_FF_FA_FS_ST_Jatim_reference.txt` | Google Apps Script reference — original Jatim FF/FA/FS/ST logic (pre-Python migration) |
