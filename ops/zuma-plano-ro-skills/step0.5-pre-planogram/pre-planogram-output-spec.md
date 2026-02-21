# Pre-Planogram Output Specification

> Parent skill: [SKILL.md](SKILL.md)
> This file contains detailed output examples, size ranges, edge cases, validation rules, and future database storage schema.

---

## Size Ranges by Gender

Size ranges by gender (approximate):
- **Baby:** 18/19 through 25/26 (double-size)
- **Kids/Junior:** 27/28 through 33/34
- **Ladies:** 34 through 40
- **Men:** 39 through 45/46

---

## Example Row

```
Store Name  | Gender | Series      | Article              | Tier | article mix | ... | 39  | 39/40 | 40  | 41  | 41/42 | 42  | 43  | 43/44 | 44  | ... | AVG Sales 3M (pairs) | AVG Sales 3M (box) | %Sales Mix | Rekom (pairs) | Rekom (box)
Zuma Matos  | MEN    | BLACKSERIES | MEN BLACK SERIES 12  | 1    | M1BLVLV212  | ... | 0.5 |       | 1.0 | 1.0 |       | 1.5 | 1.0 |       | 1.0 | ... | 22                   | 1.833              | 0.048      | 1.381         | 2
```

Notes:
- Empty cells (not 0) for sizes that do not apply to the article
- Fractional values (0.5, 1.5, etc.) are correct and intentional -- do NOT round
- One row per article per store

---

## Edge Cases

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

## Validation Checklist

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

## Future: Database Storage

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
