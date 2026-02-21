# Database Troubleshooting & Maintenance Procedures

Reference file for `zuma-database-assistant-skill`. Contains detailed fix procedures, maintenance SQL templates, and troubleshooting decision trees.

---

## 1. Fix Patterns — Detailed Procedures

### 1.1 Sales Double-Counting (Snapshot Overlap)

**Symptom:** Sales totals are higher than expected. Same invoices counted 2-3x.
**Root cause:** `fact_sales_unified` view missing `DISTINCT ON` dedup, or `DISTINCT ON` clause missing a column.

**Fix — Recreate view with DISTINCT ON:**
```sql
CREATE OR REPLACE VIEW core.fact_sales_unified AS
-- For each entity (DDD, MBB, UBB):
SELECT ... FROM (
    SELECT DISTINCT ON (nomor_invoice, kode_produk, tanggal, line_number)
        -- all raw columns
    FROM raw.accurate_sales_{entity}
    ORDER BY nomor_invoice, kode_produk, tanggal, line_number, snapshot_date DESC
) s
LEFT JOIN ...
UNION ALL
-- ... repeat for other entities
```

**Verify fix:**
```sql
-- Before: count from raw (with duplicates)
SELECT COUNT(*) FROM raw.accurate_sales_ddd;

-- After: count from view (deduped)
SELECT COUNT(*) FROM core.fact_sales_unified WHERE source_entity = 'DDD';
-- Should be LESS than raw count

-- Check for remaining duplicates (must be 0)
SELECT COUNT(*) FROM (
    SELECT nomor_invoice, kode_besar, transaction_date, line_number, COUNT(*)
    FROM core.fact_sales_unified
    GROUP BY 1, 2, 3, 4
    HAVING COUNT(*) > 1
) dup;
```

### 1.2 Multi-Line Invoice Constraint Violation

**Symptom:** Sales pull fails with `duplicate key value violates unique constraint`. Log shows same invoice+product but different prices.
**Root cause:** Same product appears multiple times in one invoice at different price points (e.g., bulk event orders). The unique constraint was too narrow.

**Example (Event Wilbex invoice):**
```
Invoice SI317..., kode_produk = b2ca03z34, price = 89189.19 (line 1)
Invoice SI317..., kode_produk = b2ca03z34, price = 99000.00 (line 2)
```

**Fix applied (Feb 2026):**
1. Added `line_number` column (default 1) to all 3 sales tables
2. Updated unique constraint to include `line_number`
3. Updated `flatten_invoice()` to track per-product line numbers
4. Updated INSERT SQL ON CONFLICT clause

**If a NEW multi-line violation occurs after the fix, it means `line_number` assignment in `flatten_invoice()` is wrong.** Debug by:
```bash
# Check the failing invoice in the log
grep "duplicate key" /opt/openclaw/logs/sales_*.log

# Dry-run to see the data before insert
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_sales.py ddd --dry-run
```

### 1.3 Adding a Column to Sales Tables

All 3 sales tables must stay in sync. Always add to all 3 + update the view:

```sql
-- Step 1: Add column to all 3 tables
ALTER TABLE raw.accurate_sales_ddd ADD COLUMN new_column_name data_type DEFAULT default_value;
ALTER TABLE raw.accurate_sales_mbb ADD COLUMN new_column_name data_type DEFAULT default_value;
ALTER TABLE raw.accurate_sales_ubb ADD COLUMN new_column_name data_type DEFAULT default_value;

-- Step 2: If column is part of uniqueness, update constraints
ALTER TABLE raw.accurate_sales_ddd DROP CONSTRAINT accurate_sales_ddd_..._key;
ALTER TABLE raw.accurate_sales_ddd ADD CONSTRAINT accurate_sales_ddd_..._key
    UNIQUE (nomor_invoice, kode_produk, tanggal, snapshot_date, line_number, new_column);
-- Repeat for mbb, ubb

-- Step 3: Recreate fact_sales_unified to include new column
CREATE OR REPLACE VIEW core.fact_sales_unified AS ...

-- Step 4: Update pull_accurate_sales.py
-- - Add to flatten_invoice() row dict
-- - Add to INSERT SQL column list
-- - Add to VALUES tuple
-- - Add to ON CONFLICT clause (if part of uniqueness)

-- Step 5: Verify
SELECT COUNT(*) FROM core.fact_sales_unified;
SELECT COUNT(*) FROM core.sales_with_product;  -- must match
```

### 1.4 Recreating a View Safely

Views can be replaced with `CREATE OR REPLACE VIEW`. This is safe — no data loss (views are just queries).

**Pre-flight checks:**
```sql
-- 1. Record current row count
SELECT COUNT(*) FROM core.fact_sales_unified;  -- save this number

-- 2. Record current column list
SELECT column_name FROM information_schema.columns
WHERE table_schema = 'core' AND table_name = 'fact_sales_unified'
ORDER BY ordinal_position;
```

**After recreation:**
```sql
-- 3. Verify row count matches or is explainable
SELECT COUNT(*) FROM core.fact_sales_unified;

-- 4. Verify downstream views still work
SELECT COUNT(*) FROM core.sales_with_product;
```

**WARNING:** If the downstream view (`sales_with_product`) references columns by name, adding/removing columns from `fact_sales_unified` may break it. Always check downstream views after changes.

### 1.5 Constraint Management

**Find existing constraints on a table:**
```sql
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'raw.accurate_sales_ddd'::regclass;
```

**Drop a constraint:**
```sql
ALTER TABLE raw.accurate_sales_ddd DROP CONSTRAINT constraint_name;
```

**Add a new unique constraint:**
```sql
ALTER TABLE raw.accurate_sales_ddd
ADD CONSTRAINT accurate_sales_ddd_unique_key
UNIQUE (nomor_invoice, kode_produk, tanggal, snapshot_date, line_number);
```

### 1.6 Re-running Failed ETL

When a sales/stock pull fails:

```bash
# 1. Check the status file
cat /opt/openclaw/logs/sales_latest_status.json

# 2. Check the log for errors
tail -100 /opt/openclaw/logs/sales_$(date +%Y%m%d).log

# 3. Re-run the failed entity
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_sales.py ddd

# 4. Update the status file after successful re-run
cat > /opt/openclaw/logs/sales_latest_status.json << EOF
{
  "type": "sales_pull",
  "date": "$(date +%Y-%m-%d)",
  "time": "$(date +%H:%M:%S)",
  "overall": "success",
  "log_file": "/opt/openclaw/logs/sales_$(date +%Y%m%d).log",
  "note": "Manual re-run after fix"
}
EOF
```

**IMPORTANT:** Always use `/opt/openclaw/venv/bin/python`, NOT `python3`. The system Python doesn't have the required packages (pandas, psycopg2, etc.).

---

## 2. Maintenance SQL Templates

### 2.1 Check for Duplicate Sales (Dedup Health)

```sql
-- Should return 0 rows if dedup is working
SELECT nomor_invoice, kode_besar, transaction_date, line_number, COUNT(*) AS occurrences
FROM core.fact_sales_unified
GROUP BY 1, 2, 3, 4
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 20;
```

### 2.2 Check Snapshot Overlap in Raw Tables

```sql
-- Shows how many snapshots exist per date range
-- If a row appears in 3 snapshots, it will show count=3
SELECT snapshot_date, COUNT(*) AS rows
FROM raw.accurate_sales_ddd
WHERE tanggal >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY snapshot_date
ORDER BY snapshot_date;
```

### 2.3 Verify View Row Counts Match

```sql
-- fact_sales_unified must equal sales_with_product
SELECT
    (SELECT COUNT(*) FROM core.fact_sales_unified) AS fact_rows,
    (SELECT COUNT(*) FROM core.sales_with_product) AS swp_rows,
    (SELECT COUNT(*) FROM core.fact_sales_unified) -
    (SELECT COUNT(*) FROM core.sales_with_product) AS difference;
-- difference MUST be 0

-- fact_stock_unified must equal stock_with_product
SELECT
    (SELECT COUNT(*) FROM core.fact_stock_unified) AS fact_rows,
    (SELECT COUNT(*) FROM core.stock_with_product) AS swp_rows,
    (SELECT COUNT(*) FROM core.fact_stock_unified) -
    (SELECT COUNT(*) FROM core.stock_with_product) AS difference;
```

### 2.4 Check Data Freshness

```sql
-- Latest sales per entity
SELECT source_entity, MAX(transaction_date) AS latest_sale, MAX(snapshot_date) AS latest_snapshot
FROM core.fact_sales_unified
GROUP BY 1
ORDER BY 1;

-- Latest stock per entity
SELECT source_entity, MAX(snapshot_date) AS latest_snapshot
FROM core.fact_stock_unified
GROUP BY 1;

-- Latest ETL runs
SELECT entity, data_type, status, rows_loaded, loaded_at
FROM raw.load_history
ORDER BY loaded_at DESC
LIMIT 10;
```

### 2.5 Check Kodemix Match Rates

```sql
-- Sales match rate (should be ~94%+)
SELECT
    COUNT(*) AS total_rows,
    COUNT(kode_mix) AS matched,
    COUNT(*) - COUNT(kode_mix) AS unmatched,
    ROUND(COUNT(kode_mix)::numeric / COUNT(*) * 100, 1) AS match_pct
FROM core.sales_with_product;

-- Stock match rate (should be ~99%+)
SELECT
    COUNT(*) AS total_rows,
    COUNT(kode_mix) AS matched,
    COUNT(*) - COUNT(kode_mix) AS unmatched,
    ROUND(COUNT(kode_mix)::numeric / COUNT(*) * 100, 1) AS match_pct
FROM core.stock_with_product;
```

### 2.6 Find Problematic Invoices

```sql
-- Invoices with multi-line same-product (line_number > 1)
SELECT nomor_invoice, kode_besar, line_number, quantity, unit_price, total_amount
FROM core.fact_sales_unified
WHERE line_number > 1
ORDER BY transaction_date DESC
LIMIT 50;
```

### 2.7 Get View Definition

```sql
-- See exact SQL of any view
SELECT pg_get_viewdef('core.fact_sales_unified'::regclass, true);
SELECT pg_get_viewdef('core.sales_with_product'::regclass, true);
```

### 2.8 Table/View Inventory

```sql
-- All objects in raw + core schemas
SELECT schemaname, tablename AS name, 'table' AS type
FROM pg_tables WHERE schemaname IN ('raw', 'core')
UNION ALL
SELECT schemaname, viewname AS name, 'view' AS type
FROM pg_views WHERE schemaname IN ('raw', 'core')
ORDER BY 1, 3, 2;
```

### 2.9 Table Size and Row Counts

```sql
SELECT
    schemaname,
    relname AS table_name,
    n_live_tup AS estimated_rows,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || relname)) AS total_size
FROM pg_stat_user_tables
WHERE schemaname IN ('raw', 'portal')
ORDER BY pg_total_relation_size(schemaname || '.' || relname) DESC;
```

---

## 3. Troubleshooting Decision Trees

### 3.1 ETL Failure Decision Tree

```
Sales pull failed?
├── Check log: /opt/openclaw/logs/sales_YYYYMMDD.log
├── "duplicate key" error?
│   ├── Same product, different prices → line_number logic bug in flatten_invoice()
│   └── Exact same data → snapshot_date collision (shouldn't happen with upsert)
├── "connection refused" / timeout?
│   ├── Accurate API down → wait and retry
│   └── VPS network issue → check internet from VPS
├── "token validation failed"?
│   └── API token expired → regenerate in Accurate Online dashboard, update .env.{entity}
├── "PG_PASSWORD is required"?
│   └── .env file missing or not readable → check /opt/openclaw/scripts/.env
└── CSV fallback created?
    └── Data saved to /opt/openclaw/scripts/{ENTITY}_sales_YYYYMMDD.csv
    └── Fix the issue, then re-run (script will upsert, no duplicates)
```

### 3.2 View Returns Wrong Row Count

```
Row count too HIGH (more than raw deduped)?
├── JOIN causing inflation → portal.kodemix has multiple rows per kode_besar
│   └── Fix: DISTINCT ON in the kodemix subquery
└── UNION ALL duplicating → check entity boundaries

Row count too LOW (less than expected)?
├── DISTINCT ON too aggressive → collapsing rows that should be separate
│   └── Fix: add missing column to DISTINCT ON (e.g., line_number)
└── WHERE filter too strict → check snapshot_date or other filters
```

### 3.3 Stock Shows Stale Data

```
Stock snapshot_date is old (not today)?
├── Cron didn't run → check: crontab -l
├── Stock pull failed → check /opt/openclaw/logs/stock_latest_status.json
├── TRUNCATE succeeded but INSERT failed → table is EMPTY (critical!)
│   └── Re-run immediately: /opt/openclaw/venv/bin/python pull_accurate_stock.py {entity}
└── API returned empty → Accurate Online might be in maintenance
```

### 3.4 Downstream View Broken After Change

```
sales_with_product returns error after fact_sales_unified change?
├── Column removed → sales_with_product references it by name
│   └── Recreate sales_with_product view to match new columns
├── Column renamed → same issue
│   └── Either rename back or update downstream
└── Column type changed → implicit cast may fail
    └── Add explicit CAST in the view definition
```
