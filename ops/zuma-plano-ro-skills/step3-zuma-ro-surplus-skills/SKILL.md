---
name: zuma-distribution-flow
description: "Zuma RO Request & Surplus Pull — original logic (protol/box >=50% threshold, tier-based surplus). Source: portal.planogram_existing_q1_2026. Output: 5-sheet Excel (cover, protol, box, surplus, reference)."
user-invocable: true
---

> **Updated 2026-02-27**: Data source changed from Excel (`RO Input {Region}.xlsx`) to DB table `portal.planogram_existing_q1_2026`.
> Logic unchanged: >=50% sizes empty → Box, <50% → Protol. Tier-based surplus (T1/T2/T3 only).

# Flow Distribusi: Surplus & Restock + RO Request Generation

## Overview

Sistem distribusi ZUMA terdiri dari 2 flow utama:
1. **Restock Flow** — mengisi kekurangan stok di toko
2. **Surplus Flow** — menarik kelebihan stok dari toko berdasarkan kapasitas tier

Kedua flow ini di-trigger otomatis oleh sistem, dengan kontrol eksekusi oleh **Allocation Planner**.

---

## Definisi & Komponen

### Gudang
| Gudang | Isi | Unit Kirim |
|--------|-----|------------|
| **Gudang Box** | Stok dalam kemasan box penuh (12 pairs, all sizes) | Per box |
| **Gudang Protol** | Stok eceran per size/pairs | Per pairs/size |

### Tipe RO (Replenishment Order)
| Tipe | Trigger | Source | Kirim |
|------|---------|--------|-------|
| **RO Box** | Size kosong ≥50% dari assortment artikel | Gudang Box | 1 box (12 pairs, all sizes) |
| **RO Protol** | Size kosong <50% dari assortment artikel | Gudang Protol | Pairs di size yang kosong saja |

### Key Metrics
- **Assortment** = jumlah size yang seharusnya tersedia untuk 1 artikel di toko tersebut
- **% Size Kosong** = (jumlah size yang stoknya 0) / (total assortment) × 100%
- **Tier Capacity %** = persentase ideal stok per tier dari total kapasitas toko
- **Actual Tier %** = persentase stok aktual per tier dari total stok toko
- **TO (Turnover)** = kecepatan jual artikel — semakin rendah, semakin lambat terjual

### Tier Surplus Rules
| Tier | Surplus Check | Alasan |
|------|--------------|--------|
| **T1** | ✅ Ya | Best seller — perlu dijaga proporsinya |
| **T2** | ✅ Ya | Secondary fast moving — perlu dijaga proporsinya |
| **T3** | ✅ Ya | Moderate — perlu dijaga proporsinya |
| **T4** | ❌ Tidak | Promo / clearance — tujuannya menghabiskan stok |
| **T5** | ❌ Tidak | Slow moving — sama seperti T4 |
| **T8** | ❌ Tidak (3 bulan) | New launch — protection period untuk test market |

---

## FLOW 1: RESTOCK

### Trigger
Sistem mendeteksi gap antara stok aktual vs kebutuhan (planogram display + storage allocation).

### Decision Tree

```
SISTEM DETEKSI GAP
        │
        ▼
Hitung % size kosong vs assortment
        │
        ├── ≥50% size kosong ──────► RO BOX
        │                              │
        │                              ▼
        │                        Cek Gudang Box
        │                              │
        │                         ├── Ada ──► Planner approve ──► Kirim box ke toko
        │                         │
        │                         └── Tidak ada ──► Flag (tunggu PO supplier)
        │
        └── <50% size kosong ──────► RO PROTOL (Tiered)
                                       │
                                  STEP 1: Cek Gudang Protol
                                       │
                                  ├── Ada ──► Kirim protol ✅
                                  │
                                  └── Tidak ada
                                       │
                                  STEP 2: Cek surplus toko lain
                                       │
                                  ├── Ada ──► Tarik ke gudang → kirim protol ✅
                                  │
                                  └── Tidak ada
                                       │
                                  STEP 3: Fallback RO Box
                                       ⚠ Wajib pre-plan surplus size yg sudah ada
```

### Restock Rules

1. Prioritas selalu RO Protol jika memenuhi syarat — lebih efisien, tidak bikin surplus baru
2. RO Box adalah last resort untuk kasus protol, kecuali memang ≥50% size kosong
3. Setiap RO Box fallback wajib disertai surplus pre-plan
4. Allocation planner = gatekeeper — sistem recommend, planner approve/reject/modify

---

## FLOW 2: SURPLUS (Tier-Based)

### Konsep Utama

Surplus BUKAN asal tarik barang dari toko. Surplus ditentukan berdasarkan **gap antara kapasitas ideal per tier vs stok aktual per tier**. Hanya tier yang over-capacity yang ditarik, dan yang ditarik adalah artikel dengan turnover (TO) terendah di tier tersebut.

### Tier yang Dicek vs Dikecualikan

**Dicek (T1, T2, T3):**
- Tier ini punya target kapasitas ideal (%) dari total kapasitas toko
- Jika actual % > ideal % → tier over-capacity → tarik selisihnya
- Yang ditarik: artikel dengan TO paling rendah / dead stock di tier tersebut

**Dikecualikan:**
- **T4**: Promo / clearance — tujuan menghabiskan stok, jangan ditarik
- **T5**: Slow moving — sama seperti T4, biarkan sampai habis atau di-clearance
- **T8**: New launch — protection period 3 bulan sejak launch untuk test market

### T8 Lifecycle

```
LAUNCH (Bulan ke-0)
    │
    ▼
Protection Period (3 bulan)
- Tidak boleh ditarik sebagai surplus
- Data sales dikumpulkan untuk evaluasi
- Exception: manual override oleh Allocation Planner
  jika toko benar-benar over-capacity parah
    │
    ▼
BULAN KE-4: Reclassification
    │
    ├── Sales bagus ──► Masuk T1/T2/T3 ──► Ikut rules surplus tier barunya
    │
    └── Sales jelek ──► Masuk T4/T5 ──► Exclude dari surplus check
                                          (masuk program clearance)
```

### Surplus Decision Tree

```
SISTEM HITUNG KAPASITAS PER TIER PER TOKO
        │
        ▼
Bandingkan per tier: Actual % vs Ideal Capacity %
        │
        ├── T1: Ideal 30%, Actual 35% ──► Over +5% ──► SURPLUS CANDIDATE
        ├── T2: Ideal 25%, Actual 22% ──► Under     ──► SKIP (butuh restock)
        ├── T3: Ideal 20%, Actual 23% ──► Over +3% ──► SURPLUS CANDIDATE
        ├── T4: ─────────────────────────────────────► SKIP (promo/clearance)
        ├── T5: ─────────────────────────────────────► SKIP (slow moving)
        └── T8: ─────────────────────────────────────► SKIP (protection 3 bln)
        │
        ▼
Untuk tier yang OVER-CAPACITY:
        │
        ▼
Hitung selisih = Actual % - Ideal %
Convert ke jumlah artikel/box
        │
        ▼
Ranking artikel di tier tsb by TO ascending
(TO terendah = dead stock = prioritas tarik pertama)
        │
        ▼
Tarik artikel dgn TO terendah sampai selisih terpenuhi
        │
        ▼
Allocation Planner review & approve list tarik
        │
        ▼
Tarik dari toko ──► Masuk GUDANG PROTOL
        │
        ▼
Sistem cek: ada toko lain yang butuh?
        │
        ├── Ada ──► Kirim protol ke toko yang butuh ✅
        │
        └── Tidak ada ──► Stay di gudang protol
```

### Surplus Calculation Example

```
Contoh: Toko Matos — Total Kapasitas 100 artikel

Tier    Ideal %    Ideal Qty    Actual Qty    Actual %    Status
T1      30%        30           35            35%         Over +5 artikel
T2      25%        25           22            22%         Under -3 artikel
T3      20%        20           23            23%         Over +3 artikel
T4      15%        15           12            12%         (skip - promo)
T5      5%         5            4             4%          (skip - slow moving)
T8      5%         5            4             4%          (skip - protection)

Action:
- T1: Tarik 5 artikel dgn TO terendah → ke gudang protol
- T3: Tarik 3 artikel dgn TO terendah → ke gudang protol
- T2: Butuh restock 3 artikel → masuk restock flow
```

### Surplus Rules

1. Hanya T1, T2, T3 yang dicek — T4/T5 excluded (clearance), T8 excluded (protection 3 bulan)
2. Surplus = actual % - ideal % — hanya tier yang over-capacity yang ditarik
3. Prioritas tarik: TO terendah dulu — dead stock dan slow mover dalam tier itu keluar duluan
4. Semua surplus dari toko masuk gudang protol — ditarik per size, bukan per box utuh
5. Surplus tidak boleh store-to-store langsung — harus lewat gudang
6. Surplus di gudang protol otomatis masuk pool untuk RO Protol toko lain
7. T8 setelah 3 bulan → reclassify berdasarkan actual sales → ikut rules tier barunya
8. Manual override T8 hanya jika extremely over-capacity — case-by-case, bukan otomatis

---

## SIKLUS LENGKAP (Interconnected)

```
┌─────────────────────────────────────────────────────────────┐
│                    ALLOCATION PLANNER                        │
│              (Control & Approve semua flow)                  │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
     ┌──── RESTOCK ────┐           ┌──── SURPLUS ────┐
     │                 │           │   (Tier-Based)   │
     │  Toko butuh     │           │  T1/T2/T3 over-  │
     │  stok           │           │  capacity → tarik │
     │                 │           │  TO rendah dulu   │
     └───────┬─────────┘           └────────┬─────────┘
             │                              │
             ▼                              ▼
     ┌───────────────┐             Tarik ke Gudang Protol
     │ % size kosong │                      │
     │ vs assortment │                      ▼
     └───┬───────┬───┘             ┌─────────────────┐
         │       │                 │  GUDANG PROTOL   │◄── Surplus masuk sini
    ≥50% │       │ <50%            │  (pool per size) │
         │       │                 └────────┬────────┘
         ▼       ▼                          │
    RO BOX    RO PROTOL ◄──────────────────┘
         │       │
         ▼       ▼
   ┌──────────┐  ┌──────────────────────────┐
   │ GUDANG   │  │ Tiered check:            │
   │ BOX      │  │ 1. Gudang Protol         │
   └────┬─────┘  │ 2. Surplus toko lain     │
        │        │ 3. Fallback RO Box       │
        ▼        └───────────┬──────────────┘
   Kirim box            Kirim protol/box
   ke toko              ke toko
        │                    │
        ▼                    ▼
   ┌─────────────────────────────────────┐
   │              TOKO                    │
   │   Display (planogram) + Storage      │
   │                                      │
   │   RO Box fallback surplus ──────────►│──► Kembali ke Surplus Flow
   └─────────────────────────────────────┘
```

---

## Edge Cases

### 1. RO Box fallback → surplus baru
Allocation Planner WAJIB pre-plan: size mana surplus setelah box masuk, kirim ke toko mana. Jika tidak ada demand, stay di storage (jika muat) atau tarik ke gudang.

### 2. T8 Protection Period
3 bulan protection: tidak boleh ditarik. Exception: manual override jika extremely over-capacity (case-by-case, documented). Setelah 3 bulan: reclassify ke tier baru.

### 3. Toko baru / Grand Opening
Full RO Box untuk semua artikel di planogram. Evaluasi surplus setelah 1 bulan. Tier capacity benchmark pakai toko serupa (size/area sama).

### 4. Artikel discontinued
Semua stok → surplus → tarik ke gudang protol. Redistribusi ke toko yang masih jual, atau markdown.

### 5. Gudang protol penuh
Prioritas redistribusi. Jika tidak ada demand → eskalasi ke Planner (markdown/promo/retur supplier).

### 6. Gudang box kosong
Flag ke procurement untuk PO. Sementara cek gudang protol untuk rakit assortment protol.

### 7. Semua tier under-capacity
Restock prioritas berdasarkan sales contribution: T1 → T2 → T3. T4/T5 hanya restock jika masih dalam program promo aktif.

### 8. T8 di toko over-capacity parah
Manual override oleh Planner. Documented: alasan, expected impact. T8 yang ditarik → gudang protol → redistribute ke toko lain yang masih dalam protection period.

---

## RO REQUEST GENERATION (Weekly Document)

### Apa Itu RO Request?

RO Request adalah dokumen mingguan yang dihasilkan oleh sistem (atau AI agent) dan diserahkan dari **Area Supervisor** ke **Warehouse Supervisor**. Dokumen ini berisi:
1. Daftar barang yang perlu dikirim ke toko (RO Protol + RO Box)
2. Daftar barang yang perlu ditarik dari toko (Surplus Pull)
3. Cover page + signature block sebagai dokumen resmi handover

### Pipeline

```
Planogram Existing (DB) → RO Request (Step 3)
```

RO Request **membutuhkan planogram** sebagai input. Saat ini menggunakan `portal.planogram_existing_q1_2026` — snapshot on-hand stock toko yang menjadi target display sementara.

### Data Sources

| Data | Source | Query |
|------|--------|-------|
| Store stock | `core.stock_with_product` | `WHERE LOWER(nama_gudang) LIKE '%{store_pattern}%'` |
| WH Pusat Box | `branch_super_app_clawdbot.ro_whs_readystock` | `WHERE ddd_available > 0` — aggregated from `master_mutasi_whs` Stock Akhir. Use this to **filter** which articles have boxes available in WH Pusat. |
| WH Pusat Protol | `core.stock_with_product` | `WHERE LOWER(nama_gudang) = 'warehouse pusat protol'` (DDD only) |
| Sales (3 month) | `core.sales_with_product` | `WHERE transaction_date >= NOW() - INTERVAL '3 months'` + exclude intercompany |
| **Planogram targets** | `portal.planogram_existing_q1_2026` | `WHERE LOWER(store_name) ILIKE '%{store}%' AND grand_total_pairs::int > 0` |

> **UPDATED (Mar 2026)**: WH Box availability now reads from `ro_whs_readystock` VIEW which auto-calculates from `master_mutasi_whs` (Stock Awal + Transaksi IN - Transaksi OUT - RO Ongoing). The old `ro_stockwhs` table has been deleted. `ro_whs_readystock` columns: `article_code`, `article_name`, `tier`, `tipe`, `gender`, `series`, `ddd_available`, `ljbb_available`, `mbb_available`, `ubb_available`, `total_available`, `last_calculated`.

**Key planogram columns:**
- `article_mix` — kode mix (UPPERCASE)
- `size_*` columns — target qty per size (42 size columns: 25 individual + 17 paired)
- `grand_total_pairs` — sum of all sizes = total display target
- `box` — box count (patokan utama)
- `updated_at` — kapan data terakhir di-update

### RO Type Decision Logic

```python
assortment_sizes = number of sizes in planogram for this article
empty_sizes = sizes where store stock = 0
pct_empty = empty_sizes / assortment_sizes

if pct_empty >= 0.50:
    ro_type = "RO_BOX"    # Send full box (12 pairs, all sizes) from Gudang Box
else:
    ro_type = "RO_PROTOL"  # Send individual pairs only for empty sizes from Gudang Protol
```

### Surplus Detection Logic

```python
# Only check articles in tier T1, T2, T3
# Skip T4 (clearance), T5 (slow moving), T8 (new launch protection 3 months)

for each article on planogram where tier in [1, 2, 3]:
    if article NOT in store stock (completely absent):
        → NOT surplus (needs restock)
    if article has sizes with stock > target:
        excess_pairs = stock - target (per size)
        if excess_pairs > 0:
            → SURPLUS CANDIDATE

# Sort surplus candidates by avg_monthly_sales ASC (slowest sellers pulled first)
# This is UNAMBIGUOUS regardless of TO definition used
```

### WH Source Rules

| Type | Warehouse | Entities | Notes |
|------|-----------|----------|-------|
| RO Box | Warehouse Pusat (Box) | `ro_whs_readystock.ddd_available > 0` | DDD + LJBB | LJBB exclusive for Box only. Filter articles using `ro_whs_readystock` before including in RO Box list. |
| RO Protol | Warehouse Pusat Protol | DDD only | No LJBB for protol |
| Surplus destination | Warehouse Pusat Protol | — | All surplus goes to protol gudang |

**IMPORTANT**: Box availability now auto-calculated via `ro_whs_readystock` VIEW (reads from `master_mutasi_whs`). No more manual `ro_stockwhs` table updates needed.
RO Box only from Warehouse Pusat — NOT from WHJ or WHB.

### Output Format: Excel (.xlsx) — 5 Sheets

The output is an official document format with cover page and signature block.

#### Sheet 1: "RO Request" (Cover Page)

```
Row 2:  WEEKLY RO REQUEST                          (bold, 16pt, green fill)
Row 3:  {Store Name}                               (bold, 14pt)
Row 5:  Week of:          {date}
Row 6:  Stock Snapshot:   {date}
Row 7:  Storage Capacity: {N} boxes
Row 9:  From:  Area Supervisor     ___________________________
Row 10: To:    Warehouse Supervisor ___________________________

Row 12: REQUEST SUMMARY                            (bold, green fill)
Row 13: Type | Articles | Total | Source/Destination | See Sheet  (header row, bold)
Row 14: RO PROTOL | {N} | {N} pairs | FROM: WH Pusat Protol | Daftar RO Protol
Row 15: RO BOX   | {N} | {N} boxes | FROM: WH Pusat Box    | Daftar RO Box
Row 16: SURPLUS  | {N} | {N} pairs | TO: WH Pusat Protol   | Daftar Surplus

Row 19: INSTRUCTIONS
Row 20-24: (numbered instructions — restock+surplus same day, priority protol first)

Row 27: SIGNATURES
Row 28: [Prepared by] [Approved by] [Received by]
Row 29-31: Name/Date/Signature lines
```

#### Sheet 2: "Daftar RO Protol" (One Row Per Article)

```
Header rows 1-4: title, store, date, source info
Row 6 (header): No | Article | Kode Mix | Tier | Sizes Needed (size:qty) | Total Pairs
Row 7+: numbered data rows

Example row:
  1 | LADIES FLO 1, BLACK | L1FL0LV101 | 1 | 36:1, 37:2, 38:4, 39:3, 40:2 | 12

Last row: TOTAL PAIRS = {sum}
```

**Key format**: Sizes Needed uses `size:qty` format, comma-separated. This shows the WH picker exactly which sizes and how many pairs to pick.

**Sorting**: By Tier ASC, then by Article name ASC within each tier.

#### Sheet 3: "Daftar RO Box" (One Row Per Article, 1 Box)

```
Header rows 1-4: title, store, date, source info + "Total: {N} boxes"
Row 6 (header): No | Article | Kode Mix | Tier | Box Qty | WH Available
Row 7+: numbered data rows

Example row:
  1 | LADIES CLASSIC 1, JET BLACK | SJ2ACAV201 | 1 | 1 | NO

Last row: TOTAL BOXES = {sum}
```

**Key format**: Box Qty is always 1 (1 box = 12 pairs, all sizes). WH Available shows YES/NO based on warehouse stock check.

**Sorting**: By Tier ASC, then by Article name ASC within each tier.

#### Sheet 4: "Daftar Surplus" (Size-Level Detail)

```
Header rows 1-4: title, store, date, destination info + "Total: {N} articles, {N} pairs"
Row 6 (header): No | Article | Kode Mix | Size | Pairs to Pull
Row 7+: numbered data rows (one row per article+size combination)

Example rows:
  1 | MEN STRIPE 1, BLACK BLUE RED | M1SP0PV201 | 40 | 3
  2 | MEN STRIPE 1, BLACK BLUE RED | M1SP0PV201 | 42 | 3

Last row: TOTAL PAIRS = {sum}
```

**Key format**: Size-level detail because WH pickers need exact size to pull from display. Same article appears multiple times if multiple sizes are surplus.

**Sorting**: By avg_monthly_sales ASC (slowest sellers first — these get pulled first).

#### Sheet 5: "Reference" (Internal Use Only)

```
Row 1: REFERENCE DATA (Internal Use)

Section 1 — Tier Capacity Analysis:
  Tier | Ideal (Planogram) | Ideal % | Actual (Stock) | Actual % | Diff | Status

Section 2 — Full Article Status:
  Article | Kode Mix | Gender | Series | Tier | Target | Actual | Gap | % Kosong | RO Type | Avg Monthly Sales | Stock Coverage

Section 3 — Off-Planogram Articles (if any):
  Articles found in store stock but NOT in planogram — flagged for review.
```

### Script Reference

**File**: `build_ro_request.py` (in `step3-ro-request/` folder)

**Dependencies** (must be installed):
```bash
pip install psycopg2-binary openpyxl
```

**Key Config Variables** (top of script):
```python
STORE_NAME = "Zuma Royal Plaza"          # Display name
STORE_DB_PATTERN = "zuma royal plaza"     # For ILIKE match in DB
STORAGE_CAPACITY = 0                      # Number of storage boxes (0 = no storage)
RO_BOX_THRESHOLD = 0.50                   # >=50% sizes empty → RO Box
SURPLUS_CHECK_TIERS = [1, 2, 3]           # Only T1/T2/T3 checked for surplus
PLANOGRAM_TABLE = "portal.planogram_existing_q1_2026"  # DB planogram source
```

**DB Connection** (in script):
```python
DB_HOST = "76.13.194.120"
DB_PORT = 5432
DB_NAME = "openclaw_ops"
DB_USER = "openclaw_app"
DB_PASS = "Zuma-0psCl4w-2026!"
```

**To generate for a different store**: Run the script with `--store "Store Name"` argument. The planogram table has 51 stores nationwide. Do NOT copy the script — just change the CLI args.

### Known Limitations & Pending Clarifications

1. **TO Metric** — Two definitions coexist in Zuma:
   - (a) Stock Coverage = stock / monthly_sales (months of stock remaining). High = slow.
   - (b) Turnover Rate = monthly_sales / stock (sales velocity). Low = slow.
   Script outputs both. Surplus sorts by `avg_monthly_sales ASC` which is unambiguous.
   → **PENDING**: Ask Allocation Planner team which label to standardize on.

2. **Ideal Tier Capacity %** — No official per-store tier targets exist yet. Script derives ideal from planogram article count per tier.
   → **PENDING**: Ask Planner for real per-store tier capacity targets.

3. **RO Protol Total Pairs accuracy** — Some `Total Pairs` show 0 because WH Protol stock for those sizes is 0. The "Sizes Needed" column still shows what's needed, but total reflects what can actually be fulfilled.

4. **Storage = 0 stores** — Every RO Box creates immediate surplus for sizes already in stock. The Allocation Planner must pre-plan redistribution before approving.

### Example Output (Royal Plaza, 10 Feb 2026)

| Metric | Count |
|--------|-------|
| RO Protol articles | 47 |
| RO Protol total pairs | 208 |
| RO Box articles | 42 |
| RO Box total boxes | 42 |
| Surplus articles | 24 |
| Surplus total pairs | 179 |
| Off-Planogram articles | 41 |

### Styling Reference (openpyxl)

The Excel output uses consistent branding:

| Element | Style |
|---------|-------|
| Title row | Font 16pt bold, fill `#00E273` (Zuma Green), white text |
| Store name | Font 14pt bold |
| Section headers | Font 12pt bold, fill `#00E273` |
| Table headers | Font 10pt bold, fill `#2E7D32` (dark green), white text |
| Data rows | Font 10pt, alternating white/`#E8F5E9` (light green) |
| Borders | Thin borders on all data cells |
| Column widths | Auto-fit with min/max constraints |
| Summary values | Bold, right-aligned |
| Total row | Bold, top border |

### How to Use This Skill (For AI Agents)

1. **Load dependencies**: `zuma-data-analyst-skill` (DB connection), `zuma-sku-context` (tier system, Kode Mix), `zuma-warehouse-and-stocks` (WH names, RO flow)
2. **Planogram source**: `portal.planogram_existing_q1_2026` (51 stores, 606 articles, BOX column = patokan)
3. **ALWAYS run `build_ro_request.py`**: Execute the script directly with `--store` and `--storage` CLI args. Do NOT write your own code or "replicate its logic" — just run the script.
4. **Output validation**: Check that all 5 sheets are populated, totals match, WH availability is checked
5. **Deliver output**: After XLSX generation, the task is NOT complete until the file is uploaded to Google Drive and the share link is sent to the requesting user.
6. **Delivery workflow (MANDATORY)**:
   - Upload XLSX to Google Drive (Zuma shared folder)
   - Share the GDrive link with the user who requested the RO
   - If GDrive upload fails → escalate to Wayan (+628983539659) via WhatsApp ONLY. Do NOT contact anyone else.
   - Task is complete ONLY when the user receives the GDrive link (or Wayan is notified of the failure)

### Available Stores (51 — from planogram_existing_q1_2026)

```sql
SELECT DISTINCT store_name FROM portal.planogram_existing_q1_2026 ORDER BY store_name;
```

Includes: Bali (28 stores), Jatim (11), Jakarta (4), Batam (2), Lombok (1), Manado (1), Pekanbaru (1).
