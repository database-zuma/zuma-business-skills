# Zuma Data Analyst — Schema Reference

> This file contains full column-level definitions for all tables and views in the `openclaw_ops` database.
> Referenced from `SKILL.md` in the same directory.

---

## Schema: `raw` (Source Data)

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

## Schema: `portal` (Reference/Master Data)

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
| `status` | text | 'Aktif' or 'Tidak Aktif' (DO NOT filter on this for joins — see Critical Rules in SKILL.md) |
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

## Schema: `core` (Transformed Views)

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

### Main Analysis Views

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

## Schema: `mart` (Ad-hoc Analysis)

**Tables in this schema always change based on user requests.** The mart schema is a workspace for creating summary tables, aggregations, and analysis-specific materializations.

**Current state:** Schema exists but tables are created and dropped as needed. Do not assume any specific table exists — always check first:

```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'mart';
```

**Common mart table patterns:**
- `mart.monthly_sales_summary` — aggregated monthly sales by article/store
- `mart.article_performance` — article-level KPIs
- `mart.store_performance` — store-level KPIs
- `mart.tier_analysis` — sales/stock by tier breakdown

**Creating mart tables:** Always use `CREATE TABLE mart.{name} AS SELECT ...` from core views.

---

## Schema: `public` (BI Tool Mirrors)

Convenience views that mirror core views. Exist because Looker Studio and some BI tools can only see the `public` schema without custom queries.

| View | Mirrors |
|------|---------|
| `public.sales_with_product` | → `core.sales_with_product` |
| `public.stock_with_product` | → `core.stock_with_product` |

---

## Intercompany Detection Logic

The `is_intercompany` flag in `core.sales_with_product` is computed as follows:

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

---

## Database Administration — Schema Queries

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
