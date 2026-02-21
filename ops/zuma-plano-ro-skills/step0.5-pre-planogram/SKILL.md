---
name: pre-planogram-zuma
version: "1.0"
description: Generate pre-planogram data table (size-level target quantities per store/article) from VPS DB. Output feeds into planogram layout engine (STEP 1) and FF/FA/FS metrics.
dependencies:
  - zuma-data-analyst-skill
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

#### Critical DB Rules (from zuma-data-analyst-skill)

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

> **Full implementation (SQL queries, Python code, complete pipeline):** See [`pre-planogram-algorithm.md`](pre-planogram-algorithm.md)

### Step 1: Pull Sales Data from VPS

Query `core.sales_with_product` for the target area. Filter to RETAIL stores only, exclude intercompany, and aggregate monthly.

**Parameters:**
- `TARGET_AREA` -- e.g., 'Jatim', 'Jakarta', 'Bali'
- `DATE_START` -- start of analysis window (typically 12 months back)
- `DATE_END` -- end of analysis window (typically current month)

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

**Output:** `adjusted_avg_sales` per article per store (pairs/month).

### Step 3: Calculate Sales Mix Percentage

Per store, compute each article's share of total adjusted average sales.

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

### Step 5: Calculate Rekomendasi (Recommendation)

Based on store capacity (MaxDisplay from `Data Option By Region.xlsx`) and sales mix:

- `rekomendasi_pairs = sales_mix * store_max_display`
- `rekomendasi_box = CEIL(rekomendasi_pairs / 12)`

**Output:** `Rekomendasi (pairs)` and `Rekomendasi (box)` per article per store.

### Step 6: Distribute to Size-Level Quantities (THE KEY STEP)

Converts article-level recommendations into size-level target quantities using the assortment ratio from `portal.kodemix`.

1. Pull assortment data (deduplicated by `DISTINCT ON (kode_mix, size) ORDER BY no_urut`)
2. Calculate size ratios: `ratio = count_by_assortment / SUM(count_by_assortment)` per kode_mix
3. Distribute: `size_qty = rekomendasi_pairs * ratio` for each size

**CRITICAL:** Do NOT round fractional values. They are proportional targets for the FF/FA/FS metric system.

**Output:** 28 size columns per row, with fractional values or empty cells.

### Step 7: Build Output Table

Assemble the final wide-format table with article metadata, 28 size columns, and aggregated metrics. Flag articles without assortment data for manual review.

---

## 4. Output Format Specification

> **Example data, edge cases, validation rules:** See [`pre-planogram-output-spec.md`](pre-planogram-output-spec.md)

### Column Layout

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

---

## 5. Business Rules

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

## 6. Relationship to Other Steps

```
Pre-Planogram (THIS SKILL - STEP 0.5)
    |
    | Output: size-level target quantities per store/article
    |
    v
Planogram Layout Engine (STEP 1 - planogram-zuma skill)
    |
    | Input: pre-planogram table + store denah (display components)
    | Output: article-to-display-component assignment (which backwall, which hook)
    |
    v
Visual Planogram (STEP 2 - visualized-planogram-zuma skill)
    |
    | Input: planogram layout
    | Output: visual Excel/PDF rendering of physical store layout
    |
    v
RO Request (STEP 3 - zuma-ro-surplus-transisi skill)
    |
    | Input: planogram targets + current stock
    | Output: weekly replenishment order document (RO Protol + RO Box + Surplus)
```

The pre-planogram is the **data foundation**. Without it, STEP 1 cannot determine which articles belong in each store, and STEP 3 cannot calculate stock gaps.

---

## 7. How to Use This Skill (For AI Agents)

1. **Load dependencies:** Ensure `zuma-data-analyst-skill` (DB connection rules) and `zuma-sku-context` (tier system, kode_mix) context is available.

2. **Determine parameters:** Ask the user for:
   - Target area (e.g., "Jatim")
   - Date range (default: last 12 months for analysis, last 3 months for output metric)
   - Store capacities (from `Data Option By Region.xlsx` or user-provided)

3. **Execute pipeline:** Run Steps 1-7 in sequence. Each step depends on the previous.

4. **Validate output:** Run the validation checklist (see [`pre-planogram-output-spec.md`](pre-planogram-output-spec.md#validation-checklist)).

5. **Deliver:** Save as Excel file (`Pre_Planogram_{Area}.xlsx`) or return as DataFrame for downstream processing.

6. **Do NOT proceed to STEP 1 logic** (display component assignment, hook allocation, compact/full box mode). That is a separate skill.

---

## Reference Files

| File | Contents |
|------|----------|
| [`pre-planogram-algorithm.md`](pre-planogram-algorithm.md) | Detailed calculation pipeline (SQL queries, adjusted average Python implementation, sales mix, assortment ratios, size-level distribution, complete Python pipeline) |
| [`pre-planogram-output-spec.md`](pre-planogram-output-spec.md) | Full output column definitions, example data, edge cases, validation rules, future DB storage schema |
