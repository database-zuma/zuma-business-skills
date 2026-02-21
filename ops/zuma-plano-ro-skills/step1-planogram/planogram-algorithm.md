# Planogram Algorithm — Step-by-Step Data Processing

> This file contains the complete data processing pipeline, article assignment algorithm,
> storage allocation logic, implementation reference, and AI agent gotchas.
> Referenced from SKILL.md Sections 2-3.

---

# SECTION 2: STEP-BY-STEP DATA PROCESSING

## 2.1 Data Preparation

### 2.1.1 Input Files Required

**OPTION A: From VPS Database (PREFERRED -- data sudah enriched)**

Jika menggunakan VPS PostgreSQL DB (`openclaw_ops`), data sudah pre-enriched di core views. Ini JAUH lebih mudah karena tidak perlu manual KODEMIX extraction dan join.

| Data Source | View/Table | Keterangan |
|------------|------------|------------|
| Sales data (enriched) | `core.sales_with_product` | Sudah include kode_mix, article, gender, series, tipe, tier. ~1.55M rows |
| Stock data (enriched) | `core.stock_with_product` | Sudah include product details. ~142K rows |
| Master Artikel | `portal.kodemix` | Backup reference. Gunakan `DISTINCT ON (TRIM(LOWER(kode_besar)))` |
| Denah Toko | `Data Option By Region.xlsx` | File lokal, sheet per region (Jatim, Jakarta, dll) |

**DB Connection:**
```
Host: 76.13.194.120 | Port: 5432 | DB: openclaw_ops
User: openclaw_app | Pass: Zuma-0psCl4w-2026!
```

**CRITICAL DB RULES (from zuma-data-ops skill):**
1. `TRIM(LOWER())` for ALL string matching (Rule 1)
2. `DISTINCT ON` for kodemix deduplication (Rule 2)
3. Do NOT filter by `WHERE status = 'Aktif'` on kodemix (Rule 3)
4. ALWAYS use `core.sales_with_product` and `core.stock_with_product` (Rule 5)
5. Use `kode_mix` for year-over-year and version-agnostic aggregation (Rule 6)
6. ALWAYS exclude intercompany: `WHERE (is_intercompany IS NULL OR is_intercompany = FALSE)` (Rule 7)

**Column mapping (core views -> skill conventions):**
```
core.sales_with_product columns:
  matched_store_name  -> filter by TRIM(LOWER(store_name))
  kode_mix            -> article grouping key
  article             -> article name
  gender              -> gender (MEN, LADIES, BABY, BOYS, GIRLS, JUNIOR)
  series              -> series name
  tipe                -> tipe (Jepit / Fashion)
  tier                -> tier_baru (1, 2, 3, 4, 5, 8)
  transaction_date    -> for date range filtering & TO_CHAR(date, 'YYYY-MM') as bulan
  quantity            -> sales quantity
  total_amount        -> revenue
  is_intercompany     -> MUST exclude TRUE values
```

Jika menggunakan Option A, **SKIP steps 2.1.2 dan 2.1.3** (KODEMIX extraction dan CSV consolidation sudah tidak perlu). Langsung ke Step 2.1.4 (Denah Toko) dan Step 2.2 (Adjusted Average).

**OPTION B: From Raw CSV Files (legacy method)**

| File | Format | Keterangan |
|------|--------|------------|
| Sales data bulanan | CSV per bulan | Kolom: Nama Departemen, Tanggal, No Faktur, Kode Barang, Nama Barang, Kuantitas, @Harga, Total Harga |
| Master Artikel + Tier | XLSX/CSV | Kolom: KODEMIX, Gender, Series, Article, Tier_Baru, Tipe (Jepit/Fashion) |
| Denah Toko | Tabel structured | Per toko: daftar display components + kapasitas (lihat format di 2.1.4) |
| Stock aktual (opsional) | XLSX | Stock per artikel per toko -- untuk comparison report |
| SPG Insight (opsional) | Form response | Customer flow, hot/cold zone, dll |

### 2.1.2 Extract KODEMIX dari Kode Barang

Kode Barang di sales data = KODEMIX + "Z" + Size.

```
Contoh:
  L1CAV222Z36 -> KODEMIX: L1CAV222, Size: 36
  M1CA25Z42   -> KODEMIX: M1CA25,   Size: 42
  B2TS01Z32   -> KODEMIX: B2TS01,   Size: 32
  K1CAV205Z22 -> KODEMIX: K1CAV205, Size: 22

Extraction rule:
  KODEMIX = Kode Barang dengan suffix "Z" + angka size dihapus
  Regex: replace /Z\d+$/ dengan ""
  Atau: split by last occurrence of "Z", ambil bagian kiri
```

HATI-HATI: Beberapa kode ada "Z" di tengah (contoh: MEN ONYX Z 10 -> kode mungkin M1ONZ10Z42). Gunakan LAST occurrence of "Z" + digits sebagai separator, bukan first.

### 2.1.3 Konsolidasi Sales Data

**Step 1: Gabung semua CSV bulanan -> 1 dataset**

```
Baca semua file penjualan_2025_*.csv
Gabung menjadi 1 dataframe/tabel
Tambah kolom "Bulan" extract dari Tanggal (YYYY-MM)
```

**Step 2: Filter hanya retail stores**

```
EXCLUDE dari "Nama Departemen":
  - Yang mengandung "Wholesale"
  - Yang mengandung "Online"
  - Yang mengandung "Bazar"
  - Yang mengandung "Pusat"
  - Non-Zuma stores (Bintang Supermarket, Padma Bali, Grandlucky, 
    Clandy's, Pepito, Paveels, Royal Surf, Omosando, Sonobebe, 
    Monkey Forest, Cilukba, dan sejenisnya -- ini consignment/external)
    
INCLUDE hanya:
  - Store yang ada di Master Store Database (47 retail stores)
  - Match by nama, perhatikan variasi penulisan 
    (contoh: "ZUMA Dalung" vs "Zuma Dalung" -- case insensitive match)
```

**Step 3: Extract KODEMIX & aggregate ke article level**

```
Untuk setiap baris sales:
  1. Extract KODEMIX dari Kode Barang (strip Z+size)
  2. Group by: Nama Departemen (store), KODEMIX, Bulan
  3. SUM: Kuantitas (= total pairs sold)
  4. SUM: Total Harga (= total revenue)

Output: tabel [Store, KODEMIX, Bulan, Total_Qty, Total_Revenue]
```

**Step 4: Join dengan Master Artikel**

```
LEFT JOIN aggregated sales ON KODEMIX = Master.KODEMIX

Hasil: [Store, KODEMIX, Gender, Series, Article, Tier_Baru, Tipe, Bulan, Total_Qty, Total_Revenue]

Cek orphans:
  - KODEMIX di sales tapi TIDAK ada di master -> log sebagai warning
  - KODEMIX di master tapi TIDAK ada di sales -> bisa jadi dead stock atau new launch belum terjual
```

### 2.1.4 Format Denah Toko

**Data Source:** File `Data Option By Region.xlsx` berisi layout per toko per region. Setiap region = 1 sheet (Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali). Kolom per toko menunjukkan: jumlah backwall + hooks, gondola, rak baby (layers), keranjang, table, VM, storage capacity.

**PENTING:** Tidak semua kolom terisi -- beberapa toko kecil TIDAK punya gondola, table, VM, keranjang, atau bahkan storage. Jika kolom kosong atau 0, artinya toko tersebut TIDAK memiliki komponen display tersebut. Jangan assume ada.

Denah toko diinput sebagai tabel structured (bukan gambar/visual):

```
Store_Name: [nama toko]
Storage_Capacity: [jumlah box]

Display Components:
| Component_ID | Type        | Gender_Type     | Hooks/Slots | Layers | Qty | Notes          |
|-------------|-------------|-----------------|-------------|--------|-----|----------------|
| BW-1        | Backwall    | [assign nanti]  | 30          | -      | 1   | Near entrance  |
| BW-2        | Backwall    | [assign nanti]  | 24          | -      | 1   | Left wall      |
| GD-1        | Gondola     | [assign nanti]  | 20          | -      | 1   | Center island  |
| RK-1        | Rak Baby    | Baby & Kids     | -           | 3      | 1   | Near cashier   |
| KR-1        | Keranjang   | Baby & Kids     | -           | -      | 2   | Beside rak     |
| TB-1        | Table       | Luca/Luna/Airmove | 4 artikel | -      | 1   | Front display  |
| VM-1        | VM Display  | Luca/Luna/Airmove | 2 artikel | -      | 1   | Has VM tools   |
```

**Type yang valid:**
- `Backwall` -- hook-based, 1 gender-type per unit
- `Gondola` -- hook-based, 1 gender-type per unit
- `Rak Baby` -- layer-based, khusus Baby & Kids
- `Keranjang` -- 12 pairs per unit, khusus Baby & Kids
- `Table` -- sample display, untuk Luca/Luna/Airmove
- `VM Display` -- wall/shelf dengan VM tools, untuk Luca/Luna/Airmove

**Gender_Type yang valid untuk Backwall/Gondola:**
- Men Jepit, Men Fashion, Ladies Jepit, Ladies Fashion
- Baby & Kids, Boys, Girls, Junior

Gender_Type untuk Backwall/Gondola TIDAK perlu diisi saat input denah -- AI akan merekomendasikan assignment optimal berdasarkan sales proportion.

---

## 2.2 Hitung Adjusted Average per Artikel per Toko

### 2.2.1 Pivot: Artikel x Bulan per Toko

```
Dari data joined (step 2.1.3), buat pivot per toko:

Rows: KODEMIX (+ Gender, Series, Tier_Baru, Tipe dari master)
Columns: Bulan (Jan, Feb, Mar, ..., hingga bulan terakhir tersedia)
Values: Total_Qty

Contoh output untuk Zuma Galaxy Mall:
| KODEMIX   | Gender | Series  | Tier | Tipe    | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Avg |
|-----------|--------|---------|------|---------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| M1CA25    | Men    | Classic | T1   | Jepit   | 48  | 52  | 45  | 0   | 50  | 55  | 48  | 42  | 5   | ... |
| L2EA10    | Ladies | Elsa    | T1   | Fashion | 30  | 28  | 35  | 32  | 0   | 29  | 33  | 30  | 3   | ... |
```

### 2.2.2 Adjusted Average per Tier

Terapkan logic dari SKILL.md Section 1.5:

**Tier 1:**
```
bulan_nonzero = [bulan dimana qty > 0]
adjusted_avg = SUM(qty semua bulan) / COUNT(bulan_nonzero)

Alasan: 0 pada T1 = kemungkinan out of stock, bukan no demand
```

**Tier 8 (New Launch):**
```
1. Cari bulan pertama dengan qty > 0 (= bulan launch)
2. Semua bulan sebelum launch -> EXCLUDE (belum ada)
3. Bulan setelah launch dengan qty = 0 -> EXCLUDE (likely OOS)
4. adjusted_avg = SUM(qty bulan aktif) / COUNT(bulan aktif)
```

**Tier 2 & T3:**
```
Untuk setiap bulan dengan qty = 0:
  - Hitung avg bulan sekitar (N-1, N-2, N+1, N+2)
  - Jika avg sekitar > 50% dari overall avg artikel -> EXCLUDE (likely OOS)
  - Jika tren menurun gradual menuju 0 -> INCLUDE (genuine decline)
  
Jika ragu -> INCLUDE bulan 0 (lebih konservatif)
```

**Tier 4 & T5:**
```
adjusted_avg = SUM(semua bulan) / total_bulan_tersedia
Tidak ada exclusion -- 0 = memang slow/dead
```

### 2.2.3 Output: Ranked Article List per Gender-Type per Toko

```
Setelah hitung adjusted_avg, buat ranking per gender-type:

Untuk setiap toko, untuk setiap gender-type:
  1. Filter artikel by gender-type
  2. Sort by: Tier ASC (T1 first), lalu adjusted_avg DESC
  3. Assign display_priority: 1, 2, 3, ...

Contoh output Zuma Galaxy Mall -- Men Jepit:
| Rank | KODEMIX | Article Name      | Tier | Adj_Avg | Display_Priority |
|------|---------|-------------------|------|---------|-----------------|
| 1    | M1CA25  | Men Classic 25    | T1   | 50.5    | MUST DISPLAY    |
| 2    | M1CA30  | Men Classic 30    | T1   | 45.2    | MUST DISPLAY    |
| 3    | M1ST08  | Men Stripe 8      | T1   | 38.7    | MUST DISPLAY    |
| 4    | M1ON04  | Men Onyx 4        | T8   | 22.0    | PRIORITY        |
| 5    | M1CA31  | Men Classic 31    | T2   | 18.5    | FILL IF SLOT    |
| 6    | M1BS05  | Men Black Series 5| T3   | 8.2     | FILLER          |
| 7    | M1CA23  | Men Classic 23    | T4   | 2.1     | DO NOT DISPLAY  |
```

Ulangi untuk SEMUA gender-type:
- Men Jepit, Men Fashion
- Ladies Jepit, Ladies Fashion
- Baby & Kids (termasuk sub: Baby, Boys, Girls, Junior)
```

---

## 2.3 Hitung Slot Capacity dari Denah

### 2.3.1 Hook-based Components (Backwall & Gondola)

```
Untuk setiap Backwall/Gondola:
  
  Input: total_hooks (dari denah)
  
  Hitung kapasitas per mode:
  
  IF gender-type = Jepit:
    full_box_slots   = FLOOR(total_hooks / 2)    -- 2 hook per artikel
    compact_slots    = FLOOR(total_hooks / 1)     -- 1 hook per artikel
    
  IF gender-type = Fashion:
    full_box_slots   = FLOOR(total_hooks / 3)    -- 3 hook per artikel
    compact_slots    = FLOOR(total_hooks / 2)     -- 2 hook per artikel
```

### 2.3.2 Baby Components (Rak & Keranjang)

```
Rak Baby:
  full_slots_per_layer = 1 artikel (6 pairs)
  compact_slots_per_layer = 2 artikel (3 pairs each)
  total_full_slots = layers x 1
  total_compact_slots = layers x 2

Keranjang:
  slots = qty_keranjang x 1 artikel per keranjang (12 pairs each)
```

### 2.3.3 Table & VM Display

```
Table:
  slots = kapasitas table (variable per toko, dari denah)
  Khusus untuk: Luca, Luna, Airmove
  Storage impact: 1 box per artikel (11 pairs ke storage)

VM Display:
  slots = kapasitas VM (variable per toko, dari denah)
  Khusus untuk: Luca, Luna, Airmove  
  Storage impact: 1 box per artikel (10-11 pairs ke storage)
```

### 2.3.4 Compile Total Slot Summary per Toko

```
Output tabel:
| Component    | Type          | Gender_Type  | Mode     | Slots | Storage_Impact_per_Artikel |
|-------------|---------------|--------------|----------|-------|---------------------------|
| BW-1        | Backwall      | (TBD)        | Full     | 15    | 0                         |
| BW-1        | Backwall      | (TBD)        | Compact  | 30    | 6 pairs (jepit)           |
| GD-1        | Gondola       | (TBD)        | Full     | 8     | 0                         |
| GD-1        | Gondola       | (TBD)        | Compact  | 12    | 4 pairs (fashion)         |
| RK-1        | Rak Baby      | Baby & Kids  | Full     | 3     | 6 pairs                   |
| RK-1        | Rak Baby      | Baby & Kids  | Compact  | 6     | 9 pairs                   |
| KR-1 (x2)   | Keranjang     | Baby & Kids  | -        | 2     | 0                         |
| TB-1        | Table         | Luca/Luna/AM | -        | 4     | 11 pairs (~1 box)         |
| VM-1        | VM Display    | Luca/Luna/AM | -        | 2     | 10-11 pairs (~1 box)      |
```

---

## 2.4 Gender-Type Assignment ke Display Unit

### 2.4.1 Hitung Sales Proportion per Gender-Type

```
Dari data sales toko tersebut:
  1. Group by gender-type
  2. SUM adjusted_avg per group
  3. Hitung % share

Contoh:
| Gender-Type     | Total Adj_Avg | % Share | Rank |
|----------------|---------------|---------|------|
| Men Jepit       | 450           | 28%     | 1    |
| Ladies Fashion  | 380           | 24%     | 2    |
| Ladies Jepit    | 290           | 18%     | 3    |
| Men Fashion     | 200           | 13%     | 4    |
| Baby & Kids     | 170           | 11%     | 5    |
| Boys            | 50            | 3%      | 6    |
| Girls           | 35            | 2%      | 7    |
| Junior          | 20            | 1%      | 8    |
```

### 2.4.2 Assign Gender-Type ke Display Unit

```
Algorithm:
1. Sort display units by size (hooks) DESCENDING
2. Sort gender-types by sales share DESCENDING
3. Assign terbesar ke terbesar

Contoh:
  BW-1 (30 hooks) -> Men Jepit (28% share, rank 1)
  BW-2 (24 hooks) -> Ladies Fashion (24% share, rank 2)
  GD-1 (20 hooks) -> Ladies Jepit (18% share, rank 3)
  GD-2 (16 hooks) -> Men Fashion (13% share, rank 4)
  
  Baby & Kids -> ke Rak Baby + Keranjang + sisa Backwall/Gondola jika ada

Adjustments berdasarkan SPG insight (jika tersedia):
  - Hot zone (near entrance) -> gender-type rank 1 ATAU T8 new launch heavy
  - Adjacency: Men Jepit & Men Fashion berdekatan, Ladies Jepit & Ladies Fashion berdekatan
```

---

## 2.5 Article Assignment Algorithm

### 2.5.0 Pre-step: Assign Luca/Luna/Airmove

```
SEBELUM assign artikel lain, handle Luca/Luna/Airmove dulu:

1. Dari ranked list, filter artikel Luca, Luna, Airmove yang tier T1 atau T8
2. Cek ketersediaan display:
   a. Table slots tersedia? -> assign ke table (up to table capacity)
   b. VM Display tersedia? -> assign ke VM (up to VM capacity)
   c. Tidak ada table DAN tidak ada VM -> FLAG WARNING, artikel ini tidak bisa display
3. Hitung storage impact: setiap artikel = 1 box ke storage
4. Kurangi storage capacity tersedia

Output: 
  - Daftar Luca/Luna/Airmove yang di-display (+ di mana)
  - Daftar yang TIDAK bisa display (warning)
  - Sisa storage capacity setelah Luca/Luna/Airmove
```

### 2.5.1 Determine Display Mode per Unit

```
SEBELUM menghitung slots, FILTER OUT artikel yang tidak boleh di backwall/gondola:

EXCLUSION LIST (WAJIB diterapkan sebelum slot calculation):
  a. Luca/Luna/Airmove -> HANYA boleh di Table/VM (Section 1.3.7)
     Filter: artikel yang mengandung "LUCA", "LUNA", atau "AIRMOVE" di nama
     -> HAPUS dari candidate list backwall/gondola
     -> Jika toko TIDAK punya Table/VM -> artikel ini TIDAK BISA display sama sekali
     -> Flag warning

  b. Artikel yang sudah di-assign ke Rak Baby / Keranjang
     -> HAPUS dari candidate list backwall Baby & Kids
     -> Mencegah duplikasi: 1 artikel hanya boleh di 1 display unit
     -> PROSES: Assign Rak Baby & Keranjang DULU, baru assign backwall Baby

  c. T4/T5 -> JANGAN masukkan ke candidate list

Setelah exclusion, BARU lanjut ke slot calculation:

Untuk SETIAP Backwall/Gondola yang sudah di-assign gender-type:

1. Hitung artikel MUST DISPLAY (T1) + PRIORITY (T8) untuk gender-type tersebut
   -> count_must = jumlah T1 + T8

2. Hitung slots di full box mode
   -> slots_full = hooks / (2 jika jepit, 3 jika fashion)

3. Decision:
   IF count_must <= slots_full:
     -> Pakai FULL BOX MODE
     -> Sisa slots (slots_full - count_must) untuk T2/T3 filler
     
   ELSE IF count_must <= slots_compact:
     -> Pakai COMPACT MODE (atau MIX MODE)
     -> Hitung storage impact
     -> Validasi: storage impact + existing usage <= storage capacity?
       YES -> proceed compact
       NO  -> prioritas T1 by rank, potong T8 yang tidak muat, FLAG warning
     
   ELSE:
     -> Bahkan compact tidak cukup
     -> Assign by rank (highest adj_avg first) sampai slot habis
     -> Sisanya FLAG sebagai "T1 not displayed -- critical"
```

### 2.5.2 Mix Mode Optimization (lanjutan dari 2.5.1)

```
Jika compact mode diperlukan, pertimbangkan MIX MODE:

Strategy:
  - Top N artikel (highest adj_avg) -> FULL BOX (display tebal, no storage cost)
  - Sisanya -> COMPACT (save hooks, tapi makan storage)

Optimization:
  1. Start dengan semua FULL BOX
  2. Jika tidak muat -> convert artikel dengan adj_avg TERENDAH ke compact, satu per satu
  3. Repeat sampai semua must-display muat
  4. Setiap konversi, cek storage impact
  
Contoh:
  30 hooks fashion, 13 T1+T8 artikel:
  - All full: 30/3 = 10 slots -> 3 artikel tidak muat
  - Convert rank 11-13 ke compact: butuh (10x3) + (3x2) = 36 hooks -- masih over
  - Convert rank 8-13 ke compact: (7x3) + (6x2) = 21+12 = 33 hooks -- masih over
  - Convert rank 5-13 ke compact: (4x3) + (9x2) = 12+18 = 30 hooks [OK]
  - Storage impact: 9 x 4 pairs = 36 pairs = 3 box equivalent
```

### 2.5.3 Fill Remaining Slots

```
Setelah T1 dan T8 di-assign:

1. Hitung sisa slots
2. Dari ranked list, ambil T2 berikutnya (by adj_avg descending)
3. Jika T2 habis, ambil T3
4. JANGAN ambil T4/T5
5. Jika semua T2/T3 habis dan masih ada slot -> biarkan kosong, flag "available slot"

Setiap artikel filler yang masuk: tentukan full/compact mode
  - Default FULL BOX (hemat storage)
  - Compact hanya jika perlu squeeze lebih banyak variety
```

### 2.5.4 Baby & Kids Assignment

```
1. Rank semua baby articles by adjusted avg (sudah dari step 2.2.3)
2. Assign ke rak baby:
   - Full mode: 1 artikel per layer
   - Compact mode: 2 artikel per layer (jika eligible > full slots)
3. Assign ke keranjang: 1 artikel per keranjang (12 pairs)
4. Sisa baby yang tidak muat di rak/keranjang:
   -> Masuk ke Backwall/Gondola yang di-assign "Baby & Kids"
   -> Ikut hook rules standar (full/compact mode per tipe artikel)
```

---

## 2.6 Storage Allocation

### 2.6.1 Hitung Storage Terpakai

```
storage_used = 0

# 1. Luca/Luna/Airmove (dari step 2.5.0)
storage_used += count_luca_luna_airmove_displayed x 1 box

# 2. Compact mode overflow (dari step 2.5.1-2.5.4)
compact_pairs_total = 0
FOR each artikel in compact mode:
  IF tipe == "Jepit":    compact_pairs_total += 6
  IF tipe == "Fashion":  compact_pairs_total += 4
  IF type == "Rak Baby": compact_pairs_total += 9   # (jika compact rak)
  IF type == "Rak Baby": compact_pairs_total += 6   # (jika full rak, sisa 1/2 box)
  
storage_used += CEIL(compact_pairs_total / 12)   # konversi ke box equivalent

# 3. Sisa storage tersedia
storage_remaining = storage_capacity - storage_used
```

### 2.6.2 Alokasi Storage Tambahan

```
IF storage_remaining > 0:
  
  # Eligible articles untuk storage tambahan:
  eligible = [artikel T1 dan T8 yang sedang di-display]
  
  # Hitung share proporsional
  total_sales_eligible = SUM(adj_avg semua eligible)
  
  FOR each artikel in eligible (sorted by adj_avg DESC):
    box_allocation = MAX(1, ROUND(storage_remaining x (adj_avg / total_sales_eligible)))
    assign box_allocation ke artikel
    
  # Validasi: total allocated <= storage_remaining
  # Jika over -> trim dari artikel dengan adj_avg terendah
  
ELSE:
  FLAG: "Storage penuh -- tidak ada alokasi tambahan"
  FLAG: "Pertimbangkan kurangi compact mode atau Luca/Luna/Airmove"
```

### 2.6.3 Rules Recap

```
Boleh di storage:
  - Luca/Luna/Airmove backup (WAJIB)
  - Compact mode overflow (otomatis)
  - T1 fast moving backup (proporsional)
  - T8 backup (proporsional, termasuk T8 yang belum di-display untuk rotation)
  
TIDAK BOLEH di storage:
  - T4 / T5
  - Non-T8 yang TIDAK di display (tidak boleh ada stok tanpa display kecuali T8)
```

---

## 2.9 Checklist Sebelum Finalisasi

```
Sebelum menyerahkan output planogram, VALIDASI:

[ ] Semua T1 ada di display? (jika tidak -> harus ada alasan + flag)
[ ] Tidak ada T4/T5 di display?
[ ] Luca/Luna/Airmove hanya di Table/VM? (bukan di hook biasa)
[ ] 1 display unit = 1 gender-type? (tidak campur)
[ ] Storage tidak exceed capacity?
[ ] Compact mode storage impact sudah dihitung?
[ ] Total hooks used <= total hooks available?
[ ] Semua flags/warnings sudah dilaporkan?
[ ] Summary report lengkap (utilization, coverage, tier distribution)?
```

---

# SECTION 3: IMPLEMENTATION REFERENCE & AI AGENT GOTCHAS

## 3.1 Reference Implementation

File `build_royal_planogram.py` di folder yang sama berisi working implementation yang sudah diverifikasi. Gunakan sebagai reference untuk membangun planogram toko lain.

**Cara menggunakan sebagai template:**
1. Copy script, ganti CONFIG section (STORE_NAME, BACKWALLS, RAK_BABY, STORAGE_CAPACITY, dll)
2. Denah toko ambil dari `Data Option By Region.xlsx` -- sheet sesuai region, kolom sesuai toko
3. Jalankan script -> output XLSX otomatis

**CONFIG yang harus diganti per toko:**
```python
STORE_NAME = "Zuma [Nama Toko]"        # Nama toko persis seperti di DB
DB_STORE_NAME = "Zuma [Nama Toko]"     # Untuk query matched_store_name
STORAGE_CAPACITY = N                    # 0 jika tidak punya storage
BACKWALLS = [                           # Dari denah toko
    {"id": "BW-1", "hooks": XX},
    {"id": "BW-2", "hooks": XX},
    # ... dst sesuai jumlah backwall
]
# Tambahkan sesuai ketersediaan:
GONDOLAS = [{"id": "GD-1", "hooks": XX}]  # Jika ada
RAK_BABY = {"layers": N, "pairs_per_layer": 6}  # Jika ada
KERANJANG_QTY = N                       # Jika ada
TABLE_CAPACITY = N                      # Jika ada (untuk Luca/Luna/Airmove)
VM_CAPACITY = N                         # Jika ada (untuk Luca/Luna/Airmove)
DATE_START = "YYYY-MM-DD"              # 12 bulan kebelakang
DATE_END = "YYYY-MM-DD"                # Bulan terakhir
```

**Script logic flow (generic):**
```
1. pull_data()        -> Query core.sales_with_product + core.stock_with_product dari VPS DB
2. process_sales()    -> Clean data, rename columns, filter non-products
3. compute_adjusted_avg() -> Hitung adjusted avg per tier rules (Section 1.4.2)
4. compute_gender_shares() -> Map gender+tipe ke gender_type, hitung sales share %
5. assign_rak_baby()  -> Assign baby articles ke rak DULU (untuk dedup)
6. assign_gender_to_backwalls() -> Biggest backwall -> highest share gender-type
7. assign_articles()  -> Per backwall: exclude Luca/Luna/Airmove, exclude rak baby articles,
                         then T1 first -> T8 -> T2 -> T3, sorted by adj_avg desc
8. generate_xlsx()    -> Multi-sheet output matching example format
```

## 3.2 AI Agent Gotchas (Learned from Implementation)

Daftar masalah yang PASTI akan ditemui oleh AI agent saat implementasi. Baca ini SEBELUM mulai coding.

### 3.2.1 Data Source Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Core views sudah enriched** | `core.sales_with_product` sudah include kode_mix, article, gender, series, tipe, tier. TIDAK perlu manual join ke portal.kodemix | Skip Steps 2.1.2-2.1.3. Langsung query core view |
| **Column naming mismatch** | Core view punya `tipe` dan `tier`, tapi skill conventions pakai `tipe` dan `tier_baru` | Rename di code: `tier` -> `tier_baru` setelah query |
| **matched_store_name format** | Di core view, store name sudah di-normalize. Filter dengan `TRIM(LOWER('Zuma Nama Toko'))` | Jangan pakai `nama_departemen` langsung, pakai `matched_store_name` |
| **is_intercompany** | Kolom ini bisa NULL atau FALSE. Keduanya = bukan intercompany | `WHERE (is_intercompany IS NULL OR is_intercompany = FALSE)` |
| **~6% unmatched rows** | Beberapa sales rows punya `kode_mix = NULL` (tidak match di master) | Filter out, log count sebagai INFO |

### 3.2.2 Processing Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Luca/Luna/Airmove di backwall** | Script yang naif akan memasukkan Luca/Luna/Airmove ke backwall candidate list | WAJIB filter out SEBELUM assign_articles: `not any(p in article for p in ["LUCA", "LUNA", "AIRMOVE"])` |
| **Rak Baby duplikasi** | Jika Baby & Kids punya backwall DAN rak baby, artikel top akan muncul di KEDUANYA | Assign Rak Baby DULU, simpan nama artikelnya, exclude dari backwall candidate |
| **Baby & Kids = umbrella** | Gender "BABY" di DB = Baby & Kids. Tapi "BOYS", "GIRLS", "JUNIOR" = SEPARATE gender-types | Gender-type mapping: BABY->"Baby & Kids", BOYS->"Boys", GIRLS->"Girls", JUNIOR->"Junior" |
| **Non-product items in sales** | Sales data include SHOPPING BAG, HANGER, PAPER BAG, THERMAL, BOX LUCA | Filter out by article name pattern matching |
| **Tier NULL** | Beberapa artikel punya tier = NULL di DB | Default ke "3" (Tertiary) -- konservatif |
| **Gender NULL/UNKNOWN** | Beberapa rows punya gender = NULL | Exclude dari planogram (cannot assign to gender-type) |

### 3.2.3 Assignment Logic Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Limited backwalls < gender-types** | Toko kecil punya 3-4 backwall tapi 8 gender-types exist | Top N gender-types by sales share get display. Sisanya = WARNING, bukan error |
| **Storage=0 blocks compact mode** | Compact mode overflow pairs BUTUH storage. No storage = no compact | Force Full Box Mode only. Flag di output |
| **Storage=0 blocks Luca/Luna/Airmove** | Bahkan dengan Table/VM, Luca/Luna/Airmove butuh storage untuk backup | Exclude Luca/Luna/Airmove entirely jika storage=0 |
| **All T1 might not fit** | Jika T1 count > available slots DAN no compact mode (no storage) | Display by adj_avg rank. Flag T1 yang tidak muat sebagai CRITICAL |

### 3.2.4 Output & Environment Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Windows encoding (cp1252)** | Print statements dengan unicode chars (arrows, checkmarks, emojis) crash on Windows | Use ASCII only: `->` bukan `->`, `[OK]` bukan checkmark |
| **pandas + psycopg2 warning** | `pd.read_sql()` with raw psycopg2 connection shows deprecation warning | Ignore (works fine) atau use SQLAlchemy engine |
| **openpyxl sheet name limit** | Excel sheet names max 31 chars | Truncate: `sheet_name[:31]` |
| **pandas groupby.apply deprecation** | `DataFrameGroupBy.apply` warning about grouping columns | Add `include_groups=False` or restructure with manual loop |

## 3.3 Execution Order (CRITICAL)

Urutan eksekusi ini WAJIB diikuti. Salah urutan = data corruption.

```
CORRECT ORDER:
  1. Pull data from DB
  2. Process & clean sales data
  3. Compute adjusted averages per tier
  4. Map gender-types & compute sales shares
  5. Assign Rak Baby & Keranjang FIRST       <- PENTING: ini SEBELUM backwall
  6. Assign Luca/Luna/Airmove to Table/VM    <- PENTING: ini SEBELUM backwall
  7. Assign gender-types to backwalls/gondolas
  8. Assign articles to backwalls/gondolas    <- Exclude rak baby + Luca/Luna/Airmove articles
  9. Allocate storage
  10. Generate XLSX output
  11. Validate against checklist (Section 2.9)

WRONG ORDER (will cause bugs):
  [X] Assign backwall BEFORE rak baby -> duplikasi
  [X] Assign articles BEFORE excluding Luca/Luna/Airmove -> rule violation
  [X] Allocate storage BEFORE knowing compact mode usage -> wrong calculation
```

## 3.4 Validation Checklist (Extended from Section 2.9)

Selain checklist di Section 2.9, tambahkan validasi berikut:

```
SECTION 2.9 ORIGINAL:
  [ ] Semua T1 ada di display? (per assigned gender-type)
  [ ] Tidak ada T4/T5 di display?
  [ ] Luca/Luna/Airmove hanya di Table/VM?
  [ ] 1 display unit = 1 gender-type?
  [ ] Storage tidak exceed capacity?
  [ ] Compact mode storage impact sudah dihitung?
  [ ] Total hooks used <= total hooks available?
  [ ] Semua flags/warnings sudah dilaporkan?
  [ ] Summary report lengkap?

ADDITIONAL (from implementation experience):
  [ ] Luca/Luna/Airmove EXCLUDED dari backwall candidate list? (bukan cuma "not assigned")
  [ ] Rak Baby articles EXCLUDED dari backwall Baby candidate list? (no duplication)
  [ ] Gender-types tanpa display unit di-FLAG sebagai WARNING?
  [ ] Storage=0 -> compact mode disabled?
  [ ] Storage=0 -> Luca/Luna/Airmove excluded entirely?
  [ ] is_intercompany transactions excluded from sales data?
  [ ] Non-product items (SHOPPING BAG, HANGER, etc.) excluded?
  [ ] All print/output uses ASCII only (no unicode arrows/symbols)?
```
