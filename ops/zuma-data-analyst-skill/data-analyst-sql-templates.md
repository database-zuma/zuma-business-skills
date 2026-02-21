# Zuma Data Analyst — SQL Templates & Query Patterns

> This file contains SQL query templates, cookbook examples, data processing patterns, and standardized conventions.
> Referenced from `SKILL.md` in the same directory.

---

## Query Cookbook

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

## Data Processing Patterns

Reusable patterns for cleaning and transforming Zuma data. Apply these whenever building reports, planograms, or any product-level analysis.

### Gender-Type Business Grouping

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

### Tier-Aware Adjusted Average

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

### Turnover (TO) = Stock Coverage

At Zuma, **TO = Stock Coverage**. One formula, no ambiguity:

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **TO / Stock Coverage** | `current_stock / avg_monthly_sales` | "How many months will stock last?" High = slow mover, Low = fast mover |

**Example:** TO 4.5 = stock can hold 4.5 months at current sales rate.

**For surplus/pull decisions:** Sort by `avg_monthly_sales ASC` (slowest sellers pulled first). Do NOT sort by TO directly — use `avg_monthly_sales` which is unambiguous.

### Tier NULL Default

When `tier` is NULL (kodemix not fully maintained), default to **T3** as conservative fallback:

```python
df["tier"] = df["tier"].fillna("3").astype(str)
```

This prevents NULL tiers from being silently dropped in tier-based filtering (`WHERE tier IN ('1','2','3','8')`).

---

## Standardized SQL Templates

**MANDATORY: All AI agents MUST use these templates when querying Zuma data.** Adjust columns, filters, and grouping per user request, but NEVER deviate from the mandatory filters, column aliases, and source tables defined here.

### Question Pattern Framework

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

Column names are DIFFERENT between sales and stock views. This is a common mistake.

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
1. Sales question → Template A
2. Stock question → Template B
3. Sales + Stock combined (TO / coverage) → Template C
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

### Column Alias Conventions

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
| Tier-adjusted average (N months) | `adj_avg_{N}_months` | See Template C |
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

### Mandatory Filters

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

### Template A — Sales Analysis

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

### Template B — Stock / Inventory Analysis

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

### Template C — Stock Coverage & Turnover (TO)

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
      -- Lookback period. Change to '6 months', '12 months' etc. per request.
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
        -- Rename to adj_avg_6_months, adj_avg_12_months etc. if lookback changes
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
| 1.0 - 3.0 | Healthy — normal replenishment cycle |
| 3.0 - 6.0 | Slow mover — monitor, consider markdown |
| > 6.0 | Dead stock — clearance candidate |
| NULL | No sales data or no stock — flag to user |

---

## Entity & Data Warnings

### WARNING A: Online Sales Entity Migration (DDD to MBB)

Online/marketplace sales migrated **gradually from DDD to MBB between Feb-Aug 2025:**

| Period | DDD (`"zuma online"`) | MBB (`"online"`) | Status |
|--------|---|---|---|
| 2022-01 to 2025-01 | All online sales | — | 100% on DDD |
| **2025-02** | 5,105 pairs | 1,194 pairs | Migration starts |
| **2025-03** | 5,081 pairs | 11,920 pairs | MBB overtakes DDD |
| 2025-04 to 2025-07 | Declining (2,374-3,947) | Growing (6,784-12,720) | Gradual shift |
| **2025-08** | 3 pairs | 14,518 pairs | DDD online effectively dead |
| 2025-08 to present | ~0 | 11,000-15,000/mo | 100% on MBB |

**Store names are different per entity:** DDD = `"zuma online"`, MBB = `"online"`.

**Rules:**
- When analyzing **online sales trends across years**, combine both entities: `WHERE LOWER(store_name_raw) IN ('zuma online', 'online')` — do NOT filter by `source_entity`.
- When filtering by `source_entity = 'DDD'` for any time range crossing 2025, **always note** that online sales moved to MBB and DDD numbers will appear to drop.
- When filtering by `source_entity = 'MBB'`, **always note** that data before Feb 2025 will show near-zero (not because no sales existed, but because they were under DDD).
- All **offline retail stores remain under DDD** — this migration only affects online channels.

### WARNING B: Cross-Entity Stock Discrepancies

Stock data can show negative quantities in one entity when stock has been physically moved but not yet recorded in the system. Common pattern:

- **LJBB** shows +N (stock received from supplier) while **DDD** shows -N for the same article → stock is physically at DDD, system transfer pending.
- **MBB** can also show negative stock for the same reason (stock already at DDD but untransacted).

**When you see negative stock for any entity:** Notify the user that this likely means the stock physically exists but the inter-entity system transfer hasn't been recorded yet. Suggest checking the same `kode_mix` across all entities to get the net real quantity.
