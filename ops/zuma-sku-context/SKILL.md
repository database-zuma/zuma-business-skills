---
name: zuma-sku-context
description: Zuma Indonesia's product SKU categorization, assortments, tiering system, and SKU naming conventions. Use when working with product data, sales analysis, or e-commerce projects.
user-invocable: false
---

# Zuma Indonesia SKU Context

You have access to Zuma Indonesia's product catalog structure and SKU management system. Use this knowledge when working with product data, inventory analysis, marketplace integrations, or e-commerce features.

## Overview

**Purpose:** Product categorization, assortment planning, inventory tiering, and SKU management
**Product Type:** Sandals
**Data Sources:**
- Accurate Online (ERP) - Master product data
- Ginee (Marketplaces) - Marketplace listings
- iSeller (POS) - Retail sales
- Supabase - Product master database
- Google Sheets - Product master data
**Location:** `Continous Improvement Data/0. Raw Data - Accurate/`, `0. Raw Data - Ginee/`, `0. Raw Data - iSeller/`

## Product Categorization

Zuma uses a five-level hierarchical categorization system from general to granular. Each level provides increasingly specific product identification.

### Category Hierarchy

**Level 1: Type**
- Fashion
- Jepit

**Level 2: Gender**
- Men
- Ladies
- Kids
- Junior
- Boys
- Girl
- Baby

**Level 3: Series**
- Classic
- Slide
- Wedges
- Airmove
- Luca
- Luna
- Velcro
- Pooh
- Princess
- (and others)

**Level 4: Article**
Color variants within each series. Examples:
- Luna White
- Airmove Deep Green
- Classic Jet Black
- Slide Puffy Redwood

**Level 5: Size**
The most granular SKU unit. Examples:
- Airmove Deep Green 39/40
- Men Classic Jet Black 42
- Luna White 40

### Categorization Examples

| Full SKU Path | Type | Gender | Series | Article | Size |
|--------------|------|--------|--------|---------|------|
| Men Classic Jet Black 42 | Fashion | Men | Classic | Jet Black | 42 |
| Ladies Slide Puffy Redwood 38 | Fashion | Ladies | Slide | Puffy Redwood | 38 |
| Men Airmove Deep Green 39/40 | Fashion | Men | Airmove | Deep Green | 39/40 |

## Product Assortment

Product assortment defines how SKUs are packaged in boxes for warehouse storage and distribution. Understanding assortment is critical for inventory management, ordering, and stock planning.

### Box Packaging Structure

**Unit Definition:**
- **Box = Article level** (Gender > Series > Article)
- Each box contains ONE article (e.g., "Men Classic Jet Black")
- Each box always contains exactly **12 pairs**
- Each box contains multiple sizes according to the article's assortment pattern

### Assortment Types

#### 1. Single-Size Assortment (Most Common)
Each pair in the box has one specific size.

**Example:** Men Classic Jet Black
- Assortment: 1-2-2-3-2-2
- Size range: 39-44
- Breakdown: 39(1), 40(2), 41(2), 42(3), 43(2), 44(2)
- Total: 12 pairs

#### 2. Double-Size Assortment
Each pair covers two adjacent sizes (e.g., 39/40).

**Example:** Men Airmove Deep Green
- Assortment: 3-6-3
- Size range: 39/40, 40/41, 42/43
- Breakdown: 39/40(3), 40/41(6), 42/43(3)
- Total: 12 pairs

### Assortment Patterns by Series

**Key Rule:** All articles within the same Gender-Series combination share the same assortment pattern, regardless of color/article variant.

| Gender-Series | Assortment Pattern | Size Range | Size Breakdown | Type |
|--------------|-------------------|------------|----------------|------|
| **Men Classic** (all colors) | 1-2-2-3-2-2 | 39-44 | 39(1), 40(2), 41(2), 42(3), 43(2), 44(2) | Single-size |
| **Men Slide** (all colors) | 2-2-3-3-2 | 40-44 | 40(2), 41(2), 42(3), 43(3), 44(2) | Single-size |
| **Men Airmove** | 3-6-3 | 39/40-42/43 | 39/40(3), 40/41(6), 42/43(3) | Double-size |
| **Ladies Slide Puffy** (all colors) | 2-2-3-3-2 | 36-40 | 36(2), 37(2), 38(3), 39(3), 40(2) | Single-size |

### Assortment Strategy

**Optimization Principles:**
- Higher quantities allocated to mid-range sizes (most popular sizes)
- Peak allocation typically in the middle of the size range (e.g., size 42 for Men Classic)
- Size ranges vary by gender and series
- Double-size assortments used for specific series (like Airmove)

**Example Application:**
- If ordering "Men Classic Jet Black" → You receive 12 pairs with sizes distributed as 1-2-2-3-2-2 (39-44)
- If ordering "Men Classic Navy Black" → Same assortment pattern (1-2-2-3-2-2)
- If ordering "Men Slide Army" → Different pattern (2-2-3-3-2, 40-44)

## Tiering System

Zuma uses a 6-tier classification system to categorize SKUs based on sales velocity, inventory status, and product lifecycle stage. The tiering system drives inventory management, merchandising decisions, and sales strategies.

### Tier Definitions

| Tier | Classification | Description | Sales Performance | Availability |
|------|---------------|-------------|-------------------|--------------|
| **Tier 1** | Fast Moving | Top 50% of sales quantity (Pareto principle) | Above median pairs sold | Active in stores |
| **Tier 2** | Secondary Fast Moving | Next 20% under the top 50% | Under median but strong | Active in stores |
| **Tier 3** | Tertiary | Not fast moving | Below T1/T2 threshold | Active in stores |
| **Tier 4** | Discontinue & Slow Moving | Discontinued or very slow sales | Minimal/declining | Limited availability |
| **Tier 5** | Dead Stock | Old discontinued SKUs | No sales | Not in stores, dead stock in WH |
| **Tier 8** | New Launch | Newly launched SKUs (first 3 months) | Evaluation period | Active in stores |

### Tier Criteria

**Tier 1 - Fast Moving:**
- Sales quantity: Top 50% (Pareto principle)
- Metric: Above median of pairs sold
- Purpose: Core assortment, highest inventory priority
- Inventory policy: Maintain high stock levels, avoid stockouts

**Tier 2 - Secondary Fast Moving:**
- Sales quantity: Pareto 20% under the top 50%
- Metric: Below median but still significant
- Purpose: Supporting assortment
- Inventory policy: Moderate stock levels

**Tier 3 - Tertiary:**
- Sales performance: Not fast moving
- Purpose: Complete assortment, variety
- Inventory policy: Lower stock levels

**Tier 4 - Discontinue & Slow Moving:**
- Status: Discontinued products or very slow sellers
- Purpose: Clearance, phasing out
- Inventory policy: Sell-through existing stock, no replenishment

**Tier 5 - Dead Stock:**
- Status: Old discontinued SKUs
- Availability: Not available in stores
- Location: Dead stock in warehouse only
- Purpose: Final liquidation or write-off candidates

**Tier 8 - New Launch:**
- Duration: First 3 months after launch
- Purpose: Evaluation period for new products
- Decision point: After 3 months, Merchandiser reclassifies as Tier 1, 2, or 3 based on sales performance
- Special handling: Close monitoring of sales velocity and customer response

### Tier Management Process

**Initial Classification:**
- All new SKUs automatically receive **Tier 8** upon launch

**Reclassification (After 3 Months):**
- Merchandiser reviews sales data (pairs sold, sales velocity)
- Compares against median and Pareto thresholds
- Reclassifies to:
  - **Tier 1** if above median (top 50%)
  - **Tier 2** if below median but in next 20%
  - **Tier 3** if below both thresholds

**Ongoing Review:**
- Tier classifications can change based on sales performance
- Products can move up or down tiers
- Discontinuation decisions move products to Tier 4, then eventually Tier 5

### Tier Usage in Business Operations

**Inventory Planning:**
- Tier 1: Highest safety stock, priority replenishment
- Tier 2: Moderate safety stock
- Tier 3: Lower safety stock
- Tier 4-5: Clearance mode, no new orders
- Tier 8: Closely monitored, flexible inventory levels

**Merchandising:**
- Tier 1-2: Prime shelf space, featured in promotions
- Tier 3: Standard shelf space
- Tier 4: Clearance sections
- Tier 5: Not displayed
- Tier 8: Highlighted as "New Arrivals"

**Data Analysis:**
- Use `tier_lama` (old tier) and `tier_baru` (new tier) to track tier changes over time
- Analyze tier migrations to understand product performance trends

## SKU Management

### SKU Naming Convention

**Reality Check:** Zuma's SKU naming convention is not standardized and can be inconsistent. Naming patterns vary across products and time periods. When working with SKU data, expect variability and use multiple code fields for matching.

### The Version Problem & Kode Mix Solution

Zuma products have multiple **versions** (V0, V1, V2, V3, V4) representing different production batches with minor design updates (logo placement, outsole design, strap pattern). From the customer's perspective, all versions of "MEN CLASSIC JET BLACK" look the same — but Accurate Online assigns **completely different codes** to each version.

**This breaks year-over-year analysis:**

```
Example: MEN CLASSIC JET BLACK (same product, same look, same function)

  V0 batch (2023) → kode kecil: SJ1ACA1    kode besar: SJ1ACA1Z42
  V1 batch (2024) → kode kecil: M1CA32     kode besar: M1CA32Z42
  V2 batch (2025) → kode kecil: M1CAV201   kode besar: M1CAV201Z42

Problem: Query "sales of MEN CLASSIC JET BLACK in 2024 vs 2025"
  → Using kode_besar: M1CAV201Z42 shows ZERO for 2024 (didn't exist yet)
  → The old code SJ1ACA1Z42 had all the 2024 sales
  → Result: misleading YoY comparison

Solution: Kode Mix merges ALL versions into ONE unified code:
  → Kode Mix:      M1CA02CA01        (article level, all V0-V4)
  → Kode Mix Size: M1CA02CA01Z42     (size level, all V0-V4)
  → Now YoY comparison works correctly across version changes
```

### Official Code Types

There are 4 code types, organized by granularity level:

#### Version-Specific Codes (from Accurate Online)

| Code Type | Also Called | Level | Example | Notes |
|-----------|------------|-------|---------|-------|
| **`kode`** | `kode kecil` (small code) | Article (color) | `M1CA32` | Changes when new version is produced. Same physical product gets a NEW code. |
| **`kode_besar`** | `kode besar` (big code) | Article + Size | `M1CA32Z42` | Most granular Accurate code. Also used as `kode_produk` or `kode_barang` in API exports. |

**`kode_produk` = `kode_barang` = `kode_besar`** — these are different names for the same thing across different Accurate exports/APIs.

#### Version-Agnostic Codes (Zuma's solution — the portal_kodemix bridge table)

| Code Type | Also Called | Level | Example | Notes |
|-----------|------------|-------|---------|-------|
| **`Kode Mix`** | Merged article code | Article (color), all versions | `M1CA02CA01` | Unifies SJ1ACA1 + M1CA32 + M1CAV201 → one code. **Use this for article-level analysis.** |
| **`Kode Mix Size`** | Merged size code | Article + Size, all versions | `M1CA02CA01Z42` | Unifies all version-specific size codes → one code. **Use this for SKU-level analysis.** |

#### The Bridge Table: `portal_kodemix`

The `portal_kodemix` table is the **critical lookup/bridge table** that maps version-specific Accurate codes to unified Kode Mix codes. It contains ~5,400+ rows with:

- **Mapping**: `kode_besar` → `Kode Mix Size`, `kode` → `Kode Mix`
- **Classification**: tier_lama, tier_baru, gender, seri, series, tipe, article, color, ukuran
- **Status**: `Aktif` (current version) or `Tidak Aktif` (old version, superseded)
- **Assortment**: assortment pattern, count_by_assortment, totalpairs_hook

**Multiple rows per Kode Mix Size** exist because each old version maps to the same unified code. Filter by `status = 'Aktif'` to get only the current version's mapping.

**Join pattern for data analysis:**
```sql
-- Raw Accurate data → Portal (the critical join)
SELECT k.kode_mix, k.article, k.series, k.tier_baru, ...
FROM raw_sales s
JOIN portal_kodemix k ON s.kode_produk = k.kode_besar AND k.status = 'Aktif'
```

### Product Versioning System

| Version | Batch | Status | Design Differences |
|---------|-------|--------|-------------------|
| **V0** | Oldest | Legacy (Tidak Aktif) | Original design |
| **V1** | Old | Legacy/Active | Updated logo |
| **V2** | Middle | Active | Updated outsole/strap |
| **V3** | Recent | Active | Latest updates |
| **V4** | Newest | Current (Aktif) | Latest production batch |

**What Changes Between Versions:**
- Zuma logo design/placement
- Outsole (upper sole) design
- Strap or "jepit" pattern design
- Production batch/factory

**What Stays the Same:**
- Visual appearance from afar (looks the same to customers)
- Product name and series
- Color/article identity
- Core product function and price point

### Code Matching Strategy

When working with SKU data across systems:

1. **Always use Kode Mix** for analysis (version-agnostic, enables YoY comparison)
2. **Use `kode_besar` / `kode_produk`** to JOIN with portal_kodemix (filter `status = 'Aktif'`)
3. **Match by name** as fallback (use `nama_barang`, `article`, `series`, `gender`)
4. **Be aware**: iSeller uses `Barcode` and `Sku` fields which correspond to `kode_besar`
5. **Validate matches** by checking gender + series + article name
6. **Never rely on code prefixes alone** — naming patterns are inconsistent (see below)

### Naming Pattern Observations (Inconsistent)

**Sometimes gender prefixes are used:**
- `M` = Men (sometimes), `L` = Ladies (sometimes), `BB` = Baby Boys (sometimes)
- `SJ` = Sometimes used (old codes, meaning unclear)
- `Z` = Sometimes used (newer codes, meaning unclear)
- `B1`, `B2` = Boys (sometimes)
- `G1`, `G2` = Girls (sometimes)

**Sometimes series codes are abbreviated:**
- `CA` = Classic, `WG` = Wedges, `SL` = Slide, `SP` = Stripe, `ON` = Onyx, `BL` = Black Series, `AM` = Airmove

**⚠️ Warning:** These patterns are NOT consistent across versions. V0 and V2 of the same product may use completely different prefix patterns. Always cross-reference with the full `nama_barang`, `gender`, `series`, and `article` fields.

## Integration Context

### Data Flow
- **Accurate Online (ERP):** Master product data, inventory levels, sales transactions
- **Ginee (Marketplaces):** Multi-channel inventory sync, marketplace listings
- **iSeller (POS):** Retail sales, in-store inventory

### Common Fields
- SKU Code
- Product Name
- Category/Sub-category
- Brand
- Tier/Classification
- Stock Level
- Price
- Status (Active/Inactive)

## When to Use This Knowledge

Apply this context when:
- Analyzing product performance and sales data
- Building inventory dashboards or reports
- Integrating with e-commerce or marketplace platforms
- Developing product recommendation systems
- Planning assortment or inventory optimization
- Working with ERP, POS, or marketplace data exports
- Creating product catalogs or listings

## Important Notes

- SKU data is sensitive business information - handle with appropriate security
- Always use the most recent data exports from source systems
- Tier classifications may change over time based on sales performance
- Cross-reference between systems (Accurate, Ginee, iSeller) using SKU codes
- Some products may exist in one system but not others (e.g., online-only SKUs)

---

**Status:** Complete
**Sections:** Product Categorization, Product Assortment, Tiering System, SKU Management, Integration Context
