# SKILL: FF / FA / FS — Store Fill Rate Metrics

> **Version**: 1.0  
> **Created**: 2026-02-11  
> **Domain**: Store performance measurement — planogram fill rate tracking  
> **Dependencies**: `zuma-data-ops` (DB connection & query rules), `SKILL_pre_planogram` (planogram generation)  
> **Output**: Daily fill rate report per store (Excel with conditional formatting)

---

## 1. Concept Overview

### What Are FF / FA / FS?

Three metrics that measure **how well each retail store is stocked relative to its planogram** (target display plan). Each measures the same thing — "are we filling the planogram?" — but at different granularity.

| Metric | Full Name | Granularity | Formula | What It Answers |
|--------|-----------|-------------|---------|-----------------|
| **FF** | Fill Factor | SIZE-level | `Count(Plan>0 AND Stock>0) / Count(Plan>0)` | "What % of planned sizes actually have stock on the shelf?" |
| **FA** | Fill Article | ARTICLE-level | `Count(Articles_with_any_stock) / Count(Articles_in_plan)` | "What % of planned articles have at least 1 size available?" |
| **FS** | Fill Stock | QUANTITY | `Sum(Actual_Stock) / Sum(Planned_Stock)` | "How deep is our stock compared to the plan? Enough depth per size?" |

### How They Relate

```
Store has 100 planned sizes across 20 articles. Planogram says total 300 pairs.
Actual: 75 sizes have stock, 18 articles have at least 1 size, total 250 pairs on hand.

FF = 75/100 = 75%    →  25 empty size slots on the shelf
FA = 18/20  = 90%    →  2 articles completely missing
FS = 250/300 = 83%   →  stock depth is light but not critical
```

- **FF < FA always** (or equal). If an article is missing (FA drops), all its sizes are missing too (FF drops more).
- **FS can exceed 100%**. More stock than plan = overstocked. This is normal for NOS (Never Out of Stock) items.
- **FF is the most important metric** for customer experience — a customer who finds the right article but not their size still walks away empty-handed.

### What About ST (Sell-Through)?

ST measures sales velocity: `Keluar / (Saldo_Awal + Masuk)` — what percentage of available stock was actually sold.

**ST is NOT included in this SKILL** because it requires **Ringkasan Mutasi Gudang** (warehouse mutation report) data from Accurate Online, which provides the `Saldo Awal`, `Masuk`, `Keluar`, and `Saldo Akhir` columns. This data is:

- Not available in VPS PostgreSQL database
- Not yet automated via Accurate Online API (the `reportId` and `planId` for Ringkasan Mutasi are still being investigated)
- Currently only obtainable via manual Excel download from Accurate Online

> **When Ringkasan Mutasi data becomes available** (either via API automation or manual file input),  
> this SKILL will be extended with ST calculation. The formula, data format, and join keys  
> are already documented in Section 12 (Future: ST Metric) for when that time comes.
>
> **DO NOT use Sales/(Stock+Sales) as a "fallback" for ST.** This approximation ignores  
> inter-warehouse transfers (RO Box, RO Protol), returns, and stock adjustments — making it  
> unreliable enough to produce misleading results. Better to have no ST than a wrong ST.

---

## 2. Data Sources

### 2.1 VPS PostgreSQL Database — Stock Data

> **CRITICAL**: Follow ALL rules from `zuma-data-ops` SKILL:
> - Rule 5: ALWAYS use `core.stock_with_product` and `core.sales_with_product`
> - Rule 7: ALWAYS exclude intercompany transactions
> - Rule 3: NEVER filter `portal.kodemix` by status

#### Connection

```
Host: 76.13.194.120
Port: 5432
Database: openclaw_ops
User: openclaw_app
Password: $PGPASSWORD
```

#### `core.stock_with_product` — The Only Stock Source

This view provides daily stock snapshots with product attributes already joined from `portal.kodemix`.

```sql
SELECT
    nama_gudang,      -- Store name (e.g., "ZUMA GALAXY MALL", "Zuma Royal Plaza")
    gudang_area,      -- Region (e.g., "Jatim", "Jakarta", "Sumatra")
    kode_mix,         -- Article mix code, 9 chars (e.g., "B1SLV101Z") — JOIN KEY to planogram
    size,             -- Individual size as string (e.g., "35", "36", "37")
    quantity,         -- Stock on hand (integer, can be 0)
    snapshot_date,    -- Date of this snapshot (DATE type, e.g., "2026-02-10")
    -- Product attributes (from portal.kodemix):
    gender,           -- "BOYS", "GIRLS", "MEN", "WOMEN", "UNISEX"
    series,           -- Product series name
    article,          -- Article name
    tier,             -- "1", "2", "3", "NOS"
    kode_besar        -- Full product code = kode_mix + size (e.g., "B1SLV101Z35")
FROM core.stock_with_product
```

**Key facts:**
- One row per `(nama_gudang, kode_besar, snapshot_date)` combination
- `snapshot_date` = the date the stock count was captured
- `quantity` can be 0 (product exists in system but physically out of stock)
- `kode_mix` is the article-level code (no size), which is what the planogram uses

### 2.2 Planogram Data — File Input

The planogram defines **what articles and sizes should be displayed** in each store, and **how many pairs per size**.

#### Source

Either:
1. Output from **Pre-Planogram Skill** (STEP 0.5) — generated from sales + stock analysis
2. Manual Excel file (e.g., `RO Input Jatim.xlsx`, sheet per store or "Planogram" sheet)
3. Existing `FF FA FS ST Jatim Q1 2026.xlsx` "Planogram" sheet (2,569 rows × 49 cols for Jatim)

#### Planogram Column Structure

```
Store Name | Gender | Series | Article | Tier | article_mix | 18/19 | 20/21 | 22/23 | 24/25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 | 40 | 41 | 42 | 43 | 44 | 45/46 | AVG Sales | Sales Mix | Rekomendasi
```

- **28 size columns** containing planned quantity per size (integer, 0 = not planned)
- `article_mix` = `kode_mix` in VPS DB — this is the primary join key
- One row per `(Store Name, article_mix)` combination
- `AVG Sales`, `Sales Mix`, `Rekomendasi` are informational — not used in metric calculation

> **Future**: Pre-planogram results will be stored in VPS DB at `mart.pre_planogram_current`.  
> For now, planogram is always a file input.

---

## 3. Store Name Mapping (CRITICAL)

Store names differ between Planogram labels and VPS `nama_gudang` values. **You MUST map them before any join.**

### Jatim Region (11 Stores)

| Planogram / Report Label | VPS DB `nama_gudang` |
|--------------------------|----------------------|
| Zuma Matos | Zuma Malang Town Square |
| Zuma Galaxy Mall | ZUMA GALAXY MALL |
| Zuma Tunjungan Plaza | Zuma Tunjungan Plaza 3 |
| ZUMA PTC | Zuma PTC |
| Zuma Icon Gresik | Zuma Icon Mall Gresik |
| Zuma Lippo Sidoarjo | Zuma Lippo Plaza Sidoarjo |
| Zuma Lippo Batu | Zuma Lippo Plaza Batu |
| Zuma Royal Plaza | Zuma Royal Plaza |
| Zuma City Of Tomorrow Mall | Zuma City of Tomorrow |
| Zuma Sunrise Mall | Zuma Sunrise Mall Mojokerto |
| Zuma Mall Olympic Garden | Zuma MOG |

```python
STORE_NAME_MAP = {
    # Jatim — Planogram label → VPS DB nama_gudang
    "Zuma Matos": "Zuma Malang Town Square",
    "Zuma Galaxy Mall": "ZUMA GALAXY MALL",
    "Zuma Tunjungan Plaza": "Zuma Tunjungan Plaza 3",
    "ZUMA PTC": "Zuma PTC",
    "Zuma Icon Gresik": "Zuma Icon Mall Gresik",
    "Zuma Lippo Sidoarjo": "Zuma Lippo Plaza Sidoarjo",
    "Zuma Lippo Batu": "Zuma Lippo Plaza Batu",
    "Zuma Royal Plaza": "Zuma Royal Plaza",
    "Zuma City Of Tomorrow Mall": "Zuma City of Tomorrow",
    "Zuma Sunrise Mall": "Zuma Sunrise Mall Mojokerto",
    "Zuma Mall Olympic Garden": "Zuma MOG",
}

STORE_NAME_MAP_REVERSE = {v: k for k, v in STORE_NAME_MAP.items()}
```

> **When expanding to other regions** (Jakarta, Sumatra, Sulawesi, Batam, Bali):  
> You MUST first query `SELECT DISTINCT nama_gudang FROM core.stock_with_product WHERE gudang_area = '{region}'`  
> and manually match those against the planogram store names.  
> Do NOT guess. Store naming is inconsistent (mixed case, abbreviations, missing suffixes).

### Size Column Mapping

Kids sizes in the planogram are paired. VPS DB stores individual sizes.

```python
SIZE_COLUMN_MAP = {
    "18/19": ["18", "19"],    # Paired: planogram qty covers both sizes
    "20/21": ["20", "21"],
    "22/23": ["22", "23"],
    "24/25": ["24", "25"],
    "26": ["26"],
    "27": ["27"],
    "28": ["28"],
    "29": ["29"],
    "30": ["30"],
    "31": ["31"],
    "32": ["32"],
    "33": ["33"],
    "34": ["34"],
    "35": ["35"],
    "36": ["36"],
    "37": ["37"],
    "38": ["38"],
    "39": ["39"],
    "40": ["40"],
    "41": ["41"],
    "42": ["42"],
    "43": ["43"],
    "44": ["44"],
    "45/46": ["45", "46"],    # Paired
}

SIZE_COLS = list(SIZE_COLUMN_MAP.keys())  # 24 column labels for 28 physical sizes
```

**How paired sizes work in FF calculation:**

For a paired column like `"18/19"` with `plan_qty = 2`:
- Check VPS stock for size "18" AND size "19" separately
- Sum their quantities: `stock_qty = stock_18 + stock_19`
- FF logic: if `plan_qty > 0 AND stock_qty > 0` → count as 1 filled size slot
- This means if size 18 has 0 but size 19 has 3, the slot counts as filled (stock_qty = 3 > 0)

---

## 4. Calculation Logic

### 4.1 Step 1 — Build "Hasil Gabungan" (Plan vs Stock Merge)

The intermediate dataset that powers all three metrics. One row per `(Store, Article)` with plan and stock quantities per size.

#### Join Key

```
Store (mapped to nama_gudang) × article_mix (= kode_mix) × size (expanded from paired)
```

#### Output Columns (68 total)

```
Store_Name, Article_Mix, Gender, Series, Article, Tier,           -- 6 identity cols
{size}_Plan × 24 columns,                                        -- planned qty per size column
{size}_Stock × 24 columns,                                       -- actual stock per size column
Total_Plan, Total_Stock,                                          -- row-level sums
Count_Plan_Positive, Count_Stock_Positive,                        -- for FF
Count_Article_Plan, Count_Article_Stock                           -- for FA
```

#### Algorithm

```python
def build_hasil_gabungan(planogram_df, stock_df):
    """
    For each (store, article) row in planogram:
    1. Map store name to VPS nama_gudang
    2. For each of 24 size columns:
       a. Read plan_qty from planogram
       b. Look up stock for all individual sizes in that column
       c. Sum stock quantities
       d. Track Plan>0 count and (Plan>0 AND Stock>0) count for FF
    3. Track article-level availability for FA
    """
    results = []

    for _, plan_row in planogram_df.iterrows():
        store_label = plan_row["Store Name"]
        store_db = STORE_NAME_MAP.get(store_label, store_label)
        article_mix = plan_row["article_mix"]

        row = {
            "Store_Name": store_label,
            "Article_Mix": article_mix,
            "Gender": plan_row.get("Gender", ""),
            "Series": plan_row.get("Series", ""),
            "Article": plan_row.get("Article", ""),
            "Tier": plan_row.get("Tier", ""),
        }

        total_plan = 0
        total_stock = 0
        count_plan_pos = 0
        count_stock_pos = 0

        for size_col in SIZE_COLS:
            plan_qty = int(plan_row.get(size_col, 0) or 0)

            # Sum stock across individual sizes in this column
            stock_qty = 0
            for ind_size in SIZE_COLUMN_MAP[size_col]:
                match = stock_df[
                    (stock_df["nama_gudang"] == store_db) &
                    (stock_df["kode_mix"] == article_mix) &
                    (stock_df["size"] == str(ind_size))
                ]
                if not match.empty:
                    stock_qty += int(match["quantity"].sum())

            row[f"{size_col}_Plan"] = plan_qty
            row[f"{size_col}_Stock"] = stock_qty

            total_plan += plan_qty
            total_stock += stock_qty

            # FF counters (size-level)
            if plan_qty > 0:
                count_plan_pos += 1
            if plan_qty > 0 and stock_qty > 0:
                count_stock_pos += 1

        # FA counters (article-level)
        row["Total_Plan"] = total_plan
        row["Total_Stock"] = total_stock
        row["Count_Plan_Positive"] = count_plan_pos
        row["Count_Stock_Positive"] = count_stock_pos
        row["Count_Article_Plan"] = 1 if total_plan > 0 else 0
        row["Count_Article_Stock"] = 1 if total_stock > 0 else 0

        results.append(row)

    return pd.DataFrame(results)
```

### 4.2 Step 2 — Calculate Metrics from Hasil Gabungan

All three metrics are simple aggregations over the Hasil Gabungan, filtered to one store.

#### FF (Fill Factor) — Size-Level

```python
def calculate_ff(hasil_df, store_name):
    """
    FF = Sum(Count_Stock_Positive) / Sum(Count_Plan_Positive) × 100

    Numerator:  How many size-column slots have BOTH plan > 0 AND stock > 0
    Denominator: How many size-column slots have plan > 0

    This is the EXACT logic from the original AppScript:
        if (planQty > 0 && stockQty > 0) countStockPositive++;
        if (planQty > 0) countPlanPositive++;
        FF = countStockPositive / countPlanPositive
    """
    store = hasil_df[hasil_df["Store_Name"] == store_name]
    num = store["Count_Stock_Positive"].sum()
    den = store["Count_Plan_Positive"].sum()
    return round(num / den * 100, 2) if den > 0 else 0.0
```

#### FA (Fill Article) — Article-Level

```python
def calculate_fa(hasil_df, store_name):
    """
    FA = Sum(Count_Article_Stock) / Sum(Count_Article_Plan) × 100

    Numerator:  How many articles have Total_Stock > 0
    Denominator: How many articles have Total_Plan > 0
    """
    store = hasil_df[hasil_df["Store_Name"] == store_name]
    num = store["Count_Article_Stock"].sum()
    den = store["Count_Article_Plan"].sum()
    return round(num / den * 100, 2) if den > 0 else 0.0
```

#### FS (Fill Stock) — Quantity Depth

```python
def calculate_fs(hasil_df, store_name):
    """
    FS = Sum(Total_Stock) / Sum(Total_Plan) × 100

    Can exceed 100% — this means overstocked (more stock than plan).
    FS > 100% is a signal for potential surplus return to warehouse.
    """
    store = hasil_df[hasil_df["Store_Name"] == store_name]
    num = store["Total_Stock"].sum()
    den = store["Total_Plan"].sum()
    return round(num / den * 100, 2) if den > 0 else 0.0
```

---

## 5. Report Output Format

### 5.1 Report Sheet Layout

The report sheet has **3 sections** stacked vertically (FF, FA, FS). Each section has:
- Row 1: Date headers
- Row 2: Metric label (colored banner)
- Rows 3–N: One row per store with daily metric values

```
       |    A                     |  B          |  C          |  D          | ...
-------+--------------------------+-------------+-------------+-------------+----
  1    | Store                    | 2026-02-01  | 2026-02-02  | 2026-02-03  | ...
  2    | FF                       |  (green banner across all columns)
  3    | Zuma Matos               | 78.5        | 79.1        | 77.3        | ...
  4    | Zuma Galaxy Mall         | 85.2        | 84.8        | 86.0        | ...
  ...  | ...                      | ...         | ...         | ...         |
  13   | Zuma Mall Olympic Garden | 72.1        | 73.5        | 71.8        | ...
  14   |                          |             |             |             |
  15   |                          |             |             |             |
  16   | Store                    | 2026-02-01  | 2026-02-02  | 2026-02-03  | ...
  17   | FA                       |  (blue banner)
  18   | Zuma Matos               | 92.0        | 92.0        | 91.5        | ...
  ...
       | FS                       |  (orange banner)
  ...
```

### 5.2 Conditional Coloring

| Metric | Green (good) | Yellow (caution) | Red (bad) |
|--------|-------------|-----------------|-----------|
| FF | >= 90% | 70–89% | < 70% |
| FA | >= 90% | 70–89% | < 70% |
| FS | >= 100% | 80–99% | < 80% |

Note: FS thresholds differ because FS > 100% is desirable (means enough depth).

### 5.3 Optional Debug Sheet — "Hasil Gabungan"

When `--debug` flag is used, the Excel output includes additional sheets showing the full Hasil Gabungan intermediate data per date. This allows manual verification of the merge logic.

---

## 6. Complete Python Script

### 6.1 Prerequisites

```bash
pip install psycopg2-binary pandas openpyxl python-dotenv
```

### 6.2 Full Script: `calculate_ff_fa_fs.py`

```python
#!/usr/bin/env python3
"""
FF / FA / FS — Store Fill Rate Metric Calculator

Compares planogram targets against actual stock from VPS PostgreSQL
to produce daily fill rate reports per store.

Usage:
    # Single date, all stores in region
    python calculate_ff_fa_fs.py \
        --planogram "RO Input Jatim.xlsx" \
        --region Jatim \
        --date 2026-02-10 \
        --output "FF_FA_FS_Jatim_2026-02-10.xlsx"

    # Date range (daily tracking)
    python calculate_ff_fa_fs.py \
        --planogram "RO Input Jatim.xlsx" \
        --region Jatim \
        --start-date 2026-02-01 \
        --end-date 2026-02-10 \
        --output "FF_FA_FS_Jatim_Feb2026.xlsx"

    # Specific stores only
    python calculate_ff_fa_fs.py \
        --planogram "RO Input Jatim.xlsx" \
        --region Jatim \
        --stores "Zuma Royal Plaza,Zuma Galaxy Mall" \
        --date 2026-02-10 \
        --output report.xlsx

    # Include Hasil Gabungan debug sheets
    python calculate_ff_fa_fs.py \
        --planogram "RO Input Jatim.xlsx" \
        --region Jatim \
        --date 2026-02-10 \
        --debug \
        --output report.xlsx

Environment Variables (or use --db-* CLI args):
    PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
"""

import os
import sys
import argparse
import pandas as pd
import psycopg2
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


# ==========================================================================
# CONSTANTS
# ==========================================================================

SIZE_COLUMN_MAP = {
    "18/19": ["18", "19"],
    "20/21": ["20", "21"],
    "22/23": ["22", "23"],
    "24/25": ["24", "25"],
    "26": ["26"], "27": ["27"], "28": ["28"], "29": ["29"],
    "30": ["30"], "31": ["31"], "32": ["32"], "33": ["33"], "34": ["34"],
    "35": ["35"], "36": ["36"], "37": ["37"], "38": ["38"], "39": ["39"],
    "40": ["40"], "41": ["41"], "42": ["42"], "43": ["43"], "44": ["44"],
    "45/46": ["45", "46"],
}
SIZE_COLS = list(SIZE_COLUMN_MAP.keys())

STORE_NAME_MAP = {
    # Jatim — Planogram label → VPS DB nama_gudang
    "Zuma Matos": "Zuma Malang Town Square",
    "Zuma Galaxy Mall": "ZUMA GALAXY MALL",
    "Zuma Tunjungan Plaza": "Zuma Tunjungan Plaza 3",
    "ZUMA PTC": "Zuma PTC",
    "Zuma Icon Gresik": "Zuma Icon Mall Gresik",
    "Zuma Lippo Sidoarjo": "Zuma Lippo Plaza Sidoarjo",
    "Zuma Lippo Batu": "Zuma Lippo Plaza Batu",
    "Zuma Royal Plaza": "Zuma Royal Plaza",
    "Zuma City Of Tomorrow Mall": "Zuma City of Tomorrow",
    "Zuma Sunrise Mall": "Zuma Sunrise Mall Mojokerto",
    "Zuma Mall Olympic Garden": "Zuma MOG",
    # Add other regions here as needed
}
STORE_NAME_MAP_REVERSE = {v: k for k, v in STORE_NAME_MAP.items()}


# ==========================================================================
# DATABASE
# ==========================================================================

def get_db_connection(args=None):
    """Connect to VPS PostgreSQL."""
    return psycopg2.connect(
        host=getattr(args, "db_host", None) or os.getenv("PG_HOST", "76.13.194.120"),
        port=getattr(args, "db_port", None) or os.getenv("PG_PORT", "5432"),
        dbname=getattr(args, "db_name", None) or os.getenv("PG_DATABASE", "openclaw_ops"),
        user=getattr(args, "db_user", None) or os.getenv("PG_USER", "openclaw_app"),
        password=getattr(args, "db_pass", None) or os.getenv("PG_PASSWORD", ""),
    )


def fetch_stock(conn, region, target_date, store_db_names=None):
    """
    Fetch stock snapshot from core.stock_with_product for a specific date and region.
    Optionally filter to specific stores.
    """
    query = """
        SELECT nama_gudang, kode_mix, size, quantity,
               gender, series, article, tier, kode_besar
        FROM core.stock_with_product
        WHERE gudang_area = %s
          AND snapshot_date = %s
          AND quantity IS NOT NULL
    """
    params = [region, target_date]

    if store_db_names:
        placeholders = ",".join(["%s"] * len(store_db_names))
        query += f" AND nama_gudang IN ({placeholders})"
        params.extend(store_db_names)

    df = pd.read_sql(query, conn, params=params)
    return df


# ==========================================================================
# PLANOGRAM LOADING
# ==========================================================================

def load_planogram(file_path, stores=None):
    """
    Load planogram from Excel file.

    Supports:
    1. Single "Planogram" sheet with all stores (has "Store Name" column)
    2. Multi-sheet where each sheet = one store's planogram

    Returns DataFrame with: Store Name, Gender, Series, Article, Tier,
        article_mix, and 24 size columns.
    """
    xls = pd.ExcelFile(file_path, engine="openpyxl")

    if "Planogram" in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name="Planogram")
        if "Store Name" not in df.columns:
            raise ValueError("Planogram sheet must have 'Store Name' column")
    else:
        all_frames = []
        for sheet_name in xls.sheet_names:
            if stores and sheet_name not in stores:
                continue
            try:
                sheet_df = pd.read_excel(xls, sheet_name=sheet_name)
                # Detect planogram-like sheets by checking for size columns
                col_str = " ".join(str(c) for c in sheet_df.columns)
                if not any(s in col_str for s in ["35", "36", "37", "38"]):
                    continue
                sheet_df["Store Name"] = sheet_name
                all_frames.append(sheet_df)
            except Exception:
                continue
        if not all_frames:
            raise ValueError(f"No planogram sheets found in {file_path}")
        df = pd.concat(all_frames, ignore_index=True)

    # Normalize article_mix column name
    for col in df.columns:
        if str(col).lower().strip() in [
            "article mix", "article_mix", "kode_mix", "kodemix"
        ]:
            df = df.rename(columns={col: "article_mix"})
            break

    if "article_mix" not in df.columns:
        raise ValueError("Cannot find article_mix / kode_mix column in planogram")

    if stores:
        df = df[df["Store Name"].isin(stores)]

    # Ensure size columns are integer
    for size_col in SIZE_COLS:
        if size_col in df.columns:
            df[size_col] = pd.to_numeric(df[size_col], errors="coerce").fillna(0).astype(int)

    print(f"Planogram loaded: {len(df):,} rows, {df['Store Name'].nunique()} stores")
    return df


# ==========================================================================
# HASIL GABUNGAN (PLAN vs STOCK MERGE)
# ==========================================================================

def build_hasil_gabungan(planogram_df, stock_df):
    """
    Merge planogram targets with actual stock snapshot.

    For each (store, article) in planogram:
    - Look up stock per size from stock_df
    - Compute size-level and article-level fill counters
    - Produce one row with Plan and Stock per size column

    Returns DataFrame with 68 columns (see Section 4.1).
    """
    results = []

    for _, plan_row in planogram_df.iterrows():
        store_label = plan_row["Store Name"]
        store_db = STORE_NAME_MAP.get(store_label, store_label)
        article_mix = plan_row["article_mix"]

        row = {
            "Store_Name": store_label,
            "Article_Mix": article_mix,
            "Gender": plan_row.get("Gender", ""),
            "Series": plan_row.get("Series", ""),
            "Article": plan_row.get("Article", ""),
            "Tier": plan_row.get("Tier", ""),
        }

        total_plan = 0
        total_stock = 0
        count_plan_pos = 0
        count_stock_pos = 0

        for size_col in SIZE_COLS:
            plan_qty = int(plan_row.get(size_col, 0) or 0)

            stock_qty = 0
            for ind_size in SIZE_COLUMN_MAP[size_col]:
                match = stock_df[
                    (stock_df["nama_gudang"] == store_db)
                    & (stock_df["kode_mix"] == article_mix)
                    & (stock_df["size"] == str(ind_size))
                ]
                if not match.empty:
                    stock_qty += int(match["quantity"].sum())

            row[f"{size_col}_Plan"] = plan_qty
            row[f"{size_col}_Stock"] = stock_qty

            total_plan += plan_qty
            total_stock += stock_qty

            if plan_qty > 0:
                count_plan_pos += 1
            if plan_qty > 0 and stock_qty > 0:
                count_stock_pos += 1

        row["Total_Plan"] = total_plan
        row["Total_Stock"] = total_stock
        row["Count_Plan_Positive"] = count_plan_pos
        row["Count_Stock_Positive"] = count_stock_pos
        row["Count_Article_Plan"] = 1 if total_plan > 0 else 0
        row["Count_Article_Stock"] = 1 if total_stock > 0 else 0

        results.append(row)

    return pd.DataFrame(results)


# ==========================================================================
# METRIC CALCULATION
# ==========================================================================

def calculate_metrics(hasil_df, store_name):
    """
    Calculate FF, FA, FS for one store from Hasil Gabungan.

    Returns dict: {"FF": float, "FA": float, "FS": float}
    """
    store = hasil_df[hasil_df["Store_Name"] == store_name]

    if store.empty:
        return {"FF": 0.0, "FA": 0.0, "FS": 0.0}

    # FF — size level
    ff_num = store["Count_Stock_Positive"].sum()
    ff_den = store["Count_Plan_Positive"].sum()
    ff = round(ff_num / ff_den * 100, 2) if ff_den > 0 else 0.0

    # FA — article level
    fa_num = store["Count_Article_Stock"].sum()
    fa_den = store["Count_Article_Plan"].sum()
    fa = round(fa_num / fa_den * 100, 2) if fa_den > 0 else 0.0

    # FS — quantity depth
    fs_num = store["Total_Stock"].sum()
    fs_den = store["Total_Plan"].sum()
    fs = round(fs_num / fs_den * 100, 2) if fs_den > 0 else 0.0

    return {"FF": ff, "FA": fa, "FS": fs}


# ==========================================================================
# EXCEL REPORT GENERATION
# ==========================================================================

METRIC_COLORS = {
    "FF": "2E7D32",  # Green
    "FA": "1565C0",  # Blue
    "FS": "E65100",  # Orange
}


def _value_fill(value, metric):
    """Conditional fill color based on metric value."""
    if metric == "FS":
        # FS: 100%+ is good (enough depth)
        if value >= 100:
            return PatternFill(start_color="C8E6C9", fill_type="solid")
        elif value >= 80:
            return PatternFill(start_color="FFF9C4", fill_type="solid")
        else:
            return PatternFill(start_color="FFCDD2", fill_type="solid")
    else:
        # FF, FA: 90%+ is good
        if value >= 90:
            return PatternFill(start_color="C8E6C9", fill_type="solid")
        elif value >= 70:
            return PatternFill(start_color="FFF9C4", fill_type="solid")
        else:
            return PatternFill(start_color="FFCDD2", fill_type="solid")


def create_report_excel(report_data, stores, dates, output_path,
                        hasil_gabungan_by_date=None):
    """
    Generate the FF/FA/FS report as a styled Excel file.

    Args:
        report_data: {"FF": {store: {date: value}}, "FA": ..., "FS": ...}
        stores: Ordered list of store names (report labels)
        dates: Ordered list of date strings
        output_path: Where to save the .xlsx
        hasil_gabungan_by_date: Optional {date: DataFrame} for debug sheets
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report"

    header_font = Font(bold=True, size=11)
    metric_font = Font(bold=True, size=12, color="FFFFFF")
    value_align = Alignment(horizontal="center")

    current_row = 1

    for metric in ["FF", "FA", "FS"]:
        color = METRIC_COLORS[metric]
        banner_fill = PatternFill(start_color=color, end_color=color, fill_type="solid")

        # Date header row
        ws.cell(row=current_row, column=1, value="Store").font = header_font
        for ci, d in enumerate(dates, start=2):
            cell = ws.cell(row=current_row, column=ci, value=d)
            cell.font = header_font
            cell.alignment = value_align
        current_row += 1

        # Metric banner row
        cell = ws.cell(row=current_row, column=1, value=metric)
        cell.font = metric_font
        cell.fill = banner_fill
        for ci in range(2, len(dates) + 2):
            ws.cell(row=current_row, column=ci).fill = banner_fill
        current_row += 1

        # Store data rows
        for store in stores:
            ws.cell(row=current_row, column=1, value=store).font = Font(size=10)
            for ci, d in enumerate(dates, start=2):
                val = report_data.get(metric, {}).get(store, {}).get(d, 0)
                cell = ws.cell(row=current_row, column=ci, value=round(val, 1))
                cell.number_format = "0.0"
                cell.alignment = value_align
                if val > 0:
                    cell.fill = _value_fill(val, metric)
            current_row += 1

        current_row += 2  # gap between sections

    # Column widths
    ws.column_dimensions["A"].width = 30
    for ci in range(2, len(dates) + 2):
        ws.column_dimensions[get_column_letter(ci)].width = 12

    # Debug sheets
    if hasil_gabungan_by_date:
        for d, hg_df in hasil_gabungan_by_date.items():
            ws_hg = wb.create_sheet(title=f"HG_{d}")
            for ci, col_name in enumerate(hg_df.columns, start=1):
                ws_hg.cell(row=1, column=ci, value=col_name).font = Font(bold=True)
            for ri, (_, row) in enumerate(hg_df.iterrows(), start=2):
                for ci, val in enumerate(row, start=1):
                    ws_hg.cell(row=ri, column=ci, value=val)

    wb.save(output_path)
    print(f"\nReport saved: {output_path}")
    print(f"  Stores: {len(stores)}")
    print(f"  Dates: {len(dates)} ({dates[0]} to {dates[-1]})")
    print(f"  Metrics: FF, FA, FS")


# ==========================================================================
# MAIN
# ==========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="FF/FA/FS Store Fill Rate Calculator"
    )

    # Required
    parser.add_argument("--planogram", required=True,
                        help="Path to planogram Excel file")
    parser.add_argument("--region", required=True,
                        help="Region filter for stock query (e.g., 'Jatim')")
    parser.add_argument("--output", required=True,
                        help="Output Excel file path")

    # Date (mutually exclusive: single date vs range)
    parser.add_argument("--date",
                        help="Single date (YYYY-MM-DD)")
    parser.add_argument("--start-date",
                        help="Start of date range (YYYY-MM-DD)")
    parser.add_argument("--end-date",
                        help="End of date range (YYYY-MM-DD)")

    # Optional filters
    parser.add_argument("--stores",
                        help="Comma-separated store names to include (planogram labels)")
    parser.add_argument("--debug", action="store_true",
                        help="Include Hasil Gabungan sheets in output for verification")

    # DB connection overrides
    parser.add_argument("--db-host", help="PostgreSQL host override")
    parser.add_argument("--db-port", help="PostgreSQL port override")
    parser.add_argument("--db-name", help="PostgreSQL database override")
    parser.add_argument("--db-user", help="PostgreSQL user override")
    parser.add_argument("--db-pass", help="PostgreSQL password override")

    args = parser.parse_args()

    # -- Resolve dates --
    if args.date:
        dates = [args.date]
    elif args.start_date and args.end_date:
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
        end = datetime.strptime(args.end_date, "%Y-%m-%d")
        dates = []
        cur = start
        while cur <= end:
            dates.append(cur.strftime("%Y-%m-%d"))
            cur += timedelta(days=1)
    else:
        print("ERROR: Provide --date or both --start-date and --end-date")
        sys.exit(1)

    # -- Resolve stores --
    target_stores = None
    if args.stores:
        target_stores = [s.strip() for s in args.stores.split(",")]

    # -- Load planogram --
    print("=" * 60)
    print("  FF / FA / FS — Store Fill Rate Calculator")
    print("=" * 60)

    planogram_df = load_planogram(args.planogram, stores=target_stores)
    stores = sorted(planogram_df["Store Name"].unique())
    if target_stores:
        stores = [s for s in target_stores if s in stores]

    print(f"Stores: {stores}")
    print(f"Dates:  {dates[0]} -> {dates[-1]} ({len(dates)} day(s))")

    # -- DB connection --
    store_db_names = [STORE_NAME_MAP.get(s, s) for s in stores]

    print(f"\nConnecting to VPS PostgreSQL...")
    conn = get_db_connection(args)
    print("Connected.\n")

    # -- Initialize results --
    report_data = {m: {s: {} for s in stores} for m in ["FF", "FA", "FS"]}
    hg_debug = {} if args.debug else None

    # -- Calculate per date --
    for di, date_str in enumerate(dates):
        print(f"[{di+1}/{len(dates)}] {date_str}")

        stock_df = fetch_stock(conn, args.region, date_str, store_db_names)
        print(f"  Stock rows: {len(stock_df):,}")

        if stock_df.empty:
            print(f"  WARNING: No stock data — skipping")
            continue

        hasil_df = build_hasil_gabungan(planogram_df, stock_df)
        print(f"  Hasil Gabungan: {len(hasil_df):,} rows")

        if args.debug:
            hg_debug[date_str] = hasil_df

        for store in stores:
            metrics = calculate_metrics(hasil_df, store)
            for m, v in metrics.items():
                report_data[m][store][date_str] = v
            print(f"    {store}: FF={metrics['FF']:.1f}%  "
                  f"FA={metrics['FA']:.1f}%  FS={metrics['FS']:.1f}%")

    conn.close()

    # -- Generate Excel --
    create_report_excel(
        report_data=report_data,
        stores=stores,
        dates=dates,
        output_path=args.output,
        hasil_gabungan_by_date=hg_debug,
    )
    print("\nDone.")


if __name__ == "__main__":
    main()
```

---

## 7. SQL Query Templates

### 7.1 Stock for Fill Rate Calculation

```sql
-- All stock for Jatim stores on a given date
SELECT nama_gudang, kode_mix, size, quantity,
       gender, series, article, tier, kode_besar
FROM core.stock_with_product
WHERE gudang_area = 'Jatim'
  AND snapshot_date = '2026-02-10'
  AND quantity IS NOT NULL
  AND nama_gudang IN (
    'Zuma Malang Town Square', 'ZUMA GALAXY MALL', 'Zuma Tunjungan Plaza 3',
    'Zuma PTC', 'Zuma Icon Mall Gresik', 'Zuma Lippo Plaza Sidoarjo',
    'Zuma Lippo Plaza Batu', 'Zuma Royal Plaza', 'Zuma City of Tomorrow',
    'Zuma Sunrise Mall Mojokerto', 'Zuma MOG'
  );
```

### 7.2 Check Available Snapshot Dates

```sql
-- What dates have stock data for Jatim?
SELECT DISTINCT snapshot_date
FROM core.stock_with_product
WHERE gudang_area = 'Jatim'
ORDER BY snapshot_date DESC
LIMIT 30;
```

### 7.3 Quick Store Article Count

```sql
-- How many distinct articles does a store have in stock?
SELECT nama_gudang, COUNT(DISTINCT kode_mix) AS article_count
FROM core.stock_with_product
WHERE gudang_area = 'Jatim'
  AND snapshot_date = '2026-02-10'
  AND quantity > 0
GROUP BY nama_gudang
ORDER BY article_count DESC;
```

---

## 8. Business Rules & Edge Cases

### 8.1 Rules

| Rule | Description |
|------|-------------|
| FF counts at SIZE-COLUMN level | Each of the 24 size columns in planogram is one "slot." A slot is filled if plan > 0 AND stock > 0. |
| Paired sizes are ONE slot | "18/19" is one slot — if either size 18 or 19 has stock, the slot is filled. |
| FA counts at ARTICLE level | An article is "present" if ANY of its sizes has stock > 0, regardless of how many sizes are missing. |
| FS is a ratio, not capped at 100% | FS > 100% = more stock than planned = overstocked. This is actionable (potential surplus return). |
| Zero-plan sizes are EXCLUDED | If planogram says 0 for a size column, that column is NOT counted in any denominator. |
| Stock without planogram is IGNORED | Extra stock in articles NOT in the planogram does not affect any metric. |
| One planogram per calculation run | The script uses a single planogram file for all dates. If the planogram changes mid-period, run separately for each planogram version. |

### 8.2 Edge Cases

| Situation | Handling |
|-----------|----------|
| No stock snapshot for a date | Skip date entirely (log warning), report shows blank for that column |
| Store in planogram but not in stock data | All metrics = 0% for that date (nothing on shelf) |
| Article in planogram but zero in all size columns | Excluded (Count_Article_Plan = 0, doesn't affect denominators) |
| Stock quantity = 0 in DB | Treated as "no stock" — the slot is not filled |
| Store name not in STORE_NAME_MAP | Falls through to exact-string match (likely fails silently — warn user) |
| Planogram has duplicate (store, article_mix) rows | Both rows are processed — will double-count. Deduplicate planogram first. |
| Negative stock quantity | Should not exist. If encountered, treat as 0. |

### 8.3 Validation Checklist

Before trusting output:

- [ ] **Planogram row count** matches expectation (~2,569 for Jatim 11 stores)
- [ ] **All store names resolved** — no "WARN: store not mapped" in output
- [ ] **Stock data exists for target dates** — check `snapshot_date` availability first
- [ ] **FF <= FA** in all cases — if FF > FA, investigate (could indicate data issue)
- [ ] **FS range is sane** — typically 50–200% for active stores
- [ ] **Cross-check one date manually** against existing Google Sheets report if available

---

## 9. Agent Instructions

### For AI Agents Using This SKILL

1. **ALWAYS load `zuma-data-ops` skill** alongside this one — it contains DB connection rules you must follow
2. **Ask the user**:
   - Which region? (e.g., "Jatim", "Jakarta")
   - Which date(s)? (single date or range)
   - Where is the planogram file? (or should you generate one via STEP 0.5?)
   - Specific stores or all stores in the region?
3. **Check stock data availability first** — run the "Check Available Snapshot Dates" query (Section 7.2) before calculating
4. **Run on VPS** (`76.13.194.120`) for large date ranges, or locally if user has network access to DB
5. **Always generate Excel output** with openpyxl and conditional coloring
6. **Verify results** — check FF <= FA, FS in reasonable range, row counts match
7. **New region?** → Gather store name mappings FIRST by querying `nama_gudang` from DB and matching against planogram
8. **Do NOT calculate ST** — this SKILL covers FF/FA/FS only. ST requires Ringkasan Mutasi data that is not yet available.

### User Prompt Template

```
Generate FF/FA/FS fill rate report for [REGION] stores.

Date: [YYYY-MM-DD] or range [START] to [END]
Planogram file: [path to planogram Excel]
Stores: [all / specific store names comma-separated]
Output: [desired output file path]
```

---

## 10. How This SKILL Was Built

### Source Material Analyzed

1. **`AppScript of FF FA FS ST Jatim.txt`** (1,279 lines) — The original Google Apps Script that runs the existing FF/FA/FS/ST automation. This is the ground truth for calculation logic. The script:
   - Syncs data from Supabase to Google Sheets daily at 11:30
   - Merges Planogram + Stock into "Hasil Gabungan" sheet at 12:00
   - Calculates FF/FA/FS/ST from merged data at 13:00
   - Writes results to "Report" sheet with 4 stacked metric sections

2. **`Copy of FF FA FS ST Jatim Q1 2026.xlsx`** (9 sheets, fully read) — The actual production spreadsheet:
   - `Stock` sheet: 42,098 rows of raw stock with mutation columns (Saldo Awal, Masuk, Keluar, Saldo Akhir)
   - `Planogram` sheet: 2,569 rows × 49 columns — this IS the planogram format (28 size cols + metadata + AVG Sales/Rekomendasi)
   - `Hasil Gabungan` sheet: 2,569 rows × 68 columns — the merged intermediate data with Plan/Stock per size + summary counters
   - `Report` sheet: 4 sections (FF/FA/FS/ST) × 11 stores × daily date columns (Oct 2025 → Feb 2026)
   - `Data` sheet: 27,816 rows — Supabase sync output (being replaced with VPS DB)
   - `Backdata`, `store`, `Summary Monthly FF 2026`, `forNotionIntegrator` sheets also analyzed

3. **VPS PostgreSQL** (`openclaw_ops`) — Confirmed available data:
   - `core.stock_with_product` — maps cleanly to the Stock sheet data (minus mutation columns)
   - `core.sales_with_product` — available but NOT used for ST (see below)
   - No mutation data exists in VPS DB (confirmed via exhaustive search: `raw`, `core`, `mart`, `portal` schemas)

4. **`RO Input Jatim.xlsx`** (15 sheets) — Confirmed planogram sheet structure is identical to the FF/FA/FS input format

5. **`ringkasan_mutasi-2025_08_01_sampai_07.xlsx`** (8,769 rows) — Manual Accurate Online download, confirmed format: `Nama Gudang | Kode Barang | Nama Barang | Saldo Awal | Masuk | Keluar | Saldo Akhir`

### What Changed vs Original AppScript

| Aspect | Original (AppScript + Supabase) | This SKILL (Python + VPS DB) |
|--------|--------------------------------|------------------------------|
| Stock source | Supabase `dbjoin_stockmutasi_final_with_portal_nisa` | `core.stock_with_product` on VPS |
| Planogram source | "Planogram" sheet in same Google Spreadsheet | External Excel file input |
| Execution | Google Apps Script time-based triggers (11:30, 12:00, 13:00) | On-demand CLI script |
| ST metric | Calculated from `Keluar/(Saldo_Awal+Masuk)` via Stock sheet mutation columns | **NOT INCLUDED** — data source unavailable |
| FF/FA/FS formulas | `countStockPositive / countPlanPositive` etc. | Identical — exact replication of AppScript logic |
| Output | Google Sheets "Report" sheet with 4 stacked sections | Standalone Excel file with 3 sections (no ST) |

### Why ST Is Excluded (Not a Shortcut — a Correctness Decision)

The original AppScript calculates ST from the `Stock` sheet which has columns: `Saldo Awal`, `Masuk`, `Keluar`, `Saldo Akhir`. This data comes from **Ringkasan Mutasi Gudang** — a report from Accurate Online that tracks stock movements (opening balance, inbound transfers, outbound/sales, closing balance).

This mutation data does NOT exist in our VPS PostgreSQL database. We only have:
- Stock snapshots (point-in-time quantities) via `core.stock_with_product`
- Sales transactions via `core.sales_with_product`

A "fallback" formula like `Sales / (Stock + Sales)` would be **incorrect** because it:
- Misses inter-warehouse transfers (RO Box, RO Protol movements are not sales)
- Misses stock adjustments and inventory corrections
- Cannot distinguish between "sold to customer" and "transferred to another store"
- Produces numbers that look plausible but are actually wrong

**Wrong data presented confidently is worse than no data.** ST will be added to this SKILL when Ringkasan Mutasi data becomes available — see Section 12.

---

## 11. Dependencies & Libraries

```bash
pip install psycopg2-binary pandas openpyxl python-dotenv
```

| Library | Min Version | Purpose |
|---------|-------------|---------|
| `psycopg2-binary` | 2.9 | PostgreSQL connection to VPS |
| `pandas` | 1.5 | Data manipulation, SQL query to DataFrame |
| `openpyxl` | 3.0 | Excel read/write with styling & conditional formatting |
| `python-dotenv` | 1.0 | Load DB credentials from .env file |

---

## 12. Future: ST Metric (When Ringkasan Mutasi Becomes Available)

This section documents everything needed to add ST. The code is ready — only the data source is missing.

### ST Formula

```
ST = Sum(Keluar) / Sum(Saldo_Awal + Masuk) × 100
```

Only for articles/sizes that exist in the planogram. Scoped to one store per one mutation period.

### Ringkasan Mutasi Data Format

```
Columns: Nama Gudang | Kode Barang | Nama Barang | Saldo Awal | Masuk | Keluar | Saldo Akhir
Example: Zuma Royal Plaza | B1SLV101Z35 | BOYS SLIDE MAX 1, 35, BLACK | 3 | 0 | 1 | 2
```

- `Kode Barang` = `kode_besar` in VPS DB (kode_mix + size, joinable)
- `Nama Gudang` = VPS `nama_gudang` (use STORE_NAME_MAP)
- ~8,769 rows per export covering all 51 warehouses + stores

### Mutation File Loader (Ready to Use)

```python
def load_mutation(file_path):
    """Load Ringkasan Mutasi Gudang from manual Excel download."""
    df = pd.read_excel(file_path, engine="openpyxl")

    col_map = {}
    for col in df.columns:
        cl = str(col).strip().lower()
        if "nama gudang" in cl:   col_map[col] = "nama_gudang"
        elif "kode barang" in cl: col_map[col] = "kode_barang"
        elif "nama barang" in cl: col_map[col] = "nama_barang"
        elif "saldo awal" in cl:  col_map[col] = "saldo_awal"
        elif cl == "masuk":       col_map[col] = "masuk"
        elif cl == "keluar":      col_map[col] = "keluar"
        elif "saldo akhir" in cl: col_map[col] = "saldo_akhir"

    df = df.rename(columns=col_map)
    for c in ["saldo_awal", "masuk", "keluar", "saldo_akhir"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    return df
```

### ST Calculation Function (Ready to Use)

```python
def calculate_st(mutation_df, hasil_df, store_name):
    """
    ST from Ringkasan Mutasi, scoped to planogram articles only.
    Join: kode_besar = article_mix + size (for each planned size slot).
    """
    store_db = STORE_NAME_MAP.get(store_name, store_name)
    store_hasil = hasil_df[hasil_df["Store_Name"] == store_name]

    # Build set of kode_besar that are in the planogram
    plano_kode_besar = set()
    for _, row in store_hasil.iterrows():
        mix = row["Article_Mix"]
        for sc in SIZE_COLS:
            if int(row.get(f"{sc}_Plan", 0) or 0) > 0:
                for ind_size in SIZE_COLUMN_MAP[sc]:
                    plano_kode_besar.add(f"{mix}{ind_size}")

    mut = mutation_df[
        (mutation_df["nama_gudang"] == store_db)
        & (mutation_df["kode_barang"].isin(plano_kode_besar))
    ]

    available = (mut["saldo_awal"] + mut["masuk"]).sum()
    sold = mut["keluar"].sum()

    return round(sold / available * 100, 2) if available > 0 else 0.0
```

### How to Enable ST

When mutation data becomes available (API or manual file), add `--mutation` CLI arg:

```bash
python calculate_ff_fa_fs.py \
    --planogram "RO Input Jatim.xlsx" \
    --region Jatim \
    --date 2026-02-10 \
    --mutation "ringkasan_mutasi_feb_w1.xlsx" \
    --output report.xlsx
```

The script would then:
1. Load mutation file via `load_mutation()`
2. After computing FF/FA/FS per store, also call `calculate_st()`
3. Add a 4th section (purple banner) to the Excel report

### Accurate Online API — Investigation Status

The report export API pattern is known from `pull_historical_sales.py` on VPS:
- `POST {host}/accurate/report/execute-report.do` → returns `cacheId`
- `POST {host}/accurate/report/export-report.do` → downloads Excel

What's missing for Ringkasan Mutasi:
- The numeric `reportId` (e.g., sales detail = 15500)
- The string `planId` (e.g., sales = "ViewSalesByItemDetailReport")

These can be found by inspecting network requests in browser DevTools when running the report in Accurate Online UI. Once found, a `pull_accurate_mutation.py` script will be built following the exact same pattern as `pull_historical_sales.py`.

### Future VPS Table

```sql
CREATE TABLE IF NOT EXISTS mart.ff_fa_fs_daily (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    region TEXT NOT NULL,
    store_label TEXT NOT NULL,
    store_db_name TEXT NOT NULL,
    ff_pct NUMERIC(5,2),
    fa_pct NUMERIC(5,2),
    fs_pct NUMERIC(5,2),
    -- st_pct NUMERIC(5,2),  -- Uncomment when ST data available
    planogram_source TEXT,
    calculated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (report_date, store_db_name)
);
```

---

## 13. Reminders for User

> **Ideal Tier Capacity %**: We still need the real per-store tier capacity percentages  
> from your colleague. Currently pre-planogram uses available-data defaults.

> **TO Metric**: You mentioned needing to clarify the "TO" (Turnover?) metric definition  
> with your team. Once clarified, it can be added as a future metric in this `notion-metrics` folder.

> **Ringkasan Mutasi API**: To find the Accurate Online `reportId` for Ringkasan Mutasi Gudang,  
> open the report in your browser, then check DevTools Network tab for the `execute-report.do`  
> request — the `id` parameter in the form data is what we need.

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial — FF/FA/FS from VPS DB + planogram file input. ST deferred pending Ringkasan Mutasi data. |
