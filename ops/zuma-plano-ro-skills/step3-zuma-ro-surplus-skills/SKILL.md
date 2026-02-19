---
name: zuma-distribution-flow
description: Zuma store distribution flow — surplus pull, restock (RO Protol/Box), and weekly RO Request generation. Covers decision logic, tier rules, output format, and Python script reference. Use when generating RO Request, calculating surplus, or working with store replenishment.
user-invocable: false
---

# Flow Distribusi: Surplus & Restock (v3)

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
| **Gudang Protol** | Stok eceran per size/pairs — juga menerima semua surplus dari toko | Per pairs/size |

### Tipe RO (Replenishment Order)
| Tipe | Trigger | Source | Kirim |
|------|---------|--------|-------|
| **RO Box** | >50% jumlah size tidak sesuai assortment | Gudang Box | 1 box (12 pairs, all sizes) |
| **RO Protol** | ≤50% jumlah size tidak sesuai | Gudang Protol | Pairs di size yang kurang saja |

**PENTING:** Persentase 50% dihitung dari **jumlah size**, bukan total kuantitas barang.

### Key Metrics
- **Max Stock Store** = total kapasitas toko, terdiri dari 2 komponen: Planogram + Storage
- **Planogram (display)** = alokasi artikel di area display, ditentukan berdasarkan tier weight dan sales weight
- **Storage** = cerminan dari planogram, dialokasikan dalam 2 tahap (lihat detail di bawah)
- **Assortment** = jumlah pairs per size yang seharusnya tersedia
- **Tier Capacity %** = persentase ideal stok per tier dari total kapasitas toko
- **Rata-rata Sales Qty** = rata-rata penjualan per artikel selama 6 bulan terakhir — digunakan untuk alokasi storage dan penarikan surplus T4/T5
- **Store Grade** = klasifikasi toko (A/B/C) untuk prioritas distribusi saat stok warehouse kurang

---

## Stok Ideal & Toleransi 10%

### Menentukan Stok Ideal

Stok ideal ditentukan berdasarkan **max stock store**, yang terdiri dari 2 komponen:

**1. Planogram (display):**
Alokasi artikel di area display ditentukan berdasarkan tier weight dan sales weight.

**2. Storage:**
Merupakan cerminan dari planogram, namun tidak semua artikel yang ada di planogram mendapat alokasi storage karena kapasitas storage berbeda (umumnya lebih kecil) dari planogram. Alokasi storage dilakukan dalam 2 tahap:
- **Tahap 1:** Kapasitas storage diproporsi ke setiap tier berdasarkan share masing-masing tier
- **Tahap 2:** Dalam setiap tier, artikel yang mendapat alokasi storage ditentukan berdasarkan rata-rata sales qty selama 6 bulan terakhir (artikel dengan sales tertinggi diprioritaskan)

```
Stok Ideal per Toko = Stok Planogram (display) + Stok Storage
```

### Toleransi 10% (Buffer Zone)

Setiap store memiliki **toleransi 10% dari total kapasitas stok**. Toleransi ini dibagi ke masing-masing tier dengan proporsi tetap:

```
Pembagian Toleransi 10%:
- 4% untuk Tier 4 dan Tier 5
- 3% untuk Tier 1
- 2% untuk Tier 2
- 1% untuk Tier 3
- Tier 8: TIDAK memiliki alokasi toleransi selama protection period
```

**Contoh: Store total kapasitas 100 artikel**

```
Tier   Ideal   Toleransi   Range Aman
T1     30      3% = 3      27 — 33
T2     25      2% = 2      23 — 27
T3     20      1% = 1      19 — 21
T4     10      4% = 4*     6 — 14
T5     10      (*shared)   6 — 14
T8     5       —           — (protection period, no surplus check)

*) 4% toleransi untuk T4 dan T5 dibagi bersama

Aturan:
- Actual DI ATAS range atas → SURPLUS → tarik kelebihan
- Actual DI BAWAH range bawah → RESTOCK → isi kekurangan
- Actual DALAM range → AMAN → tidak ada action
```

---

## Tier Surplus Rules

| Tier | Surplus Check | Mekanisme Tarik | Toleransi | Keterangan |
|------|--------------|-----------------|-----------|------------|
| **T1** | ✅ Ya | Langsung tarik seluruh kelebihan dari stok ideal | 3% | Best seller |
| **T2** | ✅ Ya | Langsung tarik seluruh kelebihan dari stok ideal | 2% | Fast moving |
| **T3** | ✅ Ya | Langsung tarik seluruh kelebihan dari stok ideal | 1% | Moderate |
| **T4** | ✅ Ya | Rata-rata sales qty — terendah ditarik duluan | 4% (shared) | Discontinue |
| **T5** | ✅ Ya | Rata-rata sales qty — terendah ditarik duluan | 4% (shared) | Slow moving |
| **T8** | ❌ Tidak (3 bln) | Protection period | — | New launch |

**Catatan penting:**
- **T1/T2/T3:** Tidak ada urutan prioritas — semua kelebihan dari stok ideal langsung ditarik
- **T4/T5:** Penarikan berdasarkan rata-rata sales qty, artikel dengan penjualan paling rendah ditarik terlebih dahulu
- **T8:** Tidak dilakukan penarikan selama 3 bulan pertama. Setelah reklasifikasi, ikut rules tier barunya

---

## FLOW 1: RESTOCK

### Trigger
Sistem mendeteksi stok aktual **di bawah range toleransi bawah** (Ideal - Toleransi per tier).

### Decision Tree

```
SISTEM DETEKSI GAP: Actual < (Ideal - Toleransi) per tier
        │
        ▼
Hitung % size yang tidak sesuai assortment / stok ideal
(% dihitung dari JUMLAH SIZE, bukan total qty)
        │
        ├── >50% size tidak sesuai ──────► RO BOX
        │                                   │
        │                                   ▼
        │                             Cek Gudang Box
        │                                   │
        │                              ├── Ada → Planner approve → Kirim box ke toko ✅
        │                              │
        │                              └── Tidak ada → Flag (tunggu PO supplier)
        │
        └── ≤50% size tidak sesuai ─────► RO PROTOL (Tiered Fallback)
                                            │
                                       OPSI 1: Cek Gudang Protol
                                       ├── Ada size yg dibutuhkan → Kirim protol ✅
                                       └── Tidak ada ↓
                                            │
                                       OPSI 2: Mutasi antar store
                                       ├── Ada toko dalam 1 AREA YANG SAMA surplus size ini
                                       │   + kondisi urgent + approval Allocation Planner
                                       │   → Mutasi langsung store-to-store ✅
                                       └── Tidak ada ↓
                                            │
                                       OPSI 3: Fallback RO Box
                                       └── Jika stok Gudang Protol tidak tersedia,
                                           dapat langsung dilakukan RO via Gudang Box
                                           → Planner approve + surplus pre-plan
                                           → Kirim box ke toko ✅
```

### Mutasi Antar Store (NEW v2)

Mutasi langsung store-to-store diperbolehkan dengan syarat:
1. **Dalam 1 area yang sama** — tidak boleh cross-area
2. **Kondisi urgent** — store penerima benar-benar butuh
3. **Approval Allocation Planner** — tidak boleh inisiatif sendiri antar store
4. Alternatif dari jalur gudang protol, bukan pengganti

### Rules Jika Warehouse Kurang Stok

Jika stok warehouse tidak mencukupi kebutuhan semua store pada hari pengiriman:

**Skenario 1: Kekurangan sedikit → Bagi rata**

```
Contoh: Stok warehouse = 3 box
- Zuma Galaxy Mall butuh 2 box
- Zuma PTC butuh 1 box
- Zuma TP butuh 1 box
Total butuh = 4 box, kurang 1 box

→ Bagi rata: masing-masing store dapat 1 box
```

**Skenario 2: Kekurangan banyak → Prioritas store grade**

```
Contoh: Stok warehouse = 3 box
- Zuma Galaxy Mall (Grade A) butuh 2 box
- Zuma PTC (Grade B) butuh 2 box
- Zuma TP (Grade C) butuh 2 box
Total butuh = 6 box, kurang 3 box

→ Prioritas:
  1. Grade A dipenuhi terlebih dahulu
  2. Grade B mendapat sisa alokasi
  3. Grade C tidak diprioritaskan pada kondisi stok kurang
```

### Prioritas Warehouse Cabang vs Retail

Jika jadwal pengiriman **Warehouse Cabang** dan **Retail Jawa Timur** bersamaan, dan terjadi kekurangan stok dengan selisih **1—3 box**, maka **prioritas pengiriman ke store** terlebih dahulu.

### Restock Rules

1. Prioritas selalu RO Protol jika memenuhi syarat — lebih efisien, tidak bikin surplus baru
2. **Jika stok Gudang Protol tidak tersedia, dapat langsung RO via Gudang Box** — tidak perlu tunggu
3. RO Box fallback wajib disertai surplus pre-plan
4. Allocation Planner = gatekeeper — sistem recommend, planner approve/reject/modify
5. Mutasi antar store diperbolehkan: dalam 1 area + urgent + approval Planner
6. Warehouse kurang stok sedikit → bagi rata; kurang banyak → prioritas Grade A → B → C
7. Warehouse cabang vs retail jadwal bareng, selisih 1-3 box → store diprioritaskan

---

## FLOW 2: SURPLUS (Tier-Based)

### Konsep Utama

Surplus = stok aktual **melebihi stok ideal** (di atas range toleransi). Penarikan dilakukan berdasarkan kesesuaian dengan stok ideal yang sudah ditentukan per tier. Semua 5 tier (T1—T5) dicek surplus, dengan perbedaan mekanisme tarik.

**Mekanisme per tier:**
- **T1/T2/T3:** Artikel yang tidak sesuai stok ideal langsung ditarik. Tidak ada urutan prioritas — seluruh kelebihan ditarik.
- **T4/T5 (discontinue/slow moving):** Penarikan menggunakan konsep rata-rata sales qty. Artikel dengan penjualan paling rendah ditarik terlebih dahulu.

### SKU Version Rule

Jika terdapat **2 versi SKU pada size yang sama** (Version 1 dan Version 2):

1. **Tarik Version 2 (versi baru) terlebih dahulu**
2. Tujuan: menghabiskan stok Version 1 (versi lama) agar tidak jadi dead stock
3. Setelah V1 habis, V2 tetap di toko sebagai artikel pengganti

### Mekanisme Penarikan Surplus

**T1, T2, T3:**
- Semua kelebihan dari stok ideal langsung ditarik — tidak ada urutan prioritas
- Jika ada V1 dan V2 pada size sama → V2 ditarik duluan (habiskan V1 dulu)

**T4, T5 (discontinue/slow moving):**
- Penarikan berdasarkan rata-rata sales qty
- Artikel dengan rata-rata penjualan paling rendah ditarik terlebih dahulu
- Jika ada V1 dan V2 → V2 ditarik duluan

### Surplus Decision Tree

```
SISTEM HITUNG KAPASITAS PER TIER PER TOKO
        │
        ▼
Bandingkan: Actual vs (Ideal + Toleransi) per tier
        │
        ├── T1: Ideal 30, Tol 3%, Actual 36 → Over (36 > 33) → SURPLUS
        │   └── Tarik seluruh kelebihan (3 artikel) langsung
        │
        ├── T2: Ideal 25, Tol 2%, Actual 24 → AMAN (23–27) → SKIP
        │
        ├── T3: Ideal 20, Tol 1%, Actual 22 → Over (22 > 21) → SURPLUS
        │   └── Tarik seluruh kelebihan (1 artikel) langsung
        │
        ├── T4: Ideal 10, Tol 4%*, Actual 16 → Over (16 > 14) → SURPLUS
        │   └── Tarik 2 artikel dengan rata-rata sales qty terendah
        │
        ├── T5: Ideal 10, Tol (shared), Actual 15 → Over → SURPLUS
        │   └── Tarik artikel dengan rata-rata sales qty terendah
        │
        └── T8: → SKIP (protection period 3 bulan)
        │
        ▼
Allocation Planner review & approve list tarik
        │
        ▼
Informasi distribusi ke Area Supervisor
        │
        ▼
Penarikan mengikuti jadwal pengiriman warehouse
        │
        ▼
Destinasi:
├── Default: Gudang Protol
└── Mutasi antar store (jika dalam 1 area + approval Planner)
```

### Surplus Calculation Example (v3)

```
Toko Matos — Total Kapasitas 100 artikel

Tier  Ideal  Tol    Range     Actual  Status
T1    30     3%=3   27–33     36      Over +3 → tarik 3 artikel langsung
T2    25     2%=2   23–27     24      AMAN → SKIP
T3    20     1%=1   19–21     22      Over +1 → tarik 1 artikel langsung
T4    10     4%=4*  6–14      16      Over +2 → tarik 2 (rata-rata sales qty terendah)
T5    10     (*sh)  6–14      15      Over +1 → tarik 1 (rata-rata sales qty terendah)
T8    5      —      —         4       SKIP (protection 3 bulan)
```

### Destinasi Surplus

| Destinasi | Kondisi |
|-----------|---------|
| **Gudang Protol** | Default — semua surplus masuk gudang protol |
| **Mutasi antar store** | Hanya jika: (1) dalam 1 area yang sama, (2) toko penerima butuh artikel/size tsb, (3) approval Allocation Planner |

### Surplus Rules

1. **T1, T2, T3, T4, T5** semua dicek surplus — T8 excluded (protection 3 bulan)
2. Surplus = actual melebihi stok ideal (di atas range toleransi) — hanya tier over-capacity yang ditarik
3. **T1/T2/T3:** Langsung tarik seluruh kelebihan dari stok ideal, tidak ada prioritas urutan
4. **T4/T5:** Tarik berdasarkan rata-rata sales qty — artikel penjualan terendah ditarik duluan
5. SKU Version: V2 ditarik sebelum V1 (untuk semua tier)
6. Semua surplus default masuk gudang protol — ditarik per size, bukan per box utuh
7. Mutasi store-to-store diperbolehkan: dalam 1 area + urgent + approval Planner
8. Surplus di gudang protol otomatis masuk pool untuk RO Protol toko lain

---

## T8 Lifecycle

```
LAUNCH (Bulan ke-0)
    │
    ▼
Protection Period (3 bulan)
- Tidak boleh ditarik sebagai surplus
- Data sales dikumpulkan untuk evaluasi
- Exception: manual override oleh Allocation Planner
  jika toko benar-benar over-capacity parah (case-by-case, documented)
    │
    ▼
BULAN KE-4: Reclassification
    │
    ├── Sales bagus → Masuk T1/T2/T3 → Ikut surplus check, langsung tarik kelebihan
    │
    └── Sales jelek → Masuk T4/T5 → Ikut surplus check, tarik by rata-rata sales qty
```

---

## Informasi & Jadwal

- Distribusi RO mengikuti **jadwal pengiriman** yang sudah ditentukan
- **Allocation Planner → Area Supervisor**: informasi penarikan surplus
- **AS + BM (Branch Manager)**: mendapat notifikasi **H-1** terkait artikel yang akan dikirim/ditarik
- Semua mutasi dan pengiriman mengikuti jadwal warehouse

---

## SIKLUS LENGKAP (Interconnected)

```
         ALLOCATION PLANNER (control semua flow)
              │                    │
              ▼                    ▼
         RESTOCK                SURPLUS (Tier-Based)
         Actual < Ideal         Actual > Ideal + Toleransi
         - Toleransi            T1/T2/T3: langsung tarik kelebihan
              │                 T4/T5: rata-rata sales qty terendah
              │                 T8: skip (3 bln protection)
              │                      │
              ▼                      ▼
         ┌─────────┐          Gudang Protol / Mutasi antar store
         │% size   │                 │
         │tdk sesuai│                │
         └─┬───┬───┘                │
       >50%│   │≤50%                │
           ▼   ▼                    │
        RO BOX  RO PROTOL ◄────────┘ (surplus = supply protol)
           │    │
           │    ├─ Gudang Protol
           │    ├─ Mutasi antar store (1 area, urgent, approval)
           │    └─ Fallback RO Box
           ▼         ▼
   ┌──────────────────────┐
   │  GUDANG BOX/PROTOL   │
   │  Kurang stok?        │
   │  - Sedikit: bagi rata│
   │  - Banyak: Grade A>B>C│
   │  WH Cabang vs Retail: │
   │  selisih 1-3 box →   │
   │  store prioritas      │
   └──────────┬───────────┘
              ▼
   ┌──────────────────────┐
   │        TOKO           │
   │  Display + Storage    │
   │  Info H-1 ke AS & BM  │
   └──────────────────────┘
```

---

## Edge Cases

### 1. RO Box fallback → surplus baru
Allocation Planner WAJIB pre-plan: size mana surplus setelah box masuk, kirim ke toko mana. Jika tidak ada demand, stay di storage (jika muat) atau tarik ke gudang.

### 2. T8 Protection Period
3 bulan protection: tidak boleh ditarik. Exception: manual override jika extremely over-capacity (case-by-case, documented). Setelah 3 bulan: reclassify ke tier baru.

### 3. Toko baru / Grand Opening
Full RO Box untuk semua artikel di planogram. Evaluasi surplus setelah 1 bulan. Tier capacity benchmark pakai toko serupa (size/area sama).

### 4. Artikel Discontinued (masuk T4)
Surplus check berlaku, penarikan berdasarkan rata-rata sales qty (terendah ditarik duluan). Stok yang ditarik masuk gudang protol atau mutasi ke store dalam 1 area.

### 5. SKU Version 1 & 2 Bersamaan
V2 ditarik dulu saat surplus → V1 dihabiskan di toko. Setelah V1 habis, V2 jadi artikel utama di toko tersebut.

### 6. Gudang protol penuh
Prioritas redistribusi ke toko. Tidak ada demand → eskalasi Planner (markdown/promo/retur supplier).

### 7. Gudang box kosong
Flag procurement untuk PO. Sementara cek gudang protol apakah bisa rakit assortment.

### 8. Semua tier under-capacity
Restock prioritas berdasarkan sales contribution: T1 → T2 → T3. T4/T5 hanya restock jika masih ada program aktif. Jika stok Gudang Protol tidak tersedia, langsung RO via Gudang Box.

### 9. Warehouse cabang & retail jadwal bareng
Selisih 1-3 box → store diprioritaskan. Di atas itu → eskalasi Planner.

---

## Changelog v2 → v3

| # | Perubahan | Detail |
|---|-----------|--------|
| 1 | **Stok Ideal — 2 komponen** | Planogram (tier weight + sales weight) dan Storage (2 tahap: proporsi tier → rata-rata sales qty 6 bulan) |
| 2 | **Toleransi — proporsi tetap** | Tidak lagi proporsional per tier. Sekarang: 4% T4/T5, 3% T1, 2% T2, 1% T3. T8 tidak ada toleransi selama protection period |
| 3 | **Surplus T1/T2/T3 — langsung tarik** | Tidak ada lagi prioritas TO/dead stock. Semua kelebihan dari stok ideal langsung ditarik |
| 4 | **Surplus T4/T5 — rata-rata sales qty** | Penarikan berdasarkan rata-rata sales qty, artikel terendah ditarik duluan |
| 5 | **Stok Minimal — DIHAPUS** | Tidak ada lagi aturan stok minimal saat surplus. Yang tidak sesuai stok ideal langsung ditarik |
| 6 | **Storage alokasi — by sales qty** | Artikel yang mendapat storage ditentukan berdasarkan rata-rata sales qty 6 bulan (bukan TO) |
| 7 | **RO Protol fallback** | Jika stok Gudang Protol tidak tersedia, dapat langsung RO via Gudang Box |

---

## RO REQUEST GENERATION (Weekly Document)

### Apa Itu RO Request?

RO Request adalah dokumen mingguan yang dihasilkan oleh sistem (atau AI agent) dan diserahkan dari **Area Supervisor** ke **Warehouse Supervisor**. Dokumen ini berisi:
1. Daftar barang yang perlu dikirim ke toko (RO Protol + RO Box)
2. Daftar barang yang perlu ditarik dari toko (Surplus Pull)
3. Cover page + signature block sebagai dokumen resmi handover

### Pipeline

```
Pre-Planogram → Planogram (Step 1) → Visual Planogram (Step 2) → RO Request (Step 3)
```

RO Request **membutuhkan planogram** sebagai input. Tanpa planogram, tidak ada target per artikel per ukuran, sehingga RO Request tidak bisa dihitung.

### Data Sources

| Data | Source | Query |
|------|--------|-------|
| Store stock | `core.stock_with_product` | `WHERE LOWER(nama_gudang) LIKE '%{store_pattern}%'` |
| WH Pusat Box | `core.stock_with_product` | `WHERE LOWER(nama_gudang) = 'warehouse pusat'` (DDD + LJBB) |
| WH Pusat Protol | `core.stock_with_product` | `WHERE LOWER(nama_gudang) = 'warehouse pusat protol'` (DDD only) |
| Sales (3 month) | `core.sales_with_product` | `WHERE tanggal >= NOW() - INTERVAL '3 months'` + exclude intercompany |
| Planogram targets | Excel file | `RO Input {Region}.xlsx` → sheet "Planogram" |

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
# Only check articles in tier T1, T2, T3, T4, T5
# Skip T8 (new launch protection 3 months)

for each article on planogram where tier in [1, 2, 3, 4, 5]:
    if article NOT in store stock (completely absent):
        → NOT surplus (needs restock)
    if article has sizes with stock > target:
        excess_pairs = stock - target (per size)
        if excess_pairs > 0:
            → SURPLUS CANDIDATE

# T1/T2/T3: Tarik SEMUA kelebihan (no sorting needed)
# T4/T5: Sort by avg_monthly_sales ASC (slowest sellers pulled first)
```

### WH Source Rules

| Type | Warehouse | Entities | Notes |
|------|-----------|----------|-------|
| RO Box | Warehouse Pusat (Box) | DDD + LJBB | LJBB exclusive for Box only |
| RO Protol | Warehouse Pusat Protol | DDD only | No LJBB for protol |
| Surplus destination | Warehouse Pusat Protol | — | All surplus goes to protol gudang |

**IMPORTANT**: RO Box only from Warehouse Pusat — NOT from WHJ or WHB.

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

**Sorting T1/T2/T3**: No specific order (all excess pulled).
**Sorting T4/T5**: By avg_monthly_sales ASC (slowest sellers first — these get pulled first).

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

**File**: `build_ro_request.py` (in `step3-zuma-ro-surplus-skills/` folder)

**Universal script** — one script for all stores. No per-store copies needed.

**Dependencies** (must be installed):
```bash
pip install psycopg2-binary openpyxl
```

**CLI Usage**:
```bash
# Required: --store
python3 build_ro_request.py --store "Icon Mall Gresik" --storage 0
python3 build_ro_request.py --store "Royal Plaza" --storage 75
python3 build_ro_request.py --store "Galaxy Mall" --storage 0

# Optional overrides
python3 build_ro_request.py --store "Royal Plaza" --storage 75 --threshold 0.60
python3 build_ro_request.py --store "Icon Mall Gresik" --output /tmp/my_ro.xlsx
```

**Arguments**:
| Arg | Required | Default | Description |
|-----|----------|---------|-------------|
| `--store` | Yes | — | Store display name. Used as `ILIKE '%{store}%'` on `nama_gudang` (stock) and `store_name` (planogram) |
| `--storage` | No | `0` | Storage capacity in boxes |
| `--output` | No | `~/Desktop/DN PO ENTITAS/RO_Request_{store}_{date}.xlsx` | Output file path |
| `--threshold` | No | `0.50` | % size kosong threshold for RO Box (default 50%) |

**Planogram source**: `portal.temp_portal_plannogram` (DB), join key `article_mix` → `kode_mix`

**Store naming note**: The planogram table (`store_name`) and stock table (`nama_gudang`) may use
slightly different names (e.g. "Zuma Icon Gresik" vs "Zuma Icon Mall Gresik"). The script handles
this automatically by stripping "Mall" from the planogram ILIKE pattern.

**DB Connection** (in script):
```python
DB_HOST = "76.13.194.120"
DB_PORT = 5432
DB_NAME = "openclaw_ops"
DB_USER = "openclaw_app"
DB_PASS = "$PGPASSWORD"
```

**Available stores** (from `portal.temp_portal_plannogram`):
- Zuma Royal Plaza → `--store "Royal Plaza"`
- Zuma Icon Gresik → `--store "Icon Mall Gresik"` or `--store "Icon Gresik"`
- Zuma Galaxy Mall → `--store "Galaxy Mall"`
- Zuma Matos → `--store "Matos"`
- Zuma Tunjungan Plaza → `--store "Tunjungan Plaza"`
- ZUMA PTC → `--store "PTC"`
- Zuma City Of Tomorrow Mall → `--store "City Of Tomorrow"`
- Zuma Mall Olympic Garden → `--store "Olympic Garden"`
- Zuma Sunrise Mall → `--store "Sunrise Mall"`
- Zuma Lippo Batu → `--store "Lippo Batu"`
- Zuma Lippo Sidoarjo → `--store "Lippo Sidoarjo"`

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

**Sample output file**: `sample_ro_request_royal_plaza.xlsx` (in this folder)

⚠️ **Note**: This sample output is **experimental** and will be updated as the RO Request generation logic evolves. Use as reference for structure and styling, but expect metrics and logic to change.

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
2. **Check planogram exists**: RO Request requires planogram. If none exists, generate one first using `SKILL_planogram_zuma_v3.md`
3. **Run script or generate equivalent**: Either execute `build_ro_royal_plaza.py` directly, or replicate its logic in a new script for a different store
4. **Output validation**: Check that all 5 sheets are populated, totals match, WH availability is checked
5. **Hand to user**: The Excel is ready to print and hand from AS to WH Supervisor
