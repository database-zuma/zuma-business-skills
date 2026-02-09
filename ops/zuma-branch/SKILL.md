---
name: zuma-branch
description: Zuma Indonesia offline retail store network and branch management. Covers 6 branches (Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali), store categories (RETAIL, NON-RETAIL, EVENT), store formats (mall units and high-street Ruko), stock management, and active events (WILBEX, IMBEX). Use when discussing retail stores, branch operations, store inventory, or retail management.
user-invocable: false
---

# Zuma Branch and Store Network

This skill provides context about Zuma Indonesia's offline retail store network, store operations, and branch-level inventory management.

## Store Network Overview

### Store Categories

| Category | Description | Stock Management | Purpose |
|----------|-------------|------------------|---------|
| **RETAIL** | Permanent retail stores | Full planogram + storage | Main sales channel |
| **NON-RETAIL** | Non-traditional outlets | Limited stock | Alternative distribution |
| **EVENT** | Temporary event locations | Event-specific allocation | Seasonal/promotional |

### Geographic Hierarchy

**Hierarchy:** Branch → Area → Store

**Branches:**
- **Jatim** (East Java)
- **Jakarta**
- **Sumatra**
- **Sulawesi**
- **Batam**
- **Bali** (includes Bali and Lombok islands)

**Areas:**
Areas generally align with branches, except Bali which is subdivided:

| Branch | Areas |
|--------|-------|
| Jatim | Jatim |
| Jakarta | Jakarta |
| Sumatra | Sumatra |
| Sulawesi | Sulawesi |
| Batam | Batam |
| Bali | **Bali 1**, **Bali 2**, **Bali 3**, **Lombok** |

**Area Structure:**
- Each area has an **Area Supervisor (AS)**
- Area Supervisor manages multiple stores in their region
- Area Supervisor creates RO (Replenishment Orders) for their stores

## Store Master Data

### Store Identification

| Field | Description | Example |
|-------|-------------|---------|
| **Code** | Unique store identifier | `ZRP`, `ZMT`, `ZSM` |
| **Name** | Full store name | "Zuma Royal Plaza" |
| **Branch** | Branch designation | "Jatim", "Jakarta", "Bali" |
| **Area** | Geographic area | "Jatim", "Jakarta" |
| **Category** | Store type | "RETAIL", "NON-RETAIL", "EVENT" |

### Example Stores

**Jatim Branch:**
- Zuma Tunjungan Plaza (mall unit - Surabaya)
- Zuma Bintaro Xchange (mall unit)

**Batam Branch:**
- Zuma Nagoya Hills Batam (mall unit)

**Bali Branch:**
- Zuma Dalung (high-street "Ruko" - Bali 1)
- Zuma Gianyar (high-street "Ruko" - Bali 2)

**Lombok Area (under Bali Branch):**
- Zuma Mataram (street store)
- Zuma Epicentrum (mall unit)

**Note:** Store names follow the pattern "Zuma [Location/Mall Name]". There are no short codes like ZRP or ZMT.

## Store Stock Management

### Stock Capacity

Each store has defined capacity limits:

| Field | Description | Unit |
|-------|-------------|------|
| **max_display** | Maximum pairs on display | Pairs |
| **max_stock** | Maximum total stock (display + storage) | Pairs |

### Stock Components

```
Total Store Stock = Display Stock + Storage Stock
```

**Display Stock (Planogram):**
- Stock visible to customers
- Organized by planogram layout
- Target quantity: `planogram_pairs`

**Storage Stock (Backroom):**
- Reserve stock in storage area
- Replenishes display as items sell
- Target quantity: `storage_pairs`

### Stock Fields (per Article per Store)

| Field | Description | Unit | Calculation |
|-------|-------------|------|-------------|
| `on_hand_pairs` | Current total stock at store | Pairs | Actual count |
| `on_hand_boxes` | Current stock in boxes | Boxes | `on_hand_pairs / 12` |
| `planogram_pairs` | Target display quantity | Pairs | Set by merchandising |
| `storage_pairs` | Target storage quantity | Pairs | Set by inventory planning |

### Assortment Status

| Status | Description | Stock Condition |
|--------|-------------|-----------------|
| **FULL** | Complete size run available | All sizes in stock according to assortment |
| **BROKEN** | Incomplete sizes | Missing some sizes from standard assortment |

**Business Impact:**
- FULL assortment = Better conversion rates
- BROKEN assortment = May trigger replenishment order
- RO system prioritizes BROKEN assortments for restock

## Store Replenishment Process

### When Store Orders Stock

**Trigger Conditions:**
1. Display stock below planogram target
2. Broken assortment (missing sizes)
3. Storage stock depleted
4. New product launch
5. Promotional campaign

### RO (Replenishment Order) Creation

**Who Creates:** Area Supervisor (AS)

**Order Details:**
- Target store: e.g., "Zuma Tunjungan Plaza"
- Delivery date: Requested delivery date
- Articles: List of products to order
- Quantities: Number of boxes per article
- Source warehouse: DDD or LJBB (or both)

**Example Order:**
```
RO ID: RO-2512-0007
Store: Zuma Tunjungan Plaza
Delivery Date: 2026-01-15
Articles: 10 different products
Total Quantity: 20 boxes
Source: DDD (15 boxes), LJBB (5 boxes)
```

### Receiving Process

**Status Flow:**
```
WAREHOUSE → IN_DELIVERY → ARRIVED → COMPLETED
```

1. **IN_DELIVERY** - Order shipped from warehouse
2. **ARRIVED** - Order received at store
   - WH Supervisor confirms arrival
   - Checks quantity against shipment
   - Records any variance
3. **COMPLETED** - Order processed and stock added
   - Stock added to `on_hand_pairs`
   - Assortment status updated
   - Order closed

### Variance Handling

**Receive Variance = Received Qty - Shipped Qty**

**Common Variances:**
- **Short delivery:** Received < Shipped (damage in transit)
- **Overage:** Received > Shipped (rare, packing error)
- **Wrong article:** Different product delivered

**Resolution:**
- Variance logged in system
- WH Supervisor investigates
- Stock adjustment processed
- Replacement order if needed

## Store Operations

### Merchandising

**Planogram Management:**
- Visual layout plan for product display
- Specifies product placement and quantities
- Updated seasonally or for campaigns

**Space Allocation:**
- Display space allocated by product tier
- Tier 1 products get prime visibility
- Lower tiers in secondary positions

### Inventory Cycle

```
┌─────────────────────────────────────────────────┐
│ 1. Customer Purchase                            │
│    → on_hand_pairs decreases                    │
│    → Display stock depletes                     │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│ 2. Display Replenishment                        │
│    → Move stock from storage to display         │
│    → Maintain planogram levels                  │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│ 3. Storage Depleted                             │
│    → Assortment becomes BROKEN                  │
│    → Trigger RO creation                        │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│ 4. Area Supervisor Creates RO                   │
│    → Order sent to warehouse                    │
│    → Stock reserved at warehouse                │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│ 5. Warehouse Fulfills Order                     │
│    → Stock picked, packed, shipped              │
│    → Delivery to store                          │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│ 6. Store Receives Stock                         │
│    → on_hand_pairs increases                    │
│    → Assortment status updated to FULL          │
│    → Cycle repeats                              │
└─────────────────────────────────────────────────┘
```

### Stock Count

**Purpose:** Verify physical stock matches system records

**Frequency:**
- Full count: Monthly or quarterly
- Spot count: Weekly for high-value items
- Cycle count: Daily for bestsellers

**Process:**
1. Count physical stock (pairs)
2. Compare to `on_hand_pairs` in system
3. Record variance
4. Investigate significant discrepancies
5. Adjust system if confirmed

**Common Discrepancies:**
- Theft/shrinkage
- Mis-scans at POS
- Transfer errors
- Damage not recorded

## Store Performance Metrics

### Sales Metrics
- **Pairs sold per day** - Store throughput
- **Revenue per square meter** - Space efficiency
- **Conversion rate** - Traffic to sales ratio

### Inventory Metrics
- **Stock turn rate** - How fast inventory moves
- **Days of inventory** - Stock coverage in days
- **Broken assortment rate** - % of articles with broken assortments
- **Out-of-stock rate** - % of time critical items unavailable

### Operational Metrics
- **RO fulfillment time** - Order to delivery duration
- **Receive variance rate** - Accuracy of deliveries
- **Stock count accuracy** - System vs physical match rate

## Store Types in Detail

### RETAIL Stores (Permanent)

**Characteristics:**
- Permanent locations (mall or high-street)
- Full product range
- Consistent operating hours
- Regular restocking schedule

**Store Formats:**

**Mall Units (Jatim, Jakarta, Sumatra, Sulawesi, Batam):**
- Island units - Free-standing displays in mall corridors
- Kiosk units - Small enclosed units in malls
- Examples: Zuma Tunjungan Plaza, Zuma Bintaro Xchange, Zuma Nagoya Hills Batam

**High-Street "Ruko" (Rumah Toko) - Primarily in Bali:**
- Physical street-facing buildings
- Indonesian-style shophouse format
- Larger footprint than mall units
- Examples: Zuma Dalung, Zuma Gianyar

**Lombok (Mixed Format):**
- 1 street store: Zuma Mataram
- 1 mall unit: Zuma Epicentrum

**Inventory Strategy:**
- Maintain full assortments across all tiers
- Higher planogram quantities for bestsellers
- Seasonal product rotation

### NON-RETAIL Channels

**Wholesale:**
- Bulk orders to wholesale partners
- Distributor agreements
- Larger order quantities
- Different pricing structure

**Consignment:**
- Stock placed at partner locations
- Payment on sold basis
- Partner manages display and sales
- Inventory tracked separately from owned stores

### EVENT Stores (Temporary)

**Characteristics:**
- Limited duration (days to weeks)
- Event-specific location
- Focused product selection
- Special pricing/promotions

**Active Repeating Events:**

**WILBEX (Willow Mom & Baby Expo):**
- Branch: Jatim
- Recurring event
- Family/baby-focused audience
- Seasonal schedule

**IMBEX (International Mom & Baby Expo):**
- Branch: Jakarta
- Recurring event
- Family/baby-focused audience
- Larger scale than WILBEX

**Inventory Strategy:**
- Pre-allocated stock for event duration
- Limited replenishment during event
- Return unused stock to warehouse
- Focus on family-friendly designs and sizes

## Store Staff Roles

### Store Manager
- Overall store operations
- Sales performance
- Staff management
- Customer service
- Inventory oversight

### Sales Staff
- Customer service
- Product knowledge
- Sales transactions
- Display maintenance
- Stock replenishment (storage to display)

### Area Supervisor (AS)
- **Not store-based** - Manages multiple stores
- Creates RO for all stores in area
- Monitors store performance
- Coordinates with warehouse
- Regional merchandising decisions

## Integration with Warehouse System

### Data Flow: Store → Warehouse

**RO Creation:**
```
Area Supervisor creates RO
  → Specifies store and articles
  → System checks warehouse stock availability
  → RO enters QUEUE at warehouse
  → Warehouse stock reserved (qty_queue)
```

### Data Flow: Warehouse → Store

**Order Fulfillment:**
```
Warehouse picks order
  → Stock status updates through stages
  → Delivery notification sent to store
  → Store receives and confirms
  → Store stock updated (on_hand_pairs)
```

### Real-time Sync

**Current System (Next.js + Supabase):**
- Real-time stock updates (< 100ms latency)
- WebSocket connections
- Live order status tracking
- Instant notifications

**Legacy System (AppSheet + Google Sheets):**
- 1-minute polling delay
- Manual refresh required
- Limited real-time capability

## Store Database Structure

### Core Fields

```sql
stores (
  id UUID PRIMARY KEY,
  code VARCHAR(50) UNIQUE,           -- ZRP, ZMT
  name VARCHAR(100) NOT NULL,        -- Zuma Royal Plaza
  branch VARCHAR(50),                -- Jatim, Jakarta
  area VARCHAR(50),                  -- Jatim
  category VARCHAR(50),              -- RETAIL, NON-RETAIL, EVENT
  area_supervisor_id UUID,           -- Link to Area Supervisor user
  max_display INTEGER,               -- Maximum display capacity (pairs)
  max_stock INTEGER,                 -- Maximum total capacity (pairs)
  is_active BOOLEAN DEFAULT true,    -- Store currently operating
  created_at TIMESTAMPTZ
)
```

### Store Stock Fields

```sql
store_stock (
  id UUID PRIMARY KEY,
  store_id UUID,                     -- Link to store
  product_id UUID,                   -- Link to article
  on_hand_pairs INTEGER,             -- Current total stock (pairs)
  on_hand_boxes NUMERIC,             -- Current stock (boxes) = on_hand_pairs / 12
  planogram_pairs INTEGER,           -- Target display stock
  storage_pairs INTEGER,             -- Target storage stock
  assort_status assort_status,       -- FULL or BROKEN
  last_updated TIMESTAMPTZ
)
```

## Business Rules

### Stock Allocation
1. **Tier-based allocation**
   - Tier 1 products get highest allocation
   - Display space prioritized by tier

2. **Seasonal rotation**
   - Seasonal products replaced quarterly
   - Off-season stock returned to warehouse

3. **Performance-based allocation**
   - High-performing stores get more stock
   - Low performers get reduced allocation

### Replenishment Rules
1. **Minimum order quantity**
   - Typically 1 box minimum per article
   - Total order minimum: 5-10 boxes

2. **Lead time**
   - Target delivery: 1-3 days from order
   - Expedited available for urgent needs

3. **Broken assortment priority**
   - BROKEN assortments prioritized in RO
   - FULL assortments lower priority

### Transfer Rules
1. **Store-to-store transfers**
   - Allowed for emergency stock needs
   - Requires Area Supervisor approval
   - Tracked separately from RO system

2. **Return to warehouse**
   - Damaged stock
   - Discontinued products
   - Event stock after event ends

## Reporting and Analytics

### Store-Level Reports
- Daily sales by article
- Current stock levels
- Broken assortment list
- Pending RO status
- Receive variance summary

### Area-Level Reports
- Sales comparison across stores
- Stock allocation by store
- RO fulfillment performance
- Store ranking by performance

### Network-Level Reports
- Total network stock
- Out-of-stock articles across network
- Sales trends by region
- Inventory turn by store category

## Common Operations

### Create Store RO
1. Area Supervisor selects target store
2. Reviews store stock levels
3. Identifies items needing replenishment
4. Specifies quantities (in boxes)
5. Selects source warehouse (DDD/LJBB)
6. Submits RO
7. Receives RO ID (e.g., RO-2512-0007)

### Receive Store Delivery
1. Driver arrives with shipment
2. Store staff checks packages
3. Counts boxes received
4. Compares to RO quantities
5. Notes any variance
6. WH Supervisor confirms in system
7. Stock added to store inventory
8. RO marked COMPLETED

### Handle Stock Transfer
1. Identify receiving store (low stock)
2. Identify sending store (excess stock)
3. Area Supervisor approves transfer
4. Update both store stock levels
5. Log transfer in system
6. Update assortment status if needed

## Key Terminology

- **Branch:** Organizational grouping of stores by region
- **Area:** Geographic region managed by Area Supervisor
- **Planogram:** Visual layout plan for product display
- **Assortment:** Size distribution within an article
- **On Hand:** Current physical stock at store
- **RO:** Replenishment Order from warehouse to store
- **AS:** Area Supervisor
- **WH SPV:** Warehouse Supervisor

## Integration Points

- **iSeller (POS System)** - Daily sales data, stock movements
- **Accurate Online (ERP)** - Store master data, financial data
- **RO App (Internal)** - Replenishment orders, stock requests
- **Ginee (Marketplace)** - Online order fulfillment from store stock

## Document References

- **RO App README:** `RO App/README.md`
- **Database Schema:** `RO App/DATABASE_SCHEMA.md`
- **Warehouse & Stock Skill:** See `zuma-warehouse-and-stocks` skill
