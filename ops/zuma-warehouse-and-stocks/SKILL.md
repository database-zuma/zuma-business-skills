---
name: zuma-warehouse-and-stocks
description: Zuma Indonesia warehouse and inventory management system. Covers physical warehouses (WHS, WHJ, WHB), administrative entities (DDD, LJBB, MBB, UBB), stock tracking, RO (Replenishment Order) system, stock stages, and product distribution channels. Use when discussing warehouse operations, inventory, order fulfillment, or stock management.
user-invocable: false
---

# Zuma Warehouse and Stock Management System

This skill provides context about Zuma Indonesia's warehouse operations, inventory tracking, and replenishment order (RO) system for distributing sandal products from warehouses to retail stores and other channels.

## Warehouse Network

### Physical Warehouses

| Code | Name | Location | Purpose |
|------|------|----------|---------|
| **WHS** | Warehouse Surabaya / Warehouse Pusat | Surabaya | Central warehouse (main operations) |
| **WHJ** | Warehouse Jakarta | Jakarta | Jakarta distribution |
| **WHB** | Warehouse Bali | Bali | Bali distribution |

### Administrative Entities (Legal/Tax Structure)

**Critical Distinction:** DDD, LJBB, MBB, UBB are **administrative/legal entities (PTs)**, NOT physical warehouse locations. They are separate companies within the Zuma Indonesia group, each with their own Accurate Online database.

| Code | Full Name | Business Function |
|------|-----------|-------------------|
| **DDD** | Dream Dare Discover | Main entity. Retail stores + Wholesale + Consignment. Most retail stores report through DDD. |
| **MBB** | Makmur Besar Bersama | Online sales (Shopee, Tokopedia, TikTok Shop) + Wholesale |
| **UBB** | Untung Besar Bersama | Wholesale + Consignment |
| **LJBB** | Lancar Jaya Besar Bersama | PO receiving for Baby & Kids. Suppliers (HJS/Ando) → LJBB Warehouse Pusat → transferred/sold to DDD |

**Primary Administrative Entities for RO System:** DDD and LJBB

**Key Points:**
- All 4 entities share the **same product SKU codes** (same catalog)
- All 4 entities share the **same physical warehouses** (WHS, WHJ, WHB)
- Each entity has its own Accurate Online database with separate API credentials
- In Accurate, "warehouse" names (e.g., "Warehouse Pusat") appear in each entity's database — they refer to the same physical location
- In the RO system, when selecting "warehouse" (DDD/LJBB), you're selecting the administrative entity that manages the stock, not a physical location

**Stock data must be pulled separately per entity** — each entity's Accurate database returns stock positions only for stock owned by that entity at each physical warehouse.

## Technical Infrastructure

### Current Production Stack (as of March 2026)

| Layer | Technology |
|-------|------------|
| **Database** | VPS PostgreSQL (`openclaw_ops` on `76.13.194.120:5432`) |
| **Auth** | NextAuth.js (credentials provider, JWT sessions) |
| **Frontend** | Next.js 15 + React (PWA) — deployed on Vercel |
| **ETL** | Python scripts (`pull_accurate_sales.py`, `pull_accurate_stock.py`) running on VPS |
| **Cron** | VPS cron jobs for daily data refresh (07:00 WIB) |

**Note:** The system was migrated from Supabase to self-hosted VPS PostgreSQL in Feb 2026. Supabase is no longer used.

### Key Database Schemas

| Schema | Purpose |
|--------|---------|
| `branch_super_app_clawdbot` | RO tables, stock tables, transaction views |
| `mart` | iSeller sales mart (`mv_iseller_summary`) |
| `core` | Stock materialized views (`dashboard_cache`) |
| `raw` | Accurate raw stock tables (`accurate_stock_*`) |
| `public` | Shared reference tables (`portal_kodemix`, article metadata) |

### Stock Data Pipeline

```
Accurate Online API (per entity: DDD, LJBB, MBB, UBB)
  → pull_accurate_stock.py (ETL, daily cron)
  → raw.accurate_stock_* tables
  → core.dashboard_cache (REFRESH MATERIALIZED VIEW CONCURRENTLY, daily 07:00 WIB)
  → Consumed by Branch Super App WH Stock page + Zuma Stock Dashboard
```

### WH Stock Page (Branch Super App)

The **WH Stock** tab in the Branch Super App (`zuma-branch-superapp.vercel.app`) is a stock dashboard showing:

- **Data source:** `core.dashboard_cache`
- **Hardcoded warehouses:** `Warehouse Pusat`, `Warehouse Pusat Protol`, `Warehouse Pusat Reject`
- **Non-product exclusion:** `kode_besar !~ '^(gwp|hanger|paperbag|shopbag)'`
- **KPI cards:** Total Pairs, Unique Articles, Dead Stock (T4+T5), Est RSP Value
- **Charts:** Warehouse×Gender stacked bar, Tipe donut, Tier bar, Size bar, Series horizontal bar
- **Top Articles table:** Sortable, shows article/kode_besar/series/tier/tipe/gender
- **Filters:** Gender, series, color, tier, tipe, size, entitas, version, search
- **No date filter** — stock is a point-in-time snapshot (snapshot_date from last refresh)

### `core.dashboard_cache` Columns

| Column | Description |
|--------|-------------|
| kode_barang | Full article code |
| kode_besar | Base article code (for grouping sizes) |
| kode | Short code |
| kode_mix | Mix code |
| article | Article display name |
| nama_gudang | Warehouse name (e.g., "Warehouse Pusat") |
| branch | Branch name |
| category | Product category |
| gender_group | Gender grouping (MEN, WOMEN, KIDS, UNISEX) |
| series | Product series (e.g., AIRMOVE, CLASSIC) |
| group_warna | Color group |
| tier | Priority tier (T1-T5) |
| tipe | Product type (Fashion, Jepit, etc.) |
| ukuran | Size |
| v | Version |
| source_entity | Source entity (DDD, LJBB, MBB, UBB) |
| pairs | Number of pairs |
| est_rsp | Estimated RSP (Retail Selling Price) value |
| snapshot_date | Date of last stock snapshot |

## Product Structure

### Product Units
- **Product:** Sandals (Zuma brand)
- **Base Unit:** Box
- **1 Box = 12 Pairs** (with size assortment)

### Product Identification
- **Article Code:** Full code (e.g., `M1AMVMV102`)
- **Kode Kecil:** Short code (e.g., `M1AMV102`) - Used in most displays
- **Full Name:** Description (e.g., "MEN AIRMOVE 2, INDIGO TAN")

### Product Categories
- **Gender:** MEN / WOMEN / KIDS / UNISEX
- **Series:** AIRMOVE, BLACKSERIES, CLASSIC, ELSA, SLIDE PUFFY, etc.
- **Tier:** Priority ranking (1-10, where 1 is highest priority)

### Size Assortment
Each box contains a size distribution pattern. Example for adult sandals (sizes 39-44):

```
Size:      39  40  41  42  43  44
Pairs:      1   2   3   3   2   1  = 12 pairs total
Pattern:   1-2-3-3-2-1
```

**Note:** Not all articles have the same assortment pattern.

## Warehouse Stock Management

### Stock Formula

```
READY STOCK = WHS_STOCK - QUEUE - PICKED - APPROVED_PICK
              - DELIVERY - COMPLETED - CUSTOM_GRAB + PO_INPUT
```

### Stock Quantity Fields

| Field | Description | When Updated |
|-------|-------------|--------------|
| `qty_whs_stock` | Base warehouse stock | Initial inventory, adjusted manually |
| `qty_queue` | In queue (pending approval) | RO created |
| `qty_approved_pick` | Approved for picking | RO approved by WH Supervisor |
| `qty_picked` | Being picked | WH Helper picking |
| `qty_delivery` | In transit to store | Shipped from warehouse |
| `qty_completed` | Delivered to store | Confirmed arrival |
| `qty_custom_grab` | Reserved for non-RO purposes | Special operations |
| `qty_po_input` | Stock added from PO | Purchase orders received |
| `qty_ready_stock` | **COMPUTED** - Available for ordering | Auto-calculated |

### Stock Status Indicators

| Ready Stock | Status | Action Required |
|-------------|--------|-----------------|
| 0 | OUT_OF_STOCK | Urgent replenishment needed |
| 1-2 | LOW_STOCK | Plan replenishment |
| 3+ | IN_STOCK | Normal operations |

### Stock Movement by RO Status

```
┌────────────────────────────────────────────────────────────┐
│ RO Status Change      │ Stock Movement                     │
├───────────────────────┼────────────────────────────────────┤
│ (RO Created)          │ qty_queue += qty                   │
│ QUEUE → APPROVED      │ qty_queue -=, qty_approved_pick += │
│ APPROVED → IN_PROGRESS│ qty_approved_pick -=, qty_picked +=│
│ IN_PROGRESS → DELIVERY│ qty_picked -=, qty_delivery +=     │
│ DELIVERY → ARRIVED    │ qty_delivery -=, qty_completed +=  │
│ ARRIVED → COMPLETED   │ (no stock change)                  │
└────────────────────────────────────────────────────────────┘
```

## RO (Replenishment Order) System

### Order ID Format

```
RO-YYMM-XXXX

RO   = Replenishment Order (constant prefix)
YY   = Year (e.g., 25 = 2025)
MM   = Month (e.g., 11 = November)
XXXX = Sequential order number (auto-increment, 4 digits)

Example: RO-2511-0007 = Order #7 from November 2025
```

**Order ID is globally unique** across all stores and warehouses.

### Order Status Flow

```
QUEUE → APPROVED → PICKING → PICK_VERIFIED → DNPB_PROCESS → READY_TO_SHIP
  → IN_DELIVERY → ARRIVED → COMPLETED
```

**Status Definitions:**

| Status | Description | Actor |
|--------|-------------|-------|
| `QUEUE` | Submitted, awaiting approval | Area Supervisor submits |
| `APPROVED` | WH SPV approved quantities | WH Supervisor |
| `PICKING` | Being picked from warehouse | WH Helper |
| `PICK_VERIFIED` | Pick quantities verified | WH Admin |
| `DNPB_PROCESS` | DNPB being generated, SOPB ready | WH Admin |
| `READY_TO_SHIP` | DNPB complete, ready for dispatch | WH Admin |
| `IN_DELIVERY` | Out for delivery to store | WH Helper |
| `ARRIVED` | Received at store | WH Supervisor confirms |
| `COMPLETED` | Fully received and closed | WH Supervisor |

### SOPB & DNPB Documents

- **SOPB (Surat Order Pengiriman Barang):** Generated in the SOPB Generator tab. Number is **user input**. Groups articles by entity.
- **DNPB (Delivery Note Pengiriman Barang):** Number comes from **Accurate Online** after the SOPB is uploaded. Each entity has its own DNPB number (`dnpb_number_ddd`, `dnpb_number_ljbb`, `dnpb_number_mbb`, `dnpb_number_ubb`).

### User Roles in RO System

| Role | Abbreviation | Responsibilities |
|------|--------------|------------------|
| **Area Supervisor** | AS | Creates orders for stores |
| **Warehouse Supervisor** | WH SPV | Approves orders, confirms arrivals, master access |
| **Warehouse Admin** | WH Admin | Verifies picks, generates DNPB/SOPB documents |
| **Warehouse Helper** | WH Helper | Picks stock, manages delivery |

## Distribution Channels

Products can be distributed to multiple channels:

1. **Retail Stores** (Primary - via RO System)
2. **Online Sales** (Shopee, Tokopedia, TikTok Shop — via MBB entity)
3. **Wholesale** (Bulk orders — via DDD/UBB)
4. **Consignment** (Stock at partner locations — via DDD/UBB)
5. **Event Sales** (Temporary allocation — WILBEX, IMBEX)

## Special Stock Operations

### Custom Stock Grab
Reserve stock for non-RO purposes (wholesale, consignment, etc.)
**Effect:** Reduces ready stock without creating RO

### Custom Stock Release
Release previously grabbed stock back to available inventory

### PO Input
Add stock from purchase orders (only operation that ADDS to base stock)

### Picking Adjustment
Correct quantity when actual picked differs from requested

## Stock Tracking Views

### Stock Summary (Per Article)
Aggregates across all warehouses: total WHS stock, total in queue, total in transit, total ready stock

### Stock by Warehouse
Per warehouse: number of articles, total stock, total ready stock, total in queue/delivery

### Low Stock Alert
Articles with ready stock ≤ 2: OUT_OF_STOCK (0), LOW_STOCK (1-2)

## Key Business Rules

1. **One RO ID = One Approval** — entire order approved/rejected together
2. **Stock Reservation** — reserved when RO created, moves through stages
3. **Variance Tracking** — pick variance and receive variance logged
4. **Stock Never Goes Negative** — database constraints prevent negative quantities
5. **Audit Trail** — all stock changes logged in `wh_stock_history`
6. **DNPB per Entity** — each entity has its own DNPB number
7. **Stage Progression** — manual, one stage at a time via "Next Stage" button

## Integration Points

- **Accurate Online** (ERP) — Sales and inventory data source, per entity
- **iSeller** (POS System) — Daily sales data for retail stores
- **Ginee** — Marketplace data integration
- **Branch Super App** (`zuma-branch-superapp.vercel.app`) — RO management + stock dashboard + sales analytics
- **Zuma Stock Dashboard** (`zuma-stock-dashboard.vercel.app`) — Dedicated stock analytics (all branches)

## Document References

- **Branch Super App:** `zuma-branch-superapp/README.md`
- **Database Schema:** See `zuma-database-assistant-skill` for full schema reference
- **Data Analyst Skill:** See `zuma-data-analyst-skill` for SQL templates and query patterns
