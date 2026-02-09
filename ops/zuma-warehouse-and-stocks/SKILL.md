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
QUEUE → APPROVED → PICKING → PICK_VERIFIED → READY_TO_SHIP
  → IN_DELIVERY → ARRIVED → COMPLETED
```

**Status Definitions:**

| Status | Description | Actor |
|--------|-------------|-------|
| `QUEUE` | Submitted, awaiting approval | Area Supervisor submits |
| `APPROVED` | WH SPV approved quantities | WH Supervisor |
| `PICKING` | Being picked from warehouse | WH Helper |
| `PICK_VERIFIED` | Pick quantities verified | WH Admin |
| `READY_TO_SHIP` | DNPB complete, ready for dispatch | WH Admin |
| `IN_DELIVERY` | Out for delivery to store | WH Helper |
| `ARRIVED` | Received at store | WH Supervisor confirms |
| `COMPLETED` | Fully received and closed | WH Supervisor |

### Order Workflow Example

```
1. Area Supervisor creates order for "Tunjungan Plaza"
   - Delivery Date: 15 Jan 2026
   - Items: 10 articles, 1-5 boxes each
   - Total: ~20 boxes
   - Gets ID: RO-2511-0007

2. Order enters QUEUE
   - Visible to WH Supervisor
   - Stock is reserved (qty_queue updated)

3. WH Supervisor reviews and approves
   - Can edit quantities if needed
   - ONE approve button per RO (not per article)
   - Status: QUEUE → APPROVED

4. WH Helper picks items
   - Updates actual picked quantities
   - May differ from approved (variance tracking)
   - Status: APPROVED → PICKING → PICK_VERIFIED

5. WH Admin verifies pick
   - Generates DNPB (delivery note)
   - Creates SOPB document (PDF)
   - Status: PICK_VERIFIED → READY_TO_SHIP

6. WH Helper delivers
   - Updates shipment status
   - Status: READY_TO_SHIP → IN_DELIVERY

7. Store receives
   - WH Supervisor confirms received quantity
   - Handles variance if actual ≠ shipped
   - Status: IN_DELIVERY → ARRIVED → COMPLETED
```

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
   - Store orders via RO App
   - Status tracking through RO stages
   - Delivery confirmation required

2. **Online Sales**
   - Direct distribution for e-commerce
   - May bypass RO system for direct shipment

3. **Wholesale**
   - Bulk orders to wholesale partners
   - May use custom stock grab

4. **Consignment**
   - Stock placed at consignment locations
   - Tracked separately from retail stores

5. **Event Sales**
   - Temporary stock allocation for events
   - Special category in store system

## Special Stock Operations

### Custom Stock Grab
Reserve stock for non-RO purposes (wholesale, consignment, etc.)

```sql
custom_stock_grab(kode_artikel, warehouse_code, qty, notes, created_by)
```

**Effect:** Reduces ready stock without creating RO

### Custom Stock Release
Release previously grabbed stock back to available inventory

```sql
custom_stock_release(kode_artikel, warehouse_code, qty, notes, created_by)
```

### PO Input
Add stock from purchase orders (only operation that ADDS to base stock)

```sql
po_input_stock(kode_artikel, warehouse_code, qty, notes, created_by)
```

### Picking Adjustment
Correct quantity when actual picked differs from requested

```sql
adjust_picking_qty(session_id, kode_artikel, warehouse_code, actual_qty, notes, created_by)
```

**Common Scenarios:**
- Item damaged during pick (actual < requested)
- Found extra stock during pick (actual > requested, rare)
- Size not available, different size picked instead

## Stock Tracking Views

### Stock Summary (Per Article)
Aggregates across all warehouses:
- Total WHS stock
- Total in queue
- Total in transit
- Total ready stock

### Stock by Warehouse
Shows per warehouse:
- Number of articles
- Total stock
- Total ready stock
- Total in queue/delivery

### Low Stock Alert
Articles with ready stock ≤ 2:
- OUT_OF_STOCK: ready stock = 0
- LOW_STOCK: ready stock = 1-2
- Sorted by urgency

## Database Structure

### Core Tables

**wh_stock** - Main stock tracking
- Tracks stock per article per warehouse
- All quantity fields (queue, picked, delivery, etc.)
- Computed ready_stock field

**wh_stock_history** - Audit trail
- Logs all stock changes
- Tracks before/after quantities
- Links to RO session if applicable

**ro_sessions** - Order headers
- One record per RO ID
- Aggregated quantities
- Status and timestamps

**ro_items** - Order line items
- One record per article per RO
- Tracks quantity at each stage
- Variance tracking (requested vs actual)

## Technical Stack

**Current Production:**
- **Frontend:** Next.js 14 + React (PWA)
- **Backend:** Supabase (PostgreSQL + Realtime)
- **Auth:** Supabase Auth with Row-Level Security (RLS)
- **Real-time:** WebSocket (< 100ms latency)

**Legacy System (being replaced):**
- AppSheet + Google Sheets
- 1-minute polling delay
- Limited scalability

## Key Business Rules

1. **One RO ID = One Approval**
   - Not approved at article level
   - Entire order approved/rejected together
   - Can edit individual article quantities before approval

2. **Stock Reservation**
   - Stock is reserved when RO created (qty_queue)
   - Reservation moves through stages (queue → picked → delivery)
   - Released only when completed or cancelled

3. **Variance Tracking**
   - Pick variance = picked - approved
   - Receive variance = received - shipped
   - Variances logged for analysis

4. **Stock Never Goes Negative**
   - Database constraints prevent negative quantities
   - Operations fail if insufficient stock

5. **Audit Trail**
   - All stock changes logged in wh_stock_history
   - Who, what, when for every operation
   - Linked to RO session if applicable

## Common Use Cases

### Check Stock Availability
```sql
SELECT kode_artikel, warehouse_code, qty_ready_stock, qty_whs_stock
FROM wh_stock
WHERE kode_artikel = 'M1CAV201'
ORDER BY warehouse_code;
```

### View Order Status
```sql
SELECT session_id, store_name, status, total_boxes_requested, total_boxes_approved
FROM ro_sessions
WHERE status = 'QUEUE';
```

### Find Low Stock Items
```sql
SELECT * FROM v_low_stock_alert
WHERE stock_status = 'OUT_OF_STOCK'
ORDER BY kode_artikel;
```

## Integration Points

- **Accurate Online** (ERP) - Sales and inventory data source
- **Ginee** - Marketplace data integration
- **iSeller** - POS system integration
- **Supabase** - Production database and real-time sync

## Document References

- **Database Schema:** `RO App/DATABASE_SCHEMA.md`
- **SQL Migration:** `RO App/web-app/supabase/migrations/002_wh_stock.sql`
- **RO App README:** `RO App/README.md`
- **RO WHS README:** `RO WHS/ro-whs-app/README.md`
