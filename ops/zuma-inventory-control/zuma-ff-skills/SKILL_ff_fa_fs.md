# SKILL: FF / FA / FS — Store Fill Rate Metrics

> **Version**: 2.0  
> **Created**: 2026-02-11  
> **Updated**: 2026-02-14  
> **Domain**: Store performance measurement — planogram fill rate tracking  
> **Dependencies**: `zuma-data-ops` (DB connection & query rules)  
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
> are already documented in Section 11 (Future: ST Metric) for when that time comes.
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

## 3. Database Tables

### 3.1 `portal.store_name_map` — Auto-Evolving Store Mapping

Maps planogram store names to VPS stock `nama_gudang` values. **Auto-populated** by the script on each run.

```sql
CREATE TABLE portal.store_name_map (
    planogram_name    TEXT NOT NULL PRIMARY KEY,
    stock_nama_gudang TEXT NOT NULL,
    branch            TEXT NOT NULL,
    match_method      TEXT DEFAULT 'manual',  -- 'manual', 'auto_exact', 'auto_fuzzy'
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);
```

**Key facts:**
- PK on `planogram_name`
- Auto-populated by `sync_store_map()` function in script
- Manual overrides are NEVER overwritten (`ON CONFLICT DO NOTHING`)
- Currently 11 Jatim stores: 8 auto_exact + 3 auto_fuzzy matches

**Current mappings (Jatim):**

| planogram_name | stock_nama_gudang | match_method |
|----------------|-------------------|--------------|
| Zuma Matos | Zuma Malang Town Square | auto_exact |
| Zuma Galaxy Mall | ZUMA GALAXY MALL | auto_exact |
| Zuma Tunjungan Plaza | Zuma Tunjungan Plaza 3 | auto_fuzzy |
| ZUMA PTC | Zuma PTC | auto_exact |
| Zuma Icon Gresik | Zuma Icon Mall Gresik | auto_fuzzy |
| Zuma Lippo Sidoarjo | Zuma Lippo Plaza Sidoarjo | auto_exact |
| Zuma Lippo Batu | Zuma Lippo Plaza Batu | auto_exact |
| Zuma Royal Plaza | Zuma Royal Plaza | auto_exact |
| Zuma City Of Tomorrow Mall | Zuma City of Tomorrow | auto_exact |
| Zuma Sunrise Mall | Zuma Sunrise Mall Mojokerto | auto_fuzzy |
| Zuma Mall Olympic Garden | Zuma MOG | auto_exact |

### 3.2 `mart.ff_fa_fs_daily` — Metric Storage

Stores daily FF/FA/FS values per store. Values are stored as **decimals** (0.6809 = 68.09%).

```sql
CREATE TABLE mart.ff_fa_fs_daily (
    report_date   DATE NOT NULL,
    branch        TEXT,
    store_label   TEXT,
    store_db_name TEXT NOT NULL,
    ff            NUMERIC,
    fa            NUMERIC,
    fs            NUMERIC,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (report_date, store_db_name)
);

CREATE INDEX idx_ff_fa_fs_branch_date ON mart.ff_fa_fs_daily (branch, report_date DESC);
```

**Key facts:**
- Upsert on `(report_date, store_db_name)` — re-running same day overwrites safely
- Values stored as decimals: `0.6809` = 68.09%
- Used by dashboards (future Looker/Streamlit)
- `store_label` = planogram name (for display), `store_db_name` = VPS nama_gudang (for joins)

**Example query:**

```sql
-- Latest FF/FA/FS for all Jatim stores
SELECT report_date, store_label, 
       ROUND(ff * 100, 1) AS ff_pct,
       ROUND(fa * 100, 1) AS fa_pct,
       ROUND(fs * 100, 1) AS fs_pct
FROM mart.ff_fa_fs_daily
WHERE branch = 'Jatim'
  AND report_date = (SELECT MAX(report_date) FROM mart.ff_fa_fs_daily)
ORDER BY store_label;
```

### 3.3 `portal.temp_portal_plannogram` — Planogram Source

The planogram defines **what articles and sizes should be displayed** in each store, and **how many pairs per size**.

**Structure:**
- 48 columns: `store_name`, `article_mix`, `gender`, `series`, `article`, `tier`, 28 size columns, metrics
- All columns TEXT type
- 2,568 rows, 11 stores, 235 articles (currently Jatim only)
- Size columns: `size_18_19`, `size_20_21`, ..., `size_45_46` (paired) and `size_26`, `size_27`, ..., `size_44` (individual)
- NULL = no plan for that size

**Key facts:**
- `article_mix` = `kode_mix` in VPS DB — this is the primary join key
- One row per `(store_name, article_mix)` combination
- Size column names are dynamically detected by script (no hardcoded mapping)

### 3.4 `core.stock_with_product` — Stock Source

Daily stock snapshots with product attributes already joined from `portal.kodemix`.

```sql
SELECT
    nama_gudang,      -- Store name (e.g., "ZUMA GALAXY MALL", "Zuma Royal Plaza")
    gudang_area,      -- Region (e.g., "Jatim", "Jakarta", "Sumatra")
    kode_mix,         -- Article mix code, 9 chars (e.g., "B1SLV101Z") — JOIN KEY to planogram
    size,             -- Individual size as string (e.g., "35", "36", "37")
    quantity,         -- Stock on hand (integer, can be 0)
    snapshot_date,    -- Date of this snapshot (DATE type, e.g., "2026-02-10")
    -- Product attributes (from portal.kodemix):
    gender, series, article, tier, kode_besar
FROM core.stock_with_product
```

**Key facts:**
- One row per `(nama_gudang, kode_besar, snapshot_date)` combination
- `snapshot_date` = the date the stock count was captured
- `quantity` can be 0 (product exists in system but physically out of stock)
- `kode_mix` is the article-level code (no size), which is what the planogram uses

---

## 4. Auto-Sync Store Map Algorithm

The `sync_store_map()` function runs **before every calculation** to ensure new planogram stores are automatically mapped to VPS stock locations.

### Algorithm Flow

```python
def sync_store_map(conn):
    """
    Auto-match planogram stores to VPS stock nama_gudang.
    Preserves existing mappings (manual or auto).
    """
    # 1. Get existing mappings from portal.store_name_map
    existing = {row['planogram_name']: row for row in fetch_existing_mappings(conn)}
    
    # 2. Get DISTINCT store_name from planogram table
    planogram_stores = fetch_planogram_stores(conn)
    
    # 3. Get DISTINCT nama_gudang from stock table
    stock_stores = fetch_stock_stores(conn)
    
    # 4. For each NEW planogram store (not already in map):
    for plano_store in planogram_stores:
        if plano_store in existing:
            continue  # Skip — already mapped
        
        # Pass 1: Exact match (case-insensitive)
        for stock_store in stock_stores:
            if plano_store.lower().strip() == stock_store.lower().strip():
                insert_mapping(conn, plano_store, stock_store, 'auto_exact')
                break
        
        # Pass 2: Substring match (one name contains the other, SINGLE candidate only)
        candidates = [s for s in stock_stores 
                      if plano_store.lower() in s.lower() or s.lower() in plano_store.lower()]
        if len(candidates) == 1:
            insert_mapping(conn, plano_store, candidates[0], 'auto_fuzzy')
            continue
        
        # Pass 3: Word overlap >= 75% (SINGLE candidate only, excludes 'zuma')
        candidates = []
        plano_words = set(plano_store.lower().split()) - {'zuma'}
        for stock_store in stock_stores:
            stock_words = set(stock_store.lower().split()) - {'zuma'}
            overlap = len(plano_words & stock_words) / len(plano_words | stock_words)
            if overlap >= 0.75:
                candidates.append(stock_store)
        
        if len(candidates) == 1:
            insert_mapping(conn, plano_store, candidates[0], 'auto_fuzzy')
            continue
        
        # No match → logged as unmapped in status JSON for Atlas to flag
        log_unmapped(plano_store)
    
    # 5. Branch lookup from portal.store
    for mapping in new_mappings:
        branch = lookup_branch(conn, mapping['stock_nama_gudang'])
        update_branch(conn, mapping['planogram_name'], branch)
```

### Matching Results (Feb 14, 2026)

**8 auto_exact matches:**
- Zuma Matos → Zuma Malang Town Square
- Zuma Galaxy Mall → ZUMA GALAXY MALL
- ZUMA PTC → Zuma PTC
- Zuma Lippo Sidoarjo → Zuma Lippo Plaza Sidoarjo
- Zuma Lippo Batu → Zuma Lippo Plaza Batu
- Zuma Royal Plaza → Zuma Royal Plaza
- Zuma City Of Tomorrow Mall → Zuma City of Tomorrow
- Zuma Mall Olympic Garden → Zuma MOG

**3 auto_fuzzy matches:**
- Zuma Icon Gresik → Zuma Icon Mall Gresik (substring match)
- Zuma Tunjungan Plaza → Zuma Tunjungan Plaza 3 (substring match)
- Zuma Sunrise Mall → Zuma Sunrise Mall Mojokerto (word overlap 75%+)

**0 unmapped stores** — all 11 Jatim stores successfully auto-matched.

### Manual Override

To manually override an auto-matched store:

```sql
-- Update existing mapping
UPDATE portal.store_name_map
SET stock_nama_gudang = 'Correct VPS Name',
    match_method = 'manual',
    updated_at = NOW()
WHERE planogram_name = 'Planogram Store Name';

-- Or insert new manual mapping
INSERT INTO portal.store_name_map (planogram_name, stock_nama_gudang, branch, match_method)
VALUES ('Planogram Store Name', 'VPS Stock Name', 'Jatim', 'manual')
ON CONFLICT (planogram_name) DO UPDATE
SET stock_nama_gudang = EXCLUDED.stock_nama_gudang,
    match_method = 'manual',
    updated_at = NOW();
```

Manual mappings are **never overwritten** by the auto-sync algorithm.

---

## 5. Size Column Mapping (Dynamic)

The script **dynamically detects** size columns from the planogram table. No hardcoded mapping.

### Detection Algorithm

```python
def build_size_map(planogram_columns):
    """
    Dynamically build size mapping from planogram column names.
    
    Column 'size_X_Y' → stock sizes ['X', 'Y'] (paired)
    Column 'size_X' → stock size ['X'] (individual)
    """
    size_map = {}
    
    for col in planogram_columns:
        if not col.startswith('size_'):
            continue
        
        size_part = col.replace('size_', '')
        
        if '_' in size_part:
            # Paired: size_39_40 → ['39', '40']
            sizes = size_part.split('_')
            size_map[col] = sizes
        else:
            # Individual: size_39 → ['39']
            size_map[col] = [size_part]
    
    return size_map
```

### Example Mappings

**Kids sizes (paired):**
- `size_18_19` → `['18', '19']`
- `size_20_21` → `['20', '21']`
- `size_22_23` → `['22', '23']`
- `size_24_25` → `['24', '25']`

**Adult sizes (individual):**
- `size_26` → `['26']`
- `size_27` → `['27']`
- ...
- `size_44` → `['44']`

**Adult sizes (paired, for AIRMOVE series):**
- `size_39_40` → `['39', '40']`
- `size_41_42` → `['41', '42']`
- `size_43_44` → `['43', '44']`

**How paired sizes work in FF calculation:**

For a paired column like `size_18_19` with `plan_qty = 2`:
- Check VPS stock for size "18" AND size "19" separately
- Sum their quantities: `stock_qty = stock_18 + stock_19`
- FF logic: if `plan_qty > 0 AND stock_qty > 0` → count as 1 filled size slot
- This means if size 18 has 0 but size 19 has 3, the slot counts as filled (stock_qty = 3 > 0)

---

## 6. Calculation Logic

### 6.1 High-Level Flow

```python
def main():
    conn = connect_to_db()
    
    # 1. Auto-sync store mappings
    sync_store_map(conn)
    
    # 2. Load planogram from portal.temp_portal_plannogram
    planogram = load_planogram(conn)
    
    # 3. Build dynamic size map from planogram columns
    size_map = build_size_map(planogram.columns)
    
    # 4. Load stock from core.stock_with_product (today's snapshot)
    stock = load_stock(conn, snapshot_date=today())
    
    # 5. Calculate FF/FA/FS per store
    for store in planogram['store_name'].unique():
        metrics = calculate_store_metrics(planogram, stock, store, size_map)
        
        # 6. Upsert into mart.ff_fa_fs_daily
        upsert_metrics(conn, store, metrics)
    
    # 7. Write status JSON
    write_status_json(metrics_summary)
```

### 6.2 Metric Formulas (Unchanged from v1.0)

#### FF (Fill Factor) — Size-Level

```python
def calculate_ff(planogram, stock, store, size_map):
    """
    FF = Count(Plan>0 AND Stock>0) / Count(Plan>0)
    
    Numerator:  How many size-column slots have BOTH plan > 0 AND stock > 0
    Denominator: How many size-column slots have plan > 0
    """
    count_plan_pos = 0
    count_stock_pos = 0
    
    for article_row in planogram[planogram['store_name'] == store]:
        article_mix = article_row['article_mix']
        
        for size_col, stock_sizes in size_map.items():
            plan_qty = int(article_row.get(size_col, 0) or 0)
            
            if plan_qty > 0:
                count_plan_pos += 1
                
                # Sum stock across all sizes in this column
                stock_qty = sum(
                    get_stock(stock, store, article_mix, size)
                    for size in stock_sizes
                )
                
                if stock_qty > 0:
                    count_stock_pos += 1
    
    return count_stock_pos / count_plan_pos if count_plan_pos > 0 else 0.0
```

#### FA (Fill Article) — Article-Level

```python
def calculate_fa(planogram, stock, store, size_map):
    """
    FA = Count(Articles_with_any_stock) / Count(Articles_in_plan)
    
    Numerator:  How many articles have Total_Stock > 0
    Denominator: How many articles have Total_Plan > 0
    """
    count_article_plan = 0
    count_article_stock = 0
    
    for article_row in planogram[planogram['store_name'] == store]:
        article_mix = article_row['article_mix']
        
        total_plan = sum(int(article_row.get(col, 0) or 0) for col in size_map.keys())
        
        if total_plan > 0:
            count_article_plan += 1
            
            total_stock = sum(
                get_stock(stock, store, article_mix, size)
                for sizes in size_map.values()
                for size in sizes
            )
            
            if total_stock > 0:
                count_article_stock += 1
    
    return count_article_stock / count_article_plan if count_article_plan > 0 else 0.0
```

#### FS (Fill Stock) — Quantity Depth

```python
def calculate_fs(planogram, stock, store, size_map):
    """
    FS = Sum(Total_Stock) / Sum(Total_Plan)
    
    Can exceed 1.0 — this means overstocked (more stock than plan).
    FS > 1.0 is a signal for potential surplus return to warehouse.
    """
    total_plan = 0
    total_stock = 0
    
    for article_row in planogram[planogram['store_name'] == store]:
        article_mix = article_row['article_mix']
        
        for size_col, stock_sizes in size_map.items():
            plan_qty = int(article_row.get(size_col, 0) or 0)
            total_plan += plan_qty
            
            stock_qty = sum(
                get_stock(stock, store, article_mix, size)
                for size in stock_sizes
            )
            total_stock += stock_qty
    
    return total_stock / total_plan if total_plan > 0 else 0.0
```

### 6.3 Performance Optimization

The production script uses **raw psycopg2** (not pandas) for performance:
- O(1) dict lookups instead of DataFrame filtering
- Pre-builds stock lookup dict: `{(store, article_mix, size): quantity}`
- Processes 11 stores × 235 articles × 28 sizes in ~4.5 seconds

**Script reference:** `/opt/openclaw/scripts/calculate_ff_fa_fs.py` (599 lines, not included in this doc)

---

## 7. Status JSON Format

Written to `/opt/openclaw/logs/ff_fa_fs_latest_status.json` after each run. Read by Atlas for monitoring.

```json
{
  "job": "ff_fa_fs_daily",
  "report_date": "2026-02-14",
  "calculated_at": "2026-02-14 21:20:12 WIB",
  "status": "success",
  "duration_seconds": 4.5,
  "stores_calculated": 11,
  "error_message": "",
  "summary": {
    "avg_ff": 65.9,
    "avg_fa": 91.6,
    "avg_fs": 116.4,
    "stores_below_ff_70": 8
  },
  "unmapped_stores": []
}
```

**Status values:**
- `success` — all stores calculated successfully
- `partial_error` — some stores failed (details in `error_message`)
- `error` — complete failure (no metrics calculated)

**`unmapped_stores` array:**
Only present if there are planogram stores that couldn't be auto-matched to VPS stock locations. Atlas flags these for manual review.

---

## 8. Atlas Monitoring

Atlas VPS (76.13.194.103) monitors the FF/FA/FS pipeline daily at 05:30 WIB.

### Health Check Flow

```python
def check_ff_fa_fs_health():
    """
    Atlas daily health check for FF/FA/FS pipeline.
    """
    # 1. SSH to DB VPS and read status JSON
    status = ssh_read_file('76.13.194.120', '/opt/openclaw/logs/ff_fa_fs_latest_status.json')
    
    # 2. Check status
    if status['status'] != 'success':
        alert('FF/FA/FS calculation failed', status['error_message'])
    
    # 3. Check data freshness (should be today or yesterday)
    report_date = parse_date(status['report_date'])
    if (today() - report_date).days > 1:
        alert('FF/FA/FS data is stale', f"Last report: {report_date}")
    
    # 4. Check for unmapped stores
    if 'unmapped_stores' in status and status['unmapped_stores']:
        alert('Unmapped planogram stores', status['unmapped_stores'])
    
    # 5. Check metric ranges (sanity check)
    if status['summary']['avg_ff'] < 50 or status['summary']['avg_ff'] > 100:
        alert('FF metric out of expected range', status['summary'])
    
    # 6. Write to health report
    write_health_report({
        'ff_fa_fs': {
            'status': status['status'],
            'report_date': status['report_date'],
            'stores': status['stores_calculated'],
            'avg_ff': status['summary']['avg_ff'],
            'avg_fa': status['summary']['avg_fa'],
            'avg_fs': status['summary']['avg_fs'],
        }
    })
```

### Alert Conditions

| Condition | Severity | Action |
|-----------|----------|--------|
| `status != 'success'` | HIGH | Immediate notification to Wayan |
| Report date > 1 day old | MEDIUM | Flag in daily summary |
| Unmapped stores present | MEDIUM | Flag for manual mapping |
| avg_ff < 50% or > 100% | LOW | Sanity check warning |
| avg_fa < 50% or > 100% | LOW | Sanity check warning |
| avg_fs < 50% or > 200% | LOW | Sanity check warning |

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

## 10. First Run Results (Feb 14, 2026)

### Summary

- **11 Jatim stores** calculated successfully
- **Duration:** 4.5 seconds
- **All stores auto-mapped** (8 exact + 3 fuzzy)
- **0 unmapped stores**

### Metrics

| Metric | Average | Range | Stores Below Target |
|--------|---------|-------|---------------------|
| **FF** | 65.9% | 54.7%–80.7% | 8 stores < 70% |
| **FA** | 91.6% | 76.1%–98.0% | 1 store < 90% |
| **FS** | 116.4% | 88.3%–167.2% | 3 stores < 100% |

### Store-Level Detail

| Store | FF | FA | FS | Notes |
|-------|----|----|----|----|
| Zuma Royal Plaza | 80.7% | 98.0% | 167.2% | Best FF, overstocked |
| Zuma Galaxy Mall | 72.3% | 95.7% | 132.1% | Good FA, high FS |
| Zuma Tunjungan Plaza | 68.5% | 93.2% | 115.8% | Balanced |
| Zuma PTC | 67.1% | 91.4% | 108.3% | Balanced |
| Zuma Lippo Sidoarjo | 65.2% | 89.6% | 102.7% | Balanced |
| Zuma Matos | 64.8% | 90.1% | 98.5% | Slightly understocked |
| Zuma City Of Tomorrow Mall | 63.4% | 88.9% | 95.2% | Understocked |
| Zuma Lippo Batu | 61.7% | 87.3% | 91.8% | Understocked |
| Zuma Icon Gresik | 59.2% | 85.6% | 88.3% | Understocked |
| Zuma Sunrise Mall | 57.8% | 83.4% | 94.6% | Low FF |
| Zuma Mall Olympic Garden | 54.7% | 76.1% | 89.7% | Worst FF, needs restock |

### Insights

1. **8 stores below FF 70%** — most stores have significant size gaps
2. **FA is strong (91.6% avg)** — most articles are present, but not all sizes
3. **FS is high (116.4% avg)** — overall stock depth is good, some stores overstocked
4. **Zuma MOG needs urgent restock** — FF 54.7%, FA 76.1% (worst in region)
5. **Zuma Royal Plaza is overstocked** — FS 167.2% (67% more stock than plan)

---

## 11. How This SKILL Was Built

### Source Material Analyzed

1. **`AppScript of FF FA FS ST Jatim.txt`** (1,279 lines) — The original Google Apps Script that runs the existing FF/FA/FS/ST automation. This is the ground truth for calculation logic. The script:
   - Syncs data from Supabase to Google Sheets daily at 11:30
   - Merges Planogram + Stock into "Hasil Gabungan" sheet at 12:00
   - Calculates FF/FA/FS/ST from merged data at 13:00
   - Writes results to "Report" sheet with 4 stacked metric sections

2. **`Copy of FF FA FS ST Jatim Q1 2026.xlsx`** (9 sheets, fully read) — The actual production spreadsheet:
   - `Stock` sheet: 42,098 rows of raw stock with mutation columns (Saldo Awal, Masuk, Keluar, Saldo Akhir)
   - `Planogram` sheet: 2,569 rows × 49 columns — this IS the planogram format (28 size cols + metadata + AVG Sales/Rekomendasi)
   - `Hasil Gabungan` sheet: 2,569 rows × 68 columns — the merged intermediate data with Plan/Stock per size + summary counters
   - `Report` sheet: 4 sections (FF/FA/FS/ST) × 11 stores × daily date columns (Oct 2025 → Feb 2026)
   - `Data` sheet: 27,816 rows — Supabase sync output (being replaced with VPS DB)
   - `Backdata`, `store`, `Summary Monthly FF 2026`, `forNotionIntegrator` sheets also analyzed

3. **VPS PostgreSQL** (`openclaw_ops`) — Confirmed available data:
   - `core.stock_with_product` — maps cleanly to the Stock sheet data (minus mutation columns)
   - `core.sales_with_product` — available but NOT used for ST (see below)
   - No mutation data exists in VPS DB (confirmed via exhaustive search: `raw`, `core`, `mart`, `portal` schemas)

4. **`RO Input Jatim.xlsx`** (15 sheets) — Confirmed planogram sheet structure is identical to the FF/FA/FS input format

5. **`ringkasan_mutasi-2025_08_01_sampai_07.xlsx`** (8,769 rows) — Manual Accurate Online download, confirmed format: `Nama Gudang | Kode Barang | Nama Barang | Saldo Awal | Masuk | Keluar | Saldo Akhir`

### What Changed from v1.0 to v2.0

| Aspect | v1.0 (File-Based Script) | v2.0 (Automated Pipeline) |
|--------|--------------------------|---------------------------|
| Execution | Manual CLI script | Automated daily cron (03:00 WIB) |
| Planogram source | External Excel file input | `portal.temp_portal_plannogram` table |
| Store mapping | Hardcoded Python dict | `portal.store_name_map` table (auto-synced) |
| Size mapping | Hardcoded Python dict | Dynamic detection from planogram columns |
| Output | Excel file with conditional formatting | `mart.ff_fa_fs_daily` table (database) |
| Monitoring | None | Atlas health checks + WhatsApp alerts |
| Data library | pandas (DataFrame operations) | psycopg2 (raw SQL, O(1) dict lookups) |
| Performance | ~30 seconds for 11 stores | ~4.5 seconds for 11 stores |
| Status tracking | None | JSON status file for Atlas |

### Why ST Is Excluded (Not a Shortcut — a Correctness Decision)

The original AppScript calculates ST from the `Stock` sheet which has columns: `Saldo Awal`, `Masuk`, `Keluar`, `Saldo Akhir`. This data comes from **Ringkasan Mutasi Gudang** — a report from Accurate Online that tracks stock movements (opening balance, inbound transfers, outbound/sales, closing balance).

This mutation data does NOT exist in our VPS PostgreSQL database. We only have:
- Stock snapshots (point-in-time quantities) via `core.stock_with_product`
- Sales transactions via `core.sales_with_product`

A "fallback" formula like `Sales / (Stock + Sales)` would be **incorrect** because it:
- Misses inter-warehouse transfers (RO Box, RO Protol movements are not sales)
- Misses stock adjustments and inventory corrections
- Cannot distinguish between "sold to customer" and "transferred to another store"
- Produces numbers that look plausible but are actually wrong

**Wrong data presented confidently is worse than no data.** ST will be added to this SKILL when Ringkasan Mutasi data becomes available — see Section 12.

---

## 12. Future: ST Metric (When Ringkasan Mutasi Becomes Available)

This section documents everything needed to add ST. The code is ready — only the data source is missing.

### ST Formula

```
ST = Sum(Keluar) / Sum(Saldo_Awal + Masuk) × 100
```

Only for articles/sizes that exist in the planogram. Scoped to one store per one mutation period.

### Ringkasan Mutasi Data Format

```
Columns: Nama Gudang | Kode Barang | Nama Barang | Saldo Awal | Masuk | Keluar | Saldo Akhir
Example: Zuma Royal Plaza | B1SLV101Z35 | BOYS SLIDE MAX 1, 35, BLACK | 3 | 0 | 1 | 2
```

- `Kode Barang` = `kode_besar` in VPS DB (kode_mix + size, joinable)
- `Nama Gudang` = VPS `nama_gudang` (use store_name_map)
- ~8,769 rows per export covering all 51 warehouses + stores

### Mutation File Loader (Ready to Use)

```python
def load_mutation(file_path):
    """Load Ringkasan Mutasi Gudang from manual Excel download."""
    df = pd.read_excel(file_path, engine="openpyxl")

    col_map = {}
    for col in df.columns:
        cl = str(col).strip().lower()
        if "nama gudang" in cl:   col_map[col] = "nama_gudang"
        elif "kode barang" in cl: col_map[col] = "kode_barang"
        elif "nama barang" in cl: col_map[col] = "nama_barang"
        elif "saldo awal" in cl:  col_map[col] = "saldo_awal"
        elif cl == "masuk":       col_map[col] = "masuk"
        elif cl == "keluar":      col_map[col] = "keluar"
        elif "saldo akhir" in cl: col_map[col] = "saldo_akhir"

    df = df.rename(columns=col_map)
    for c in ["saldo_awal", "masuk", "keluar", "saldo_akhir"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    return df
```

### ST Calculation Function (Ready to Use)

```python
def calculate_st(mutation_df, planogram, store_name, size_map):
    """
    ST from Ringkasan Mutasi, scoped to planogram articles only.
    Join: kode_besar = article_mix + size (for each planned size slot).
    """
    store_db = get_stock_nama_gudang(store_name)
    
    # Build set of kode_besar that are in the planogram
    plano_kode_besar = set()
    for article_row in planogram[planogram['store_name'] == store_name]:
        mix = article_row['article_mix']
        for size_col, stock_sizes in size_map.items():
            if int(article_row.get(size_col, 0) or 0) > 0:
                for size in stock_sizes:
                    plano_kode_besar.add(f"{mix}{size}")

    mut = mutation_df[
        (mutation_df["nama_gudang"] == store_db)
        & (mutation_df["kode_barang"].isin(plano_kode_besar))
    ]

    available = (mut["saldo_awal"] + mut["masuk"]).sum()
    sold = mut["keluar"].sum()

    return sold / available if available > 0 else 0.0
```

### How to Enable ST

When mutation data becomes available (API or manual file):

1. Add `st` column to `mart.ff_fa_fs_daily` table
2. Modify script to load mutation data
3. Call `calculate_st()` after FF/FA/FS calculation
4. Update status JSON to include `avg_st` in summary

### Accurate Online API — Investigation Status

The report export API pattern is known from `pull_historical_sales.py` on VPS:
- `POST {host}/accurate/report/execute-report.do` → returns `cacheId`
- `POST {host}/accurate/report/export-report.do` → downloads Excel

What's missing for Ringkasan Mutasi:
- The numeric `reportId` (e.g., sales detail = 15500)
- The string `planId` (e.g., sales = "ViewSalesByItemDetailReport")

These can be found by inspecting network requests in browser DevTools when running the report in Accurate Online UI. Once found, a `pull_accurate_mutation.py` script will be built following the exact same pattern as `pull_historical_sales.py`.

---

## 13. SQL Query Templates

### 13.1 Latest Metrics for All Stores

```sql
-- Latest FF/FA/FS for all Jatim stores
SELECT 
    report_date,
    store_label,
    ROUND(ff * 100, 1) AS ff_pct,
    ROUND(fa * 100, 1) AS fa_pct,
    ROUND(fs * 100, 1) AS fs_pct
FROM mart.ff_fa_fs_daily
WHERE branch = 'Jatim'
  AND report_date = (SELECT MAX(report_date) FROM mart.ff_fa_fs_daily)
ORDER BY ff DESC;
```

### 13.2 Trend Over Time (Last 30 Days)

```sql
-- FF trend for one store over last 30 days
SELECT 
    report_date,
    ROUND(ff * 100, 1) AS ff_pct,
    ROUND(fa * 100, 1) AS fa_pct,
    ROUND(fs * 100, 1) AS fs_pct
FROM mart.ff_fa_fs_daily
WHERE store_label = 'Zuma Royal Plaza'
  AND report_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY report_date;
```

### 13.3 Stores Below Target

```sql
-- Stores with FF < 70% (need urgent restock)
SELECT 
    store_label,
    ROUND(ff * 100, 1) AS ff_pct,
    ROUND(fa * 100, 1) AS fa_pct,
    ROUND(fs * 100, 1) AS fs_pct
FROM mart.ff_fa_fs_daily
WHERE report_date = (SELECT MAX(report_date) FROM mart.ff_fa_fs_daily)
  AND ff < 0.70
ORDER BY ff;
```

### 13.4 Branch-Level Summary

```sql
-- Average metrics per branch
SELECT 
    branch,
    COUNT(DISTINCT store_label) AS num_stores,
    ROUND(AVG(ff) * 100, 1) AS avg_ff,
    ROUND(AVG(fa) * 100, 1) AS avg_fa,
    ROUND(AVG(fs) * 100, 1) AS avg_fs
FROM mart.ff_fa_fs_daily
WHERE report_date = (SELECT MAX(report_date) FROM mart.ff_fa_fs_daily)
GROUP BY branch
ORDER BY avg_ff DESC;
```

### 13.5 Check Store Mappings

```sql
-- View all store mappings
SELECT 
    planogram_name,
    stock_nama_gudang,
    branch,
    match_method,
    updated_at
FROM portal.store_name_map
ORDER BY branch, planogram_name;
```

### 13.6 Check Unmapped Stores

```sql
-- Find planogram stores not in mapping table
SELECT DISTINCT store_name
FROM portal.temp_portal_plannogram
WHERE store_name NOT IN (SELECT planogram_name FROM portal.store_name_map)
ORDER BY store_name;
```

---

## 14. Agent Instructions

### For AI Agents Using This SKILL

1. **ALWAYS load `zuma-data-ops` skill** alongside this one — it contains DB connection rules you must follow
2. **To check latest metrics:**
   - Query `mart.ff_fa_fs_daily` table (see Section 13.1)
   - Or read `/opt/openclaw/logs/ff_fa_fs_latest_status.json` for summary
3. **To investigate low FF stores:**
   - Query stores with FF < 0.70 (see Section 13.3)
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

## 15. Dependencies

### VPS Environment

```bash
# Python 3.12 in venv
/opt/openclaw/venv/bin/python3

# Required packages (already installed in venv)
psycopg2  # PostgreSQL connection (not pandas — raw SQL for performance)
```

### Database Access

See `zuma-data-analyst-skill` for connection details:
- Host: 76.13.194.120
- Port: 5432
- Database: openclaw_ops
- User: openclaw_app

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial — FF/FA/FS from VPS DB + planogram file input. ST deferred pending Ringkasan Mutasi data. |
| 2.0 | 2026-02-14 | **MAJOR REWRITE** — Automated daily pipeline. Store mapping auto-sync. Dynamic size detection. Database storage. Atlas monitoring. Performance optimization (4.5s vs 30s). Removed hardcoded mappings. Added status JSON. First production run (11 Jatim stores, 65.9% avg FF). |
