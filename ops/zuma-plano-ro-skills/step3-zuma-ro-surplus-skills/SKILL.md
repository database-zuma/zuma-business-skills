---
name: zuma-ro-surplus-transisi
description: Zuma RO & Surplus TRANSISI — versi transisi dari distribution flow (surplus pull, restock, RO Request). Logic sedang diedit/diupdate. Use when working with the transitional/updated RO surplus logic.
user-invocable: false
---

# Flow Distribusi TRANSISI: Restock Dulu -> Baru Surplus

## Overview

Sistem distribusi ZUMA (versi TRANSISI) terdiri dari 3 tahap **berurutan**:
1. **TAHAP 0: IDENTIFIKASI URGENT SURPLUS** — scan artikel di toko yang **tidak ada di planogram baru** (off-planogram). Ini adalah "barang lama" yang HARUS keluar. Total pairs urgent surplus menjadi **budget RO**.
2. **TAHAP 1: RESTOCK (RO)** — tambal kekurangan stok di toko. **RO Box adalah DEFAULT**. RO Protol hanya untuk gap minor (1-2 size kosong). **Total RO pairs dibatasi ≈ total urgent surplus pairs** (swap: barang keluar = barang masuk).
3. **TAHAP 2: SURPLUS** — tarik kelebihan stok SETELAH restock masuk. Dua kategori: **URGENT** (off-planogram, harus ditarik) dan **REGULAR** (on-planogram over-capacity, visibility/planning only).

**Konsep inti**: RO bukan untuk menutup 100% maxstock gap. RO hanya "menukar" barang buruk (off-plano) dengan barang bagus (on-plano yang kosong). **Pairs IN ≈ Pairs OUT (urgent only)**.

**Jika urgent surplus = 0** (semua stok sesuai planogram): RO proceeds normally tanpa budget cap (uncapped fallback).

Kontrol eksekusi tetap oleh **Allocation Planner**.

---

## Definisi & Komponen

### Gudang
| Gudang | Isi | Unit Kirim |
|--------|-----|------------|
| **Gudang Box** | Stok dalam kemasan box penuh (12 pairs, all sizes) | Per box |
| **Gudang Protol** | Stok eceran per size/pairs | Per pairs/size |

### Tipe RO (Replenishment Order) — TRANSISI
| Tipe | Trigger | Source | Kirim |
|------|---------|--------|-------|
| **RO Box** DEFAULT | **3+ size kosong** dari assortment artikel | Gudang Box | 1 box (12 pairs, all sizes) |
| **RO Protol** | **1-2 size kosong** dari assortment (gap minor) | Gudang Protol | Pairs di size yang kosong saja |

> **PERUBAHAN DARI LOGIC LAMA**: Dulu threshold >=50% -> Box, <50% -> Protol (Protol preferred). Sekarang **Box adalah DEFAULT** — Protol hanya untuk gap sangat kecil (1-2 size). Surplus yang dihasilkan Box diterima dan ditarik di tahap surplus.

### Key Metrics
- **Assortment** = jumlah size yang seharusnya tersedia untuk 1 artikel di toko tersebut
- **Empty Size Count** = jumlah size yang stoknya 0 (count-based, bukan persentase)
- **Tier Capacity %** = persentase ideal stok per tier dari total kapasitas toko
- **Actual Tier %** = persentase stok aktual per tier dari total stok toko
- **TO (Turnover)** = kecepatan jual artikel — semakin rendah, semakin lambat terjual

### Tier Surplus Rules
| Tier | Surplus Check | Alasan |
|------|--------------|--------|
| **T1** | Ya | Best seller — perlu dijaga proporsinya |
| **T2** | Ya | Secondary fast moving — perlu dijaga proporsinya |
| **T3** | Ya | Moderate — perlu dijaga proporsinya |
| **T4** | Tidak | Promo / clearance — tujuannya menghabiskan stok |
| **T5** | Tidak | Slow moving — sama seperti T4 |
| **T8** | Tidak (3 bulan) | New launch — protection period untuk test market |

---

## TAHAP 1 (Detail): RESTOCK (Tambal Dulu — Box Priority)

### Trigger
Sistem mendeteksi gap antara stok aktual vs kebutuhan (planogram display + storage allocation).

### Decision Tree — TRANSISI (Box Default)

```
SISTEM DETEKSI GAP
        |
        v
Hitung jumlah size kosong (count, bukan %)
        |
        +-- 3+ size kosong -----------> RO BOX (DEFAULT)
        |                                |
        |                                v
        |                          Cek Gudang Box
        |                                |
        |                           +-- Ada --> Tampil di daftar RO Box
        |                           |           Planner approve --> Kirim box ke toko
        |                           |           Surplus dari Box = ACCEPTED
        |                           |           (akan ditarik di TAHAP 2: SURPLUS)
        |                           |
        |                           +-- Tidak ada --> EXCLUDE dari daftar
        |                                             (tidak ditampilkan sama sekali)
        |
        +-- 1-2 size kosong ----------> RO PROTOL (Gap Minor)
                                         |
                                    Cek Gudang Protol
                                         |
                                    +-- Ada --> Kirim protol
                                    |
                                    +-- Tidak ada --> Fallback RO Box
                                                       (sama: surplus dari Box = accepted)
```

### Restock Rules — TRANSISI

1. **RO Box adalah DEFAULT** — 3+ size kosong langsung kirim box. Tidak perlu pre-plan surplus karena surplus akan ditangani di TAHAP 2.
2. **RO Protol hanya untuk gap minor** — 1-2 size kosong saja. Ini ~30% dari total restock.
3. **Surplus dari Box = accepted** — Box mengirim ALL sizes (12 pairs). Size yang sudah ada stok akan menjadi surplus. Ini TIDAK diblok — surplus tersebut akan dihitung dan ditarik di TAHAP 2.
4. **Fallback Protol -> Box** — Jika protol tidak tersedia di gudang, langsung fallback ke Box tanpa harus pre-plan surplus.
5. **WH Stock Filter** — Jika artikel di-recommend RO Box tapi stok Box di WH Pusat = 0, artikel tersebut **TIDAK DITAMPILKAN** di daftar RO Box (di-exclude sepenuhnya, bukan ditandai "NO"). Artikel hanya muncul jika WH Pusat punya stok box.
6. Allocation planner = gatekeeper — sistem recommend, planner approve/reject/modify

---

## TAHAP 0: IDENTIFIKASI URGENT SURPLUS (Off-Planogram)

### Konsep

Sebelum restock, sistem scan **semua artikel yang ada stok di toko** dan bandingkan dengan **planogram baru**. Artikel yang **tidak ada di planogram baru** tapi **punya stok di toko** = **URGENT surplus**.

Ini adalah barang lama / discontinued dari planogram sebelumnya yang HARUS dikeluarkan dari toko agar space bisa diisi barang baru.

### Fungsi

```python
identify_urgent_surplus(planogram, db_data)
# Returns: (urgent_list, total_urgent_pairs)
# urgent_list = list of {"article", "kode_mix", "gender", "series", "tier", "sizes": {size: qty}, "total_stock", "avg_monthly_sales"}
```

### Dampak ke RO Budget

`total_urgent_pairs` menjadi **budget cap untuk RO**:
- Jika urgent = 50 pairs -> RO maksimal 50 pairs (protol + box combined)
- Jika urgent = 0 -> RO **uncapped** (fallback ke full maxstock gap)

---

## TAHAP 1: RESTOCK (Tambal Dulu — Box Priority, Budget-Capped)

*(Sama seperti sebelumnya, tapi dengan tambahan budget cap dari TAHAP 0)*

### RO Budget Capping

Setelah generate full RO list (tanpa cap), sistem menjalankan `cap_ro_to_budget()`:

```python
cap_ro_to_budget(ro_protol_list, ro_box_list, budget_pairs)
# Prioritization sort:
# 1. Artikel dengan >=50% size kosong -> FIRST (paling butuh restock)
# 2. Artikel best seller (avg_monthly_sales tertinggi) -> SECOND
# Goal: "size full di artikel best seller"
#
# Greedy knapsack: iterate sorted list, skip items exceeding remaining budget
# (continue, not break — smaller items can still fit)
```

---

## TAHAP 2: SURPLUS (Setelah Restock Masuk — Dua Kategori)

### Konsep Utama — TRANSISI

Surplus sekarang terbagi **dua kategori**:

| Kategori | Definisi | Aksi | Warna di Excel |
|----------|----------|------|----------------|
| **URGENT** (off-planogram) | Artikel yang tidak ada di planogram baru tapi punya stok di toko | **HARUS ditarik minggu ini** | Orange (`FILL_URGENT`) |
| **REGULAR** (over-capacity) | Artikel on-planogram yang stoknya melebihi kapasitas tier (post-restock) | **Visibility/planning only** — tidak wajib ditarik minggu ini | Purple (`HEADER_FILL_PURPLE`) |

URGENT surplus sudah di-identify di TAHAP 0. REGULAR surplus dihitung SETELAH restock masuk.

Untuk REGULAR surplus:
- Stok yang dipakai = **stok POST-restock** (snapshot + RO Box + RO Protol yang dikirim)
- Surplus numbers akan **lebih tinggi** karena RO Box menambah stok di ALL sizes
- Surplus dari Box = **intended behavior** — Box sengaja dikirim dulu untuk memastikan display lengkap, lalu kelebihannya ditarik

**PENTING**: Artikel off-planogram **tidak menambah** jumlah artikel tier saat menghitung kapasitas tier. Hanya artikel on-planogram yang dihitung sebagai `actual_tier_articles`.

Surplus REGULAR ditentukan berdasarkan **gap antara kapasitas ideal per tier vs stok aktual POST-restock per tier**. Hanya tier yang over-capacity yang ditarik, dan yang ditarik adalah artikel dengan turnover (TO) terendah di tier tersebut.

### Tier yang Dicek vs Dikecualikan

**Dicek (T1, T2, T3):**
- Tier ini punya target kapasitas ideal (%) dari total kapasitas toko
- Jika actual POST-restock % > ideal % -> tier over-capacity -> tarik selisihnya
- Yang ditarik: artikel dengan TO paling rendah / dead stock di tier tersebut

**Dikecualikan:**
- **T4**: Promo / clearance — tujuan menghabiskan stok, jangan ditarik
- **T5**: Slow moving — sama seperti T4, biarkan sampai habis atau di-clearance
- **T8**: New launch — protection period 3 bulan sejak launch untuk test market

### T8 Lifecycle

```
LAUNCH (Bulan ke-0)
    |
    v
Protection Period (3 bulan)
- Tidak boleh ditarik sebagai surplus
- Data sales dikumpulkan untuk evaluasi
- Exception: manual override oleh Allocation Planner
  jika toko benar-benar over-capacity parah
    |
    v
BULAN KE-4: Reclassification
    |
    +-- Sales bagus --> Masuk T1/T2/T3 --> Ikut rules surplus tier barunya
    |
    +-- Sales jelek --> Masuk T4/T5 --> Exclude dari surplus check
                                          (masuk program clearance)
```

### Surplus Decision Tree — TRANSISI

```
TAHAP 1 SELESAI: Restock (RO Box + RO Protol) sudah dikirim
        |
        v
SIMULASI STOK POST-RESTOCK
= Stok snapshot + RO Box (12 pairs all sizes) + RO Protol (pairs per size)
        |
        v
HITUNG KAPASITAS PER TIER PER TOKO (dari stok POST-RESTOCK)
        |
        v
Bandingkan per tier: Actual POST-RESTOCK % vs Ideal Capacity %
        |
        +-- T1: Ideal 30%, Actual 40% --> Over +10% --> SURPLUS CANDIDATE
        +-- T2: Ideal 25%, Actual 28% --> Over +3%  --> SURPLUS CANDIDATE
        +-- T3: Ideal 20%, Actual 22% --> Over +2%  --> SURPLUS CANDIDATE
        +-- T4: --> SKIP (promo/clearance)
        +-- T5: --> SKIP (slow moving)
        +-- T8: --> SKIP (protection 3 bln)
        |
        v
Untuk tier yang OVER-CAPACITY (post-restock):
  Hitung selisih = Actual POST-RESTOCK % - Ideal %
  Convert ke jumlah artikel
        |
        v
  Ranking artikel di tier tsb by TO ascending
  (TO terendah = dead stock = prioritas tarik pertama)
        |
        v
  Tarik artikel dgn TO terendah sampai selisih terpenuhi
        |
        v
  Allocation Planner review & approve list tarik
        |
        v
  Tarik dari toko --> Masuk GUDANG PROTOL
        |
        v
  Sistem cek: ada toko lain yang butuh?
  +-- Ada --> Kirim protol ke toko yang butuh
  +-- Tidak ada --> Stay di gudang protol
```

### Surplus Calculation Example — TRANSISI

```
Contoh: Toko Matos — Total Kapasitas 100 artikel
SETELAH restock (10 artikel dapat RO Box, 3 artikel dapat RO Protol)

Tier    Ideal %    Ideal Qty    Post-Restock Qty    Actual %    Status
T1      30%        30           40                  37%         Over +10 artikel
T2      25%        25           28                  26%         Over +3 artikel
T3      20%        20           22                  20%         Over +2 artikel
T4      15%        15           12                  11%         (skip - promo)
T5      5%         5            4                   4%          (skip - slow moving)
T8      5%         5            3                   3%          (skip - protection)

Action:
- T1: Tarik 10 artikel dgn TO terendah -> ke gudang protol
- T2: Tarik 3 artikel dgn TO terendah -> ke gudang protol
- T3: Tarik 2 artikel dgn TO terendah -> ke gudang protol

NOTE: Surplus numbers lebih tinggi dari logic lama karena Box sudah masuk.
Ini INTENTIONAL — Box dikirim dulu untuk display lengkap, lalu kelebihan ditarik.
```

### Surplus Rules — TRANSISI

1. **URGENT surplus = off-planogram articles** — artikel yang tidak ada di planogram baru tapi punya stok di toko -> HARUS ditarik
2. **REGULAR surplus dihitung SETELAH restock masuk** — stok = snapshot + RO Box + RO Protol yang dikirim
3. **Off-planogram articles tidak inflate tier count** — tidak ditambahkan ke `actual_tier_articles` saat hitung kapasitas tier
4. Hanya T1, T2, T3 yang dicek untuk REGULAR surplus — T4/T5 excluded (clearance), T8 excluded (protection 3 bulan)
5. REGULAR surplus = actual POST-RESTOCK % - ideal % — hanya tier over-capacity
6. Prioritas tarik (REGULAR): TO terendah dulu — dead stock dan slow mover keluar duluan
7. **Surplus dari RO Box = expected** — ini bukan masalah, ini fitur. Box masuk -> display lengkap -> surplus ditarik
8. Semua surplus dari toko masuk gudang protol — ditarik per size, bukan per box utuh
9. Surplus tidak boleh store-to-store langsung — harus lewat gudang
10. Surplus di gudang protol otomatis masuk pool untuk RO Protol toko lain
11. T8 setelah 3 bulan -> reclassify berdasarkan actual sales -> ikut rules tier barunya
12. Manual override T8 hanya jika extremely over-capacity — case-by-case, bukan otomatis

---

## SIKLUS LENGKAP — TRANSISI

> Full ASCII flow diagram: see [`ro-surplus-output-format.md`](ro-surplus-output-format.md#siklus-lengkap--transisi-urgent---ro-budget-capped---surplus)

---

## Edge Cases

### 1. RO Box -> surplus baru (EXPECTED BEHAVIOR di Transisi)
Surplus dari Box = normal dan accepted. Tidak perlu pre-plan — surplus akan dihitung otomatis di TAHAP 2 dan ditarik setelahnya. Planner cukup review list surplus final.

### 2. T8 Protection Period
3 bulan protection: tidak boleh ditarik. Exception: manual override jika extremely over-capacity (case-by-case, documented). Setelah 3 bulan: reclassify ke tier baru.

### 3. Toko baru / Grand Opening
Full RO Box untuk semua artikel di planogram. Evaluasi surplus setelah 1 bulan. Tier capacity benchmark pakai toko serupa (size/area sama).

### 4. Artikel discontinued
Semua stok -> surplus -> tarik ke gudang protol. Redistribusi ke toko yang masih jual, atau markdown.

### 5. Gudang protol penuh
Prioritas redistribusi. Jika tidak ada demand -> eskalasi ke Planner (markdown/promo/retur supplier).

### 6. Gudang box kosong
Flag ke procurement untuk PO. Sementara cek gudang protol untuk rakit assortment protol.

### 7. Semua tier under-capacity
Restock prioritas berdasarkan sales contribution: T1 -> T2 -> T3. T4/T5 hanya restock jika masih dalam program promo aktif.

### 8. T8 di toko over-capacity parah
Manual override oleh Planner. Documented: alasan, expected impact. T8 yang ditarik -> gudang protol -> redistribute ke toko lain yang masih dalam protection period.

---

## RO REQUEST GENERATION (Weekly Document)

### Apa Itu RO Request?

RO Request adalah dokumen mingguan yang dihasilkan oleh sistem (atau AI agent) dan diserahkan dari **Area Supervisor** ke **Warehouse Supervisor**. Dokumen ini berisi:
1. Daftar barang yang perlu dikirim ke toko (RO Protol + RO Box)
2. Daftar barang yang perlu ditarik dari toko (Surplus Pull)
3. Cover page + signature block sebagai dokumen resmi handover

### Pipeline

```
Pre-Planogram -> Planogram (Step 1) -> Visual Planogram (Step 2) -> RO Request (Step 3)
```

RO Request **membutuhkan planogram** sebagai input. Tanpa planogram, tidak ada target per artikel per ukuran, sehingga RO Request tidak bisa dihitung.

### Data Sources

| Data | Source | Query |
|------|--------|-------|
| Store stock | `core.stock_with_product` | `WHERE LOWER(nama_gudang) LIKE '%{store_pattern}%'` |
| WH Pusat Box | `core.stock_with_product` | `WHERE LOWER(nama_gudang) = 'warehouse pusat'` (DDD + LJBB) |
| WH Pusat Protol | `core.stock_with_product` | `WHERE LOWER(nama_gudang) = 'warehouse pusat protol'` (DDD only) |
| Sales (3 month) | `core.sales_with_product` | `WHERE tanggal >= NOW() - INTERVAL '3 months'` + exclude intercompany |
| Planogram targets | Excel file | `RO Input {Region}.xlsx` -> sheet "Planogram" |

### RO Type Decision Logic — TRANSISI (Count-Based, Box Default)

```python
assortment_sizes = number of sizes in planogram for this article
empty_sizes = sizes where store stock = 0

# TRANSISI: Box is DEFAULT. Protol only for minor gaps (1-2 sizes).
if empty_sizes >= 3:
    ro_type = "RO_BOX"    # DEFAULT — send full box (12 pairs, all sizes) from Gudang Box
elif empty_sizes >= 1:
    ro_type = "RO_PROTOL"  # Minor gap — send individual pairs for 1-2 empty sizes
else:
    ro_type = "NO_RESTOCK"  # All sizes have stock
```

### Surplus Detection Logic — TRANSISI (Three-Phase)

```python
# PHASE 0: Identify URGENT surplus (off-planogram)
planogram_articles = set(planogram keys)
all_store_articles = set(articles with stock in store)
off_planogram = all_store_articles - planogram_articles

urgent_surplus = []
for article in off_planogram:
    urgent_surplus.append({article, sizes, total_stock, ...})
total_urgent_pairs = sum(a["total_stock"] for a in urgent_surplus)
# total_urgent_pairs = BUDGET for RO

# PHASE 1: Generate RO (budget-capped)
ro_protol_full, ro_box_full = generate_ro_decisions(gap_results)  # full, uncapped

if total_urgent_pairs > 0:
    ro_protol, ro_box, actual_ro_pairs = cap_ro_to_budget(
        ro_protol_full, ro_box_full, budget=total_urgent_pairs
    )
    # Prioritization: (1) >=50% sizes empty -> first, (2) best sellers -> second
    # Greedy knapsack: skip big items, continue to smaller ones
else:
    ro_protol, ro_box = ro_protol_full, ro_box_full  # uncapped fallback

# PHASE 2: Simulate restock + calculate REGULAR surplus
post_restock_stock = copy(current_store_stock)

for each article getting RO_BOX:
    for each size in box (all assortment sizes):
        post_restock_stock[article][size] += 1  # box adds 1 pair per size

for each article getting RO_PROTOL:
    for each empty_size:
        post_restock_stock[article][empty_size] += protol_qty

# Calculate REGULAR surplus from post_restock_stock
# IMPORTANT: off-planogram articles do NOT count in actual_tier_articles
for each article on planogram where tier in [1, 2, 3]:
    if article has sizes with post_restock_stock > target:
        excess_pairs = post_restock_stock - target (per size)
        if excess_pairs > 0:
            -> REGULAR SURPLUS CANDIDATE

# Sort regular surplus by avg_monthly_sales ASC (slowest sellers pulled first)

# OUTPUT: Both URGENT (off-plano) + REGULAR (over-capacity) in Excel
# URGENT = must pull this week. REGULAR = visibility/planning only.
```

### WH Source Rules

| Type | Warehouse | Entities | Notes |
|------|-----------|----------|-------|
| RO Box | Warehouse Pusat (Box) | DDD + LJBB | LJBB exclusive for Box only |
| RO Protol | Warehouse Pusat Protol | DDD only | No LJBB for protol |
| Surplus destination | Warehouse Pusat Protol | — | All surplus goes to protol gudang |

**IMPORTANT**: RO Box only from Warehouse Pusat — NOT from WHJ or WHB.

### Output Format: Excel (.xlsx) — 5 Sheets

Output: 5-sheet Excel (Cover Page, Daftar RO Protol, Daftar RO Box, Daftar Surplus [URGENT+REGULAR], Reference).

> Full sheet specifications, column layouts, and styling: see [`ro-surplus-output-format.md`](ro-surplus-output-format.md#output-format-excel-xlsx--5-sheets)

### Script Reference

**File**: `build_ro_royal_plaza.py` (in `step3-ro-request-transisi/` folder)

**Dependencies** (must be installed):
```bash
pip install psycopg2-binary openpyxl
```

**Key Config Variables** (top of script) — TRANSISI:
```python
STORE_NAME = "Zuma Royal Plaza"          # Display name
STORE_DB_PATTERN = "zuma royal plaza"     # For ILIKE match in DB
STORAGE_CAPACITY = 0                      # Number of storage boxes (0 = no storage)
RO_PROTOL_MAX_EMPTY = 2                   # <=2 sizes empty -> Protol (minor gap); 3+ -> Box (DEFAULT)
SURPLUS_CHECK_TIERS = [1, 2, 3]           # Only T1/T2/T3 checked for surplus
PLANOGRAM_FILE = "../RO Input Jatim.xlsx" # Relative path to planogram
PLANOGRAM_SHEET = "Planogram"             # Sheet name in planogram file
```

**Key Functions** (TRANSISI additions):
- `identify_urgent_surplus(planogram, db_data)` — scans all store articles for off-planogram items. Returns `(urgent_list, total_urgent_pairs)`. Budget for RO = total_urgent_pairs.
- `cap_ro_to_budget(ro_protol_list, ro_box_list, budget_pairs)` — prioritizes: (1) >=50% sizes empty first, (2) best sellers (highest avg_monthly_sales). Greedy knapsack — skips items exceeding budget, continues to smaller items. Returns `(capped_protol, capped_box, actual_pairs)`.
- `simulate_restock(ro_protol_list, ro_box_list, db_data, planogram)` — simulates post-restock stock state by adding Box (1 pair per size) and Protol fills to current stock
- `calculate_surplus(..., post_restock_stock=None)` — now accepts optional post-restock stock dict; when provided, uses it instead of current stock for tier distribution calculations. Off-planogram articles do NOT inflate `actual_tier_articles`.

**DB Connection** (in script):
```python
DB_HOST = "76.13.194.120"
DB_PORT = 5432
DB_NAME = "openclaw_ops"
DB_USER = "openclaw_app"
DB_PASS = "Zuma-0psCl4w-2026!"
```

**To generate for a different store**: Copy the script, change `STORE_NAME`, `STORE_DB_PATTERN`, `STORAGE_CAPACITY`, and ensure the planogram file has rows for that store.

> Known limitations, example output, and pending clarifications: see [`ro-surplus-output-format.md`](ro-surplus-output-format.md#known-limitations--pending-clarifications)

### How to Use This Skill (For AI Agents)

1. **Load dependencies**: `zuma-data-analyst-skill` (DB connection), `zuma-sku-context` (tier system, Kode Mix), `zuma-warehouse-and-stocks` (WH names, RO flow)
2. **Check planogram exists**: RO Request requires planogram. If none exists, generate one first using `planogram-zuma` skill
3. **Run script or generate equivalent**: Either execute `build_ro_royal_plaza.py` directly, or replicate its logic in a new script for a different store
4. **TRANSISI flow is sequential**: Script runs TAHAP 0 (`identify_urgent_surplus`) -> TAHAP 1 (restock with `cap_ro_to_budget` if urgent > 0) -> `simulate_restock()` -> TAHAP 2 (surplus: urgent + regular). Do NOT calculate surplus from pre-restock stock.
5. **Output validation**: Check that all 5 sheets are populated, totals match, WH availability is checked. Cover page should show 3 surplus rows (URGENT, REGULAR, TOTAL). Sheet 4 should have orange URGENT section + purple REGULAR section.
6. **Hand to user**: The Excel is ready to print and hand from AS to WH Supervisor

---

## Reference Files

| File | Contents |
|------|----------|
| [`ro-surplus-output-format.md`](ro-surplus-output-format.md) | Full cycle ASCII diagram, Excel 5-sheet output specification (cover page, column layouts per sheet), openpyxl styling/branding reference, worked example output (Royal Plaza), known limitations & pending clarifications |
| [`section-for-planogram.md`](section-for-planogram.md) | Distribution flow TRANSISI section formatted for planogram context — gudang types, RO decision tree, surplus tiers, T8 lifecycle, edge cases (standalone reference for planogram skill integration) |
| `build_ro_royal_plaza.py` | Working Python script for generating RO Request & Surplus Pull for Royal Plaza — use as template for other stores |
