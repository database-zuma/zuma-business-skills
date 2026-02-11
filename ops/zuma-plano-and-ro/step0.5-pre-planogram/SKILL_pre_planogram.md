---
name: pre-planogram-zuma
version: "1.0"
description: Generate pre-planogram data table (size-level target quantities per store/article) from VPS DB. Output feeds into planogram layout engine (STEP 1) and FF/FA/FS metrics.
dependencies:
  - zuma-data-ops
  - zuma-sku-context
user-invocable: true
---

# Pre-Planogram Data Table Generator

This skill produces the **pre-planogram data table** -- a size-level target quantity matrix per store per article. It is the numerical foundation that feeds into:

1. **STEP 1 (Planogram Layout Engine)** -- assigns articles to physical display components (backwalls, gondolas, tables)
2. **FF/FA/FS Metric System** -- calculates Fill Factor, Fill Accuracy, and Fill Score per store

The pre-planogram answers: "For each article in each store, how many pairs of each size should ideally be present?"

---

## 1. What the Pre-Planogram Is

The pre-planogram is a **wide-format table** with one row per article per store. Each row contains:

- Article identification (gender, series, article name, tier, kode_mix)
- 28 size columns (from Baby 18/19 through Adult 45/46) with fractional target quantities
- Aggregated sales metrics (adjusted average, sales mix percentage)
- Recommendation quantities (pairs and boxes)

It does NOT contain:
- Physical display assignment (which backwall, which hook) -- that is STEP 1
- RO request logic (what to order from warehouse) -- that is STEP 3
- Visual layout rendering -- that is STEP 2

### Output Shape

For a typical Jatim region planogram: ~2,500-2,900 rows across ~11 retail stores, with 28 size columns plus metadata columns.

---

## 2. Data Sources

### 2.1 VPS PostgreSQL Database (Primary)

| Field | Value |
|-------|-------|
| Host | `76.13.194.120` |
| Port | `5432` |
| Database | `openclaw_ops` |
| User | `openclaw_app` |
| Password | `Zuma-0psCl4w-2026!` |

**Connection string:**
```
postgresql://openclaw_app:Zuma-0psCl4w-2026!@76.13.194.120:5432/openclaw_ops
```

**Python connection:**
```python
import psycopg2
import pandas as pd

DB = dict(host="76.13.194.120", port=5432, dbname="openclaw_ops",
          user="openclaw_app", password="Zuma-0psCl4w-2026!")
conn = psycopg2.connect(**DB)
```

#### Tables and Views Used

| Source | Schema.Object | Purpose |
|--------|--------------|---------|
| Sales data | `core.sales_with_product` | Monthly sales per article per store (~1.55M rows) |
| Stock data | `core.stock_with_product` | Current stock per article per store/warehouse (~142K rows) |
| Product master | `portal.kodemix` | Assortment ratios: kode_mix, size, count_by_assortment (~5,464 rows) |
| Store master | `portal.store` | Store list with branch, area, category |

#### Critical DB Rules (from zuma-data-ops)

These rules are NON-NEGOTIABLE. Violating any of them produces incorrect data.

1. **TRIM(LOWER()) for all string matching.** Raw tables use lowercase; portal tables use mixed case. Every join to portal must normalize both sides.
2. **DISTINCT ON for kodemix deduplication.** `portal.kodemix` has multiple rows per `kode_besar` (one per version V0-V4). Always deduplicate with `DISTINCT ON (TRIM(LOWER(kode_besar)))` ordered by `no_urut`.
3. **Never filter kodemix by status.** Do NOT add `WHERE status = 'Aktif'`. All products must be matchable regardless of active/discontinued status.
4. **Always use core views, not raw tables.** `core.sales_with_product` and `core.stock_with_product` are pre-enriched with product and store data.
5. **Use kode_mix for version-agnostic aggregation.** Different product versions (V0-V4) have different `kode_besar` codes but the same `kode_mix`. Always group by `kode_mix` for cross-version analysis.
6. **Always exclude intercompany transactions.** Filter: `WHERE (is_intercompany IS NULL OR is_intercompany = FALSE)`.
7. **Exclude non-product items.** Filter out SHOPPING BAG, HANGER, PAPER BAG, THERMAL, BOX LUCA from article names.
8. **Default NULL tier to '3'.** When `tier` is NULL, treat as T3 (conservative fallback).

### 2.2 External File (Store Layout)

| File | Location | Purpose |
|------|----------|---------|
| `Data Option By Region.xlsx` | Same directory as planogram skills | MaxDisplay, MaxStock, Storage capacity per store |

This file has one sheet per region (Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali). Each sheet lists stores with their display capacity constraints.

Key columns from this file:
- **MaxDisplay** -- maximum pairs that can be displayed (across all display components)
- **MaxStock** -- maximum total stock (display + storage)
- **Storage** -- storage capacity in boxes

---

## 3. Calculation Pipeline

### Step 1: Pull Sales Data from VPS

Query `core.sales_with_product` for the target area. Filter to RETAIL stores only, exclude intercompany, and aggregate monthly.

**Parameters:**
- `TARGET_AREA` -- e.g., 'Jatim', 'Jakarta', 'Bali'
- `DATE_START` -- start of analysis window (typically 12 months back)
- `DATE_END` -- end of analysis window (typically current month)

```sql
SELECT
    matched_store_name AS store_name,
    kode_mix,
    article,
    gender,
    series,
    tipe,
    COALESCE(tier, '3') AS tier,
    TO_CHAR(transaction_date, 'YYYY-MM') AS bulan,
    SUM(quantity) AS total_qty
FROM core.sales_with_product
WHERE area = :target_area
  AND store_category = 'RETAIL'
  AND (is_intercompany IS NULL OR is_intercompany = FALSE)
  AND transaction_date >= :date_start
  AND transaction_date <= :date_end
  AND quantity > 0
  AND kode_mix IS NOT NULL
  AND UPPER(article) NOT LIKE '%SHOPPING BAG%'
  AND UPPER(article) NOT LIKE '%HANGER%'
  AND UPPER(article) NOT LIKE '%PAPER BAG%'
  AND UPPER(article) NOT LIKE '%THERMAL%'
  AND UPPER(article) NOT LIKE '%BOX LUCA%'
GROUP BY matched_store_name, kode_mix, article, gender, series, tipe, tier,
         TO_CHAR(transaction_date, 'YYYY-MM')
ORDER BY store_name, kode_mix, bulan;
```

**Output:** Monthly sales pivot table per article per store.

### Step 2: Calculate Adjusted Average Sales

Apply tier-specific averaging rules to handle out-of-stock months vs genuine zero-demand months. This prevents penalizing fast sellers that were temporarily unavailable.

**Tier rules:**

| Tier | Zero-Month Treatment | Rationale |
|------|---------------------|-----------|
| T1 (Fast Moving) | EXCLUDE all zero months from divisor | Zeros = out-of-stock, not demand drop |
| T8 (New Launch) | EXCLUDE leading zeros (pre-launch) + post-launch zeros (OOS) | Leading zeros = not yet launched |
| T2/T3 (Mid-tier) | Contextual: exclude zero if surrounding months have >50% of overall avg; include if genuine decline | Distinguishes OOS from real demand decay |
| T4/T5 (Slow/Dead) | INCLUDE all months (simple average) | Zeros are genuine low demand |

```python
def adjusted_average(month_values, tier):
    """Calculate tier-aware adjusted average from monthly sales list."""
    tier = str(tier)

    if tier == '1':
        # T1: exclude zero months (likely OOS)
        nonzero = [v for v in month_values if v > 0]
        return sum(nonzero) / len(nonzero) if nonzero else 0

    elif tier == '8':
        # T8: skip pre-launch zeros, skip post-launch OOS zeros
        first_sale = next((i for i, v in enumerate(month_values) if v > 0), None)
        if first_sale is not None:
            active = [v for v in month_values[first_sale:] if v > 0]
            return sum(active) / len(active) if active else 0
        return 0

    elif tier in ('2', '3'):
        # T2/T3: contextual -- check surrounding months
        overall_avg = sum(month_values) / len(month_values) if month_values else 0
        active_months = 0
        active_total = 0
        for i, v in enumerate(month_values):
            if v > 0:
                active_months += 1
                active_total += v
            else:
                surrounding = []
                for j in range(max(0, i - 2), min(len(month_values), i + 3)):
                    if j != i and month_values[j] > 0:
                        surrounding.append(month_values[j])
                if surrounding and (sum(surrounding) / len(surrounding)) > overall_avg * 0.5:
                    pass  # Exclude this zero (likely OOS)
                else:
                    active_months += 1  # Include zero (genuine decline)
        return active_total / active_months if active_months > 0 else 0

    else:
        # T4/T5: full average including zeros
        return sum(month_values) / len(month_values) if month_values else 0
```

**Output:** `adjusted_avg_sales` per article per store (pairs/month).

### Step 3: Calculate Sales Mix Percentage

Per store, compute each article's share of total adjusted average sales.

```python
# Per store: calculate sales mix
for store in stores:
    store_articles = df[df['store_name'] == store]
    total_adj_avg = store_articles['adj_avg'].sum()
    store_articles['sales_mix'] = store_articles['adj_avg'] / total_adj_avg
```

**Formula:** `sales_mix = article_adj_avg / SUM(all_article_adj_avg_in_store)`

**Output:** `%Sales Mix` per article per store (decimal, e.g., 0.048 = 4.8%).

### Step 4: Determine Article Eligibility per Store

Filter articles based on tier for display eligibility:

| Tier | Eligibility | Rule |
|------|------------|------|
| T1 | MUST display | Non-negotiable, all T1 articles included |
| T8 | Priority display | New launches need exposure |
| T2 | Fill remaining | Secondary fast movers fill remaining capacity |
| T3 | Filler | For variety/completeness if capacity allows |
| T4 | DO NOT display | Discontinued/slow -- exclude from pre-planogram |
| T5 | DO NOT display | Dead stock -- exclude from pre-planogram |

```python
ELIGIBLE_TIERS = ['1', '8', '2', '3']
df_eligible = df[df['tier'].isin(ELIGIBLE_TIERS)].copy()
```

### Step 5: Calculate Rekomendasi (Recommendation)

Based on store capacity (MaxDisplay from `Data Option By Region.xlsx`) and sales mix, calculate how many pairs and boxes each article should have.

```python
# MaxDisplay comes from the external Excel file per store
# rekomendasi_pairs = sales_mix * total_store_display_capacity_pairs
df_eligible['rekomendasi_pairs'] = df_eligible['sales_mix'] * store_max_display

# rekomendasi_box = CEIL(rekomendasi_pairs / 12)
import math
df_eligible['rekomendasi_box'] = df_eligible['rekomendasi_pairs'].apply(
    lambda x: math.ceil(x / 12)
)
```

**Output:** `Rekomendasi (pairs)` and `Rekomendasi (box)` per article per store.

### Step 6: Distribute to Size-Level Quantities (THE KEY STEP)

This is the core transformation that converts article-level recommendations into size-level target quantities using the assortment ratio from `portal.kodemix`.

#### 6a. Pull Assortment Data

```sql
-- Get size distribution per kode_mix (deduplicated)
-- IMPORTANT: Multiple assortment patterns may exist per kode_mix (different versions).
-- Use the LATEST version's assortment (lowest no_urut).
SELECT
    kode_mix,
    size,
    count_by_assortment::int AS count_by_assortment
FROM (
    SELECT DISTINCT ON (kode_mix, size)
        kode_mix,
        size,
        count_by_assortment,
        no_urut
    FROM portal.kodemix
    WHERE kode_mix IS NOT NULL
      AND size IS NOT NULL
      AND count_by_assortment IS NOT NULL
    ORDER BY kode_mix, size, no_urut
) sub
WHERE count_by_assortment::int > 0;
```

#### 6b. Calculate Size Ratios

For each article (kode_mix), compute the proportional ratio per size:

```python
def get_size_ratios(assortment_df, kode_mix):
    """
    Get size distribution ratios for a given kode_mix.

    Example for MEN CLASSIC (kode_mix M1AZCZCA22, assortment 1-2-3-3-2-1):
        size 39: count_by_assortment = 1, ratio = 1/12 = 0.0833
        size 40: count_by_assortment = 2, ratio = 2/12 = 0.1667
        size 41: count_by_assortment = 3, ratio = 3/12 = 0.2500
        size 42: count_by_assortment = 3, ratio = 3/12 = 0.2500
        size 43: count_by_assortment = 2, ratio = 2/12 = 0.1667
        size 44: count_by_assortment = 1, ratio = 1/12 = 0.0833
        TOTAL = 12/12 = 1.0
    """
    article_sizes = assortment_df[assortment_df['kode_mix'] == kode_mix].copy()
    if article_sizes.empty:
        return None  # No assortment data -- flag this article

    total_assortment = article_sizes['count_by_assortment'].sum()
    if total_assortment == 0:
        return None

    article_sizes['ratio'] = article_sizes['count_by_assortment'] / total_assortment
    return article_sizes[['size', 'ratio']].set_index('size')['ratio'].to_dict()
```

#### 6c. Distribute Recommendation to Sizes

```python
# 28 standard size columns (ordered)
SIZE_COLUMNS = [
    '18/19', '20/21', '21/22', '22/23', '23/24', '24/25', '25/26',
    '27/28', '29/30', '31/32', '33/34',
    '34', '35', '35/36', '36', '37', '37/38', '38',
    '39', '39/40', '40', '41', '41/42', '42', '43', '43/44', '44', '45/46'
]

def distribute_to_sizes(rekomendasi_pairs, size_ratios, size_columns):
    """
    Distribute article-level recommendation to size-level quantities.

    CRITICAL: Do NOT round the results. Fractional values are intentional.
    They represent proportional targets for the FF/FA/FS metric system.

    Example:
        rekomendasi_pairs = 6.0
        size_ratios = {39: 0.0833, 40: 0.1667, 41: 0.25, 42: 0.25, 43: 0.1667, 44: 0.0833}

        Result:
            39: 6.0 * 0.0833 = 0.5
            40: 6.0 * 0.1667 = 1.0
            41: 6.0 * 0.25   = 1.5
            42: 6.0 * 0.25   = 1.5
            43: 6.0 * 0.1667 = 1.0
            44: 6.0 * 0.0833 = 0.5
    """
    result = {}
    for size_col in size_columns:
        if size_col in size_ratios:
            result[size_col] = rekomendasi_pairs * size_ratios[size_col]
        else:
            result[size_col] = None  # Empty -- size does not apply to this article
    return result
```

**Output:** 28 size columns per row, with fractional values or empty cells.

### Step 7: Build Output Table

Assemble the final wide-format table.

```python
output_rows = []
for _, row in df_eligible.iterrows():
    size_ratios = get_size_ratios(assortment_df, row['kode_mix'])

    if size_ratios is None:
        # Flag: no assortment data
        size_values = {col: None for col in SIZE_COLUMNS}
        flag = 'NO_ASSORTMENT'
    else:
        size_values = distribute_to_sizes(row['rekomendasi_pairs'], size_ratios, SIZE_COLUMNS)
        flag = None

    output_row = {
        'Store Name': row['store_name'],
        'Gender': row['gender'],
        'Series': row['series'],
        'Article': row['article'],
        'Tier': row['tier'],
        'article mix': row['kode_mix'],  # kode_mix from portal.kodemix
        **size_values,
        'AVG Sales 3 Months (pairs)': row['avg_sales_3mo'],
        'AVG Sales 3 Months (box)': row['avg_sales_3mo'] / 12,
        '%Sales Mix': row['sales_mix'],
        'Rekomendasi (pairs)': row['rekomendasi_pairs'],
        'Rekomendasi (box)': row['rekomendasi_box'],
    }
    if flag:
        output_row['_flag'] = flag
    output_rows.append(output_row)

output_df = pd.DataFrame(output_rows)
```

---

## 4. Output Format Specification

### Column Layout

The output table has the following column order:

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | Store Name | text | Store name (e.g., "Zuma Matos") |
| 2 | Gender | text | MEN, LADIES, BABY, BOYS, GIRLS, JUNIOR |
| 3 | Series | text | CLASSIC, SLIDE, AIRMOVE, ELSA, etc. |
| 4 | Article | text | Full article name (e.g., "MEN BLACK SERIES 12") |
| 5 | Tier | text | 1, 2, 3, 8 (T4/T5 excluded) |
| 6 | article mix | text | kode_mix from portal.kodemix (e.g., "M1BLVLV212") |
| 7-34 | 28 size columns | float/empty | Fractional target quantities per size |
| 35 | AVG Sales 3 Months (pairs) | float | Adjusted average over last 3 months |
| 36 | AVG Sales 3 Months (box) | float | AVG Sales 3 Months (pairs) / 12 |
| 37 | %Sales Mix | float | Article share of total store sales (decimal) |
| 38 | Rekomendasi (pairs) | float | Target pairs = sales_mix * MaxDisplay |
| 39 | Rekomendasi (box) | int | CEIL(Rekomendasi pairs / 12) |

### 28 Size Columns (Ordered)

```
18/19, 20/21, 21/22, 22/23, 23/24, 24/25, 25/26,
27/28, 29/30, 31/32, 33/34,
34, 35, 35/36, 36, 37, 37/38, 38,
39, 39/40, 40, 41, 41/42, 42, 43, 43/44, 44, 45/46
```

Size ranges by gender (approximate):
- **Baby:** 18/19 through 25/26 (double-size)
- **Kids/Junior:** 27/28 through 33/34
- **Ladies:** 34 through 40
- **Men:** 39 through 45/46

### Example Row

```
Store Name  | Gender | Series      | Article              | Tier | article mix | ... | 39  | 39/40 | 40  | 41  | 41/42 | 42  | 43  | 43/44 | 44  | ... | AVG Sales 3M (pairs) | AVG Sales 3M (box) | %Sales Mix | Rekom (pairs) | Rekom (box)
Zuma Matos  | MEN    | BLACKSERIES | MEN BLACK SERIES 12  | 1    | M1BLVLV212  | ... | 0.5 |       | 1.0 | 1.0 |       | 1.5 | 1.0 |       | 1.0 | ... | 22                   | 1.833              | 0.048      | 1.381         | 2
```

Notes:
- Empty cells (not 0) for sizes that do not apply to the article
- Fractional values (0.5, 1.5, etc.) are correct and intentional -- do NOT round
- One row per article per store

---

## 5. SQL Query Templates

### 5.1 Monthly Sales Pivot per Article per Store

```sql
-- Parameters: :target_area, :date_start, :date_end
SELECT
    matched_store_name AS store_name,
    kode_mix,
    article,
    gender,
    series,
    tipe,
    COALESCE(tier, '3') AS tier,
    TO_CHAR(transaction_date, 'YYYY-MM') AS bulan,
    SUM(quantity) AS total_qty
FROM core.sales_with_product
WHERE area = :target_area
  AND store_category = 'RETAIL'
  AND (is_intercompany IS NULL OR is_intercompany = FALSE)
  AND transaction_date >= :date_start
  AND transaction_date <= :date_end
  AND quantity > 0
  AND kode_mix IS NOT NULL
  AND UPPER(article) NOT LIKE '%SHOPPING BAG%'
  AND UPPER(article) NOT LIKE '%HANGER%'
  AND UPPER(article) NOT LIKE '%PAPER BAG%'
  AND UPPER(article) NOT LIKE '%THERMAL%'
  AND UPPER(article) NOT LIKE '%BOX LUCA%'
GROUP BY matched_store_name, kode_mix, article, gender, series, tipe, tier,
         TO_CHAR(transaction_date, 'YYYY-MM')
ORDER BY store_name, kode_mix, bulan;
```

### 5.2 Current Stock per Article per Store

```sql
-- Parameters: :target_area
SELECT
    TRIM(LOWER(nama_gudang)) AS store_name,
    kode_mix,
    article,
    gender,
    series,
    tipe AS product_type,
    COALESCE(tier, '3') AS tier,
    size,
    SUM(quantity) AS stock_qty
FROM core.stock_with_product
WHERE gudang_area = :target_area
  AND gudang_category = 'RETAIL'
  AND kode_mix IS NOT NULL
GROUP BY nama_gudang, kode_mix, article, gender, series, tipe, tier, size
ORDER BY store_name, kode_mix, size;
```

### 5.3 Assortment / Size Distribution per kode_mix

```sql
-- Get the latest version's assortment per kode_mix per size (deduplicated)
SELECT
    kode_mix,
    size,
    count_by_assortment::int AS count_by_assortment
FROM (
    SELECT DISTINCT ON (kode_mix, size)
        kode_mix,
        size,
        count_by_assortment,
        no_urut
    FROM portal.kodemix
    WHERE kode_mix IS NOT NULL
      AND size IS NOT NULL
      AND count_by_assortment IS NOT NULL
      AND count_by_assortment::int > 0
    ORDER BY kode_mix, size, no_urut
) sub
ORDER BY kode_mix, size;
```

### 5.4 Store List with Capacity Data

```sql
-- Parameters: :target_area
SELECT DISTINCT ON (TRIM(LOWER(nama_accurate)))
    TRIM(LOWER(nama_accurate)) AS store_name,
    branch,
    area,
    category
FROM portal.store
WHERE area = :target_area
  AND category = 'RETAIL'
ORDER BY TRIM(LOWER(nama_accurate));
```

Note: MaxDisplay, MaxStock, and Storage capacity come from the external `Data Option By Region.xlsx` file, not from the database. Join the store list with the Excel data by store name (case-insensitive match).

### 5.5 AVG Sales Last 3 Months (for output column)

The "AVG Sales 3 Months" output column uses the same adjusted average logic but over only the last 3 months instead of 12. Compute this separately:

```sql
-- Parameters: :target_area, 3 months back from :date_end
SELECT
    matched_store_name AS store_name,
    kode_mix,
    TO_CHAR(transaction_date, 'YYYY-MM') AS bulan,
    SUM(quantity) AS total_qty
FROM core.sales_with_product
WHERE area = :target_area
  AND store_category = 'RETAIL'
  AND (is_intercompany IS NULL OR is_intercompany = FALSE)
  AND transaction_date >= (:date_end::date - INTERVAL '3 months')
  AND transaction_date <= :date_end
  AND quantity > 0
  AND kode_mix IS NOT NULL
GROUP BY matched_store_name, kode_mix, TO_CHAR(transaction_date, 'YYYY-MM');
```

Then apply the same `adjusted_average()` function from Step 2 over the 3-month window.

---

## 6. Complete Python Pipeline

```python
"""
Pre-Planogram Data Table Generator
Generates size-level target quantities per store/article for a given area.
"""

import psycopg2
import pandas as pd
import numpy as np
import math

# ============================================================
# CONFIG
# ============================================================
TARGET_AREA = "Jatim"  # Parameterize: Jatim, Jakarta, Bali, etc.
DATE_START = "2025-02-01"
DATE_END = "2026-01-31"
DATE_3MO_START = "2025-11-01"  # 3 months before DATE_END

DB = dict(host="76.13.194.120", port=5432, dbname="openclaw_ops",
          user="openclaw_app", password="Zuma-0psCl4w-2026!")

SIZE_COLUMNS = [
    '18/19', '20/21', '21/22', '22/23', '23/24', '24/25', '25/26',
    '27/28', '29/30', '31/32', '33/34',
    '34', '35', '35/36', '36', '37', '37/38', '38',
    '39', '39/40', '40', '41', '41/42', '42', '43', '43/44', '44', '45/46'
]

NON_PRODUCT = ["SHOPPING BAG", "HANGER", "PAPER BAG", "THERMAL", "BOX LUCA"]

# Store capacities from Data Option By Region.xlsx (load separately)
# Format: {store_name_lower: {'MaxDisplay': int, 'MaxStock': int, 'Storage': int}}
STORE_CAPACITIES = {}  # Populate from Excel file

# ============================================================
# STEP 1: PULL DATA
# ============================================================
def pull_data():
    conn = psycopg2.connect(**DB)

    # 12-month sales
    sales_df = pd.read_sql(f"""
        SELECT matched_store_name AS store_name, kode_mix, article,
               gender, series, tipe, COALESCE(tier, '3') AS tier,
               TO_CHAR(transaction_date, 'YYYY-MM') AS bulan,
               SUM(quantity) AS total_qty
        FROM core.sales_with_product
        WHERE area = '{TARGET_AREA}'
          AND store_category = 'RETAIL'
          AND (is_intercompany IS NULL OR is_intercompany = FALSE)
          AND transaction_date >= '{DATE_START}' AND transaction_date <= '{DATE_END}'
          AND quantity > 0 AND kode_mix IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8
        ORDER BY 1,2,8
    """, conn)

    # 3-month sales (for output column)
    sales_3mo_df = pd.read_sql(f"""
        SELECT matched_store_name AS store_name, kode_mix,
               TO_CHAR(transaction_date, 'YYYY-MM') AS bulan,
               SUM(quantity) AS total_qty
        FROM core.sales_with_product
        WHERE area = '{TARGET_AREA}'
          AND store_category = 'RETAIL'
          AND (is_intercompany IS NULL OR is_intercompany = FALSE)
          AND transaction_date >= '{DATE_3MO_START}' AND transaction_date <= '{DATE_END}'
          AND quantity > 0 AND kode_mix IS NOT NULL
        GROUP BY 1,2,3
    """, conn)

    # Assortment data (deduplicated)
    assortment_df = pd.read_sql("""
        SELECT kode_mix, size, count_by_assortment::int AS count_by_assortment
        FROM (
            SELECT DISTINCT ON (kode_mix, size)
                kode_mix, size, count_by_assortment, no_urut
            FROM portal.kodemix
            WHERE kode_mix IS NOT NULL AND size IS NOT NULL
              AND count_by_assortment IS NOT NULL
              AND count_by_assortment::int > 0
            ORDER BY kode_mix, size, no_urut
        ) sub
        ORDER BY kode_mix, size
    """, conn)

    # Store list
    stores_df = pd.read_sql(f"""
        SELECT DISTINCT ON (TRIM(LOWER(nama_accurate)))
            TRIM(LOWER(nama_accurate)) AS store_name, branch, area, category
        FROM portal.store
        WHERE area = '{TARGET_AREA}' AND category = 'RETAIL'
        ORDER BY TRIM(LOWER(nama_accurate))
    """, conn)

    conn.close()

    # Filter non-product items
    mask = sales_df['article'].str.upper().apply(
        lambda x: not any(p in str(x) for p in NON_PRODUCT))
    sales_df = sales_df[mask].copy()

    return sales_df, sales_3mo_df, assortment_df, stores_df


# ============================================================
# STEP 2: ADJUSTED AVERAGE
# ============================================================
def adjusted_average(month_values, tier):
    tier = str(tier)
    if tier == '1':
        nonzero = [v for v in month_values if v > 0]
        return sum(nonzero) / len(nonzero) if nonzero else 0
    elif tier == '8':
        first_sale = next((i for i, v in enumerate(month_values) if v > 0), None)
        if first_sale is not None:
            active = [v for v in month_values[first_sale:] if v > 0]
            return sum(active) / len(active) if active else 0
        return 0
    elif tier in ('2', '3'):
        overall_avg = sum(month_values) / len(month_values) if month_values else 0
        active_months, active_total = 0, 0
        for i, v in enumerate(month_values):
            if v > 0:
                active_months += 1
                active_total += v
            else:
                surrounding = [month_values[j] for j in range(max(0, i-2), min(len(month_values), i+3))
                               if j != i and month_values[j] > 0]
                if surrounding and np.mean(surrounding) > overall_avg * 0.5:
                    pass  # Exclude (likely OOS)
                else:
                    active_months += 1
        return active_total / active_months if active_months > 0 else 0
    else:
        return sum(month_values) / len(month_values) if month_values else 0


def compute_adjusted_averages(sales_df, date_start, date_end):
    all_months = pd.date_range(date_start, date_end, freq='MS').strftime('%Y-%m').tolist()

    results = []
    for (store, kode_mix, article, gender, series, tipe, tier), grp in \
            sales_df.groupby(['store_name', 'kode_mix', 'article', 'gender', 'series', 'tipe', 'tier']):
        monthly = dict(zip(grp['bulan'], grp['total_qty']))
        month_values = [monthly.get(m, 0) for m in all_months]
        adj_avg = adjusted_average(month_values, tier)
        results.append({
            'store_name': store, 'kode_mix': kode_mix, 'article': article,
            'gender': gender, 'series': series, 'tipe': tipe, 'tier': tier,
            'adj_avg_12mo': round(adj_avg, 2),
        })
    return pd.DataFrame(results)


# ============================================================
# STEP 3-5: SALES MIX, ELIGIBILITY, RECOMMENDATION
# ============================================================
def compute_recommendations(avg_df, sales_3mo_df, store_capacities):
    # Filter eligible tiers
    eligible = avg_df[avg_df['tier'].isin(['1', '8', '2', '3'])].copy()

    # Compute 3-month adjusted average per article per store
    months_3mo = pd.date_range(DATE_3MO_START, DATE_END, freq='MS').strftime('%Y-%m').tolist()
    avg_3mo_map = {}
    for (store, kode_mix), grp in sales_3mo_df.groupby(['store_name', 'kode_mix']):
        monthly = dict(zip(grp['bulan'], grp['total_qty']))
        vals = [monthly.get(m, 0) for m in months_3mo]
        # Use simple average for 3-month column (tier logic already applied in 12mo)
        avg_3mo_map[(store, kode_mix)] = sum(vals) / len(vals) if vals else 0

    eligible['avg_sales_3mo'] = eligible.apply(
        lambda r: avg_3mo_map.get((r['store_name'], r['kode_mix']), 0), axis=1)
    eligible['avg_sales_3mo_box'] = eligible['avg_sales_3mo'] / 12

    # Sales mix per store
    store_totals = eligible.groupby('store_name')['adj_avg_12mo'].sum().to_dict()
    eligible['sales_mix'] = eligible.apply(
        lambda r: r['adj_avg_12mo'] / store_totals[r['store_name']]
        if store_totals.get(r['store_name'], 0) > 0 else 0, axis=1)

    # Recommendation
    eligible['rekomendasi_pairs'] = eligible.apply(
        lambda r: r['sales_mix'] * store_capacities.get(r['store_name'], {}).get('MaxDisplay', 0),
        axis=1)
    eligible['rekomendasi_box'] = eligible['rekomendasi_pairs'].apply(lambda x: math.ceil(x / 12))

    return eligible


# ============================================================
# STEP 6: SIZE DISTRIBUTION
# ============================================================
def get_size_ratios(assortment_df, kode_mix):
    sizes = assortment_df[assortment_df['kode_mix'] == kode_mix]
    if sizes.empty:
        return None
    total = sizes['count_by_assortment'].sum()
    if total == 0:
        return None
    return dict(zip(sizes['size'], sizes['count_by_assortment'] / total))


def distribute_to_sizes(rekomendasi_pairs, size_ratios):
    result = {}
    for col in SIZE_COLUMNS:
        if size_ratios and col in size_ratios:
            result[col] = rekomendasi_pairs * size_ratios[col]
        else:
            result[col] = None  # Empty -- size does not apply
    return result


# ============================================================
# STEP 7: BUILD OUTPUT
# ============================================================
def build_output(eligible_df, assortment_df):
    rows = []
    no_assortment = []

    for _, r in eligible_df.iterrows():
        ratios = get_size_ratios(assortment_df, r['kode_mix'])
        if ratios is None:
            no_assortment.append(r['kode_mix'])
            # Fallback: equal distribution across known sizes for this gender
            size_vals = {col: None for col in SIZE_COLUMNS}
        else:
            size_vals = distribute_to_sizes(r['rekomendasi_pairs'], ratios)

        row = {
            'Store Name': r['store_name'],
            'Gender': r['gender'],
            'Series': r['series'],
            'Article': r['article'],
            'Tier': r['tier'],
            'article mix': r['kode_mix'],
            **size_vals,
            'AVG Sales 3 Months (pairs)': round(r['avg_sales_3mo'], 2),
            'AVG Sales 3 Months (box)': round(r['avg_sales_3mo'] / 12, 3),
            '%Sales Mix': round(r['sales_mix'], 4),
            'Rekomendasi (pairs)': round(r['rekomendasi_pairs'], 3),
            'Rekomendasi (box)': r['rekomendasi_box'],
        }
        rows.append(row)

    if no_assortment:
        unique_missing = set(no_assortment)
        print(f"WARNING: {len(unique_missing)} articles have no assortment data: "
              f"{list(unique_missing)[:10]}...")

    return pd.DataFrame(rows)


# ============================================================
# MAIN
# ============================================================
def main():
    print("Step 1: Pulling data from VPS...")
    sales_df, sales_3mo_df, assortment_df, stores_df = pull_data()
    print(f"  Sales rows: {len(sales_df)}, Stores: {len(stores_df)}")

    print("Step 2: Computing adjusted averages (12 months)...")
    avg_df = compute_adjusted_averages(sales_df, DATE_START, DATE_END)
    print(f"  Article-store combinations: {len(avg_df)}")

    print("Steps 3-5: Sales mix, eligibility, recommendations...")
    eligible_df = compute_recommendations(avg_df, sales_3mo_df, STORE_CAPACITIES)
    print(f"  Eligible rows (T1/T2/T3/T8): {len(eligible_df)}")

    print("Steps 6-7: Size distribution and output...")
    output_df = build_output(eligible_df, assortment_df)
    print(f"  Output rows: {len(output_df)}")

    # Save to Excel
    output_df.to_excel(f"Pre_Planogram_{TARGET_AREA}.xlsx", index=False)
    print(f"Saved: Pre_Planogram_{TARGET_AREA}.xlsx")

if __name__ == "__main__":
    main()
```

---

## 7. Business Rules

1. **"article mix" column** = `kode_mix` from `portal.kodemix`. This is the version-agnostic article identifier that unifies V0-V4 product codes.

2. **AVG Sales 3 Months** = adjusted average over the last 3 months (not 12). The 12-month window is used for sales mix and recommendation calculation; the 3-month window is displayed as a reference metric.

3. **AVG Sales 3 Months (box)** = AVG Sales 3 Months (pairs) / 12. Always 12 pairs per box.

4. **Assortment distribution uses `count_by_assortment`**, NOT equal distribution. The ratio is `count_by_assortment / SUM(count_by_assortment)` per kode_mix. This reflects the actual box packing pattern (e.g., more size 42 than size 39 in a Men Classic box).

5. **Fractional size quantities are intentional.** A value of 0.5 means "half a pair target for this size" -- this is a proportional target used by the FF/FA/FS metric system, not a physical count. Do NOT round.

6. **One row per article per store.** Sizes are columns, not rows. This wide format matches the FF/FA/FS planogram sheet structure.

7. **Stores filtered by area + category RETAIL only.** Non-retail, event, and wholesale channels are excluded.

8. **Empty cells for inapplicable sizes** (not 0). A Men article has no value in Baby size columns. An empty cell means "this size does not exist for this article." A 0 would mean "this size exists but target is zero" -- different semantics.

9. **Tier NULL defaults to '3'.** If `tier` is NULL in the database (kodemix not fully maintained), treat as T3 (conservative mid-tier).

10. **Intercompany transactions are always excluded.** These are paper transfers between Zuma entities (DDD, MBB, UBB, LJBB), not real customer sales.

---

## 8. Edge Cases

### Articles with No Assortment Data

Some articles in sales data may not have a matching entry in `portal.kodemix` with valid `count_by_assortment` values.

**Detection:**
```python
if get_size_ratios(assortment_df, kode_mix) is None:
    # No assortment data for this article
```

**Handling:**
- Log a warning with the kode_mix and article name
- Leave all 28 size columns as empty (None)
- Still include the row in output with article-level metrics (adj_avg, sales_mix, rekomendasi)
- Flag the row for manual review

**Fallback (optional):** If the user requests it, use equal distribution across the sizes known for that gender-series combination. This is a rough approximation and should be clearly marked.

### New Stores with No Sales History

A store that recently opened will have no or very limited sales data.

**Handling:**
- Use the area average as a proxy: compute adjusted averages across all stores in the same area, then apply those averages to the new store
- Scale by the new store's MaxDisplay capacity relative to the area average MaxDisplay
- Flag these rows as "PROXY_FROM_AREA_AVG"

### Articles Sold but Not in Kodemix

Some `kode_besar` values in raw sales may not map to any `kode_mix` in `portal.kodemix`.

**Detection:** `kode_mix IS NULL` in `core.sales_with_product` (~6% of rows).

**Handling:**
- These are already filtered out by `AND kode_mix IS NOT NULL` in the sales query
- Log the count of excluded rows for transparency
- Do NOT attempt to guess the kode_mix

### Size Columns That Do Not Exist for an Article

Most articles only use 3-8 of the 28 size columns.

**Handling:** Leave cells empty (None/blank), not 0. The downstream FF/FA/FS system interprets empty as "not applicable" and 0 as "target is zero pairs."

### Multiple Assortment Patterns per kode_mix

The same kode_mix can have multiple assortment patterns across versions (e.g., "1-2-3-3-2-1" for V1 and "1-2-2-3-2-2" for V2).

**Handling:** The SQL query uses `DISTINCT ON (kode_mix, size) ... ORDER BY kode_mix, size, no_urut` which picks the row with the lowest `no_urut` (most recent/preferred version). This ensures one assortment pattern per kode_mix.

### Store Name Matching Between DB and Excel

Store names in `portal.store` may differ slightly from names in `Data Option By Region.xlsx`.

**Handling:**
- Normalize both sides: `TRIM(LOWER(name))`
- Use fuzzy matching (ILIKE with `%pattern%`) as fallback
- Log any unmatched stores

---

## 9. Validation Checklist

After generating the pre-planogram table, verify:

| Check | Expected | How to Verify |
|-------|----------|---------------|
| Row count per store | ~200-300 articles per store | `output_df.groupby('Store Name').size()` |
| Total rows for region | ~2,500-2,900 for Jatim (11 stores) | `len(output_df)` |
| No T4/T5 rows | 0 rows with Tier 4 or 5 | `output_df[output_df['Tier'].isin(['4','5'])]` should be empty |
| Size columns sum | Should approximate Rekomendasi (pairs) | `row[SIZE_COLUMNS].sum() ~= row['Rekomendasi (pairs)']` (within rounding) |
| Sales mix sums to 1.0 per store | Each store's %Sales Mix should sum to ~1.0 | `output_df.groupby('Store Name')['%Sales Mix'].sum()` |
| No negative values | All quantities >= 0 | `(output_df[SIZE_COLUMNS] < 0).any().any()` should be False |
| Assortment coverage | >90% of articles have size data | Count rows where all size columns are None |

---

## 10. Future: Database Storage

In the future, the pre-planogram output will be stored in a new VPS DB table so downstream systems (FF/FA/FS metric calculator, RO Request generator, planogram layout engine) can query it directly instead of regenerating from scratch.

**Proposed table:** `mart.pre_planogram_current` or `portal.planogram`

**Proposed schema:**
```sql
CREATE TABLE mart.pre_planogram_current (
    id SERIAL PRIMARY KEY,
    area TEXT NOT NULL,
    store_name TEXT NOT NULL,
    gender TEXT,
    series TEXT,
    article TEXT NOT NULL,
    tier TEXT,
    kode_mix TEXT NOT NULL,
    -- 28 size columns as NUMERIC (nullable)
    s_18_19 NUMERIC, s_20_21 NUMERIC, s_21_22 NUMERIC, s_22_23 NUMERIC,
    s_23_24 NUMERIC, s_24_25 NUMERIC, s_25_26 NUMERIC, s_27_28 NUMERIC,
    s_29_30 NUMERIC, s_31_32 NUMERIC, s_33_34 NUMERIC,
    s_34 NUMERIC, s_35 NUMERIC, s_35_36 NUMERIC, s_36 NUMERIC,
    s_37 NUMERIC, s_37_38 NUMERIC, s_38 NUMERIC,
    s_39 NUMERIC, s_39_40 NUMERIC, s_40 NUMERIC, s_41 NUMERIC,
    s_41_42 NUMERIC, s_42 NUMERIC, s_43 NUMERIC, s_43_44 NUMERIC,
    s_44 NUMERIC, s_45_46 NUMERIC,
    -- Metrics
    avg_sales_3mo_pairs NUMERIC,
    avg_sales_3mo_box NUMERIC,
    sales_mix NUMERIC,
    rekomendasi_pairs NUMERIC,
    rekomendasi_box INTEGER,
    -- Metadata
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    date_range_start DATE,
    date_range_end DATE
);

CREATE INDEX idx_preplan_area ON mart.pre_planogram_current(area);
CREATE INDEX idx_preplan_store ON mart.pre_planogram_current(store_name);
CREATE INDEX idx_preplan_kode_mix ON mart.pre_planogram_current(kode_mix);
```

**Refresh strategy:** Regenerate weekly (after ETL completes) or on-demand when planogram review is triggered.

---

## 11. Relationship to Other Steps

```
Pre-Planogram (THIS SKILL - STEP 0.5)
    |
    | Output: size-level target quantities per store/article
    |
    v
Planogram Layout Engine (STEP 1 - SKILL_planogram_zuma_v3.md)
    |
    | Input: pre-planogram table + store denah (display components)
    | Output: article-to-display-component assignment (which backwall, which hook)
    |
    v
Visual Planogram (STEP 2 - SKILL_visualized-plano_zuma_v1.md)
    |
    | Input: planogram layout
    | Output: visual Excel/PDF rendering of physical store layout
    |
    v
RO Request (STEP 3 - zuma-distribution-flow SKILL.md)
    |
    | Input: planogram targets + current stock
    | Output: weekly replenishment order document (RO Protol + RO Box + Surplus)
```

The pre-planogram is the **data foundation**. Without it, STEP 1 cannot determine which articles belong in each store, and STEP 3 cannot calculate stock gaps.

---

## 12. How to Use This Skill (For AI Agents)

1. **Load dependencies:** Ensure `zuma-data-ops` (DB connection rules) and `zuma-sku-context` (tier system, kode_mix) context is available.

2. **Determine parameters:** Ask the user for:
   - Target area (e.g., "Jatim")
   - Date range (default: last 12 months for analysis, last 3 months for output metric)
   - Store capacities (from `Data Option By Region.xlsx` or user-provided)

3. **Execute pipeline:** Run Steps 1-7 in sequence. Each step depends on the previous.

4. **Validate output:** Run the validation checklist (Section 9).

5. **Deliver:** Save as Excel file (`Pre_Planogram_{Area}.xlsx`) or return as DataFrame for downstream processing.

6. **Do NOT proceed to STEP 1 logic** (display component assignment, hook allocation, compact/full box mode). That is a separate skill.
