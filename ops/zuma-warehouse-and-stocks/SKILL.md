#BQ|---
#ZS|name: zuma-warehouse-and-stocks
#XT|description: Zuma Indonesia warehouse and inventory management system. Covers physical warehouses (WHS, WHJ, WHB), administrative entities (DDD, LJBB, MBB, UBB), stock tracking, RO (Replenishment Order) system, stock stages, and product distribution channels. Use when discussing warehouse operations, inventory, order fulfillment, or stock management.
#YW|user-invocable: false
#HH|---
#SY|
#HN|# Zuma Warehouse and Stock Management System
#XW|
#PT|This skill provides context about Zuma Indonesia's warehouse operations, inventory tracking, and replenishment order (RO) system for distributing sandal products from warehouses to retail stores and other channels.
#SK|
#WR|## Warehouse Network
#TX|
#XZ|### Physical Warehouses
#BY|
#HM|| Code | Name | Location | Purpose |
#XV||------|------|----------|---------|
#NN|| **WHS** | Warehouse Surabaya / Warehouse Pusat | Surabaya | Central warehouse (main operations) |
#RQ|| **WHJ** | Warehouse Jakarta | Jakarta | Jakarta distribution |
#YH|| **WHB** | Warehouse Bali | Bali | Bali distribution |
#YQ|
#QH|### Administrative Entities (Legal/Tax Structure)
#ZP|
#PV|**Critical Distinction:** DDD, LJBB, MBB, UBB are **administrative/legal entities (PTs)**, NOT physical warehouse locations. They are separate companies within the Zuma Indonesia group, each with their own Accurate Online database.
#KW|
#HT|| Code | Full Name | Business Function |
#BN||------|-----------|-------------------|
#HB|| **DDD** | Dream Dare Discover | Main entity. Retail stores + Wholesale + Consignment. Most retail stores report through DDD. |
#MV|| **MBB** | Makmur Besar Bersama | Online sales (Shopee, Tokopedia, TikTok Shop) + Wholesale |
#HM|| **UBB** | Untung Besar Bersama | Wholesale + Consignment |
#YK|| **LJBB** | Lancar Jaya Besar Bersama | PO receiving for Baby & Kids. Suppliers (HJS/Ando) → LJBB Warehouse Pusat → transferred/sold to DDD |
#SZ|
#XN|**Primary Administrative Entities for RO System:** DDD and LJBB
#QY|
#HJ|**Key Points:**
#QR|- All 4 entities share the **same product SKU codes** (same catalog)
#SQ|- All 4 entities share the **same physical warehouses** (WHS, WHJ, WHB)
#TB|- Each entity has its own Accurate Online database with separate API credentials
#RT|- In Accurate, "warehouse" names (e.g., "Warehouse Pusat") appear in each entity's database — they refer to the same physical location
#BS|- In the RO system, when selecting "warehouse" (DDD/LJBB), you're selecting the administrative entity that manages the stock, not a physical location
#ZK|
#XR|**Stock data must be pulled separately per entity** — each entity's Accurate database returns stock positions only for stock owned by that entity at each physical warehouse.
#XN|
#PB|## Technical Infrastructure
#PB|
#QT|### Current Production Stack (as of March 2026)
#TJ|
#PV|| Layer | Technology |
#NZ||-------|------------|
#RY|| **Database** | VPS PostgreSQL (`openclaw_ops` on `76.13.194.120:5432`) |
#KW|| **Auth** | NextAuth.js (credentials provider, JWT sessions) |
#TT|| **Frontend** | Next.js 15 + React (PWA) — deployed on Vercel |
#RT|| **ETL** | Python scripts (`pull_accurate_sales.py`, `pull_accurate_stock.py`) running on VPS |
#QT|| **Cron** | VPS cron jobs for daily data refresh (07:00 WIB) |
#YJ|
#YX|**Note:** The system was migrated from Supabase to self-hosted VPS PostgreSQL in Feb 2026. Supabase is no longer used.
#XN|
#KR|### Key Database Schemas
#KR|
#WQ|| Schema | Purpose |
#HT||--------|---------|
#BT|| `branch_super_app_clawdbot` | RO tables, stock tables, transaction views |
#SQ|| `mart` | iSeller sales mart (`mv_iseller_summary`) |
#TP|| `core` | Stock materialized views (`dashboard_cache`) |
#NR|| `raw` | Accurate raw stock tables (`accurate_stock_*`) |
#PY|| `public` | Shared reference tables (`portal_kodemix`, article metadata) |
#JQ|
#YR|### Stock Data Pipeline
#RT|
#KQ|```
#JW|Accurate Online API (per entity: DDD, LJBB, MBB, UBB)
#YQ|  → pull_accurate_stock.py (ETL, daily cron)
#TB|  → raw.accurate_stock_* tables
#KP|  → core.dashboard_cache (REFRESH MATERIALIZED VIEW CONCURRENTLY, daily 07:00 WIB)
#TX|  → Consumed by Branch Super App WH Stock page + Zuma Stock Dashboard
#ZW|```
#JW|
#JX|### WH Stock Page (Branch Super App)
#PX|
#RR|The **WH Stock** tab in the Branch Super App (`zuma-branch-superapp.vercel.app`) is a stock dashboard showing:
#KB|
#NQ|- **Data source:** `core.dashboard_cache`
#PS|- **Hardcoded warehouses:** `Warehouse Pusat`, `Warehouse Pusat Protol`, `Warehouse Pusat Reject`
#NP|- **Non-product exclusion:** `kode_besar !~ '^(gwp|hanger|paperbag|shopbag)'`
#QR|- **KPI cards:** Total Pairs, Unique Articles, Dead Stock (T4+T5), Est RSP Value
#MH|- **Charts:** Warehouse×Gender stacked bar, Tipe donut, Tier bar, Size bar, Series horizontal bar
#QJ|- **Top Articles table:** Sortable, shows article/kode_besar/series/tier/tipe/gender
#XM|- **Filters:** Gender, series, color, tier, tipe, size, entitas, version, search
#HH|- **No date filter** — stock is a point-in-time snapshot (snapshot_date from last refresh)
#WY|
#WR|### `core.dashboard_cache` Columns
#RT|
#SQ|| Column | Description |
#PM||--------|-------------|
#SS|| kode_barang | Full article code |
#PZ|| kode_besar | Base article code (for grouping sizes) |
#YK|| kode | Short code |
#ZY|| kode_mix | Mix code |
#WJ|| article | Article display name |
#VX|| nama_gudang | Warehouse name (e.g., "Warehouse Pusat") |
#WZ|| branch | Branch name |
#MK|| category | Product category |
#XQ|| gender_group | Gender grouping (MEN, WOMEN, KIDS, UNISEX) |
#NX|| series | Product series (e.g., AIRMOVE, CLASSIC) |
#MV|| group_warna | Color group |
#ZK|| tier | Priority tier (T1-T5) |
#NB|| tipe | Product type (Fashion, Jepit, etc.) |
#RS|| ukuran | Size |
#RX|| v | Version |
#PP|| source_entity | Source entity (DDD, LJBB, MBB, UBB) |
#HZ|| pairs | Number of pairs |
#NX|| est_rsp | Estimated RSP (Retail Selling Price) value |
#ST|| snapshot_date | Date of last stock snapshot |
#PP|
#MT|## Product Structure
#PV|
#MT|### Product Units
#ZH|- **Product:** Sandals (Zuma brand)
#SY|- **Base Unit:** Box
#HV|- **1 Box = 12 Pairs** (with size assortment)
#XM|
#VY|### Product Identification
#SX|- **Article Code:** Full code (e.g., `M1AMVMV102`)
#RK|- **Kode Kecil:** Short code (e.g., `M1AMV102`) - Used in most displays
#HN|- **Full Name:** Description (e.g., "MEN AIRMOVE 2, INDIGO TAN")
#YB|
#HM|### Product Categories
#PN|- **Gender:** MEN / WOMEN / KIDS / UNISEX
#HJ|- **Series:** AIRMOVE, BLACKSERIES, CLASSIC, ELSA, SLIDE PUFFY, etc.
#XT|- **Tier:** Priority ranking (1-10, where 1 is highest priority)
#PX|
#SZ|### Size Assortment
#BY|Each box contains a size distribution pattern. Example for adult sandals (sizes 39-44):
#BM|
#BW|```
#VQ|Size:      39  40  41  42  43  44
#TV|Pairs:      1   2   3   3   2   1  = 12 pairs total
#RM|Pattern:   1-2-3-3-2-1
#RY|```
#QR|
#SR|**Note:** Not all articles have the same assortment pattern.
#WX|
#QK|## Warehouse Stock Management
#RS|
#MZ|### Stock Formula
#VM|
#VZ|```
#XY|READY STOCK = WHS_STOCK - QUEUE - PICKED - APPROVED_PICK
#BH|              - DELIVERY - COMPLETED - CUSTOM_GRAB + PO_INPUT
#NN|```
#PY|
#XM|### Stock Quantity Fields
#HM|
#XZ|| Field | Description | When Updated |
#NV||-------|-------------|--------------|
#VN|| `qty_whs_stock` | Base warehouse stock | Initial inventory, adjusted manually |
#PZ|| `qty_queue` | In queue (pending approval) | RO created |
#XW|| `qty_approved_pick` | Approved for picking | RO approved by WH Supervisor |
#RX|| `qty_picked` | Being picked | WH Helper picking |
#MJ|| `qty_delivery` | In transit to store | Shipped from warehouse |
#ZB|| `qty_completed` | Delivered to store | Confirmed arrival |
#BS|| `qty_custom_grab` | Reserved for non-RO purposes | Special operations |
#MP|| `qty_po_input` | Stock added from PO | Purchase orders received |
#HJ|| `qty_ready_stock` | **COMPUTED** - Available for ordering | Auto-calculated |
#SK|
#NS|### Stock Status Indicators
#QB|
#ZR|| Ready Stock | Status | Action Required |
#VY||-------------|--------|-----------------|
#MT|| 0 | OUT_OF_STOCK | Urgent replenishment needed |
#RH|| 1-2 | LOW_STOCK | Plan replenishment |
#JN|| 3+ | IN_STOCK | Normal operations |
#VK|
#KN|### Stock Movement by RO Status
#RT|
#BR|```
#JT|┌────────────────────────────────────────────────────────────┐
#RJ|│ RO Status Change      │ Stock Movement                     │
#XM|├───────────────────────┼────────────────────────────────────┤
#KH|│ (RO Created)          │ qty_queue += qty                   │
#QX|│ QUEUE → APPROVED      │ qty_queue -=, qty_approved_pick += │
#RP|│ APPROVED → IN_PROGRESS│ qty_approved_pick -=, qty_picked +=│
#PX|│ IN_PROGRESS → DELIVERY│ qty_picked -=, qty_delivery +=     │
#PQ|│ DELIVERY → ARRIVED    │ qty_delivery -=, qty_completed +=  │
#HB|│ ARRIVED → COMPLETED   │ (no stock change)                  │
#XK|└────────────────────────────────────────────────────────────┘
#QQ|```
#YV|
#BJ|## RO (Replenishment Order) System
#RS|
#RR|### Order ID Format
#BH|
#PJ|```
#VK|RO-YYMM-XXXX
#QX|
#VQ|RO   = Replenishment Order (constant prefix)
#SQ|YY   = Year (e.g., 25 = 2025)
#TP|MM   = Month (e.g., 11 = November)
#XZ|XXXX = Sequential order number (auto-increment, 4 digits)
#BN|
#ST|Example: RO-2511-0007 = Order #7 from November 2025
#XB|```
#JM|
#QM|**Order ID is globally unique** across all stores and warehouses.
#PX|
#MX|### Order Status Flow
#XQ|
#NZ|```
#QR|QUEUE → APPROVED → PICKING → PICK_VERIFIED → DNPB_PROCESS → READY_TO_SHIP
#TM|  → IN_DELIVERY → ARRIVED → COMPLETED
#HY|```
#YZ|
#WJ|**Status Definitions:**
#ZP|
#PK|| Status | Description | Actor |
#YZ||--------|-------------|-------|
#TX|| `QUEUE` | Submitted, awaiting approval | Area Supervisor submits |
#JY|| `APPROVED` | WH SPV approved quantities | WH Supervisor |
#NZ|| `PICKING` | Being picked from warehouse | WH Helper |
#NX|| `PICK_VERIFIED` | Pick quantities verified | WH Admin |
#BN|| `DNPB_PROCESS` | DNPB being generated, SOPB ready | WH Admin |
#YX|| `READY_TO_SHIP` | DNPB complete, ready for dispatch | WH Admin |
#HQ|| `IN_DELIVERY` | Out for delivery to store | WH Helper |
#BY|| `ARRIVED` | Received at store | WH Supervisor confirms |
#WH|| `COMPLETED` | Fully received and closed | WH Supervisor |
#MJ|
#WQ|### SOPB & DNPB Documents
#VQ|
#VY|- **SOPB (Surat Order Pengiriman Barang):** Generated in the SOPB Generator tab. Number is **user input**. Groups articles by entity.
#BW|- **DNPB (Delivery Note Pengiriman Barang):** Number comes from **Accurate Online** after the SOPB is uploaded. Each entity has its own DNPB number (`dnpb_number_ddd`, `dnpb_number_ljbb`, `dnpb_number_mbb`, `dnpb_number_ubb`).
#QP|
#TX|### User Roles in RO System
#WV|
#KZ|| Role | Abbreviation | Responsibilities |
#WK||------|--------------|------------------|
#WZ|| **Area Supervisor** | AS | Creates orders for stores |
#NV|| **Warehouse Supervisor** | WH SPV | Approves orders, confirms arrivals, master access |
#PM|| **Warehouse Admin** | WH Admin | Verifies picks, generates DNPB/SOPB documents |
#HX|| **Warehouse Helper** | WH Helper | Picks stock, manages delivery |
#HS|
#MH|## Distribution Channels
#QW|
#NZ|Products can be distributed to multiple channels:
#RJ|
#SR|1. **Retail Stores** (Primary - via RO System)
#QT|2. **Online Sales** (Shopee, Tokopedia, TikTok Shop — via MBB entity)
#QT|3. **Wholesale** (Bulk orders — via DDD/UBB)
#QP|4. **Consignment** (Stock at partner locations — via DDD/UBB)
#ZQ|5. **Event Sales** (Temporary allocation — WILBEX, IMBEX)
#JX|
## RO Lifecycle Apps (Phase 4 - 2026)
The RO system now includes two web apps for end-to-end tracking from warehouse delivery to store confirmation.
### App Overview
| App | URL | Purpose | Users |
|-----|-----|---------|-------|
| **Super App** | zuma-branch-superapp.vercel.app | Driver coordination, Mark Arrived, DNPB handling, Banding confirmation | Warehouse/Driver/Admin |
| **SPG App** | ro-arrival-spg-app.vercel.app | Physical RO confirmation, Fisik entry, Selisih/Banding resolution | Store SPG |
### Super App Features (zuma-branch-superapp)
1. **Mark Arrived** — Driver marks RO as arrived at store (status: IN_DELIVERY → ARRIVED)
2. **DNPB Error Handling** — Resolve "Daftar Numero Pengiriman Barang" discrepancies
3. **Banding Confirmation** — Confirm box count reconciliation (fisik vs pairs_shipped)
4. **RO Status Dashboard** — View all RO stages from QUEUE to COMPLETED
### SPG App Features (ro-arrival-spg-app)
1. **4-Tab Interface** — Tunggu (ARRIVED), Selisih (DISCREPANCY), Banding (BANDING_SENT), Done (COMPLETED)
2. **Fisik Entry** — Enter actual physical count received
3. **Selisih Resolution** — Handle discrepancy between shipped and received
4. **Banding Recount** — Re-count loop when fisik ≠ pairs_shipped
### Database Schema Updates
New tables in `branch_super_app_clawdbot` schema:
1. **ro_receipt** — Track RO receipts per article/size
   - Fields: ro_id, article_code, sku_code, size, pairs_shipped, fisik, selisih, boxes_ddd/ljbb/mbb/ubb, is_confirmed, received_at, resolution_status
2. **ro_banding_notices** — Banding notification records
   - Fields: ro_id, article_code, created_at, status
3. **Views:** ro_arrive_detail (JOINs ro_process × portal.kodemix)
4. **Functions:** get_arrived_ro_list(), confirm_ro_receipt(), complete_ro_status(), get_resolved_ro_list()
### Status Flow
```
QUEUE → APPROVED → PICKING → PICK_VERIFIED → DNPB_PROCESS → READY_TO_SHIP → IN_DELIVERY → ARRIVED → COMPLETED
                                                                    ↓
                                                            BANDING_SENT (re-entry for recount)
```
### Deployment
- Super App: Vercel (master branch)
- SPG App: Vercel (main branch)
- Database: VPS 76.13.194.120 (openclaw_ops)
#VS|## Special Stock Operations
#TM|
#NJ|### Custom Stock Grab
#WV|Reserve stock for non-RO purposes (wholesale, consignment, etc.)
#VZ|**Effect:** Reduces ready stock without creating RO
#VZ|
#JH|### Custom Stock Release
#YN|Release previously grabbed stock back to available inventory
#PY|
#ZY|### PO Input
#KQ|Add stock from purchase orders (only operation that ADDS to base stock)
#YM|
#KR|### Picking Adjustment
#VB|Correct quantity when actual picked differs from requested
#BP|
#ZH|## Stock Tracking Views
#XK|
#HZ|### Stock Summary (Per Article)
#RR|Aggregates across all warehouses: total WHS stock, total in queue, total in transit, total ready stock
#PX|
#ZX|### Stock by Warehouse
#MQ|Per warehouse: number of articles, total stock, total ready stock, total in queue/delivery
#NM|
#BZ|### Low Stock Alert
#PS|Articles with ready stock ≤ 2: OUT_OF_STOCK (0), LOW_STOCK (1-2)
#MV|
#KK|## Key Business Rules
#WQ|
#JM|1. **One RO ID = One Approval** — entire order approved/rejected together
#WJ|2. **Stock Reservation** — reserved when RO created, moves through stages
#JW|3. **Variance Tracking** — pick variance and receive variance logged
#KY|4. **Stock Never Goes Negative** — database constraints prevent negative quantities
#PZ|5. **Audit Trail** — all stock changes logged in `wh_stock_history`
#SV|6. **DNPB per Entity** — each entity has its own DNPB number
#KB|7. **Stage Progression** — manual, one stage at a time via "Next Stage" button
#BX|
#BV|## Integration Points
#HB|
#VZ|- **Accurate Online** (ERP) — Sales and inventory data source, per entity
#KQ|- **iSeller** (POS System) — Daily sales data for retail stores
#KB|- **Ginee** — Marketplace data integration
#YX|- **Branch Super App** (`zuma-branch-superapp.vercel.app`) — RO management + stock dashboard + sales analytics
#SP|- **Zuma Stock Dashboard** (`zuma-stock-dashboard.vercel.app`) — Dedicated stock analytics (all branches)
#VK|
#HT|## Document References
#NP|
#JS|- **Branch Super App:** `zuma-branch-superapp/README.md`
#PT|- **Database Schema:** See `zuma-database-assistant-skill` for full schema reference
#HP|- **Data Analyst Skill:** See `zuma-data-analyst-skill` for SQL templates and query patterns
