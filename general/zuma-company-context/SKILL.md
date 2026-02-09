---
name: zuma-company-context
description: Zuma Indonesia brand identity and business context. Covers brand guidelines (tone, colors, aesthetic) and data sources. Use when working on Zuma projects to maintain brand consistency.
user-invocable: false
---

# Zuma Indonesia Company Knowledge

You have access to Zuma Indonesia's brand identity and business context. Use this knowledge when working on Zuma work projects to maintain brand consistency.

## Company Overview

**Company:** Zuma Indonesia
**Location:** Indonesia (HQ: Surabaya, East Java)
**Industry:** Footwear (Sandals & Flip-flops)
**Business Model:** Manufacturing + Retail + E-commerce + Wholesale + Consignment

## Business Entity Structure

Zuma Indonesia operates through **4 administrative/legal entities (PTs)**, each with its own Accurate Online database. These are NOT physical locations — they are tax and legal structures.

| Entity Code | Full Name | Business Function | Accurate Host |
|-------------|-----------|-------------------|---------------|
| **DDD** | Dream Dare Discover | **Main entity**. Retail stores + Wholesale + Consignment. Covers all physical Zuma stores. | `zeus.accurate.id` |
| **MBB** | Makmur Besar Bersama | Online sales (Shopee, Tokopedia, TikTok Shop) + Wholesale | `iris.accurate.id` |
| **UBB** | Untung Besar Bersama | Wholesale + Consignment | `zeus.accurate.id` |
| **LJBB** | Lancar Jaya Besar Bersama | PO receiving entity for Baby & Kids products. Suppliers (HJS = PT. Halim Jaya Sakti / Ando Footwear Indonesia) ship to LJBB's Warehouse Pusat, then stock is sold/transferred to DDD for retail distribution. | Auto-discover |

### Entity Relationships

```
Supplier (HJS / Ando)
    │
    ▼ Purchase Orders
  LJBB (receives Baby & Kids stock at Warehouse Pusat)
    │
    ▼ Internal transfer / sale
  DDD (distributes to retail stores, wholesale, consignment)

  MBB (handles online marketplace sales independently)
  UBB (handles wholesale & consignment independently)
```

**Key Points:**
- All 4 entities share the **same product SKU codes** (same catalog)
- All 4 entities share the **same physical warehouses** (WHS, WHJ, WHB)
- DDD is the largest entity — most retail stores report through DDD
- LJBB only handles incoming POs for Baby & Kids, no direct retail sales
- Each entity has separate Accurate Online credentials and API access

## Brand Identity

**See [brand-guidelines.md](brand-guidelines.md) for complete details.**

### Quick Reference

**Brand Tonality:**
- **Witty:** Wordplay, puns (Zuma = "Cuma" meaning "just/only" in Indonesian), hopeful outlook
- **Casual:** Conversational, friendly, approachable language
- **Confident:** Empowering, encouraging, never intimidating

**Visual Identity:**
- **Colors:** Zuma Teal `#002A3A`, Zuma Green `#00E273`, White `#FFFFFF`
- **Aesthetic:** Japandi minimalism (generous whitespace, crisp shadows, clean lines)
- **Typography:** GT Walsheim, BDO Grotesk
- **Lighting:** Strong sunlight, dramatic shadows (tropical feel)

## Data Sources

Zuma uses multiple business systems for operations:

| System | Type | Purpose | Notes |
|--------|------|---------|-------|
| **Accurate Online** | ERP | Sales invoices, inventory, accounting. 4 separate databases (DDD, MBB, UBB, LJBB). | Official REST API (HMAC-SHA256) + cookie-based export for BPP/COGS data |
| **iSeller** | POS System | Real-time retail sales at cashier. Accurate sales are batch-streamed FROM iSeller. | iSeller is the source of truth for POS; Accurate is the delayed mirror |
| **Ginee** | Marketplace Aggregator | Multi-channel marketplace listings, sync (Shopee, Tokopedia, Lazada) | |
| **Supabase** | Database | Branch Super App (RO system), product master | Connected via API |
| **Google Sheets** | Manual data | Portal tables (SKU master, store master, HPP), manual reports, targets | Primary source for master/reference data |

### Data Flow: iSeller → Accurate

```
Customer pays at store (iSeller POS)
  → iSeller records transaction in real-time
  → Accurate automatically batch-imports from iSeller (delayed)
  → Accurate adds accounting context (tax, GL accounts, etc.)
```

**Implication:** For near-real-time sales data, use iSeller. For complete financial data (BPP/COGS, tax details), use Accurate.

### Accurate API Limitation: BPP (Cost of Goods)

The official Accurate REST API does NOT return costing fields (`unitCost`, `averageCost`, `cogs`) for security reasons. BPP = 0 from API.

**Workaround:** Cookie-based export (using browser session cookies `_dsi` + `_usi`) returns full BPP data. Cookies expire and require manual browser re-login.

**Hybrid approach:** API for daily automated pulls (no BPP), cookie export weekly for BPP backfill.

## Key Business Metrics

| Metric | Threshold | Who Cares |
|--------|-----------|-----------|
| FF (Full Floor) % | Alert if < 70% | Virra (OPS) |
| FB (Full Box) % | Alert if < 80% | Virra (OPS) |
| Stock Minus | Alert if < 0 | Galuh, Nabila |
| Sales MTD vs Target | Alert if < 95% | Branch Managers |
| Inventory Depth (days) | Alert if < 14 days | Merchandiser |
| Tier performance | Track by tier (1-5, 8) | Production Planning Meeting |
| Marketplace channel mix | Shopee vs Tokped vs Lazada | Online Sales team |

## Suppliers

| Supplier | Code | Products |
|----------|------|----------|
| **PT. Halim Jaya Sakti (HJS)** | - | Primary supplier, most products (Jepit, Fashion). Also known as Ando Footwear Indonesia |
| **CV. Era Sukses** | - | Select Fashion products (e.g., Onyx series) |
| **PT. Indoeva Mitra Abadi** | - | Select Fashion products (e.g., Leon series) |

## When to Use This Knowledge

Apply this context when:
- **Writing customer-facing copy** (use brand tone: witty, casual, confident)
- **Designing UI/UX** (use brand colors, Japandi aesthetic, generous whitespace)
- **Working with business data** (understand entities, data sources, and systems)
- **Creating brand materials** (maintain visual consistency)
- **Building data pipelines** (understand entity structure and data flow between systems)
- **Analyzing sales data** (know which entity covers which channel)

## Important Notes

- **Brand Guidelines** apply ONLY to Zuma work projects, NOT personal projects
- Each project chooses its own technology stack independently
- Always check project-specific CLAUDE.md files for technical details
- SKU/product details are in the separate `zuma-sku-context` skill
- Warehouse/stock operations are in the separate `zuma-warehouse-and-stocks` skill
- Branch/store network is in the separate `zuma-branch` skill
