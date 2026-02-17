---
name: zuma-data-analyst-skill
description: Zuma Indonesia data analyst skill — database querying, SQL templates, and business analysis. Covers PostgreSQL database on VPS (schemas, tables, views, ETL), standardized SQL query templates with mandatory filters and column conventions, connection details, and data analysis methodology for sales, stock, and product performance. Use when analyzing Zuma business data, querying the database, building reports, or running standardized SQL queries.
user-invocable: false
---

# Zuma Data Operations & Analysis

You have access to Zuma Indonesia's centralized PostgreSQL data warehouse. Use this knowledge to connect to the database, understand the schema structure, write correct SQL queries, and perform business-accurate data analysis.

**Combine with other Zuma skills for full context:**
- `zuma-sku-context` — Product categorization, versioning, Kode Mix, assortment, tiering
- `zuma-branch` — Store network, branches, areas, store categories
- `zuma-warehouse-and-stocks` — Warehouse operations, RO system, stock stages
- `zuma-company-context` — Brand identity, entity structure, data sources

---

## 1. Database Connection

### VPS Server

| Field | Value |
|-------|-------|
| **Host** | `76.13.194.120` |
| **Port** | `5432` |
| **Database** | `openclaw_ops` |
| **User** | `openclaw_app` |
| **Password** | `Zuma-0psCl4w-2026!` |
| **SSH Access** | `ssh root@76.13.194.120` |

### Connection Methods

**Direct PostgreSQL (from any tool/app):**
```
postgresql://openclaw_app:Zuma-0psCl4w-2026!@76.13.194.120:5432/openclaw_ops
```

**psql CLI (from VPS via SSH):**
```bash
ssh root@76.13.194.120
psql -U openclaw_app -d openclaw_ops
```

**psql CLI (remote with password):**
```bash
PGPASSWORD='Zuma-0psCl4w-2026!' psql -h 76.13.194.120 -U openclaw_app -d openclaw_ops
```

**Python (psycopg2 + pandas) — used by all Zuma scripts:**
```python
import psycopg2
import pandas as pd

DB = dict(host="76.13.194.120", port=5432, dbname="openclaw_ops",
          user="openclaw_app", password="Zuma-0psCl4w-2026!")

conn = psycopg2.connect(**DB)
df = pd.read_sql("SELECT * FROM core.sales_with_product LIMIT 10", conn)
conn.close()
```

**Looker Studio / BI Tools:**
- Use host, port, database, user, password above
- For Looker Studio: connect to `public` schema (mirrors of core views are there)
- Custom Query mode supports any schema

### Connection Notes
- VPS is always on (dedicated server, not serverless)
- No SSL required for connections from trusted networks
- `openclaw_app` has read/write on all schemas
- For heavy analytical queries, prefer off-peak hours (outside 03:00-06:00 WIB when ETL runs)

---

## 1.5. Product Analysis — NEW Unified Approach (2026-02-15)

**⭐ PRIMARY REFERENCE:** `templates/product-analysis-unified.md`

For ALL product/SKU performance queries, use the unified template which covers:
- **Decision tree:** When to use `mart.sku_portfolio` vs `core.sales_with_product`
- **Query framework:** WHAT/WHERE/WHEN pattern for structured queries
- **Column mapping:** New (mart) vs old (core) column equivalents
- **WhatsApp formatting:** Compact list vs detailed blocks
- **Auto-flags:** 🔥 stockout, 🐌 overstock, ⚠️ negative WH, 📉 YoY drop

**Default data source:** `mart.sku_portfolio_size` (use for 90% of product queries — most granular, can aggregate up)

**Key Rule:**
- **NATIONAL aggregate?** → Use `mart.sku_portfolio_size` (107 columns, size-level, pre-computed monthly, YoY)
- **Store-level breakdown?** → Use `core.sales_with_product` (has matched_store_name)
- **Custom date range?** → Use `core.sales_with_product` (flexible WHERE clause)
- **Article-level only (no size)?** → Can use `mart.sku_portfolio` (101 columns) OR aggregate `sku_portfolio_size` by kodemix

See section on `mart.*` schema below for full `sku_portfolio` column reference.

---

## 2. Schema Architecture

```
openclaw_ops database
├── raw          — Source data from Accurate Online API (auto-updated daily by cron)
├── portal       — Reference/master data from Google Sheets (manually maintained)
├── core         — Transformed views joining raw + portal (auto-computed, read-only)
├── mart         — Ad-hoc analysis tables (created on demand per user request, always changing)
└── public       — Convenience mirrors of core views (for Looker Studio / BI tools)
```

### Schema Stability

| Schema | Stability | Update Frequency | Who Maintains |
|--------|-----------|------------------|---------------|
| `raw` | Stable structure, data changes daily | Auto: cron jobs pull from Accurate API daily | Cron scripts on VPS |
| `portal` | Stable structure, data changes occasionally | Manual: updated when master data changes in Google Sheets | User (Wayan) via N8N or manual |
| `core` | Stable structure (views) | Auto: views recompute on query | Views auto-reflect raw + portal changes |
| `mart` | **UNSTABLE** — tables come and go | On demand | Created per analysis request, may be dropped/recreated |
| `public` | Mirrors core | Auto: views reference core views | Mirrors update when core updates |

---

## 3. Schema: `raw` (Source Data)

Raw data pulled from Accurate Online API. Each entity (DDD, MBB, UBB, LJBB) has separate tables.

### Sales Tables

| Table | Entity | Size | Rows | Date Range | Description |
|-------|--------|------|------|------------|-------------|
| `raw.accurate_sales_ddd` | DDD | ~563 MB | ~1.3M | 2022-01-01 → present | Main entity retail + wholesale sales |
| `raw.accurate_sales_mbb` | MBB | ~101 MB | ~197K | 2024-04-18 → present | Online marketplace sales |
| `raw.accurate_sales_ubb` | UBB | ~27 MB | ~41K | 2023-02-11 → present | Wholesale + consignment sales |

**Sales table columns (all 3 tables share same structure):**

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial | Auto-increment PK |
| `source_entity` | text | 'DDD', 'MBB', or 'UBB' |
| `nomor_invoice` | text | Invoice number from Accurate |
| `transaction_date` | date | Sale date |
| `kode_barang` / `kode_produk` | text | = `kode_besar` (article+size code from Accurate) |
| `nama_barang` | text | Product name from Accurate |
| `quantity` | numeric | Pairs sold |
| `unit_price` | numeric | Selling price per pair |
| `total_amount` | numeric | quantity * unit_price |
| `cost_of_goods` | numeric | BPP/COGS (may be 0 from API, backfilled from cookie export) |
| `warehouse_code` | text | Which warehouse fulfilled the sale |
| `snapshot_date` | date | When this data was pulled |
| `loaded_at` | timestamptz | ETL load timestamp |

### Stock Tables

| Table | Entity | Description |
|-------|--------|-------------|
| `raw.accurate_stock_ddd` | DDD | ~142K rows, latest snapshot only (overwrites daily) |
| `raw.accurate_stock_ljbb` | LJBB | ~128 rows (Baby & Kids PO receiving entity) |
| `raw.accurate_stock_mbb` | MBB | Minimal/empty (online entity, stock managed elsewhere) |
| `raw.accurate_stock_ubb` | UBB | Minimal/empty (wholesale entity) |

**Stock table columns:**

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial | Auto-increment PK |
| `source_entity` | text | 'DDD', 'LJBB', 'MBB', or 'UBB' |
| `kode_barang` / `kode_produk` | text | = `kode_besar` |
| `nama_barang` | text | Product name |
| `nama_gudang` | text | Warehouse/store name in Accurate (e.g., "Warehouse Pusat", "Zuma Tunjungan Plaza") |
| `quantity` | numeric | Current stock in pairs |
| `unit_price` | numeric | Unit cost |
| `warehouse_code` | text | Entity warehouse code |
| `snapshot_date` | date | Date of this stock snapshot |
| `loaded_at` | timestamptz | ETL load timestamp |

### Other Raw Tables

| Table | Description |
|-------|-------------|
| `raw.iseller_sales` | POS sales from iSeller (real-time retail). Structure may change as integration evolves. |
| `raw.load_history` | ETL audit trail — logs every data pull with entity, table, row counts, timestamps |

---

## 4. Schema: `portal` (Reference/Master Data)

Manually maintained reference tables synced from Google Sheets. These are the "bridge" tables that enrich raw data with business classifications.

### `portal.kodemix` (~5,464 rows)

**The critical product bridge table.** Maps version-specific Accurate codes to unified Kode Mix codes.

| Column | Type | Description |
|--------|------|-------------|
| `no_urut` | integer | Sort order (lower = more recent/preferred) |
| `kode_besar` | text | Accurate code (article+size), **MIXED CASE** |
| `kode` | text | Accurate code (article only, kode kecil) |
| `kode_mix` | text | Unified article code (version-agnostic) |
| `kode_mix_size` | text | Unified article+size code (version-agnostic) |
| `article` | text | Article name (e.g., "JET BLACK") |
| `version` | text | V0, V1, V2, V3, V4 |
| `tipe` | text | Product type (Fashion / Jepit) |
| `gender` | text | Men, Ladies, Kids, Junior, etc. |
| `seri` | text | Series in Indonesian |
| `series` | text | Series in English (Classic, Slide, Airmove, etc.) |
| `color` | text | Color name |
| `ukuran` | text | Size |
| `nama_variant` | text | Full variant name |
| `size` | text | Size value |
| `group_warna` | text | Color group |
| `assortment` | text | Size assortment pattern (e.g., "1-2-2-3-2-2") |
| `count_by_assortment` | integer | Pairs per box for this size |
| `v` | text | Version indicator |
| `status` | text | 'Aktif' or 'Tidak Aktif' (DO NOT filter on this for joins — see Critical Rules) |
| `tier_lama` | text | Previous tier |
| `tier_baru` | text | Current tier |
| `season` | text | Season designation |
| `product_status` | text | Product lifecycle status |

### `portal.hpprsp` (Pricing)

| Column | Type | Description |
|--------|------|-------------|
| `kode` | text | Article code (kode kecil) |
| `nama_barang` | text | Product name |
| `harga_beli` | numeric | Purchase price (HPP) |
| `price_taq` | numeric | Price tag |
| `rsp` | numeric | Recommended selling price |

### `portal.store` (Store Master)

| Column | Type | Description |
|--------|------|-------------|
| `nama_accurate` | text | Store name as it appears in Accurate, **MIXED CASE** |
| `branch` | text | Branch (Jatim, Jakarta, Bali, Sumatra, Sulawesi, Batam) |
| `area` | text | Area (Jatim, Jakarta, Bali 1, Bali 2, Bali 3, Lombok, etc.) |
| `category` | text | RETAIL, NON-RETAIL, EVENT |
| `stock_filter` | text | Stock filter category |
| `as_name` | text | Area Supervisor name |
| `bm_name` | text | Branch Manager name |

### `portal.stock_capacity` (Warehouse/Store Capacity)

| Column | Type | Description |
|--------|------|-------------|
| `stock_location` | text | Store/warehouse name, **MIXED CASE** |
| `branch` | text | Branch |
| `area` | text | Area |
| `category` | text | Category |

---

## 5. Schema: `core` (Transformed Views)

All objects in `core` are **views** (not tables). They auto-recompute when queried.

### Dimension Views

| View | Source | Description |
|------|--------|-------------|
| `core.dim_product` | portal.kodemix + portal.hpprsp | Deduplicated product dimension (DISTINCT ON kode_besar) |
| `core.dim_store` | portal.store | Store dimension |
| `core.dim_warehouse` | Hardcoded mapping | Entity code → name mapping (DDD, LJBB, MBB, UBB) |
| `core.dim_date` | Generated | Date dimension (date_key, year, month, day, quarter, etc.) |

### Fact Views

| View | Source | Description |
|------|--------|-------------|
| `core.fact_sales_unified` | UNION ALL of raw.accurate_sales_ddd + mbb + ubb | All sales from all entities, unified. Adds `matched_kode_besar` (TRIM LOWER) and `matched_store_name` (TRIM LOWER) |
| `core.fact_stock_unified` | UNION ALL of raw.accurate_stock_ddd + ljbb + mbb + ubb | All stock from all entities, latest snapshot. Adds `matched_kode_besar` and matched store name |

### Main Analysis Views (USE THESE)

#### `core.sales_with_product` (46 columns) — PRIMARY SALES VIEW

**This is your go-to view for ALL sales analysis.** Joins fact_sales_unified with portal.kodemix (product enrichment), portal.hpprsp (pricing), and portal.store (store enrichment).

| Column Group | Columns |
|-------------|---------|
| **Transaction** | source_entity, nomor_invoice, transaction_date, date_key, kode_besar, matched_kode_besar, kode, store_name_raw, matched_store_name, nama_barang, nama_pelanggan, is_intercompany, quantity, unit_price, total_amount, cost_of_goods, vendor_price, dpp_amount, tax_amount, warehouse_code, snapshot_date, loaded_at |
| **Product IDs** | kode_mix, kode_mix_size, article, version |
| **Product Attrs** | product_name, product_type, tipe, series, gender, tier, color, assortment, nama_variant, size, group_warna |
| **Pricing** | harga_beli, price_taq, rsp |
| **Store** | branch, area, store_category, stock_filter, as_name, bm_name |
| **Technical** | v, count_by_assortment |

**Row count:** ~1.55M rows (48 columns, matches fact_sales_unified exactly, no duplicates)
**Kodemix match rate:** ~94.1% (unmatched = kode_besar not in portal.kodemix)
**Store match rate:** ~86.2%

#### `core.stock_with_product` (38 columns) — PRIMARY STOCK VIEW

**This is your go-to view for ALL stock/inventory analysis.**

| Column Group | Columns |
|-------------|---------|
| **Stock** | source_entity, snapshot_date, date_key, kode_besar, matched_kode_besar, kode, nama_gudang, quantity, unit_price, vendor_price, warehouse_code, loaded_at |
| **Product IDs** | kode_mix, kode_mix_size, article, version |
| **Product Attrs** | product_name, product_type, tipe, series, gender, tier, color, ukuran, assortment, season, product_status, nama_variant, size, group_warna |
| **Pricing** | harga_beli, price_taq, rsp |
| **Warehouse** | gudang_branch, gudang_area, gudang_category |
| **Technical** | v, count_by_assortment |

**Row count:** ~142K rows (matches fact_stock_unified exactly, no duplicates)
**Kodemix match rate:** ~99.9%
**Capacity match rate:** ~96.4%

### Legacy / Supporting Views

| View | Description |
|------|-------------|
| `core.sales_with_store` | Older sales view (less enriched, kept for backward compat) |
| `core.fact_sales_ddd` / `_mbb` / `_ubb` | Per-entity sales views |
| `core.fact_stock_ddd` / `_ljbb` / `_mbb` / `_ubb` | Per-entity stock views |

---

## 6. Schema: `mart` (Ad-hoc Analysis & Daily Automation)

**New as of 2026-02-15:** This schema now contains **permanent daily automation tables** alongside ad-hoc analysis tables.

### 6.1. Permanent Daily Tables (Automated via Cron)

#### `mart.sku_portfolio` — Article-Level Fallback

**Purpose:** All-in-one comprehensive SKU analysis table (article-level, national aggregate only)
**Updated:** Daily (post Stock Pull + Sales Pull)
**Rows:** ~598 (all articles from kodemix)
**Columns:** 101 active + 2 future (PO columns)

**Use when:** Already have article-level aggregates or prefer simpler structure (no size breakdown)

**Column Groups:**
1. **ID/Base (7 cols):** id, kodemix, gender, series, color, tipe, tier
2. **Sales (83 cols):** Monthly YoY (72 cols: 6×12 months), year totals (6), labels (2), mix/avg (3)
3. **Stock (13 cols):** wh_pusat, wh_bali, wh_jkt, wh_total, stok_toko, stok_online, stok_unlabel, stok_global, to_wh, to_total

**Key Features:**
- Auto-detect year (current_year_label, last_year_label) — no hardcoded years
- YoY comparison (var_year_qty, var_year_rp in %)
- Monthly trends (now_jan vs last_jan, now_feb vs last_feb, etc.)
- Turnover metrics (to_total = months of coverage, critical for PO decisions)
- Sales mix % (current_sales_mix, last_sales_mix)

**Example Query:**
```sql
SELECT kodemix, gender, series, color, tier,
       current_year_qty, last_year_qty, var_year_qty,
       current_sales_mix, to_total, stok_global
FROM mart.sku_portfolio
WHERE tier = '1'
ORDER BY current_year_qty DESC
LIMIT 10;
```

**Limitations:**
- **NATIONAL only** — no store/area/branch breakdown
- **Article level only** — no size breakdown
- **Fixed time periods** — current year vs last year (for custom dates, use core views)

#### `mart.sku_portfolio_size` ⭐ PRIMARY for Product Analysis ⚠️ CRITICAL QUERY RULE

**Purpose:** Most granular SKU analysis table (size-level, can aggregate to article-level)
**Updated:** Snapshot table — rebuild daily/periodically
**Rows:** 5,220 (all SKU versions × sizes)
**Columns:** 107 (11 ID/Base + 83 Sales + 13 Stock)

**Use this table for 90% of product queries!** (Replaces `mart.sku_portfolio` as default since 2026-02-17)

**Column Groups:**
1. **ID/Base (11 cols):** id, kode_besar (PK UNIQUE), kode_kecil, kode_mix_size, kodemix, gender, series, color, tipe, tier, size
2. **Sales (83 cols):** Same as sku_portfolio (monthly YoY + totals + mix)
3. **Stock (13 cols):** Same as sku_portfolio (warehouse + channel breakdown)

**⚠️ CRITICAL ANALYSIS RULE (2026-02-17):**

**ALWAYS aggregate by `kodemix` (or `kode_mix_size`) — NEVER filter by single `kode_besar`!**

**Why:**
- One article has **multiple kode_besar versions** over time (M1SPV201, M1SP01, M1SPV101, SJ1A)
- Kode lama → kode baru evolution (same product, different codes)
- `kode_besar` = PRIMARY KEY for data integrity (prevent duplicates)
- **Business analysis** = SUM across ALL versions (ignore kode version differences)

**Wrong vs Right Query:**
```sql
-- ❌ WRONG (only 1 version, incomplete data):
SELECT current_year_qty, current_year_rp
FROM mart.sku_portfolio_size
WHERE kode_besar = 'M1SPV201Z42';  -- Only gets M1SPV201 version!

-- ✅ CORRECT (all versions combined):
SELECT 
    kodemix, size,
    SUM(current_year_qty) AS total_qty,
    SUM(current_year_rp) AS total_rp,
    SUM(stok_global) AS total_stock
FROM mart.sku_portfolio_size
WHERE kodemix = 'M1SP0PV201'  -- Gets ALL versions: M1SPV201, M1SP01, M1SPV101, SJ1A
GROUP BY kodemix, size
ORDER BY size;
```

**Example Use Case:**
- User asks: "Penjualan MEN STRIPE BLACK BLUE RED per size"
- Steps:
  1. Identify kodemix: `M1SP0PV201` (from portal.kodemix or previous queries)
  2. Query: `WHERE kodemix = 'M1SP0PV201' GROUP BY size`
  3. Result: Size 42 = SUM(M1SPV201Z42 + M1SP01Z42 + M1SPV101Z42) = true article performance

**Key Difference from sku_portfolio:**
- **Grain:** kode_besar (with size) vs kodemix (article, no size)
- **Analysis pattern:** Both use `kodemix` for business queries (ignore versions)
- **When to use:** Need size breakdown → sku_portfolio_size | Article-level only → sku_portfolio

**Technical Notes:**
- Case-sensitivity fix: All CTEs use `UPPER(kode_besar)` to ensure JOIN success
- Sales source: `core.sales_with_product` (lowercase kode_besar)
- Stock source: `core.stock_with_product` (lowercase kode_besar)
- Portal.kodemix: UPPERCASE kode_besar

#### `mart.ff_fa_fs_daily`

**Purpose:** Daily Fill Factor/Article/Stock metrics per store
**Updated:** Daily 03:00 WIB (post Stock Pull)
**Coverage:** Currently Jatim stores (11 stores), expanding to all branches

**Columns:** report_date, branch, store_label, ff, fa, fs

**Targets:** FF ≥70%, FA ≥90%, FS ≥80%

#### `mart.stock_opname_l2_daily`

**Purpose:** Daily stock vs sales reconciliation (detect shrinkage/theft)
**Updated:** Daily 05:00 WIB (post Sales Pull)
**Coverage:** 56 retail stores × 3 gender groups = 168 rows/day

**Key Columns:** snapshot_date, store_name, gender_group, stock_qty, sales_qty, prev_stock_qty, expected_stock_qty, selisih (discrepancy), selisih_pct

**Alert:** selisih < 0 = potential shrinkage/theft ⚠️

### 6.2. Ad-hoc Analysis Tables

**Tables in this section change based on user requests.** Do not assume any specific ad-hoc table exists — always check first:

```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'mart' 
  AND table_name NOT IN ('sku_portfolio', 'ff_fa_fs_daily', 'stock_opname_l2_daily');
```

**Common ad-hoc patterns:**
- `mart.monthly_sales_summary` — custom monthly aggregations
- `mart.store_performance` — store-level KPIs
- `mart.tier_analysis` — tier breakdown analysis

**Creating ad-hoc tables:** Always use `CREATE TABLE mart.{name} AS SELECT ...` from core views.

---

## 7. Schema: `public` (BI Tool Mirrors)

Convenience views that mirror core views. Exist because Looker Studio and some BI tools can only see the `public` schema without custom queries.

| View | Mirrors |
|------|---------|
| `public.sales_with_product` | → `core.sales_with_product` |
| `public.stock_with_product` | → `core.stock_with_product` |

---

## 8. ETL / Auto-Update Schedule

Cron jobs on the VPS pull data from Accurate Online API daily.

| Time (WIB) | Job | Description |
|-------------|-----|-------------|
| **02:00** | Database backup | Full `pg_dump` of `openclaw_ops` |
| **03:00** | Stock pull | All 4 entities (DDD, LJBB, MBB, UBB) — overwrites stock tables with latest snapshot |
| **05:00** | Sales pull | 3 entities (DDD, MBB, UBB) — incremental, pulls last 3 days to catch late-arriving invoices |

**No LJBB sales pull** — LJBB is a PO receiving entity only, no direct sales.

**ETL audit trail:**
```sql
SELECT * FROM raw.load_history ORDER BY loaded_at DESC LIMIT 20;
```

**iSeller data:** Currently minimal (`raw.iseller_sales`). Integration still evolving — structure may change.

---

## 9. CRITICAL Query Rules

### Rule 1: ALWAYS use TRIM(LOWER()) for portal joins

Raw tables store codes in lowercase. Portal tables store codes in mixed case. **Every join to portal must normalize:**

```sql
-- CORRECT
LEFT JOIN portal.kodemix km ON TRIM(LOWER(km.kode_besar)) = s.matched_kode_besar

-- WRONG (will miss matches due to case mismatch)
LEFT JOIN portal.kodemix km ON km.kode_besar = s.kode_besar
```

### Rule 2: ALWAYS deduplicate portal tables in joins

portal.kodemix has multiple rows per kode_besar (one per version: V0, V1, V2...). Joining directly causes row inflation (duplicates).

```sql
-- CORRECT: Deduplicated subquery
LEFT JOIN (
    SELECT DISTINCT ON (TRIM(LOWER(kode_besar)))
        TRIM(LOWER(kode_besar)) AS kode_besar,
        kode_mix, kode_mix_size, article, version, tipe,
        nama_variant, size, count_by_assortment, group_warna, v
    FROM portal.kodemix
    ORDER BY TRIM(LOWER(kode_besar)), no_urut
) km ON s.matched_kode_besar = km.kode_besar

-- CORRECT: Deduplicated store
LEFT JOIN (
    SELECT DISTINCT ON (TRIM(LOWER(nama_accurate)))
        TRIM(LOWER(nama_accurate)) AS nama_accurate,
        branch, area, category, stock_filter, as_name, bm_name
    FROM portal.store
    ORDER BY TRIM(LOWER(nama_accurate))
) st ON s.matched_store_name = st.nama_accurate

-- WRONG (causes row duplication)
LEFT JOIN portal.kodemix km ON s.matched_kode_besar = TRIM(LOWER(km.kode_besar))
```

### Rule 3: NEVER filter portal.kodemix by status

Do NOT add `WHERE status = 'Aktif'` or any status filter when joining kodemix. The user explicitly requires ALL products to be matched regardless of active/discontinued status.

```sql
-- CORRECT: No status filter
FROM portal.kodemix

-- WRONG: Excludes ~50% of kodemix rows
FROM portal.kodemix WHERE status = 'Aktif'
```

### Rule 4: ALWAYS verify row counts after creating views/tables

After any view or table creation that involves joins, verify no row inflation:

```sql
-- Check: view rows must equal fact table rows
SELECT COUNT(*) FROM core.fact_sales_unified;   -- e.g., 1,545,304
SELECT COUNT(*) FROM core.sales_with_product;    -- must be exactly 1,545,304
```

### Rule 5: Use core views, not raw tables

For analysis, ALWAYS use `core.sales_with_product` and `core.stock_with_product`. They already have all the enrichment (product names, series, gender, tier, store branch/area, pricing). Only go to raw tables if you need something not in the core views.

### Rule 6: Use Kode Mix for year-over-year analysis

Different product versions (V0-V4) have different kode_besar codes but represent the same physical product. Use `kode_mix` (article level) or `kode_mix_size` (SKU level) for any comparison across time periods. See `zuma-sku-context` skill for full explanation.

### Rule 7: ALWAYS exclude intercompany transactions (Transaksi Affiliasi)

Zuma operates 4 entities (DDD, MBB, UBB, LJBB) that sometimes "sell" to each other on paper for tax minimization. These are **fake transactions** — not real sales to customers. If you include them, you'll double-count revenue and inflate metrics.

**How to detect:** The `nama_pelanggan` (customer name) in the raw sales tables contains the OTHER entity's legal name. The `is_intercompany` flag in `core.sales_with_product` marks these rows.

**Complete list of intercompany transactions (exact `nama_pelanggan` matches):**

| Source Entity | Fake Customer (`nama_pelanggan`) | Is Actually | Pairs | Revenue |
|---|---|---|---|---|
| DDD | `CV MAKMUR BESAR BERSAMA` | MBB | 163,809 | Rp 9.53Bn |
| DDD | `CV. UNTUNG BESAR BERSAMA` | UBB | 120,238 | Rp 5.65Bn |
| DDD | `CV Lancar Jaya Besar Bersama` | LJBB | 288 | Rp 0.02Bn |
| MBB | `PT Dream Dare Discover` | DDD | 87 | Rp 0.01Bn |
| UBB | `CV. Makmur Besar Bersama` | MBB | 12 | Rp 0.00Bn |

**Total fake: ~284K pairs, ~Rp 15.2Bn revenue across all time.**

**Detection logic (used in core views):**

```sql
CASE WHEN (
  (source_entity = 'DDD' AND TRIM(LOWER(nama_pelanggan)) IN (
    'cv makmur besar bersama',
    'cv. untung besar bersama',
    'cv lancar jaya besar bersama'
  ))
  OR (source_entity = 'MBB' AND TRIM(LOWER(nama_pelanggan)) IN (
    'pt dream dare discover'
  ))
  OR (source_entity = 'UBB' AND TRIM(LOWER(nama_pelanggan)) IN (
    'cv. makmur besar bersama'
  ))
) THEN TRUE ELSE FALSE END AS is_intercompany
```

**CRITICAL:** Use exact full-name match only. Do NOT use fuzzy/LIKE matching — words like "makmur", "bersama", "untung" are common in Indonesian company names and you'll accidentally exclude real wholesale customers.

```sql
-- CORRECT: Filter out intercompany
SELECT * FROM core.sales_with_product WHERE is_intercompany = FALSE;

-- CORRECT: All mart tables exclude intercompany by default
CREATE TABLE mart.xxx AS SELECT ... WHERE is_intercompany = FALSE;

-- WRONG: Fuzzy match catches real customers
WHERE LOWER(nama_pelanggan) LIKE '%makmur%'  -- catches PT. Unggul Sukses Makmur (real customer!)
```

**Note:** `nama_pelanggan` column is available in `core.sales_with_product`. Mart tables pre-filter intercompany out so you don't need to worry about it when querying mart.

**When to apply intercompany filter:**

Intercompany transactions are between entities (DDD→MBB, UBB→DDD, LJBB→DDD), **NOT within a single store location**.

✅ **Apply filter (`is_intercompany = FALSE`) for:**
- **Aggregated queries** — Multi-store totals, nasional summaries, branch-level reports
- **Cross-store comparisons** — Store rankings, regional performance
- **Revenue reports** — Total sales by area, territory summaries

❌ **NOT needed for:**
- **Single store queries** — Sales for 1 specific toko (e.g., "Mega Mall Manado sales")
- **Store-specific reports** — RO Request, planogram allocation, single store performance

**Reason:** A single retail store can't have intercompany transactions — those only happen between warehouse/distribution entities. The filter prevents double-counting at aggregate level.

**Clarified by:** Wayan (2026-02-13 14:20)

### Rule 8: ALWAYS exclude non-product items from product analysis

The sales data contains accessory/packaging items that inflate article counts and skew metrics. Filter them out in any product-level analysis (rankings, planograms, performance reports).

```sql
-- Exclusion list (match against article name, case-insensitive)
WHERE UPPER(article) NOT LIKE '%SHOPPING BAG%'
  AND UPPER(article) NOT LIKE '%HANGER%'
  AND UPPER(article) NOT LIKE '%PAPER BAG%'
  AND UPPER(article) NOT LIKE '%THERMAL%'
  AND UPPER(article) NOT LIKE '%BOX LUCA%'
```

**Pandas equivalent:**
```python
NON_PRODUCT = ["SHOPPING BAG", "HANGER", "PAPER BAG", "THERMAL", "BOX LUCA"]
df = df[~df["article"].str.upper().apply(lambda x: any(p in str(x) for p in NON_PRODUCT))]
```

### Rule 9: Store name matching — exact vs ILIKE

`nama_gudang` in stock tables may have slight naming variations. Use the right strategy:

```sql
-- PREFERRED: Exact match on normalized name (when name is clean)
WHERE LOWER(nama_gudang) = 'zuma royal plaza'

-- FALLBACK: ILIKE pattern match (when name has variations or extra text)
WHERE LOWER(nama_gudang) ILIKE '%tunjungan plaza%'
```

**When to use which:** Check `SELECT DISTINCT nama_gudang FROM core.stock_with_product WHERE nama_gudang ILIKE '%your_store%'` first. If only 1 result, use exact. If multiple similar results, use ILIKE with the most specific pattern.

---

## 10. Query Cookbook

### Sales Performance of an Article in a Specific Area (Last 3 Months)

```sql
SELECT
    DATE_TRUNC('month', transaction_date) AS month,
    article,
    series,
    gender,
    area,
    SUM(quantity) AS total_pairs,
    SUM(total_amount) AS total_revenue,
    COUNT(DISTINCT nomor_invoice) AS num_transactions,
    COUNT(DISTINCT matched_store_name) AS num_stores_selling
FROM core.sales_with_product
WHERE kode_mix = 'M1CA02CA01'  -- Use kode_mix for version-agnostic
  AND area = 'Jatim'
  AND transaction_date >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY 1, 2, 3, 4, 5
ORDER BY month;
```

### Current Stock by Store for an Article

```sql
SELECT
    nama_gudang AS store_or_warehouse,
    gudang_branch AS branch,
    gudang_area AS area,
    gudang_category AS category,
    kode_mix,
    article,
    SUM(quantity) AS total_pairs
FROM core.stock_with_product
WHERE kode_mix = 'M1CA02CA01'
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY branch, area, total_pairs DESC;
```

### Stock by Warehouse Only (exclude stores)

```sql
SELECT
    nama_gudang,
    source_entity,
    kode_mix,
    article,
    SUM(quantity) AS total_pairs
FROM core.stock_with_product
WHERE nama_gudang ILIKE '%warehouse%'
   OR nama_gudang ILIKE '%gudang%'
GROUP BY 1, 2, 3, 4
ORDER BY total_pairs DESC;
```

### Top 20 Best-Selling Articles (Current Month)

```sql
SELECT
    kode_mix,
    article,
    series,
    gender,
    tier,
    SUM(quantity) AS total_pairs,
    SUM(total_amount) AS total_revenue,
    ROUND(AVG(unit_price), 0) AS avg_selling_price
FROM core.sales_with_product
WHERE transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY 1, 2, 3, 4, 5
ORDER BY total_pairs DESC
LIMIT 20;
```

### Sales by Branch (Month-over-Month)

```sql
SELECT
    branch,
    DATE_TRUNC('month', transaction_date) AS month,
    SUM(quantity) AS total_pairs,
    SUM(total_amount) AS total_revenue,
    COUNT(DISTINCT kode_mix) AS unique_articles
FROM core.sales_with_product
WHERE branch IS NOT NULL
  AND transaction_date >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY 1, 2
ORDER BY branch, month;
```

### Tier Performance Analysis

```sql
SELECT
    tier,
    COUNT(DISTINCT kode_mix) AS num_articles,
    SUM(quantity) AS total_pairs,
    SUM(total_amount) AS total_revenue,
    ROUND(SUM(total_amount) / NULLIF(SUM(quantity), 0), 0) AS avg_price_per_pair
FROM core.sales_with_product
WHERE transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
  AND tier IS NOT NULL
GROUP BY 1
ORDER BY total_pairs DESC;
```

### Stock Value by Entity and Warehouse

```sql
SELECT
    source_entity,
    nama_gudang,
    COUNT(DISTINCT kode_mix) AS unique_articles,
    SUM(quantity) AS total_pairs,
    SUM(quantity * unit_price) AS total_stock_value
FROM core.stock_with_product
GROUP BY 1, 2
ORDER BY source_entity, total_pairs DESC;
```

### Series Sell-Through Rate (Sales vs Stock Ratio)

```sql
WITH sales AS (
    SELECT series, SUM(quantity) AS sold_pairs
    FROM core.sales_with_product
    WHERE transaction_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY series
),
stock AS (
    SELECT series, SUM(quantity) AS stock_pairs
    FROM core.stock_with_product
    GROUP BY series
)
SELECT
    COALESCE(sa.series, st.series) AS series,
    COALESCE(sa.sold_pairs, 0) AS sold_last_30d,
    COALESCE(st.stock_pairs, 0) AS current_stock,
    CASE
        WHEN st.stock_pairs > 0
        THEN ROUND(sa.sold_pairs::numeric / st.stock_pairs * 100, 1)
        ELSE NULL
    END AS sell_through_pct
FROM sales sa
FULL OUTER JOIN stock st ON sa.series = st.series
ORDER BY sold_last_30d DESC NULLS LAST;
```

### Find Unmatched Products (no kodemix mapping)

```sql
-- Sales with no kodemix match
SELECT
    kode_besar,
    nama_barang,
    SUM(quantity) AS total_pairs,
    COUNT(*) AS num_transactions
FROM core.sales_with_product
WHERE kode_mix IS NULL
GROUP BY 1, 2
ORDER BY total_pairs DESC
LIMIT 30;
```

---

## 11. Data Processing Patterns

Reusable patterns for cleaning and transforming Zuma data. Apply these whenever building reports, planograms, or any product-level analysis.

### 11.1 Gender-Type Business Grouping

The raw `gender` field has 5+ values. Zuma's business operates on **4 consumer segments**. Always map before grouping:

| Raw `gender` value | Business Segment |
|---|---|
| `Men` | **Men** |
| `Ladies` | **Ladies** |
| `Baby`, `Boys`, `Girls`, `Junior` | **Baby & Kids** (all collapse into one) |

Combine with `tipe` (Fashion/Jepit) for display-level grouping: `"Men Fashion"`, `"Ladies Jepit"`, `"Baby & Kids"`.

```python
def map_gender_type(gender, tipe):
    g = gender.upper()
    if g == "MEN":       return f"Men {tipe}"
    if g == "LADIES":    return f"Ladies {tipe}"
    if g in ("BABY", "BOYS", "GIRLS", "JUNIOR"): return "Baby & Kids"
    return f"{gender} {tipe}"
```

### 11.2 Tier-Aware Adjusted Average

Raw monthly average penalizes fast sellers (zero months = OOS, not low demand). Use tier-aware logic:

| Tier | Zero-Month Treatment | Why |
|------|---------------------|-----|
| **T1** (fast moving) | Exclude ALL zero months | Zeros = out-of-stock, not demand drop |
| **T8** (new launch) | Exclude leading zeros + post-launch zeros | Leading zeros = not yet launched; post-launch zeros = OOS |
| **T2/T3** (mid-tier) | Contextual: exclude zero if surrounding months have decent sales (>50% of overall avg); include zero if genuine decline | Distinguishes OOS from real demand decay |
| **T4/T5/other** | Include all months (simple average) | Low movers — zeros likely genuine |

```python
# T1: only count months where it actually sold
nonzero = [v for v in monthly_values if v > 0]
adj_avg = sum(nonzero) / len(nonzero) if nonzero else 0

# T8: skip pre-launch, skip post-launch OOS
first_sale = next((i for i, v in enumerate(monthly_values) if v > 0), None)
if first_sale is not None:
    active = [v for v in monthly_values[first_sale:] if v > 0]
    adj_avg = sum(active) / len(active) if active else 0
```

**When to use:** Sales velocity rankings, planogram scoring, replenishment prioritization — any context where "average monthly sales" is a key input.

### 11.3 Turnover (TO) = Stock Coverage

At Zuma, **TO = Stock Coverage**. One formula, no ambiguity:

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **TO / Stock Coverage** | `current_stock / avg_monthly_sales` | "How many months will stock last?" High = slow mover, Low = fast mover |

**Example:** TO 4.5 = stock can hold 4.5 months at current sales rate.

**For surplus/pull decisions:** Sort by `avg_monthly_sales ASC` (slowest sellers pulled first). Do NOT sort by TO directly — use `avg_monthly_sales` which is unambiguous.

### 11.4 Tier NULL Default

When `tier` is NULL (kodemix not fully maintained), default to **T3** as conservative fallback:

```python
df["tier"] = df["tier"].fillna("3").astype(str)
```

This prevents NULL tiers from being silently dropped in tier-based filtering (`WHERE tier IN ('1','2','3','8')`).

---

## 12. Analysis Methodology

When the user asks for business analysis, follow this structured approach:

### Step 1: Clarify Scope
- **What product?** → Use kode_mix (article level) or series/gender for broader scope
- **What time period?** → Default to last 3 months if unspecified
- **What geography?** → Branch, area, or specific store
- **What metric?** → Pairs sold, revenue, stock level, sell-through

### Step 2: Choose the Right View
- **Sales analysis** → `core.sales_with_product`
- **Stock/inventory analysis** → `core.stock_with_product`
- **Combined (sell-through, coverage)** → Join both on `kode_mix`

### Step 3: Apply Business Context
- **Entity context:** DDD = retail/wholesale, MBB = online, UBB = wholesale/consignment
- **Store context:** Use branch/area for geographic analysis (see `zuma-branch` skill)
- **Product context:** Use kode_mix for version-agnostic analysis (see `zuma-sku-context` skill)
- **Tier context:** Tier 1 = fast moving (top 50%), Tier 8 = new launch (see `zuma-sku-context` skill)
- **Pricing context:** `rsp` = recommended selling price, `harga_beli` = purchase cost, `price_taq` = price tag

### Step 4: Interpret Results
- **Sales per store:** Higher in Bali (tourist area) and Jatim (home base) is normal
- **Stock distribution:** DDD holds most stock, LJBB holds Baby & Kids receiving stock
- **Tier 8 articles:** New launches — don't compare against established Tier 1 without noting this
- **Missing data:** `kode_mix IS NULL` means product not in portal.kodemix bridge table — flag but don't exclude
- **BPP/COGS:** May be 0 for some transactions (API limitation) — use `harga_beli` from portal.hpprsp as proxy
- **Assortment:** 1 box = 12 pairs always. Use `count_by_assortment` for size-level box calculation

### Step 5: Present Findings
- Lead with the key insight, not the SQL
- Use tables for comparisons
- Note data quality caveats (match rates, missing BPP, etc.)
- Suggest actionable next steps when relevant

---

## 13. Common Pitfalls (Avoid These)

| Pitfall | Why It Happens | Correct Approach |
|---------|----------------|------------------|
| Duplicate rows after JOIN | portal.kodemix has multiple versions per kode_besar | Use DISTINCT ON subquery (Rule 2) |
| Missing product enrichment | Case mismatch between raw (lowercase) and portal (mixed case) | Use TRIM(LOWER()) on portal side (Rule 1) |
| Wrong YoY comparison | Different kode_besar codes across product versions | Use kode_mix instead of kode_besar (Rule 6) |
| Excluding valid products | Filtering kodemix by `status = 'Aktif'` | Never filter by status in joins (Rule 3) |
| Empty BPP/COGS | Accurate API doesn't return cost data | Use portal.hpprsp.harga_beli as cost proxy |
| Stock seems low | Only looking at one entity | UNION ALL entities or use fact_stock_unified |
| Slow query | Querying raw tables with complex joins | Use pre-enriched core views instead (Rule 5) |
| Mart table not found | Mart tables are ephemeral | Always check `information_schema.tables` first |
| Accessories inflate article counts | SHOPPING BAG, HANGER etc. in sales data | Exclude non-product items (Rule 8) |
| Unfair sales average across tiers | T1 zeros = OOS, T8 zeros = pre-launch | Use tier-aware adjusted average (Section 11.2) |
| NULL tier silently dropped | kodemix not fully maintained for all products | Default `tier` NULL → "3" (Section 11.4) |
| Misunderstanding "TO" metric | TO = Stock Coverage (`stock / avg_sales`), not turnover rate | Use `stock_coverage_months` only (Section 11.3) |
| Store stock query returns 0 | `nama_gudang` has naming variations | Check with ILIKE first, then pick exact or pattern (Rule 9) |

---

## 14. Database Administration Quick Reference

### Check ETL Status
```sql
SELECT entity, table_name, row_count, loaded_at
FROM raw.load_history
ORDER BY loaded_at DESC
LIMIT 10;
```

### Check Data Freshness
```sql
-- Latest sales date per entity
SELECT source_entity, MAX(transaction_date) AS latest_sale
FROM core.fact_sales_unified
GROUP BY 1;

-- Latest stock snapshot
SELECT source_entity, MAX(snapshot_date) AS latest_snapshot
FROM core.fact_stock_unified
GROUP BY 1;
```

### Check Match Rates
```sql
-- Sales kodemix match rate
SELECT
    COUNT(*) AS total_rows,
    COUNT(kode_mix) AS matched,
    ROUND(COUNT(kode_mix)::numeric / COUNT(*) * 100, 1) AS match_pct
FROM core.sales_with_product;

-- Stock kodemix match rate
SELECT
    COUNT(*) AS total_rows,
    COUNT(kode_mix) AS matched,
    ROUND(COUNT(kode_mix)::numeric / COUNT(*) * 100, 1) AS match_pct
FROM core.stock_with_product;
```

### List All Tables/Views in a Schema
```sql
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_schema IN ('raw', 'portal', 'core', 'mart', 'public')
ORDER BY table_schema, table_name;
```

### Table Row Counts
```sql
SELECT schemaname, relname, n_live_tup AS estimated_rows
FROM pg_stat_user_tables
WHERE schemaname IN ('raw', 'portal', 'core', 'mart', 'public')
ORDER BY n_live_tup DESC;
```

---

## 14. Setup Guide — Persiapan Mesin untuk Non-Teknis

> **Siapa yang butuh baca ini?**
> Kamu yang bukan programmer tapi perlu menjalankan script Python Zuma — seperti generate planogram, RO Request, laporan stok, analisis penjualan, dll.
> Panduan ini step-by-step, asumsi kamu mulai dari NOL.

### 14.1 Install Python

Python adalah "mesin" yang menjalankan semua script Zuma.

**Windows:**
1. Buka https://www.python.org/downloads/
2. Klik **Download Python 3.13** (atau versi terbaru, minimal 3.8)
3. **PENTING**: Di installer, centang **"Add Python to PATH"** (ada di bawah, jangan sampai kelewat!)
4. Klik **Install Now**
5. Setelah selesai, buka **Command Prompt** (ketik `cmd` di Start Menu) dan ketik:
   ```
   python --version
   ```
   Kalau muncul `Python 3.13.x` → berhasil.

**macOS:**
```bash
# Buka Terminal, lalu:
brew install python
# Kalau belum ada Homebrew: https://brew.sh
```

**Cek apakah Python sudah ada:**
```
python --version
# atau
python3 --version
```
Kalau muncul versi 3.8 ke atas → sudah aman, skip langkah install.

### 14.2 Install Library Python

Library = "alat tambahan" yang dibutuhkan script. Buka Command Prompt / Terminal, lalu jalankan:

```bash
pip install psycopg2-binary openpyxl pandas
```

| Library | Fungsi | Kenapa Dibutuhkan |
|---------|--------|-------------------|
| `psycopg2-binary` | Koneksi ke database PostgreSQL | Semua script perlu ambil data dari VPS database Zuma |
| `openpyxl` | Baca dan tulis file Excel (.xlsx) | Generate planogram, RO Request, laporan — semua output-nya Excel |
| `pandas` | Olah data (tabel, filter, grouping) | Proses data sebelum ditulis ke Excel |

**Kalau ada error saat install:**

| Error | Solusi |
|-------|--------|
| `'pip' is not recognized` | Python belum di-PATH. Uninstall Python, install ulang, pastikan centang "Add to PATH" |
| `pip: command not found` (Mac) | Coba `pip3 install ...` |
| `error: Microsoft Visual C++ is required` | Install Visual Studio Build Tools dari https://visualstudio.microsoft.com/visual-cpp-build-tools/ |
| `permission denied` | Tambah `--user` di akhir: `pip install --user psycopg2-binary openpyxl pandas` |

**Verifikasi instalasi berhasil:**
```bash
python -c "import psycopg2; import openpyxl; import pandas; print('Semua library OK!')"
```
Kalau muncul `Semua library OK!` → lanjut.

### 14.3 Cek Akses ke Database VPS

Database Zuma ada di server VPS (IP: `76.13.194.120`). Komputer kamu harus bisa "reach" server ini.

**Test koneksi (dari Command Prompt / Terminal):**
```bash
python -c "
import psycopg2
conn = psycopg2.connect(host='76.13.194.120', port=5432, dbname='openclaw_ops', user='openclaw_app', password='Zuma-0psCl4w-2026!')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM core.stock_with_product')
print(f'Koneksi berhasil! Stock rows: {cur.fetchone()[0]}')
conn.close()
"
```

**Kalau berhasil:** Muncul `Koneksi berhasil! Stock rows: 142xxx` → lanjut.

**Kalau gagal:**

| Error | Artinya | Solusi |
|-------|---------|--------|
| `connection refused` | VPS tidak bisa dicapai dari jaringan kamu | Hubungi admin IT — mungkin perlu VPN atau IP kamu perlu di-whitelist di VPS |
| `timeout` / `could not connect` | Sama — jaringan terblokir | Coba dari WiFi lain, atau minta admin buka port 5432 untuk IP kamu |
| `password authentication failed` | Password salah | Cek ulang password di section 1 skill ini |
| `database "openclaw_ops" does not exist` | Konek ke server lain atau DB belum dibuat | Pastikan host `76.13.194.120` dan dbname `openclaw_ops` |

### 14.4 Download Script dari GitHub

Semua script Zuma ada di repo **private** GitHub:

```bash
git clone https://github.com/database-zuma/zuma-business-skills.git
```

**Kalau belum ada Git:**
1. Download dari https://git-scm.com/downloads
2. Install (default settings semua OK)
3. Buka ulang Command Prompt, coba `git --version`

**Kalau tidak mau install Git:**
- Buka https://github.com/database-zuma/zuma-business-skills
- Login dengan akun GitHub yang punya akses
- Klik **Code** → **Download ZIP**
- Extract ZIP-nya

**Struktur penting setelah download:**
```
zuma-business-skills/
└── ops/
    └── zuma-plano-and-ro/
        ├── step1-planogram/
        │   ├── build_royal_planogram.py      ← Script planogram Royal Plaza
        │   └── build_tunjungan_planogram.py  ← Script planogram Tunjungan
        ├── step2-visualizations/
        │   ├── visualize_planogram.py        ← Visual planogram Royal Plaza
        │   └── visualize_tunjungan_planogram.py
        └── step3-ro-request/
            └── build_ro_royal_plaza.py       ← Script RO Request Royal Plaza
```

### 14.5 Menjalankan Script

**Contoh: Generate RO Request untuk Royal Plaza:**

1. Buka Command Prompt / Terminal
2. Navigasi ke folder script:
   ```bash
   cd path/ke/zuma-business-skills/ops/zuma-plano-and-ro/step3-ro-request
   ```
3. Jalankan:
   ```bash
   python build_ro_royal_plaza.py
   ```
4. Tunggu ~10-30 detik (koneksi ke database, proses data, tulis Excel)
5. File output muncul di folder yang sama: `RO_REQUEST_Royal_Plaza.xlsx`
6. Buka file Excel-nya — siap cetak dan serahkan ke Warehouse Supervisor

**PENTING:** Beberapa script butuh file input (seperti planogram Excel). Pastikan file `RO Input Jatim.xlsx` ada di folder yang benar (biasanya satu level di atas folder script).

### 14.6 Pakai Claude Code (AI-Assisted) — Opsional

Kalau kamu pakai **Claude Code** (Anthropic CLI), AI bisa generate dan jalankan script langsung. Lebih mudah — kamu tinggal bilang apa yang mau dianalisis.

**Install Claude Code:**
```bash
npm install -g @anthropic-ai/claude-code
```
(Butuh Node.js — download dari https://nodejs.org jika belum ada)

**Install Zuma skills ke Claude Code:**
```bash
# Clone repo (kalau belum)
git clone https://github.com/database-zuma/zuma-business-skills.git ~/.claude/skills-repo

# Copy skills
# Windows PowerShell:
Copy-Item -Recurse "$env:USERPROFILE\.claude\skills-repo\general\*" "$env:USERPROFILE\.claude\skills\" -Force
Copy-Item -Recurse "$env:USERPROFILE\.claude\skills-repo\ops\*" "$env:USERPROFILE\.claude\skills\" -Force

# macOS/Linux:
cp -r ~/.claude/skills-repo/general/* ~/.claude/skills/
cp -r ~/.claude/skills-repo/ops/* ~/.claude/skills/
```

**Setelah install, di Claude Code kamu bisa bilang:**
```
"Generate RO Request mingguan untuk Zuma Royal Plaza"
"Analisa penjualan Classic Jet Black di semua toko Jatim bulan ini"
"Cek stok Warehouse Pusat — artikel mana yang tinggal sedikit?"
```
Claude otomatis load skill yang relevan dan tau cara query database-nya.

### 14.7 Checklist Persiapan Lengkap

Sebelum bisa menjalankan script apapun, pastikan semua ini sudah OK:

| # | Item | Cara Cek | Status |
|---|------|----------|--------|
| 1 | Python 3.8+ ter-install | `python --version` → muncul versi | ☐ |
| 2 | `pip` tersedia | `pip --version` → muncul versi | ☐ |
| 3 | `psycopg2-binary` ter-install | `python -c "import psycopg2"` → no error | ☐ |
| 4 | `openpyxl` ter-install | `python -c "import openpyxl"` → no error | ☐ |
| 5 | `pandas` ter-install | `python -c "import pandas"` → no error | ☐ |
| 6 | Bisa konek ke VPS database | Test koneksi (lihat 14.3) → muncul row count | ☐ |
| 7 | Script sudah di-download | Folder `zuma-business-skills/` ada | ☐ |
| 8 | File input tersedia | `RO Input {Region}.xlsx` ada di folder yang benar | ☐ |

**Kalau semua ☐ sudah ☑ → kamu siap jalankan script apapun.**

### 14.8 Troubleshooting Umum

| Masalah | Penyebab | Solusi |
|---------|----------|--------|
| `ModuleNotFoundError: No module named 'psycopg2'` | Library belum di-install | `pip install psycopg2-binary` |
| `ModuleNotFoundError: No module named 'openpyxl'` | Library belum di-install | `pip install openpyxl` |
| `SyntaxError: invalid syntax` | Python versi lama (< 3.8) | Upgrade Python ke 3.8+ |
| `UnicodeEncodeError` | Windows console encoding | Script Zuma sudah handle ini otomatis. Kalau masih muncul, tambah `chcp 65001` sebelum jalankan script |
| `FileNotFoundError: RO Input Jatim.xlsx` | File planogram tidak ditemukan | Pastikan path relatif benar. Biasanya 1 folder di atas script |
| `PermissionError: ... .xlsx` | File Excel masih dibuka | Tutup dulu file Excel-nya, baru jalankan script lagi |
| Script jalan tapi output Excel kosong | Planogram tidak ada data untuk toko tersebut | Cek sheet "Planogram" di file input — pastikan ada baris untuk toko target |
| `psycopg2.OperationalError: connection refused` | Tidak bisa konek ke VPS | Lihat troubleshooting di section 14.3 |
| Excel output tidak rapi (tanpa warna/border) | `openpyxl` versi terlalu lama | `pip install --upgrade openpyxl` (minimal versi 3.1+) |

---

## 15. Standardized SQL Templates

**MANDATORY: All AI agents (Atlas, Apollo, Iris) MUST use these templates when querying Zuma data.** Adjust columns, filters, and grouping per user request, but NEVER deviate from the mandatory filters, column aliases, and source tables defined here.

### 15.1 Question Pattern Framework

Every Zuma data question follows this structure:

```
"Berapa [METRIC] dari [WHAT] di [WHERE] selama [WHEN]?"
```

**Step 1 — Identify METRIC (what to measure):**

| User says | Sales metric | Stock metric |
|-----------|-------------|-------------|
| "berapa penjualan / sales" | `SUM(quantity) AS total_pairs` | — |
| "berapa revenue / omzet" | `SUM(total_amount) AS total_revenue` | — |
| "berapa stok / stock" | — | `SUM(quantity) AS total_pairs` |
| "berapa nilai stok" | — | `SUM(quantity * unit_price) AS total_stock_value` |
| "rata-rata harga jual" | `ROUND(SUM(total_amount) / NULLIF(SUM(quantity), 0), 0) AS avg_price_per_pair` | — |

**Step 2 — Identify WHAT (product granularity):**

Pick the **lowest granularity** the user mentions. If they say "Classic Jet Black" → article level. If they say "Classic" → series level. If they say "Men Jepit" → gender+tipe level.

| User says | GROUP BY columns | Filter |
|-----------|-----------------|--------|
| Specific article ("Jet Black") | `kode_mix, article` | `AND article ILIKE '%jet black%'` |
| Series ("Classic", "Stripe") | `series` | `AND series = 'Classic'` |
| Gender ("Men", "Ladies") | `gender` | `AND gender = 'Men'` |
| Gender + Tipe ("Men Jepit") | `gender, tipe` | `AND gender = 'Men' AND tipe = 'Jepit'` |
| Tier ("T1 articles") | `tier` | `AND tier = '1'` |
| All products | _(no product grouping)_ | _(no product filter)_ |

> **IMPORTANT:** Read `zuma-sku-context` skill to understand the difference between `kode_mix` (version-agnostic article), `kode_mix_size` (article+size), `kode_besar` (version-specific), `series`, `gender`, `tipe`. Getting the wrong level = wrong numbers.

**Step 3 — Identify WHERE (geography level):**

⚠️ **Column names are DIFFERENT between sales and stock views.** This is a common mistake.

| User says | Sales column (`core.sales_with_product`) | Stock column (`core.stock_with_product`) |
|-----------|---|---|
| Specific store ("Royal Plaza") | `AND matched_store_name ILIKE '%royal plaza%'` | `AND nama_gudang ILIKE '%royal plaza%'` |
| Area ("Bali 1", "Jatim") | `AND area = 'Jatim'` | `AND gudang_area = 'Jatim'` |
| Branch ("Bali", "Jakarta") | `AND branch = 'Bali'` | `AND gudang_branch = 'Bali'` |
| Warehouse only | `AND matched_store_name ILIKE '%warehouse%'` | `AND nama_gudang ILIKE '%warehouse%'` |
| National (all) | _(no geo filter)_ | _(no geo filter)_ |
| Retail stores only | `AND store_category = 'RETAIL'` | `AND gudang_category = 'RETAIL'` |

> **TRAP:** Using `branch` on stock view returns NULL — stock uses `gudang_branch`. Using `matched_store_name` on stock view doesn't exist — stock uses `nama_gudang`. Always check which view you're querying.

**Step 4 — Identify WHEN (time period):**

| User says | Sales filter | Stock filter |
|-----------|-------------|-------------|
| "bulan ini" | `AND transaction_date >= DATE_TRUNC('month', CURRENT_DATE)` | _(no filter — always latest snapshot)_ |
| "3 bulan terakhir" | `AND transaction_date >= CURRENT_DATE - INTERVAL '3 months'` | N/A |
| "YTD" / "tahun ini" | `AND transaction_date >= DATE_TRUNC('year', CURRENT_DATE)` | N/A |
| "2024" | `AND transaction_date >= '2024-01-01' AND transaction_date < '2025-01-01'` | N/A |
| "Jan-Mar 2025" | `AND transaction_date >= '2025-01-01' AND transaction_date < '2025-04-01'` | N/A |
| Not specified | Default: `AND transaction_date >= CURRENT_DATE - INTERVAL '3 months'` | N/A |

> **Stock has NO period filter.** Stock data is always the latest daily snapshot (overwrites every morning). There is no historical stock — only "stock right now."

**Step 5 — Pick template and assemble:**

```
1. Sales question → Template A (Section 15.4)
2. Stock question → Template B (Section 15.5)
3. Sales + Stock combined (TO / coverage) → Template C (Section 15.6)
```

**Quick example — "Berapa penjualan series Classic di area Jatim 3 bulan terakhir?"**

```sql
SELECT
    series,
    DATE_TRUNC('month', transaction_date) AS month,
    SUM(quantity) AS total_pairs,
    SUM(total_amount) AS total_revenue
FROM core.sales_with_product
WHERE is_intercompany = FALSE
  AND UPPER(article) NOT LIKE '%SHOPPING BAG%'
  AND UPPER(article) NOT LIKE '%HANGER%'
  AND UPPER(article) NOT LIKE '%PAPER BAG%'
  AND UPPER(article) NOT LIKE '%THERMAL%'
  AND UPPER(article) NOT LIKE '%BOX LUCA%'
  AND series = 'Classic'                                    -- WHAT
  AND area = 'Jatim'                                        -- WHERE
  AND transaction_date >= CURRENT_DATE - INTERVAL '3 months' -- WHEN
GROUP BY 1, 2
ORDER BY month;
```

**Quick example — "Berapa stock Airmove di gudang pusat?"**

```sql
SELECT
    article,
    kode_mix,
    nama_gudang,
    SUM(quantity) AS total_pairs
FROM core.stock_with_product
WHERE UPPER(article) NOT LIKE '%SHOPPING BAG%'
  AND UPPER(article) NOT LIKE '%HANGER%'
  AND UPPER(article) NOT LIKE '%PAPER BAG%'
  AND UPPER(article) NOT LIKE '%THERMAL%'
  AND UPPER(article) NOT LIKE '%BOX LUCA%'
  AND series = 'Airmove'                                    -- WHAT
  AND nama_gudang ILIKE '%warehouse pusat%'                 -- WHERE (stock column!)
GROUP BY 1, 2, 3
ORDER BY total_pairs DESC;
```

### 15.2 Column Alias Conventions

**RULE: Always English, always snake_case, always descriptive. Never Indonesian (no `jumlah`, no `stok`, no `penjualan`). Never abbreviations (no `qty`, no `rev`, no `txn`).**

| Semantic | Standard Alias | Example |
|----------|---------------|---------|
| Pairs sold/in stock | `total_pairs` | `SUM(quantity) AS total_pairs` |
| Revenue | `total_revenue` | `SUM(total_amount) AS total_revenue` |
| Transaction count | `num_transactions` | `COUNT(DISTINCT nomor_invoice) AS num_transactions` |
| Unique article count | `num_articles` | `COUNT(DISTINCT kode_mix) AS num_articles` |
| Store count | `num_stores` | `COUNT(DISTINCT matched_store_name) AS num_stores` |
| Average price per pair | `avg_price_per_pair` | `ROUND(SUM(total_amount) / NULLIF(SUM(quantity), 0), 0) AS avg_price_per_pair` |
| Stock value | `total_stock_value` | `SUM(quantity * unit_price) AS total_stock_value` |
| Simple average (N months) | `avg_{N}_months` | `AVG(monthly_pairs) AS avg_3_months` |
| Tier-adjusted average (N months) | `adj_avg_{N}_months` | See Section 15.6 |
| Current stock | `current_stock` | `SUM(quantity) AS current_stock` |
| Stock coverage / TO in months | `stock_coverage_months` | `ROUND(current_stock / adj_avg_3_months, 1)` |
| Monthly sales per period | `monthly_pairs` | Used in CTEs |
| Monthly grouping | `month` | `DATE_TRUNC('month', transaction_date) AS month` |
| Article ID | `kode_mix` | Never `sku`, never `article_code` |

**Pattern rules:**
```
Sums      → total_{unit}     (total_pairs, total_revenue, total_stock_value)
Counts    → num_{thing}      (num_transactions, num_articles, num_stores)
Averages  → avg_{metric}     (avg_3_months, avg_price_per_pair)
Adjusted  → adj_avg_{metric} (adj_avg_3_months, adj_avg_6_months)
Coverage  → {metric}_{unit}  (stock_coverage_months)
```

### 15.3 Mandatory Filters

**Every sales query MUST include these filters unless explicitly told otherwise:**

```sql
-- MANDATORY for ALL sales queries
WHERE is_intercompany = FALSE                          -- Rule 7: exclude fake inter-entity transfers
  AND UPPER(article) NOT LIKE '%SHOPPING BAG%'         -- Rule 8: exclude non-product items
  AND UPPER(article) NOT LIKE '%HANGER%'
  AND UPPER(article) NOT LIKE '%PAPER BAG%'
  AND UPPER(article) NOT LIKE '%THERMAL%'
  AND UPPER(article) NOT LIKE '%BOX LUCA%'
```

**Stock queries:** No intercompany filter needed (stock is per entity — DDD is DDD, MBB is MBB). Non-product exclusion still applies if doing product-level analysis.

### 15.4 Template A — Sales Analysis

```sql
-- TEMPLATE: Sales Analysis
-- Source: core.sales_with_product (ALWAYS use this, never raw tables)
-- Adjust: columns, date range, grouping per user request
-- Default: last 3 months if unspecified

SELECT
    -- Dimensions (pick what's needed)
    kode_mix,
    article,
    series,
    gender,
    tipe,
    tier,
    branch,
    area,
    DATE_TRUNC('month', transaction_date) AS month,

    -- Metrics (standard aliases only)
    SUM(quantity) AS total_pairs,
    SUM(total_amount) AS total_revenue,
    COUNT(DISTINCT nomor_invoice) AS num_transactions,
    COUNT(DISTINCT matched_store_name) AS num_stores,
    ROUND(SUM(total_amount) / NULLIF(SUM(quantity), 0), 0) AS avg_price_per_pair

FROM core.sales_with_product

-- MANDATORY filters (never remove)
WHERE is_intercompany = FALSE
  AND UPPER(article) NOT LIKE '%SHOPPING BAG%'
  AND UPPER(article) NOT LIKE '%HANGER%'
  AND UPPER(article) NOT LIKE '%PAPER BAG%'
  AND UPPER(article) NOT LIKE '%THERMAL%'
  AND UPPER(article) NOT LIKE '%BOX LUCA%'

  -- User-specific filters (adjust per request)
  AND transaction_date >= CURRENT_DATE - INTERVAL '3 months'
  -- AND branch = 'Jatim'
  -- AND kode_mix = 'M1CA02CA01'

GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
ORDER BY total_pairs DESC;
```

### 15.5 Template B — Stock / Inventory Analysis

```sql
-- TEMPLATE: Stock / Inventory Analysis
-- Source: core.stock_with_product (ALWAYS use this, never raw tables)
-- Note: No intercompany filter needed for stock
-- Note: Stock is latest snapshot only (overwrites daily)

SELECT
    -- Dimensions (pick what's needed)
    kode_mix,
    article,
    series,
    gender,
    tipe,
    tier,
    source_entity,
    nama_gudang,
    gudang_branch,
    gudang_area,
    gudang_category,

    -- Metrics (standard aliases only)
    SUM(quantity) AS total_pairs,
    COUNT(DISTINCT kode_mix) AS num_articles,
    SUM(quantity * unit_price) AS total_stock_value

FROM core.stock_with_product

-- Non-product exclusion (for product-level analysis)
WHERE UPPER(article) NOT LIKE '%SHOPPING BAG%'
  AND UPPER(article) NOT LIKE '%HANGER%'
  AND UPPER(article) NOT LIKE '%PAPER BAG%'
  AND UPPER(article) NOT LIKE '%THERMAL%'
  AND UPPER(article) NOT LIKE '%BOX LUCA%'

  -- User-specific filters (adjust per request)
  -- AND gudang_branch = 'Jatim'
  -- AND kode_mix = 'M1CA02CA01'
  -- AND nama_gudang ILIKE '%warehouse%'  -- warehouses only

GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
ORDER BY total_pairs DESC;
```

### 15.6 Template C — Stock Coverage & Turnover (TO)

```sql
-- TEMPLATE: Stock Coverage & Turnover Rate
-- Combines sales (last N months) + current stock
-- Default lookback: 3 months. Adjust INTERVAL per user request.
-- Uses simplified tier-aware adjusted average:
--   T1/T2/T3/T8: exclude zero months (zeros = OOS, not low demand)
--   T4/T5: include zero months (zeros = genuine low demand)
-- For full contextual T2/T3 logic (surrounding-month check), use Python compute_adjusted_avg()

WITH monthly_sales AS (
    SELECT
        kode_mix,
        article,
        series,
        gender,
        tier,
        DATE_TRUNC('month', transaction_date) AS month,
        SUM(quantity) AS monthly_pairs
    FROM core.sales_with_product
    WHERE is_intercompany = FALSE
      AND UPPER(article) NOT LIKE '%SHOPPING BAG%'
      AND UPPER(article) NOT LIKE '%HANGER%'
      AND UPPER(article) NOT LIKE '%PAPER BAG%'
      AND UPPER(article) NOT LIKE '%THERMAL%'
      AND UPPER(article) NOT LIKE '%BOX LUCA%'
      AND transaction_date >= CURRENT_DATE - INTERVAL '3 months'
      -- ↑ Lookback period. Change to '6 months', '12 months' etc. per request.
    GROUP BY 1, 2, 3, 4, 5, 6
),
adj_sales AS (
    SELECT
        kode_mix,
        article,
        series,
        gender,
        tier,
        -- Tier-aware adjusted average (simplified)
        CASE
            WHEN tier IN ('1','2','3','8')
                THEN AVG(monthly_pairs) FILTER (WHERE monthly_pairs > 0)
            ELSE AVG(monthly_pairs)
        END AS adj_avg_3_months
        -- ↑ Rename to adj_avg_6_months, adj_avg_12_months etc. if lookback changes
    FROM monthly_sales
    GROUP BY 1, 2, 3, 4, 5
),
current_stock AS (
    SELECT
        kode_mix,
        SUM(quantity) AS current_stock
    FROM core.stock_with_product
    WHERE UPPER(article) NOT LIKE '%SHOPPING BAG%'
      AND UPPER(article) NOT LIKE '%HANGER%'
      AND UPPER(article) NOT LIKE '%PAPER BAG%'
      AND UPPER(article) NOT LIKE '%THERMAL%'
      AND UPPER(article) NOT LIKE '%BOX LUCA%'
    GROUP BY 1
)
SELECT
    COALESCE(s.kode_mix, st.kode_mix) AS kode_mix,
    s.article,
    s.series,
    s.gender,
    s.tier,
    COALESCE(s.adj_avg_3_months, 0) AS adj_avg_3_months,
    COALESCE(st.current_stock, 0) AS current_stock,

    -- Stock Coverage / TO (bulan): "Stok cukup berapa bulan?"
    -- Tinggi = slow mover, Rendah = fast mover / mau habis
    CASE
        WHEN s.adj_avg_3_months > 0
        THEN ROUND(st.current_stock / s.adj_avg_3_months, 1)
        ELSE NULL  -- no sales data → cannot compute
    END AS stock_coverage_months

FROM adj_sales s
FULL OUTER JOIN current_stock st ON s.kode_mix = st.kode_mix
ORDER BY stock_coverage_months ASC NULLS LAST;
```

**Interpreting results:**

| stock_coverage_months | Meaning |
|---|---|
| < 1.0 | Fast seller, stock running out — restock urgently |
| 1.0 – 3.0 | Healthy — normal replenishment cycle |
| 3.0 – 6.0 | Slow mover — monitor, consider markdown |
| > 6.0 | Dead stock — clearance candidate |
| NULL | No sales data or no stock — flag to user |

### 15.7 Entity & Data Warnings

#### ⚠️ WARNING A: Online Sales Entity Migration (DDD → MBB)

Online/marketplace sales migrated **gradually from DDD to MBB between Feb–Aug 2025:**

| Period | DDD (`"zuma online"`) | MBB (`"online"`) | Status |
|--------|---|---|---|
| 2022-01 → 2025-01 | All online sales | — | 100% on DDD |
| **2025-02** | 5,105 pairs | 1,194 pairs | Migration starts |
| **2025-03** | 5,081 pairs | 11,920 pairs | MBB overtakes DDD |
| 2025-04 → 2025-07 | Declining (2,374–3,947) | Growing (6,784–12,720) | Gradual shift |
| **2025-08** | 3 pairs | 14,518 pairs | DDD online effectively dead |
| 2025-08 → present | ~0 | 11,000–15,000/mo | 100% on MBB |

**Store names are different per entity:** DDD = `"zuma online"`, MBB = `"online"`.

**Rules:**
- When analyzing **online sales trends across years**, combine both entities: `WHERE LOWER(store_name_raw) IN ('zuma online', 'online')` — do NOT filter by `source_entity`.
- When filtering by `source_entity = 'DDD'` for any time range crossing 2025, **always note** that online sales moved to MBB and DDD numbers will appear to drop.
- When filtering by `source_entity = 'MBB'`, **always note** that data before Feb 2025 will show near-zero (not because no sales existed, but because they were under DDD).
- All **offline retail stores remain under DDD** — this migration only affects online channels.

#### ⚠️ WARNING B: Cross-Entity Stock Discrepancies

Stock data can show negative quantities in one entity when stock has been physically moved but not yet recorded in the system. Common pattern:

- **LJBB** shows +N (stock received from supplier) while **DDD** shows -N for the same article → stock is physically at DDD, system transfer pending.
- **MBB** can also show negative stock for the same reason (stock already at DDD but untransacted).

**When you see negative stock for any entity:** Notify the user that this likely means the stock physically exists but the inter-entity system transfer hasn't been recorded yet. Suggest checking the same `kode_mix` across all entities to get the net real quantity.

---

## 16. When to Use This Skill

**Always use this skill when:**
- User asks to "analyze", "query", "check", "look into" any Zuma business data
- User mentions sales, stock, inventory, performance, revenue, pairs sold
- User asks about specific articles, series, stores, branches, warehouses
- User wants to create mart/summary tables
- User asks to connect to or query the database
- User asks about data freshness, ETL status, or data quality
- User says "pull data", "run a query", "check the numbers"

**Combine with other skills when:**
- Product details needed → load `zuma-sku-context`
- Store/branch details needed → load `zuma-branch`
- Warehouse operations details needed → load `zuma-warehouse-and-stocks`
- Brand/entity context needed → load `zuma-company-context`

---

**Status:** Complete
**Last Updated:** 13 Feb 2026
**Covers:** Database connection, schema architecture, all tables/views, ETL schedule, query rules, data processing patterns, SQL cookbook, analysis methodology, common pitfalls, admin reference, **standardized SQL templates** (sales, stock, TO/coverage, column conventions, entity warnings), **setup guide for non-technical users** (Python, libraries, DB access, script execution, troubleshooting)

---

## 🚨 CRITICAL: Branch/Store Mapping (Added 2026-02-16)

**NEVER map branch/area using store name patterns!**

### ❌ WRONG Approach
```sql
-- DON'T DO THIS - assumptions based on store names fail!
CASE 
  WHEN store_name ILIKE '%epicentrum%' THEN 'Jakarta'  -- WRONG! Epicentrum is in Lombok
  WHEN store_name ILIKE '%level 21%' THEN 'Jakarta'     -- WRONG! Level 21 is in Bali
  WHEN store_name ILIKE '%city of tomorrow%' THEN 'Jakarta'  -- WRONG! City of Tomorrow is in Surabaya
END AS branch
```

**Why it fails:** Store names don't reliably indicate location. Many stores have deceptive names.

### ✅ CORRECT Approach

**ALWAYS JOIN with `portal.store` table** (source of truth):

```sql
SELECT 
  s.store_name_raw,
  ps.branch,           -- ← Definitive branch from master data
  ps.area,             -- ← Specific area/city
  ps.category,         -- ← RETAIL/NON-RETAIL/EVENT
  SUM(s.quantity) AS total_qty,
  SUM(s.total_amount) AS total_revenue
FROM core.sales_with_product s
LEFT JOIN portal.store ps 
  ON s.store_name_raw = ps.nama_accurate 
  OR s.store_name_raw = ps.nama_iseller
WHERE ps.category = 'RETAIL'  -- Exclude NON-RETAIL/EVENT if needed
  AND ps.branch IS NOT NULL
GROUP BY ps.branch, ps.area, ps.category, s.store_name_raw
ORDER BY total_revenue DESC;
```

### Portal Store Table Reference

**Columns:**
- `nama_accurate` — Store name in Accurate (ERP)
- `nama_iseller` — Store name in iSeller (POS)
- `branch` — Branch classification (Jakarta, Jatim, Bali, Lombok, etc.)
- `area` — Specific area/city
- `category` — RETAIL / NON-RETAIL / EVENT
- `max_display` — Display capacity
- `storage` — Storage capacity
- `monthly_target` — Revenue target

**Categories to filter:**
- `RETAIL` — Permanent retail stores (include in analysis)
- `NON-RETAIL` — Wholesale, konsinyasi, hublife (usually exclude)
- `EVENT` — Temporary pameran/bazar (exclude for permanent store analysis)

### Validation Workflow

**Before any branch/area analysis:**
1. Query `portal.store` to see which stores belong to which branch
2. JOIN sales data with portal.store
3. Filter by category if needed
4. Present results

**Example: Jakarta stores only**
```sql
SELECT 
  nama_accurate,
  nama_iseller,
  category,
  storage
FROM portal.store
WHERE branch = 'Jakarta'
  AND category = 'RETAIL'
ORDER BY nama_accurate;
```

### Lesson Learned (2026-02-16)

**Incident:** Performance analysis with 3 wrong revisions due to assumed mappings.

**Root cause:** Used `ILIKE` patterns based on gut feeling instead of master data.

**Solution:** ALWAYS use `portal.store` as source of truth for branch/area mapping.

**Rule:** Master data > assumptions. Don't guess locations, JOIN with portal.store.
