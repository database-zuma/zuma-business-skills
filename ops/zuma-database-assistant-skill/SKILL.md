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

## 2. Raw Tables — Schema Overview

All raw tables live in the `raw` schema. Each entity (DDD, MBB, UBB, LJBB) has separate tables with identical structure per data type.

> Full column-level definitions: see `database-column-reference.md`

### Sales Tables (`raw.accurate_sales_{ddd,mbb,ubb}`)

20 columns. Key columns: `tanggal` (date), `nomor_invoice`, `kode_produk` (= kode_besar), `kuantitas`, `harga_satuan`, `total_harga`, `snapshot_date`, `line_number`.

**Unique constraint:** `UNIQUE (nomor_invoice, kode_produk, tanggal, snapshot_date, line_number)`

### Stock Tables (`raw.accurate_stock_{ddd,ljbb,mbb,ubb}`)

10 columns. Key columns: `kode_barang` (= kode_besar), `nama_gudang`, `kuantitas`, `snapshot_date`.

**Note:** Stock uses `kode_barang`, NOT `kode_produk` (historical naming inconsistency).

### Other Raw Tables

| Table | Description |
|-------|-------------|
| `raw.iseller_sales` | POS sales from iSeller (evolving structure) |
| `raw.iseller_2023` / `_2025` / `_2026` | Historical iSeller POS data by year |
| `raw.accurate_item_transfer_{ddd,ljbb,mbb,ubb}` | Inter-warehouse stock transfers (4 tables, per-entity) |
| `raw.accurate_purchase_invoice_{ddd,ljbb,mbb,ubb}` | Purchase invoices from suppliers (4 tables) |
| `raw.accurate_purchase_order_{ddd,ljbb,mbb,ubb}` | Purchase orders to suppliers (4 tables) |
| `raw.accurate_logistics_{ddd,ljbb,mbb,ubb}` | Logistics/shipping records (4 tables) |
| `raw.load_history` | ETL audit trail — every data pull logged here |
---

## 3. View Architecture — How Deduplication Works

### 3.1 The Snapshot Overlap Problem (Sales)

Sales ETL pulls a **3-day rolling window** daily. This means the same invoice can appear in multiple snapshots:

```
Day 1 pull: [Jan 10, Jan 11, Jan 12] → snapshot_date = Jan 12
Day 2 pull: [Jan 11, Jan 12, Jan 13] → snapshot_date = Jan 13
Day 3 pull: [Jan 12, Jan 13, Jan 14] → snapshot_date = Jan 14
```

Jan 12 data exists in ALL THREE snapshots. Without dedup, queries return 3x the real sales.

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

### 3.3 `core.fact_stock_unified` — Stock View

Stock uses a completely different strategy — **no overlap problem** because stock ETL does `TRUNCATE` + fresh insert (only 1 snapshot exists at any time).

**Actual row counts (25 Feb 2026):** DDD ~1.39M | MBB ~209K | UBB ~52K | LJBB ~17K | **Total ~1.66M**

```sql
-- Pattern repeated for DDD, LJBB, MBB, UBB (UNION ALL)
SELECT ... FROM raw.accurate_stock_{entity} s
LEFT JOIN core.dim_product p ON TRIM(LOWER(s.kode_barang)) = p.kode_besar
LEFT JOIN core.dim_warehouse w ON w.warehouse_code = '{ENTITY}'
WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM raw.accurate_stock_{entity})
```

**Key detail:** `WHERE snapshot_date = MAX(snapshot_date)` — safety net even though TRUNCATE means only 1 snapshot.
### 3.4 Downstream Views

| View | Reads From | Adds |
|------|-----------|------|
| `core.sales_with_product` (48 cols, ~1.55M rows) | `fact_sales_unified` | Product enrichment (kodemix, hpprsp), store enrichment (portal.store), `is_intercompany` flag |
| `core.stock_with_product` (38 cols, **~1.66M rows**) | `fact_stock_unified` | Product enrichment, warehouse/capacity enrichment |
| `core.sales_with_store` | `fact_sales_unified` | Store enrichment only (legacy, less enriched) |

### 3.5 Additional Core Objects

| Object | Type | Description |
|--------|------|-------------|
| `core.item_transfer` | view | Inter-warehouse stock transfer view |
| `core.iseller` | view | iSeller POS data view |
| `core.bm_metrics` | **table** | Branch Manager performance metrics |
| `core.fact_sales_ddd` / `_mbb` / `_ubb` | views | Per-entity sales views |
| `core.fact_stock_ddd` / `_ljbb` / `_mbb` / `_ubb` | views | Per-entity stock views |

### 3.7 Portal Tables (Reference Data)

| Table | Rows | Description |
|-------|------|-------------|
| `portal.kodemix` | ~5,481 | Product bridge table (kode_besar → kode_mix) |
| `portal.hpprsp` | — | Pricing (HPP, price_taq, rsp) |
| `portal.store` | — | Store master (name, branch, area, category) |
| `portal.stock_capacity` | — | Store/warehouse capacity |
| `portal.temp_portal_plannogram` | ~2,568 | **DEFAULT planogram source** (~11 Jatim stores) |
| `portal.store_coordinates` | ~66 | Store GPS coordinates |
| `portal.store_display_options` | ~509 | Store display hook/shelf options |
| `portal.store_monthly_target` | ~218 | Monthly sales targets per store |
| `portal.store_name_map` | ~65 | Store name aliases between systems |

### 3.8 Mart Schema

**UNSTABLE** — tables created/dropped per request. Current semi-permanent: `mart.purchasing_monthly`, `mart.purchasing_top10_monthly`.

### 3.6 Dimension Views
> Full output column lists for all views: see `database-column-reference.md`

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
5. `flatten_invoice()` — converts API response to flat rows, assigns `line_number` per (invoice, product) pair
6. UPSERT to PostgreSQL: `INSERT ... ON CONFLICT (nomor_invoice, kode_produk, tanggal, snapshot_date, line_number) DO UPDATE`
7. Log to `raw.load_history`
8. On failure: save CSV fallback to `/opt/openclaw/scripts/{ENTITY}_sales_{date}.csv`

**Usage:**
```bash
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_sales.py ddd          # last 3 days
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_sales.py ddd --days 5  # custom days
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_sales.py all            # all entities
/opt/openclaw/venv/bin/python /opt/openclaw/scripts/pull_accurate_sales.py ddd --dry-run  # preview
```

### 4.3 Stock ETL: `pull_accurate_stock.py`

**Location:** `/opt/openclaw/scripts/pull_accurate_stock.py`

**Flow:** Same API auth as sales → Fetch all items → **TRUNCATE** target table → INSERT fresh → always 1 snapshot.

**Critical difference from sales:** Stock does TRUNCATE + INSERT. There is never more than 1 snapshot_date in stock tables. This is why stock has no dedup problem.

### 4.4 Cron Wrappers & Status Files

Cron wrappers run all entities sequentially and write status files:

- **Sales log:** `/opt/openclaw/logs/sales_{YYYYMMDD}.log`
- **Sales status:** `/opt/openclaw/logs/sales_latest_status.json` (`overall`: success / partial_error / error)
- **Stock status:** `/opt/openclaw/logs/stock_latest_status.json` (same format)

> Status file format and `flatten_invoice()` internals: see `database-column-reference.md`

### 4.5 Entity Credential Files

Each entity has a `.env` file in `/opt/openclaw/scripts/`:

| File | Entity | API Host |
|------|--------|----------|
| `.env.ddd` | DDD (PT Dream Dare Discover) | `zeus.accurate.id` |
| `.env.mbb` | MBB (CV Makmur Besar Bersama) | `iris.accurate.id` |
| `.env.ubb` | UBB (CV Untung Besar Bersama) | `zeus.accurate.id` |

Each contains: `ACCURATE_API_TOKEN` and `ACCURATE_SIGNATURE_SECRET`

PostgreSQL credentials are in `/opt/openclaw/scripts/.env` (shared): `PG_HOST`, `PG_PORT`, `PG_DATABASE`, `PG_USER`, `PG_PASSWORD`

**IMPORTANT:** Always use `/opt/openclaw/venv/bin/python`, NOT `python3`. The system Python doesn't have the required packages (pandas, psycopg2, etc.).

---

## 5. Common Fix Patterns

> Detailed SQL and step-by-step procedures: see `database-troubleshooting.md`

| Issue | Quick Fix |
|-------|-----------|
| Sales double-counting | Recreate `fact_sales_unified` with `DISTINCT ON` dedup |
| Multi-line invoice constraint violation | Check `line_number` logic in `flatten_invoice()` |
| Adding a column to sales tables | Add to ALL 3 tables + update constraint + update view + update ETL script |
| Recreating a view | `CREATE OR REPLACE VIEW` — record row count before & after |
| Constraint management | `pg_constraint` to inspect, `ALTER TABLE` to modify |
| Re-running failed ETL | Check status JSON → check log → re-run with venv python |

---

## 6. Essential Maintenance SQL

### Check for Duplicate Sales (Dedup Health)

```sql
-- Should return 0 rows if dedup is working
SELECT nomor_invoice, kode_besar, transaction_date, line_number, COUNT(*) AS occurrences
FROM core.fact_sales_unified
GROUP BY 1, 2, 3, 4
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 20;
```

### Verify View Row Counts Match

```sql
SELECT
    (SELECT COUNT(*) FROM core.fact_sales_unified) AS fact_rows,
    (SELECT COUNT(*) FROM core.sales_with_product) AS swp_rows,
    (SELECT COUNT(*) FROM core.fact_sales_unified) -
    (SELECT COUNT(*) FROM core.sales_with_product) AS difference;
-- difference MUST be 0
```

### Check Data Freshness

```sql
-- Latest sales per entity
SELECT source_entity, MAX(transaction_date) AS latest_sale, MAX(snapshot_date) AS latest_snapshot
FROM core.fact_sales_unified
GROUP BY 1 ORDER BY 1;

-- Latest ETL runs
SELECT entity, data_type, status, rows_loaded, loaded_at
FROM raw.load_history
ORDER BY loaded_at DESC LIMIT 10;
```

### Get View Definition

```sql
SELECT pg_get_viewdef('core.fact_sales_unified'::regclass, true);
SELECT pg_get_viewdef('core.sales_with_product'::regclass, true);
```

> More maintenance SQL (snapshot overlap, kodemix match rates, table sizes, inventory): see `database-troubleshooting.md`

---

## 7. Troubleshooting — ETL Failure Decision Tree

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

> More troubleshooting trees (view row counts, stale stock, downstream views): see `database-troubleshooting.md`

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

## Reference Files

| File | Contents |
|------|----------|
| `database-column-reference.md` | Full column-level definitions for raw tables (sales 20 cols, stock 10 cols), unique constraint details, view output columns, ETL script internals |
| `database-troubleshooting.md` | Detailed fix procedures (dedup, constraints, columns, views), all maintenance SQL templates, troubleshooting decision trees |

---

**Status:** Complete
**Created:** 13 Feb 2026
**Updated:** 25 Feb 2026 — Added missing raw tables (item_transfer, logistics, purchase_invoice, purchase_order × 4 entities + 3 iseller), portal tables (temp_portal_plannogram, store_coordinates, store_display_options, store_monthly_target, store_name_map), core views (item_transfer, iseller, bm_metrics, per-entity fact views), mart tables, and corrected stock row counts (total ~1.66M, up from ~142K documented previously)
**Covers:** Raw table schemas (columns, constraints), view architecture (dedup logic), ETL pipeline (sales/stock scripts, cron, credentials), common fix patterns (dedup, constraints, columns, views), maintenance SQL templates, troubleshooting guide, historical fixes log, all 5 schemas (raw, portal, core, mart, public)
