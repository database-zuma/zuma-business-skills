---
name: zuma-database-assistant-skill
description: Zuma Indonesia database administration & maintenance skill — schema internals, ETL pipeline (pull_accurate_sales.py / pull_accurate_stock.py), view architecture, constraint management, deduplication patterns, and troubleshooting. Use when fixing database issues, modifying views/tables, debugging ETL failures, adding columns, recreating constraints, or performing any DBA-level work on the openclaw_ops PostgreSQL database.
user-invocable: false
---

# Zuma Database Administration & Maintenance

You are maintaining Zuma Indonesia's centralized PostgreSQL data warehouse (`openclaw_ops`) on VPS `76.13.194.120`. This skill covers the **internals** — how data flows in, how views are constructed, how to fix things when they break.

**This skill is for DBA/maintenance work.** For querying and analysis, use `zuma-data-analyst-skill` instead.

---

## 1. Infrastructure

### VPS Database Server

| Field | Value |
|-------|-------|
| **Host** | `76.13.194.120` |
| **Port** | `5432` |
| **Database** | `openclaw_ops` |
| **User** | `openclaw_app` |
| **Password** | `Zuma-0psCl4w-2026!` |
| **SSH** | `ssh root@76.13.194.120` |
| **Python venv** | `/opt/openclaw/venv/bin/python` |
| **Scripts dir** | `/opt/openclaw/scripts/` |
| **Logs dir** | `/opt/openclaw/logs/` |

### Quick Access

```bash
# SSH into VPS
ssh root@76.13.194.120

# psql from VPS (localhost, no password prompt)
PGPASSWORD='Zuma-0psCl4w-2026!' psql -h localhost -U openclaw_app -d openclaw_ops

# Run ETL scripts (MUST use venv Python)
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_sales.py ddd
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_stock.py ddd
```

---

## 2. Raw Tables — Column-Level Reference

All raw tables live in the `raw` schema. Each entity (DDD, MBB, UBB, LJBB) has separate tables with identical structure per data type.

### 2.1 Sales Tables (`raw.accurate_sales_{ddd,mbb,ubb}`)

All 3 sales tables share this exact structure (20 columns):

| # | Column | Type | Nullable | Default | Description |
|---|--------|------|----------|---------|-------------|
| 1 | `tanggal` | date | NOT NULL | — | Transaction date (YYYY-MM-DD) |
| 2 | `nama_departemen` | text | YES | — | Department/store name from Accurate |
| 3 | `nama_pelanggan` | text | YES | — | Customer name (used for intercompany detection) |
| 4 | `nomor_invoice` | text | YES | — | Invoice number from Accurate |
| 5 | `kode_produk` | text | NOT NULL | — | Product code = `kode_besar` (article+size) |
| 6 | `nama_barang` | text | YES | — | Product name from Accurate |
| 7 | `satuan` | text | YES | — | Unit of measure (usually "PAIR") |
| 8 | `kuantitas` | numeric | NOT NULL | — | Quantity sold |
| 9 | `harga_satuan` | numeric | YES | — | Unit selling price |
| 10 | `total_harga` | numeric | YES | — | Total amount (kuantitas × harga_satuan) |
| 11 | `bpp` | numeric | YES | `0` | Cost of goods (BPP), often 0 from API |
| 12 | `snapshot_date` | date | NOT NULL | — | Date this data was pulled by ETL |
| 13 | `loaded_at` | timestamptz | NOT NULL | `now()` | ETL load timestamp |
| 14 | `load_batch_id` | text | YES | — | Batch identifier for audit trail |
| 15 | `id` | bigint (serial) | NOT NULL | `nextval(...)` | Auto-increment PK |
| 16 | `nama_gudang` | text | YES | — | Warehouse/store name for this line item |
| 17 | `vendor_price` | numeric | YES | — | Vendor/supplier price |
| 18 | `dpp_amount` | numeric | YES | — | DPP (tax base) amount |
| 19 | `tax_amount` | numeric | YES | — | Tax amount |
| 20 | `line_number` | integer | YES | `1` | Line item sequence within same (invoice, product) pair. Handles multi-line invoices where same product appears at different prices. |

**Unique constraint** (all 3 tables):
```
UNIQUE (nomor_invoice, kode_produk, tanggal, snapshot_date, line_number)
```

**Why 5 columns in the constraint:**
- `nomor_invoice + kode_produk + tanggal` — identifies a sale line
- `snapshot_date` — allows overlapping 3-day windows to coexist without conflict
- `line_number` — handles same product appearing multiple times in one invoice at different prices (e.g., Event Wilbex bulk orders)

### 2.2 Stock Tables (`raw.accurate_stock_{ddd,ljbb,mbb,ubb}`)

All 4 stock tables share this structure (10 columns):

| # | Column | Type | Nullable | Default | Description |
|---|--------|------|----------|---------|-------------|
| 1 | `kode_barang` | text | NOT NULL | — | Product code = `kode_besar` |
| 2 | `nama_barang` | text | YES | — | Product name |
| 3 | `nama_gudang` | text | YES | — | Warehouse/store name |
| 4 | `kuantitas` | integer | NOT NULL | — | Stock quantity in pairs |
| 5 | `snapshot_date` | date | NOT NULL | — | Date of snapshot |
| 6 | `loaded_at` | timestamptz | NOT NULL | `now()` | ETL load timestamp |
| 7 | `load_batch_id` | text | YES | — | Batch identifier |
| 8 | `id` | bigint (serial) | NOT NULL | `nextval(...)` | Auto-increment PK |
| 9 | `unit_price` | numeric | YES | — | Unit cost |
| 10 | `vendor_price` | numeric | YES | — | Vendor/supplier price |

**Note:** Stock column is `kode_barang`, NOT `kode_produk` (unlike sales tables). This naming inconsistency is historical.

### 2.3 Other Raw Tables

| Table | Description |
|-------|-------------|
| `raw.iseller_sales` | POS sales from iSeller (evolving structure) |
| `raw.load_history` | ETL audit trail — every data pull logged here |

**`raw.load_history` columns:** `id`, `loaded_at`, `source`, `entity`, `data_type`, `batch_id`, `date_from`, `date_to`, `rows_loaded`, `status`, `error_message`

---

## 3. View Architecture — How Deduplication Works

### 3.1 The Snapshot Overlap Problem (Sales)

Sales ETL pulls a **3-day rolling window** daily. This means the same invoice can appear in multiple snapshots:

```
Day 1 pull: [Jan 10, Jan 11, Jan 12] → snapshot_date = Jan 12
Day 2 pull: [Jan 11, Jan 12, Jan 13] → snapshot_date = Jan 13
Day 3 pull: [Jan 12, Jan 13, Jan 14] → snapshot_date = Jan 14
```

Jan 12 data exists in ALL THREE snapshots. Without dedup, queries return 3× the real sales.

### 3.2 `core.fact_sales_unified` — Sales Dedup View

Uses `DISTINCT ON` to pick the **latest snapshot** for each unique line item:

```sql
-- Pattern repeated for DDD, MBB, UBB (UNION ALL)
SELECT ... FROM (
    SELECT DISTINCT ON (nomor_invoice, kode_produk, tanggal, line_number)
        -- all columns
    FROM raw.accurate_sales_{entity}
    ORDER BY nomor_invoice, kode_produk, tanggal, line_number, snapshot_date DESC
) s
LEFT JOIN core.dim_product p ON TRIM(LOWER(s.kode_produk)) = p.kode_besar
LEFT JOIN core.dim_store st ON TRIM(LOWER(s.nama_departemen)) = st.store_name
LEFT JOIN core.dim_warehouse w ON w.warehouse_code = '{ENTITY}'
```

**Key details:**
- `DISTINCT ON (nomor_invoice, kode_produk, tanggal, line_number)` — dedup key
- `ORDER BY ... snapshot_date DESC` — picks the LATEST snapshot (most recent data wins)
- `line_number` in DISTINCT ON — prevents collapsing multi-line same-product items
- Output includes `line_number` as a column

**Output columns (21):** `source_entity`, `nomor_invoice`, `transaction_date`, `date_key`, `kode_besar`, `matched_kode_besar`, `store_name_raw`, `matched_store_name`, `nama_barang`, `quantity`, `unit_price`, `total_amount`, `cost_of_goods`, `vendor_price`, `dpp_amount`, `tax_amount`, `warehouse_code`, `snapshot_date`, `loaded_at`, `nama_pelanggan`, `line_number`

### 3.3 `core.fact_stock_unified` — Stock View

Stock uses a completely different strategy — **no overlap problem** because stock ETL does `TRUNCATE` + fresh insert (only 1 snapshot exists at any time).

```sql
-- Pattern repeated for DDD, LJBB, MBB, UBB (UNION ALL)
SELECT ... FROM raw.accurate_stock_{entity} s
LEFT JOIN core.dim_product p ON TRIM(LOWER(s.kode_barang)) = p.kode_besar
LEFT JOIN core.dim_warehouse w ON w.warehouse_code = '{ENTITY}'
WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM raw.accurate_stock_{entity})
```

**Key detail:** `WHERE snapshot_date = MAX(snapshot_date)` — even though TRUNCATE means only 1 snapshot, this is a safety net.

**Output columns (11):** `source_entity`, `snapshot_date`, `date_key`, `kode_besar`, `matched_kode_besar`, `nama_gudang`, `quantity`, `unit_price`, `vendor_price`, `warehouse_code`, `loaded_at`

### 3.4 Downstream Views

| View | Reads From | Adds |
|------|-----------|------|
| `core.sales_with_product` (48 cols) | `fact_sales_unified` | Product enrichment (kodemix, hpprsp), store enrichment (portal.store), `is_intercompany` flag |
| `core.stock_with_product` (38 cols) | `fact_stock_unified` | Product enrichment, warehouse/capacity enrichment |
| `core.sales_with_store` | `fact_sales_unified` | Store enrichment only (legacy, less enriched) |

### 3.5 Dimension Views

| View | Source | Dedup Method |
|------|--------|-------------|
| `core.dim_product` (16 cols) | `portal.kodemix` + `portal.hpprsp` | `DISTINCT ON (kode_besar)` ordered by `no_urut` |
| `core.dim_store` (12 cols) | `portal.store` | `DISTINCT ON (TRIM(LOWER(nama_accurate)))` |
| `core.dim_warehouse` (3 cols) | Hardcoded | `VALUES ('DDD','MBB','UBB','LJBB')` |
| `core.dim_date` (11 cols) | Generated | Date dimension `generate_series()` |

---

## 4. ETL Pipeline

### 4.1 Cron Schedule

| Time (WIB) | Script | What It Does |
|------------|--------|-------------|
| **02:00** | DB backup | `pg_dump` of `openclaw_ops` → `/root/backups/` |
| **03:00** | `cron_stock_pull.sh` | Pulls stock for DDD, LJBB, MBB, UBB (TRUNCATE + insert) |
| **05:00** | `cron_sales_pull.sh` | Pulls sales for DDD, MBB, UBB (3-day rolling UPSERT) |

### 4.2 Sales ETL: `pull_accurate_sales.py`

**Location:** `/opt/openclaw/scripts/pull_accurate_sales.py`
**Venv:** `/opt/openclaw/venv/bin/python`
**Env files:** `/opt/openclaw/scripts/.env.{ddd,mbb,ubb}`

**Flow:**
1. Load entity credentials from `.env.{entity}` (API token + signature secret)
2. Connect to Accurate Online API (HMAC-SHA256 auth)
3. Fetch invoice list for date range (paginated, 100 per page)
4. Fetch detail for each invoice (rate limited: 8 req/sec)
5. `flatten_invoice()` — converts API response to flat rows
6. Assigns `line_number` per (invoice, product) pair (1, 2, 3... for same product at different prices)
7. UPSERT to PostgreSQL: `INSERT ... ON CONFLICT (nomor_invoice, kode_produk, tanggal, snapshot_date, line_number) DO UPDATE`
8. Log to `raw.load_history`
9. On failure: save CSV fallback to `/opt/openclaw/scripts/{ENTITY}_sales_{date}.csv`

**Key function — `flatten_invoice()`:**
```python
# Tracks line_number per product code within each invoice
product_line_counter = {}

for item in invoice.get("detailItem", []):
    kode = item_obj.get("no", "")
    product_line_counter[kode] = product_line_counter.get(kode, 0) + 1
    row = {
        ...
        "line_number": product_line_counter[kode],
        ...
    }
```

**Usage:**
```bash
# Single entity (last 3 days default)
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_sales.py ddd

# Custom days
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_sales.py ddd --days 5

# All entities
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_sales.py all

# Dry run (preview without writing)
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_sales.py ddd --dry-run
```

### 4.3 Stock ETL: `pull_accurate_stock.py`

**Location:** `/opt/openclaw/scripts/pull_accurate_stock.py`

**Flow:**
1. Same API auth as sales
2. Fetch all items from Accurate inventory endpoint
3. **TRUNCATE** the target table (full replace, not upsert)
4. INSERT all rows fresh
5. Result: always exactly 1 snapshot in each stock table

**Critical difference from sales:** Stock does TRUNCATE + INSERT. There is never more than 1 snapshot_date in stock tables. This is why stock has no dedup problem.

### 4.4 Cron Wrapper: `cron_sales_pull.sh`

**Location:** `/opt/openclaw/scripts/cron_sales_pull.sh`

Runs all 3 entities sequentially (DDD → MBB → UBB), writes:
- **Log:** `/opt/openclaw/logs/sales_{YYYYMMDD}.log`
- **Status:** `/opt/openclaw/logs/sales_latest_status.json`

**Status file format:**
```json
{
  "type": "sales_pull",
  "date": "2026-02-13",
  "time": "05:02:00",
  "overall": "success",
  "log_file": "/opt/openclaw/logs/sales_20260213.log"
}
```

**`overall` values:** `success` (all 3 OK), `partial_error` (1-2 failed), `error` (all failed)

**Stock equivalent:** `/opt/openclaw/logs/stock_latest_status.json` (same format)

### 4.5 Entity Credential Files

Each entity has a `.env` file in `/opt/openclaw/scripts/`:

| File | Entity | API Host |
|------|--------|----------|
| `.env.ddd` | DDD (PT Dream Dare Discover) | `zeus.accurate.id` |
| `.env.mbb` | MBB (CV Makmur Besar Bersama) | `iris.accurate.id` |
| `.env.ubb` | UBB (CV Untung Besar Bersama) | `zeus.accurate.id` |

Each contains: `ACCURATE_API_TOKEN` and `ACCURATE_SIGNATURE_SECRET`

PostgreSQL credentials are in `/opt/openclaw/scripts/.env` (shared): `PG_HOST`, `PG_PORT`, `PG_DATABASE`, `PG_USER`, `PG_PASSWORD`

---

## 5. Common Fix Patterns

### 5.1 Sales Double-Counting (Snapshot Overlap)

**Symptom:** Sales totals are higher than expected. Same invoices counted 2-3×.
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

### 5.2 Multi-Line Invoice Constraint Violation

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

### 5.3 Adding a Column to Sales Tables

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

### 5.4 Recreating a View Safely

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

### 5.5 Constraint Management

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

### 5.6 Re-running Failed ETL

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

## 6. Maintenance SQL Templates

### 6.1 Check for Duplicate Sales (Dedup Health)

```sql
-- Should return 0 rows if dedup is working
SELECT nomor_invoice, kode_besar, transaction_date, line_number, COUNT(*) AS occurrences
FROM core.fact_sales_unified
GROUP BY 1, 2, 3, 4
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 20;
```

### 6.2 Check Snapshot Overlap in Raw Tables

```sql
-- Shows how many snapshots exist per date range
-- If a row appears in 3 snapshots, it will show count=3
SELECT snapshot_date, COUNT(*) AS rows
FROM raw.accurate_sales_ddd
WHERE tanggal >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY snapshot_date
ORDER BY snapshot_date;
```

### 6.3 Verify View Row Counts Match

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

### 6.4 Check Data Freshness

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

### 6.5 Check Kodemix Match Rates

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

### 6.6 Find Problematic Invoices

```sql
-- Invoices with multi-line same-product (line_number > 1)
SELECT nomor_invoice, kode_besar, line_number, quantity, unit_price, total_amount
FROM core.fact_sales_unified
WHERE line_number > 1
ORDER BY transaction_date DESC
LIMIT 50;
```

### 6.7 Get View Definition

```sql
-- See exact SQL of any view
SELECT pg_get_viewdef('core.fact_sales_unified'::regclass, true);
SELECT pg_get_viewdef('core.sales_with_product'::regclass, true);
```

### 6.8 Table/View Inventory

```sql
-- All objects in raw + core schemas
SELECT schemaname, tablename AS name, 'table' AS type
FROM pg_tables WHERE schemaname IN ('raw', 'core')
UNION ALL
SELECT schemaname, viewname AS name, 'view' AS type
FROM pg_views WHERE schemaname IN ('raw', 'core')
ORDER BY 1, 3, 2;
```

### 6.9 Table Size and Row Counts

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

## 7. Troubleshooting Guide

### 7.1 ETL Failure Decision Tree

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

### 7.2 View Returns Wrong Row Count

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

### 7.3 Stock Shows Stale Data

```
Stock snapshot_date is old (not today)?
├── Cron didn't run → check: crontab -l
├── Stock pull failed → check /opt/openclaw/logs/stock_latest_status.json
├── TRUNCATE succeeded but INSERT failed → table is EMPTY (critical!)
│   └── Re-run immediately: /opt/openclaw/venv/bin/python pull_accurate_stock.py {entity}
└── API returned empty → Accurate Online might be in maintenance
```

### 7.4 Downstream View Broken After Change

```
sales_with_product returns error after fact_sales_unified change?
├── Column removed → sales_with_product references it by name
│   └── Recreate sales_with_product view to match new columns
├── Column renamed → same issue
│   └── Either rename back or update downstream
└── Column type changed → implicit cast may fail
    └── Add explicit CAST in the view definition
```

---

## 8. Historical Fixes Log

Track significant database fixes here for future reference.

### 2026-02-13: Sales Double-Counting Fix

**Problem:** `fact_sales_unified` had no `DISTINCT ON` dedup. The 3-day rolling sales pull created overlapping snapshots, causing 4,179 duplicate rows (+Rp 605M overcounted).

**Impact:** Every agent query through `core.sales_with_product` returned inflated sales numbers.

**Fix applied:**
1. Recreated `core.fact_sales_unified` with `DISTINCT ON (nomor_invoice, kode_produk, tanggal)` dedup, `ORDER BY snapshot_date DESC`
2. Row count: 1,551,651 → 1,547,472 (4,179 duplicates removed)

### 2026-02-13: Multi-Line Invoice Fix (line_number)

**Problem:** `pull_accurate_sales.py` failed on DDD with `duplicate key` error. Event Wilbex invoice had same product codes at different price points (16 duplicate key groups).

**Fix applied:**
1. Added `line_number` column (integer, default 1) to all 3 sales tables
2. Dropped old 4-column unique constraints, created new 5-column constraints including `line_number`
3. Updated `flatten_invoice()` to track `product_line_counter` per invoice and assign sequential `line_number`
4. Updated INSERT SQL to include `line_number` in column list, VALUES, and ON CONFLICT clause
5. Updated `fact_sales_unified` DISTINCT ON to include `line_number`
6. Re-ran DDD pull: 1,723 records loaded successfully (including 116-line Event Wilbex invoice)

**Verification:** 0 duplicate groups, Event Wilbex invoice shows `line_number` 1 and 2 for multi-line products.

---

## 9. When to Use This Skill

**Use this skill when:**
- Debugging ETL failures (sales/stock pull errors)
- Modifying database schema (adding columns, changing constraints)
- Recreating or modifying views
- Investigating data integrity issues (duplicates, missing data, wrong counts)
- Understanding how the data pipeline works internally
- Performing any `ALTER TABLE`, `CREATE VIEW`, or constraint operation

**Use `zuma-data-analyst-skill` instead when:**
- Querying data for analysis or reports
- Building SQL queries for business questions
- Understanding what columns mean from a business perspective
- Creating mart tables for ad-hoc analysis

---

**Status:** Complete
**Created:** 13 Feb 2026
**Covers:** Raw table schemas (columns, constraints), view architecture (dedup logic), ETL pipeline (sales/stock scripts, cron, credentials), common fix patterns (dedup, constraints, columns, views), maintenance SQL templates, troubleshooting guide, historical fixes log
