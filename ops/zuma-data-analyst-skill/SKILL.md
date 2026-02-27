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

## 3. Schema Quick Reference

> Full column-level definitions: see `data-analyst-schema-reference.md`

### `raw` — Source Data (from Accurate Online API)

| Table | Description |
|-------|-------------|
| `raw.accurate_sales_ddd` | DDD retail+wholesale sales (~1.3M rows, 2022-01 to present). Key cols: transaction_date, kode_barang, quantity, total_amount, nama_pelanggan, warehouse_code |
| `raw.accurate_sales_mbb` | MBB online marketplace sales (~197K rows, 2024-04 to present). Same structure |
| `raw.accurate_sales_ubb` | UBB wholesale+consignment (~41K rows, 2023-02 to present). Same structure |
| `raw.accurate_stock_ddd` | DDD stock snapshot (~142K rows, overwrites daily). Key cols: kode_barang, nama_gudang, quantity |
| `raw.accurate_stock_ljbb` | LJBB Baby & Kids receiving (~128 rows) |
| `raw.accurate_stock_mbb/ubb` | Minimal/empty |
| `raw.load_history` | ETL audit trail: entity, table_name, row_count, loaded_at |

### `portal` — Reference/Master Data (from Google Sheets)

| `portal.planogram_existing_q1_2026` | **Planogram target Q1 2026** — max stock per artikel per toko. Source untuk kalkulasi FF/FA/FS |

| Table | Description |
|-------|-------------|
| `portal.kodemix` (~5.4K rows) | **Product bridge table.** Maps kode_besar (MIXED CASE) to kode_mix. Key cols: kode_besar, kode_mix, article, series, gender, tipe, tier_baru, version |
| `portal.hpprsp` | Pricing: kode, harga_beli (HPP), price_taq, rsp |
| `portal.store` | Store master: nama_accurate (MIXED CASE), branch, area, category |
| `portal.stock_capacity` | Store/warehouse capacity: stock_location (MIXED CASE), branch, area |

### `core` — Transformed Views (USE THESE for analysis)

#### `core.sales_with_product` (46 columns) — PRIMARY SALES VIEW

Joins fact_sales_unified with kodemix + hpprsp + store. **Use for ALL sales analysis.**

| Column Group | Columns |
|-------------|---------|
| **Transaction** | source_entity, nomor_invoice, transaction_date, date_key, kode_besar, matched_kode_besar, kode, store_name_raw, matched_store_name, nama_barang, nama_pelanggan, is_intercompany, quantity, unit_price, total_amount, cost_of_goods, vendor_price, dpp_amount, tax_amount, warehouse_code, snapshot_date, loaded_at |
| **Product IDs** | kode_mix, kode_mix_size, article, version |
| **Product Attrs** | product_name, product_type, tipe, series, gender, tier, color, assortment, nama_variant, size, group_warna |
| **Pricing** | harga_beli, price_taq, rsp |
| **Store** | branch, area, store_category, stock_filter, as_name, bm_name |
| **Technical** | v, count_by_assortment |

~1.55M rows | 94.1% kodemix match | 86.2% store match

#### `core.stock_with_product` (38 columns) — PRIMARY STOCK VIEW

**Use for ALL stock/inventory analysis.**

| Column Group | Columns |
|-------------|---------|
| **Stock** | source_entity, snapshot_date, date_key, kode_besar, matched_kode_besar, kode, nama_gudang, quantity, unit_price, vendor_price, warehouse_code, loaded_at |
| **Product IDs** | kode_mix, kode_mix_size, article, version |
| **Product Attrs** | product_name, product_type, tipe, series, gender, tier, color, ukuran, assortment, season, product_status, nama_variant, size, group_warna |
| **Pricing** | harga_beli, price_taq, rsp |
| **Warehouse** | gudang_branch, gudang_area, gudang_category |
| **Technical** | v, count_by_assortment |

~142K rows | 99.9% kodemix match | 96.4% capacity match

#### Other Core Views

| View | Description |
|------|-------------|
| `core.fact_sales_unified` | UNION ALL raw sales (base for sales_with_product) |
| `core.fact_stock_unified` | UNION ALL raw stock (base for stock_with_product) |
| `core.dim_product` / `dim_store` / `dim_date` / `dim_warehouse` | Dimension views |

### `mart` — Ad-hoc Analysis + FF/FA/FS

**UNSTABLE** — tables created/dropped per request. Always check: `SELECT table_name FROM information_schema.tables WHERE table_schema = 'mart';`

**Persistent mart tables (jangan di-drop):**

| Table | Description |
|-------|-------------|
| `mart.ff_fa_fs_daily_q1_2026` | Output FF/FA/FS harian Q1 2026 — di-update otomatis setiap hari setelah stock pull. Kolom: `report_date`, `branch`, `store_label`, `store_db_name`, `ff`, `fa`, `fs` |
| `mart.ff_fa_fs_daily` | Versi lama (sebelum Q1 2026) — legacy, jangan pakai untuk analisis terkini |
| `mart.stock_opname_l2_daily` | SO L2 daily — stock opname level 2 |

Create with: `CREATE TABLE mart.{name} AS SELECT ... FROM core.{view} WHERE ...`

### `public` — BI Tool Mirrors

| View | Mirrors |
|------|---------|
| `public.sales_with_product` | `core.sales_with_product` |
| `public.stock_with_product` | `core.stock_with_product` |

---

## 4. ETL / Auto-Update Schedule

| Time (WIB) | Job | Description |
|-------------|-----|-------------|
| **02:00** | Database backup | Full `pg_dump` of `openclaw_ops` |
| **03:00** | Stock pull | All 4 entities — overwrites stock tables with latest snapshot |
| **05:00** | Sales pull | 3 entities (DDD, MBB, UBB) — incremental, pulls last 3 days |
| **08:00-09:00** | FF/FA/FS calc | `calculate_ff_fa_fs_q12026.py` — membaca `portal.planogram_existing_q1_2026` + stock aktual → output ke `mart.ff_fa_fs_daily_q1_2026` |

No LJBB sales pull (PO receiving entity only). ETL audit: `SELECT * FROM raw.load_history ORDER BY loaded_at DESC LIMIT 20;`

> Full ETL details, admin SQL, and setup guide: see `data-analyst-etl-cron.md`

---

## 5. CRITICAL Query Rules

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

Do NOT add `WHERE status = 'Aktif'` or any status filter when joining kodemix. ALL products must be matched regardless of active/discontinued status.

### Rule 4: ALWAYS verify row counts after creating views/tables

After any view or table creation that involves joins, verify no row inflation:

```sql
SELECT COUNT(*) FROM core.fact_sales_unified;   -- e.g., 1,545,304
SELECT COUNT(*) FROM core.sales_with_product;    -- must be exactly 1,545,304
```

### Rule 5: Use core views, not raw tables

For analysis, ALWAYS use `core.sales_with_product` and `core.stock_with_product`. They already have all the enrichment. Only go to raw tables if you need something not in the core views.

### Rule 6: Use Kode Mix for year-over-year analysis

Different product versions (V0-V4) have different kode_besar codes but represent the same physical product. Use `kode_mix` (article level) or `kode_mix_size` (SKU level) for any comparison across time periods.

### Rule 7: ALWAYS exclude intercompany transactions

Zuma's 4 entities (DDD, MBB, UBB, LJBB) sometimes "sell" to each other on paper. These are **fake transactions**. The `is_intercompany` flag in `core.sales_with_product` marks these rows.

| Source Entity | Fake Customer (`nama_pelanggan`) | Is Actually |
|---|---|---|
| DDD | `CV MAKMUR BESAR BERSAMA` | MBB |
| DDD | `CV. UNTUNG BESAR BERSAMA` | UBB |
| DDD | `CV Lancar Jaya Besar Bersama` | LJBB |
| MBB | `PT Dream Dare Discover` | DDD |
| UBB | `CV. Makmur Besar Bersama` | MBB |

**Total fake: ~284K pairs, ~Rp 15.2Bn revenue across all time.**

```sql
-- CORRECT: Filter out intercompany
SELECT * FROM core.sales_with_product WHERE is_intercompany = FALSE;

-- WRONG: Fuzzy match catches real customers
WHERE LOWER(nama_pelanggan) LIKE '%makmur%'  -- catches PT. Unggul Sukses Makmur (real customer!)
```

**CRITICAL:** Use exact full-name match only. Do NOT use fuzzy/LIKE matching. The `is_intercompany` flag handles this correctly. See `data-analyst-schema-reference.md` for the full detection logic SQL.

### Rule 8: ALWAYS exclude non-product items from product analysis

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

```sql
-- PREFERRED: Exact match on normalized name (when name is clean)
WHERE LOWER(nama_gudang) = 'zuma royal plaza'

-- FALLBACK: ILIKE pattern match (when name has variations)
WHERE LOWER(nama_gudang) ILIKE '%tunjungan plaza%'
```

**When to use which:** Check `SELECT DISTINCT nama_gudang FROM core.stock_with_product WHERE nama_gudang ILIKE '%your_store%'` first. If only 1 result, use exact. If multiple, use ILIKE with the most specific pattern.

### Mandatory Filters Summary

**Every sales query MUST include:**

```sql
WHERE is_intercompany = FALSE                          -- Rule 7
  AND UPPER(article) NOT LIKE '%SHOPPING BAG%'         -- Rule 8
  AND UPPER(article) NOT LIKE '%HANGER%'
  AND UPPER(article) NOT LIKE '%PAPER BAG%'
  AND UPPER(article) NOT LIKE '%THERMAL%'
  AND UPPER(article) NOT LIKE '%BOX LUCA%'
```

**Stock queries:** No intercompany filter needed. Non-product exclusion still applies for product-level analysis.

---

## 6. Data Processing Patterns (Summary)

> Full code examples and SQL templates: see `data-analyst-sql-templates.md`

### Gender-Type Business Grouping

| Raw `gender` value | Business Segment |
|---|---|
| `Men` | **Men** |
| `Ladies` | **Ladies** |
| `Baby`, `Boys`, `Girls`, `Junior` | **Baby & Kids** (all collapse into one) |

Combine with `tipe` (Fashion/Jepit) for display-level grouping: `"Men Fashion"`, `"Ladies Jepit"`, `"Baby & Kids"`.

### Tier-Aware Adjusted Average

| Tier | Zero-Month Treatment | Why |
|------|---------------------|-----|
| **T1** (fast moving) | Exclude ALL zero months | Zeros = out-of-stock, not demand drop |
| **T8** (new launch) | Exclude leading + post-launch zeros | Leading = not yet launched; post-launch = OOS |
| **T2/T3** (mid-tier) | Contextual (exclude if surrounding months have decent sales) | Distinguishes OOS from real demand decay |
| **T4/T5/other** | Include all months (simple average) | Low movers — zeros likely genuine |

### Turnover (TO) = Stock Coverage

**TO = `current_stock / avg_monthly_sales`** — "How many months will stock last?" High = slow mover, Low = fast mover.

For surplus/pull decisions: sort by `avg_monthly_sales ASC` (slowest sellers pulled first).

### Tier NULL Default

When `tier` is NULL, default to **T3** as conservative fallback: `df["tier"] = df["tier"].fillna("3").astype(str)`

---

## 7. Analysis Methodology

### Step 1: Clarify Scope
- **What product?** Use kode_mix (article) or series/gender for broader scope
- **What time period?** Default to last 3 months if unspecified
- **What geography?** Branch, area, or specific store
- **What metric?** Pairs sold, revenue, stock level, sell-through

### Step 2: Choose the Right View
- **Sales analysis** → `core.sales_with_product`
- **Stock/inventory** → `core.stock_with_product`
- **Combined (sell-through, coverage)** → Join both on `kode_mix`

### Step 3: Apply Business Context
- **Entity:** DDD = retail/wholesale, MBB = online, UBB = wholesale/consignment
- **Store:** Use branch/area for geographic analysis (see `zuma-branch` skill)
- **Product:** Use kode_mix for version-agnostic analysis (see `zuma-sku-context` skill)
- **Tier:** Tier 1 = fast moving, Tier 8 = new launch
- **Pricing:** `rsp` = recommended selling price, `harga_beli` = purchase cost, `price_taq` = price tag

### Step 4: Interpret Results
- **Sales per store:** Higher in Bali (tourist) and Jatim (home base) is normal
- **Stock distribution:** DDD holds most stock, LJBB holds Baby & Kids receiving
- **Tier 8:** New launches — don't compare against established Tier 1 without noting this
- **Missing data:** `kode_mix IS NULL` = product not in kodemix bridge — flag but don't exclude
- **BPP/COGS:** May be 0 (API limitation) — use `harga_beli` from portal.hpprsp as proxy
- **Assortment:** 1 box = 12 pairs always. Use `count_by_assortment` for size-level box calc

### Step 5: Present Findings
- Lead with the key insight, not the SQL
- Use tables for comparisons
- Note data quality caveats (match rates, missing BPP, etc.)
- Suggest actionable next steps when relevant

---

## 8. Common Pitfalls (Avoid These)

| Pitfall | Why It Happens | Correct Approach |
|---------|----------------|------------------|
| Duplicate rows after JOIN | kodemix has multiple versions per kode_besar | Use DISTINCT ON subquery (Rule 2) |
| Missing product enrichment | Case mismatch raw vs portal | Use TRIM(LOWER()) on portal side (Rule 1) |
| Wrong YoY comparison | Different kode_besar across versions | Use kode_mix instead (Rule 6) |
| Excluding valid products | Filtering kodemix by `status = 'Aktif'` | Never filter by status in joins (Rule 3) |
| Empty BPP/COGS | API doesn't return cost data | Use portal.hpprsp.harga_beli as proxy |
| Stock seems low | Only looking at one entity | Use fact_stock_unified or core view |
| Slow query | Querying raw tables with complex joins | Use pre-enriched core views (Rule 5) |
| Mart table not found | Mart tables are ephemeral | Check `information_schema.tables` first |
| Accessories inflate counts | SHOPPING BAG, HANGER in sales data | Exclude non-product items (Rule 8) |
| Unfair sales average | T1 zeros = OOS, T8 zeros = pre-launch | Use tier-aware adjusted average |
| NULL tier silently dropped | kodemix not fully maintained | Default tier NULL to "3" |
| Misunderstanding "TO" | TO = Stock Coverage (stock / avg_sales) | Use `stock_coverage_months` only |
| Store stock returns 0 | `nama_gudang` naming variations | Check with ILIKE first (Rule 9) |

---

## 9. When to Use This Skill

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

## Reference Files

For detailed definitions, query templates, and operational guides, see these files in the same directory:

| File | Contents |
|------|----------|
| `data-analyst-schema-reference.md` | Full column-level definitions for all tables and views across raw, portal, core, mart, public schemas. Includes intercompany detection logic and admin schema queries. |
| `data-analyst-sql-templates.md` | SQL query cookbook (8 example queries), data processing patterns (gender mapping, tier-aware avg, TO formula), standardized SQL templates A/B/C (sales, stock, coverage), column alias conventions, entity migration warnings. |
| `data-analyst-etl-cron.md` | ETL pipeline schedules, DB admin queries (ETL status, data freshness, match rates), and complete setup guide for non-technical users (Python install, library setup, DB access, script execution, troubleshooting). |

---

**Status:** Complete
**Last Updated:** 13 Feb 2026
**Covers:** Database connection, schema architecture, all tables/views, ETL schedule, query rules, data processing patterns, SQL cookbook, analysis methodology, common pitfalls, admin reference, standardized SQL templates, setup guide for non-technical users
