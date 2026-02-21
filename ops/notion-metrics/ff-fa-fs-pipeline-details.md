# FF/FA/FS Pipeline Details

> Reference file for SKILL: FF / FA / FS — Store Fill Rate Metrics  
> Contains: Full database DDL (Section 3), Status JSON format (Section 7), Atlas monitoring (Section 8)

---

## 3. Database Tables (Full DDL)

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
