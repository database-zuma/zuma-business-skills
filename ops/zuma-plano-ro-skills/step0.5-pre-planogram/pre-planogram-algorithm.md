# Pre-Planogram Algorithm Reference

> Parent skill: [SKILL.md](SKILL.md)
> This file contains the detailed SQL queries, Python implementations, and complete pipeline code for the pre-planogram calculation.

---

## 1. Calculation Pipeline (Detailed Steps)

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

## 2. SQL Query Templates

### 2.1 Monthly Sales Pivot per Article per Store

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

### 2.2 Current Stock per Article per Store

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

### 2.3 Assortment / Size Distribution per kode_mix

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

### 2.4 Store List with Capacity Data

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

### 2.5 AVG Sales Last 3 Months (for output column)

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

## 3. Complete Python Pipeline

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
