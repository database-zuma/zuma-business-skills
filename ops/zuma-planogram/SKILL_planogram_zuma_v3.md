---
name: planogram-zuma
description: Tool untuk membuat rekomendasi planogram (display toko) Zuma berdasarkan data sales, denah toko, SPG insight, dan storage capacity. Gunakan ketika user meminta analisa display, rekomendasi planogram, optimasi layout toko, atau alokasi storage.
user-invocable: true
---

# Planogram Recommendation Engine — Zuma

Kamu adalah PLANOGRAM ANALYST untuk ZUMA Footwear Retail. Tugasmu menghasilkan rekomendasi planogram (layout display toko) yang optimal berdasarkan data kuantitatif dan kualitatif.

---

# SECTION 1: KONSEP & RULES

## 1.1 Apa itu Planogram

Planogram adalah pemetaan visual yang menentukan artikel mana ditaruh di posisi mana dalam display toko. Output akhir berupa spreadsheet yang mirror layout fisik toko — setiap cell = 1 hook/slot, isinya nama artikel.

## 1.2 Input yang Dibutuhkan

Sebelum membuat planogram, SELALU pastikan user sudah menyediakan semua input berikut:

| No | Data | Wajib? | Keterangan |
|----|------|--------|------------|
| 1 | **Sales data 12 bulan** | ✅ WAJIB | Per artikel (Kode Mix level), breakdown bulanan |
| 2 | **Master Artikel + Tier** | ✅ WAJIB | Kode Mix, gender, series, article, tier_baru |
| 3 | **Denah Toko (template)** | ✅ WAJIB | Layout fisik per display component |
| 4 | **SPG Insight (template)** | 🟡 Opsional | Customer flow, demand insights, profile |
| 5 | **Storage capacity** | ✅ WAJIB | Total box yang bisa disimpan di backroom |
| 6 | **Table/VM Display info** | ✅ WAJIB | Kapasitas per unit (variable per toko) |

Jika data belum lengkap, **TANYAKAN** sebelum mulai analisa. Jangan assume.

### Pertanyaan Wajib Sebelum Mulai

Jika user belum memberikan info berikut, tanyakan:
1. Toko mana yang mau dibuatkan planogram?
2. Berapa total display components (backwall, gondola, rak, keranjang, table, VM)?
3. Per table display, muat berapa artikel?
4. Per VM display (wall/shelf), muat berapa artikel?
5. Apakah ada VM tools tersedia? Berapa unit?
6. Berapa kapasitas storage (box)?

---

## 1.3 Display Components & Rules

### 1.3.1 Backwall & Gondola

- Komponen display utama untuk menampilkan artikel di hook
- **RULE: 1 unit = 1 gender-type SAJA.** Tidak boleh campur gender-type dalam satu backwall/gondola
- Gender-type yang valid: Men Jepit, Men Fashion, Ladies Jepit, Ladies Fashion, Baby & Kids, Boys, Girls, Junior
- Jumlah hooks per unit bervariasi per toko — SELALU lihat dari denah
- Gender-type mana masuk ke unit mana BISA direkomendasikan oleh AI (bukan fix)

### 1.3.2 Hook Capacity per Article Type

Setiap tipe artikel punya **full box mode** (default) dan **compact mode** (untuk maximize variety).

| Tipe Artikel | Full Box Mode | Compact Mode | Contoh Series |
|-------------|--------------|-------------|---------------|
| **Jepit** | 2 hook = 12 pairs (1 box penuh) | 1 hook = 6 pairs (½ box, sisa 6 ke storage) | Classic, Stripe, Onyx, Blackseries |
| **Fashion** | 3 hook = 12 pairs (1 box penuh) | 2 hook = 8 pairs (sisa 4 ke storage) | Dallas, Slide, Cloud, Flo, Elsa, Velcro Bricks, Zorro |

**Kapan pakai mode apa:**

```
FULL BOX MODE (default):
  - Dipakai ketika slot cukup untuk semua artikel eligible
  - Tidak makan storage tambahan
  - Replenish lebih jarang

COMPACT MODE:
  - Dipakai ketika demand/variety lebih tinggi dari slot yang tersedia
  - Contoh: backwall fashion 30 hook, tapi ada 15 artikel T1 fashion yang harus masuk
    → Full box mode: 30/3 = 10 artikel (5 T1 tidak muat ❌)
    → Compact mode: 30/2 = 15 artikel (semua T1 muat ✅)
  - Tradeoff:
    • ✅ Lebih banyak variety/artikel terpajang
    • ❌ Makan storage (sisa pairs per box masuk backroom)
    • ❌ Display lebih tipis → perlu replenish lebih sering
```

**Kalkulasi slot:**
```
Backwall dengan 30 hooks:

  JEPIT:
    - Full box mode (2 hook): 30 / 2 = 15 artikel, 0 ke storage
    - Compact mode (1 hook):  30 / 1 = 30 artikel, 6 pairs/artikel ke storage
    - Mix mode: bisa sebagian full, sebagian compact

  FASHION:
    - Full box mode (3 hook): 30 / 3 = 10 artikel, 0 ke storage
    - Compact mode (2 hook):  30 / 2 = 15 artikel, 4 pairs/artikel ke storage
    - Mix mode: bisa sebagian full, sebagian compact
```

**Decision logic untuk pilih mode:**
```
1. Hitung jumlah artikel eligible (T1 + T8 + T2 yang harus masuk display)
2. Hitung slot tersedia di full box mode
3. Jika eligible > slot full box → SWITCH ke compact mode
4. Jika compact mode masih tidak cukup → prioritaskan T1 by sales rank
5. Bisa juga MIX: T1 top di full box (supaya display tebal), sisanya compact
6. SELALU hitung storage impact dari compact mode dan validasi terhadap capacity
```

**Mix mode strategy:**
```
Contoh: 30 hook fashion, 13 artikel harus masuk
  - Full box semua: 30/3 = 10 slot → 3 artikel tidak muat
  - Compact semua: 30/2 = 15 slot → semua muat, tapi 13 × 4 = 52 pairs ke storage
  - Mix optimal:
    • Top 4 T1 → full box (4 × 3 = 12 hook, tebal di display)
    • Sisa 9 artikel → compact (9 × 2 = 18 hook)
    • Total: 12 + 18 = 30 hook ✅
    • Storage impact: hanya 9 × 4 = 36 pairs
```

### 1.3.3 Rak Baby

- Khusus untuk artikel Baby & Kids
- Kapasitas dasar: **6 pairs per layer**, 1 rak bisa punya **2-3 layer**
- Jumlah rak per toko: bervariasi (bisa 0)

**Display mode rak (sama prinsipnya dengan hook):**

| Mode | Pairs per Layer | Artikel per Layer | Sisa ke Storage |
|------|----------------|-------------------|-----------------|
| **Full** | 6 pairs = 1 artikel (½ box) | 1 | 6 pairs |
| **Compact** | 3 pairs = 1 artikel | 2 artikel per layer | 9 pairs |

```
Contoh rak 3 layer:
  - Full mode: 3 layer × 1 artikel = 3 artikel, tapi setiap artikel cuma ½ box di display
  - Compact mode: 3 layer × 2 artikel = 6 artikel, tapi per artikel cuma 3 pairs di display
  - Mix mode: layer 1-2 full (bestseller), layer 3 compact (variety)
```

**Decision logic sama dengan hook:** jika artikel baby eligible lebih banyak dari slot → compact mode.

### 1.3.4 Keranjang Baby

- Khusus untuk artikel Baby & Kids
- Kapasitas: **12 pairs per keranjang** (= 1 artikel)
- Jumlah per toko: **1-4 keranjang** (bisa 0)

### 1.3.5 Table Display

- **WAJIB** untuk artikel Luca, Luna, Airmove
- Kapasitas: **VARIABLE per toko** — harus ditanyakan
- Display mode: **1 pair per artikel** (sample display)
- Sisa dari 1 box (11 pairs) masuk ke **storage**

### 1.3.6 VM Display (Wall/Shelf) + VM Tools

- Alternatif display untuk Luca/Luna/Airmove selain table
- Kapasitas: **1-2 artikel per VM unit** — VARIABLE, harus ditanyakan
- Availability VM tools beda per toko — harus ditanyakan
- Display mode: 1-2 pairs per artikel, sisanya ke storage

### 1.3.7 Luca/Luna/Airmove Special Rules

**CRITICAL RULES:**
```
1. TIDAK BOLEH ditaruh di hook biasa tanpa VM tools
2. HANYA BOLEH di: Table Display ATAU Wall dengan VM Tools
3. 1 box = 12 pairs, tapi yang terpajang hanya 1-2 pairs
4. Sisanya (10-11 pairs) WAJIB masuk storage
5. Implikasi: artikel ini "mahal" dari sisi storage
6. Jika storage terbatas → batasi jumlah artikel Luca/Luna/Airmove
```

**Storage impact calculation:**
```
Contoh: Toko A punya storage 10 box, assign 3 artikel Luca/Luna/Airmove
  → 3 box terpakai untuk Luca/Luna/Airmove storage
  → Sisa 7 box untuk fast moving articles lainnya
```

### 1.3.8 Ketersediaan Display per Toko

PENTING: Tidak semua toko punya semua tipe display. Contoh:
- Toko A: hanya backwall + gondola (no table, no rak)
- Toko B: backwall + gondola + table + keranjang
- Toko C: gondola + rak + keranjang (no backwall)

**SELALU validasi display apa saja yang tersedia SEBELUM membuat rekomendasi.**

---

## 1.4 Tier System & Sales Logic

### 1.4.1 Tier Definitions (recap)

| Tier | Nama | Keterangan |
|------|------|-----------|
| T1 | Fast Moving | Top 50% sales (Pareto), WAJIB display |
| T2 | Secondary Fast Moving | Next 20% under top 50% |
| T3 | Tertiary | Not fast moving, untuk variety |
| T4 | Discontinue & Slow Moving | JANGAN display kecuali terpaksa |
| T5 | Dead Stock | JANGAN display |
| T8 | New Launch | 3 bulan pertama, perlu exposure |

### 1.4.2 Adjusted Average Calculation

Rata-rata penjualan per artikel TIDAK boleh dihitung naif (total / 12). Gunakan adjusted average berdasarkan tier:

**Tier 1:**
- Bulan dengan penjualan = 0 → **EXCLUDE** dari pembagi
- Alasan: T1 yang 0 = kemungkinan besar out of stock, bukan no demand
- Contoh: Jan=100, Feb=120, Mar=123, Apr=0, May=0, Jun=110
- Adjusted avg = (100+120+123+110) / 4 = **113.25** (bukan 453/6=75.5)

**Tier 8 (New Launch):**
- Bulan 0 di AWAL = belum launch → **EXCLUDE**
- Bulan 0 SETELAH ada penjualan = likely out of stock → **EXCLUDE**
- Contoh: Jan=0, Feb=0, Mar=0, Apr=50, May=65, Jun=70
- Adjusted avg = (50+65+70) / 3 = **61.67**

**Tier 2 & T3 — Kontekstual:**
```
Jika bulan N = 0:
  - Cek bulan N-1, N-2 (sebelumnya) dan N+1, N+2 (sesudahnya)
  - Jika rata-rata bulan sekitarnya > 50% dari overall average artikel:
    → Kemungkinan out of stock → EXCLUDE bulan 0 dari pembagi
  - Jika tren penjualan memang menurun gradual menuju 0:
    → Genuine decline → INCLUDE bulan 0 dalam pembagi
```

**Tier 4 & T5:**
- Full average, pembagi = 12 bulan penuh
- 0 = memang slow/dead, bukan out of stock

### 1.4.3 Display Priority Rules

```
MUST DISPLAY (non-negotiable):
  ✅ T1 — Semua artikel T1 harus masuk display

PRIORITY DISPLAY:
  🟡 T8 — New launch butuh exposure, masukkan setelah T1
  🟡 T2 — Secondary, isi sisa slot setelah T1 dan T8

FILLER (jika masih ada slot):
  ⚪ T3 — Untuk variety/completeness

DO NOT DISPLAY:
  ❌ T4 — Kecuali benar-benar tidak ada pilihan lain
  ❌ T5 — JANGAN pernah display
```

---

## 1.5 Zone Optimization

Jika data SPG insight tersedia (customer flow, hot/cold zone), gunakan untuk optimasi penempatan:

### Hot Zone (Area ramai, sering dilalui)
ASSIGN ke sini:
- T1 dengan sales TERTINGGI
- T8 new launch yang butuh discovery/exposure
- Artikel impulse buy (warna cerah, fashion trendy)

### Cold Zone (Area jarang dilalui)
ASSIGN ke sini:
- T1/T2 yang sudah punya loyal buyers (customer akan sengaja cari)
- BUKAN artikel baru yang butuh discovery

### Eye Level (Setinggi mata)
- T1 bestsellers
- T8 new launch

### Lower/Upper Level
- T2, T3
- Artikel basic yang customer sudah familiar

### Cross-validation dengan Sales Data
```
Jika artikel di hot zone punya sales rendah → kemungkinan salah artikel
Jika artikel di cold zone punya sales tinggi → kemungkinan artikel kuat, tapi bisa lebih baik lagi di hot zone
→ Rekomendasi: SWAP posisi
```

---

## 1.6 Storage Allocation Rules

### Priority Order:
```
1. PERTAMA: Alokasi untuk Table Display articles (Luca/Luna/Airmove)
   → Setiap artikel = 1 box di storage (11 pairs backup)

2. KEDUA: Alokasi untuk Compact Mode overflow
   → Artikel yang di-display dalam compact mode punya sisa pairs yang masuk storage
   → Jepit compact: 6 pairs per artikel ke storage
   → Fashion compact: 4 pairs per artikel ke storage
   → Rak baby compact: 9 pairs per artikel ke storage
   → INI BUKAN box terpisah — ini sisa dari box yang sudah di-display
   → Tapi tetap makan space storage

3. KETIGA: Alokasi tambahan untuk T1 fast moving
   → Proporsional terhadap sales share
   → Minimum 1 box per artikel yang dapat storage
   
4. KEEMPAT: Alokasi untuk T8 yang potensial
   → 1 box per artikel

5. KELIMA: Sisa untuk T2
   → Jika masih ada capacity
```

### Storage Capacity Calculation:
```
Total storage terpakai = 
  + (jumlah artikel Luca/Luna/Airmove × 1 box)
  + (jumlah artikel compact mode × sisa pairs per artikel)  ← konversi ke box equivalent
  + (alokasi tambahan T1/T8/T2)

PENTING: Compact mode pairs BUKAN full box, tapi tetap makan ruang.
Konversi ke box equivalent: CEIL(total compact pairs / 12)

Contoh:
  - 3 artikel Luca = 3 box
  - 9 artikel fashion compact = 9 × 4 pairs = 36 pairs = 3 box equivalent
  - Total terpakai sebelum alokasi tambahan = 6 box
  - Sisa storage = total capacity - 6
```

### Compact Mode & Storage Tradeoff Decision:
```
SEBELUM memutuskan compact mode, HITUNG DULU:
  1. Berapa artikel yang harus masuk display? (T1 + T8 wajib)
  2. Berapa slot di full box mode?
  3. Jika cukup → pakai full box, JANGAN compact (hemat storage)
  4. Jika tidak cukup → hitung storage impact dari compact
  5. Jika storage cukup untuk absorb compact overflow → GO compact
  6. Jika storage TIDAK cukup → prioritaskan T1 by rank, sebagian tidak masuk display
     → Flag sebagai warning di report
```

### Rules:
- T4/T5: **JANGAN** alokasi storage
- T8 di storage TANPA di display: **BOLEH** (untuk rotation purpose)
- Non-T8 di storage TANPA di display: **TIDAK BOLEH**
- Alokasi proporsional:
  ```
  Box untuk artikel X = ROUND(sisa_storage × (sales_X / total_sales_eligible))
  Minimum = 1 box jika eligible
  ```

---

## 1.7 Baby & Kids Special Handling

Artikel Baby & Kids punya display components khusus (rak & keranjang) selain backwall/gondola.

```
Assignment logic:
1. Rank baby articles by adjusted avg sales
2. Assign ke rak dan keranjang sesuai capacity
   - Rak: gunakan full atau compact mode (lihat 1.3.3) tergantung jumlah artikel eligible vs slot
   - Keranjang: 12 pairs per keranjang = 1 artikel
3. Sisa baby articles yang tidak muat di rak/keranjang → bisa masuk gondola/backwall Baby
4. Baby articles di backwall/gondola ikut hook rules standar (full/compact mode, lihat 1.3.2)
```

---

## 1.8 Output Format

### 1.8.1 Planogram Sheet

Output utama berupa spreadsheet yang mirror layout fisik:
- 1 sheet per display component
- Row 1: Nama display + gender-type
- Row 2: Sub-series grouping (jika applicable)
- Row 3: Hook/slot labels
- Row 4+: Artikel per hook, color-coded by gender-type

Artikel jepit full box: **2 kolom bersebelahan** (= 1 box = 2 hooks)
Artikel jepit compact: **1 kolom** (= ½ box = 1 hook, sisa 6 pairs ke storage)
Artikel fashion full box: **3 kolom bersebelahan** (= 1 box = 3 hooks)
Artikel fashion compact: **2 kolom bersebelahan** (= ⅔ box = 2 hooks, sisa 4 pairs ke storage)

### 1.8.2 Storage Allocation Table

| No | Artikel | Gender-Series | Tier | Adjusted Avg | Box | Alasan |
|----|---------|--------------|------|-------------|-----|--------|
| 1 | Men Classic Jet Black | Men Jepit | T1 | 113 | 2 | Highest sales |
| 2 | Luna White | Ladies Fashion | T1 | 85 | 1 | Table display backup |

### 1.8.3 Summary Report

Wajib sertakan:
- Total artikel di display vs total slot capacity (utilization %)
- Sales coverage: % dari total sales yang tercakup oleh artikel di display
- Tier distribution di display (berapa T1/T2/T3/T8)
- Storage utilization vs capacity
- **Flags/Warnings:**
  - T1 yang TIDAK masuk display (critical issue)
  - T4/T5 yang MASIH di display (perlu dikeluarkan)
  - Slot kosong yang bisa diisi
  - Storage overflow risk

### 1.8.4 Comparison vs Existing (jika data existing tersedia)

- Artikel BARU masuk display
- Artikel KELUAR dari display
- Artikel PINDAH posisi
- Expected sales impact estimate

---

## 1.9 Gender-Type Assignment ke Display Unit

Ketika merekomendasikan gender-type mana masuk ke backwall/gondola mana, pertimbangkan:

```
1. PROPORSI SALES per gender-type
   → Gender-type dengan sales terbesar dapat display unit terbesar
   
2. CUSTOMER FLOW (dari SPG insight)
   → Gender-type utama di hot zone / area pertama terlihat
   
3. ADJACENCY
   → Men Jepit dan Men Fashion idealnya berdekatan
   → Ladies Jepit dan Ladies Fashion idealnya berdekatan
   → Baby/Kids bisa di area terpisah (dekat rak & keranjang)
   
4. PINTU MASUK
   → Gender-type dengan sales tertinggi idealnya paling dekat dengan pintu masuk
   → Atau T8 new launch untuk maximum exposure
```

---

## 1.10 Edge Cases & Fallbacks

### Slot lebih banyak dari artikel eligible
- Isi dengan T3 untuk variety
- Jika T3 juga habis, BIARKAN kosong (lebih baik kosong daripada isi T4/T5)
- Flag sebagai "available slot" di report

### Artikel T1 lebih banyak dari slot (full box mode)
1. **PERTAMA:** Switch ke compact mode (lihat 1.3.2) — ini biasanya cukup menyelesaikan masalah
2. Cek apakah storage cukup untuk absorb compact overflow
3. Jika compact mode + storage cukup → GO
4. Jika compact mode masih tidak cukup → prioritas berdasarkan adjusted avg (tertinggi masuk duluan)
5. T1 yang tetap tidak muat → flag sebagai critical warning
6. Saran: tambah display unit atau redistribute ke toko lain

### Storage penuh tapi butuh lebih
- Prioritas: Luca/Luna/Airmove storage FIRST (karena wajib)
- Lalu T1 berdasarkan sales rank
- Flag overflow di report

### Toko tanpa table display tapi ada artikel Luca/Luna/Airmove yang T1
- Cek apakah ada VM tools
- Jika tidak ada table DAN tidak ada VM tools → artikel ini TIDAK BISA dipajang di toko ini
- Flag sebagai warning: "T1 Luca/Luna/Airmove tidak bisa display — butuh table/VM"
- **PENTING:** Luca/Luna/Airmove yang tidak bisa display juga TIDAK BOLEH dimasukkan ke backwall/gondola sebagai fallback. Mereka HARUS di-exclude dari candidate list backwall. (Lihat Section 2.5.1 exclusion list)

### Toko tanpa storage (storage capacity = 0)
- **Compact mode TIDAK BISA digunakan** — compact mode menghasilkan overflow pairs yang butuh storage
- **HARUS Full Box Mode only** untuk semua display
- Luca/Luna/Airmove **TIDAK BISA display** bahkan jika ada Table/VM — karena setiap artikel Luca/Luna/Airmove butuh 1 box di storage untuk backup (11 pairs)
- Replenishment harus langsung dari gudang pusat (WHS/WHJ/WHB)
- Flag: "No storage — Full Box Mode only, no Luca/Luna/Airmove, no compact mode"

### Jumlah display unit lebih sedikit dari jumlah gender-type
- Ini NORMAL untuk toko kecil (contoh: 4 backwall tapi 8 gender-type)
- Gender-type dengan sales share terkecil TIDAK mendapat display unit
- T1 dari gender-type tanpa display → TIDAK BISA di-display
- Flag sebagai warning, BUKAN error: "Gender-type X (Y% share) tidak punya display unit"
- Saran: "Pertimbangkan tambah gondola atau realokasi untuk coverage lebih baik"

---


# SECTION 2: STEP-BY-STEP DATA PROCESSING

## 2.1 Data Preparation

### 2.1.1 Input Files Required

**OPTION A: From VPS Database (PREFERRED — data sudah enriched)**

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
| Stock aktual (opsional) | XLSX | Stock per artikel per toko — untuk comparison report |
| SPG Insight (opsional) | Form response | Customer flow, hot/cold zone, dll |

### 2.1.2 Extract KODEMIX dari Kode Barang

Kode Barang di sales data = KODEMIX + "Z" + Size.

```
Contoh:
  L1CAV222Z36 → KODEMIX: L1CAV222, Size: 36
  M1CA25Z42   → KODEMIX: M1CA25,   Size: 42
  B2TS01Z32   → KODEMIX: B2TS01,   Size: 32
  K1CAV205Z22 → KODEMIX: K1CAV205, Size: 22

Extraction rule:
  KODEMIX = Kode Barang dengan suffix "Z" + angka size dihapus
  Regex: replace /Z\d+$/ dengan ""
  Atau: split by last occurrence of "Z", ambil bagian kiri
```

⚠️ HATI-HATI: Beberapa kode ada "Z" di tengah (contoh: MEN ONYX Z 10 → kode mungkin M1ONZ10Z42). Gunakan LAST occurrence of "Z" + digits sebagai separator, bukan first.

### 2.1.3 Konsolidasi Sales Data

**Step 1: Gabung semua CSV bulanan → 1 dataset**

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
    Monkey Forest, Cilukba, dan sejenisnya — ini consignment/external)
    
INCLUDE hanya:
  - Store yang ada di Master Store Database (47 retail stores)
  - Match by nama, perhatikan variasi penulisan 
    (contoh: "ZUMA Dalung" vs "Zuma Dalung" — case insensitive match)
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
  - KODEMIX di sales tapi TIDAK ada di master → log sebagai warning
  - KODEMIX di master tapi TIDAK ada di sales → bisa jadi dead stock atau new launch belum terjual
```

### 2.1.4 Format Denah Toko

**Data Source:** File `Data Option By Region.xlsx` berisi layout per toko per region. Setiap region = 1 sheet (Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali). Kolom per toko menunjukkan: jumlah backwall + hooks, gondola, rak baby (layers), keranjang, table, VM, storage capacity.

**PENTING:** Tidak semua kolom terisi — beberapa toko kecil TIDAK punya gondola, table, VM, keranjang, atau bahkan storage. Jika kolom kosong atau 0, artinya toko tersebut TIDAK memiliki komponen display tersebut. Jangan assume ada.

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
- `Backwall` — hook-based, 1 gender-type per unit
- `Gondola` — hook-based, 1 gender-type per unit
- `Rak Baby` — layer-based, khusus Baby & Kids
- `Keranjang` — 12 pairs per unit, khusus Baby & Kids
- `Table` — sample display, untuk Luca/Luna/Airmove
- `VM Display` — wall/shelf dengan VM tools, untuk Luca/Luna/Airmove

**Gender_Type yang valid untuk Backwall/Gondola:**
- Men Jepit, Men Fashion, Ladies Jepit, Ladies Fashion
- Baby & Kids, Boys, Girls, Junior

Gender_Type untuk Backwall/Gondola TIDAK perlu diisi saat input denah — AI akan merekomendasikan assignment optimal berdasarkan sales proportion.

---

## 2.2 Hitung Adjusted Average per Artikel per Toko

### 2.2.1 Pivot: Artikel × Bulan per Toko

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

Terapkan logic dari Section 1.4.2:

**Tier 1:**
```
bulan_nonzero = [bulan dimana qty > 0]
adjusted_avg = SUM(qty semua bulan) / COUNT(bulan_nonzero)

Alasan: 0 pada T1 = kemungkinan out of stock, bukan no demand
```

**Tier 8 (New Launch):**
```
1. Cari bulan pertama dengan qty > 0 (= bulan launch)
2. Semua bulan sebelum launch → EXCLUDE (belum ada)
3. Bulan setelah launch dengan qty = 0 → EXCLUDE (likely OOS)
4. adjusted_avg = SUM(qty bulan aktif) / COUNT(bulan aktif)
```

**Tier 2 & T3:**
```
Untuk setiap bulan dengan qty = 0:
  - Hitung avg bulan sekitar (N-1, N-2, N+1, N+2)
  - Jika avg sekitar > 50% dari overall avg artikel → EXCLUDE (likely OOS)
  - Jika tren menurun gradual menuju 0 → INCLUDE (genuine decline)
  
Jika ragu → INCLUDE bulan 0 (lebih konservatif)
```

**Tier 4 & T5:**
```
adjusted_avg = SUM(semua bulan) / total_bulan_tersedia
Tidak ada exclusion — 0 = memang slow/dead
```

### 2.2.3 Output: Ranked Article List per Gender-Type per Toko

```
Setelah hitung adjusted_avg, buat ranking per gender-type:

Untuk setiap toko, untuk setiap gender-type:
  1. Filter artikel by gender-type
  2. Sort by: Tier ASC (T1 first), lalu adjusted_avg DESC
  3. Assign display_priority: 1, 2, 3, ...

Contoh output Zuma Galaxy Mall — Men Jepit:
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
    full_box_slots   = FLOOR(total_hooks / 2)    — 2 hook per artikel
    compact_slots    = FLOOR(total_hooks / 1)     — 1 hook per artikel
    
  IF gender-type = Fashion:
    full_box_slots   = FLOOR(total_hooks / 3)    — 3 hook per artikel
    compact_slots    = FLOOR(total_hooks / 2)     — 2 hook per artikel
```

### 2.3.2 Baby Components (Rak & Keranjang)

```
Rak Baby:
  full_slots_per_layer = 1 artikel (6 pairs)
  compact_slots_per_layer = 2 artikel (3 pairs each)
  total_full_slots = layers × 1
  total_compact_slots = layers × 2

Keranjang:
  slots = qty_keranjang × 1 artikel per keranjang (12 pairs each)
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
| KR-1 (×2)   | Keranjang     | Baby & Kids  | -        | 2     | 0                         |
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
  BW-1 (30 hooks) → Men Jepit (28% share, rank 1)
  BW-2 (24 hooks) → Ladies Fashion (24% share, rank 2)
  GD-1 (20 hooks) → Ladies Jepit (18% share, rank 3)
  GD-2 (16 hooks) → Men Fashion (13% share, rank 4)
  
  Baby & Kids → ke Rak Baby + Keranjang + sisa Backwall/Gondola jika ada

Adjustments berdasarkan SPG insight (jika tersedia):
  - Hot zone (near entrance) → gender-type rank 1 ATAU T8 new launch heavy
  - Adjacency: Men Jepit & Men Fashion berdekatan, Ladies Jepit & Ladies Fashion berdekatan
```

---

## 2.5 Article Assignment Algorithm

### 2.5.0 Pre-step: Assign Luca/Luna/Airmove

```
SEBELUM assign artikel lain, handle Luca/Luna/Airmove dulu:

1. Dari ranked list, filter artikel Luca, Luna, Airmove yang tier T1 atau T8
2. Cek ketersediaan display:
   a. Table slots tersedia? → assign ke table (up to table capacity)
   b. VM Display tersedia? → assign ke VM (up to VM capacity)
   c. Tidak ada table DAN tidak ada VM → FLAG WARNING, artikel ini tidak bisa display
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
  a. Luca/Luna/Airmove → HANYA boleh di Table/VM (Section 1.3.7)
     Filter: artikel yang mengandung "LUCA", "LUNA", atau "AIRMOVE" di nama
     → HAPUS dari candidate list backwall/gondola
     → Jika toko TIDAK punya Table/VM → artikel ini TIDAK BISA display sama sekali
     → Flag warning

  b. Artikel yang sudah di-assign ke Rak Baby / Keranjang
     → HAPUS dari candidate list backwall Baby & Kids
     → Mencegah duplikasi: 1 artikel hanya boleh di 1 display unit
     → PROSES: Assign Rak Baby & Keranjang DULU, baru assign backwall Baby

  c. T4/T5 → JANGAN masukkan ke candidate list

Setelah exclusion, BARU lanjut ke slot calculation:

Untuk SETIAP Backwall/Gondola yang sudah di-assign gender-type:

1. Hitung artikel MUST DISPLAY (T1) + PRIORITY (T8) untuk gender-type tersebut
   → count_must = jumlah T1 + T8

2. Hitung slots di full box mode
   → slots_full = hooks / (2 jika jepit, 3 jika fashion)

3. Decision:
   IF count_must <= slots_full:
     → Pakai FULL BOX MODE
     → Sisa slots (slots_full - count_must) untuk T2/T3 filler
     
   ELSE IF count_must <= slots_compact:
     → Pakai COMPACT MODE (atau MIX MODE)
     → Hitung storage impact
     → Validasi: storage impact + existing usage <= storage capacity?
       YES → proceed compact
       NO  → prioritas T1 by rank, potong T8 yang tidak muat, FLAG warning
     
   ELSE:
     → Bahkan compact tidak cukup
     → Assign by rank (highest adj_avg first) sampai slot habis
     → Sisanya FLAG sebagai "T1 not displayed — critical"
```

### 2.5.2 Mix Mode Optimization (lanjutan dari 2.5.1)

```
Jika compact mode diperlukan, pertimbangkan MIX MODE:

Strategy:
  - Top N artikel (highest adj_avg) → FULL BOX (display tebal, no storage cost)
  - Sisanya → COMPACT (save hooks, tapi makan storage)

Optimization:
  1. Start dengan semua FULL BOX
  2. Jika tidak muat → convert artikel dengan adj_avg TERENDAH ke compact, satu per satu
  3. Repeat sampai semua must-display muat
  4. Setiap konversi, cek storage impact
  
Contoh:
  30 hooks fashion, 13 T1+T8 artikel:
  - All full: 30/3 = 10 slots → 3 artikel tidak muat ❌
  - Convert rank 11-13 ke compact: butuh (10×3) + (3×2) = 36 hooks ❌ masih over
  - Convert rank 8-13 ke compact: (7×3) + (6×2) = 21+12 = 33 hooks ❌ masih over
  - Convert rank 5-13 ke compact: (4×3) + (9×2) = 12+18 = 30 hooks ✅
  - Storage impact: 9 × 4 pairs = 36 pairs = 3 box equivalent
```

### 2.5.3 Fill Remaining Slots

```
Setelah T1 dan T8 di-assign:

1. Hitung sisa slots
2. Dari ranked list, ambil T2 berikutnya (by adj_avg descending)
3. Jika T2 habis, ambil T3
4. JANGAN ambil T4/T5
5. Jika semua T2/T3 habis dan masih ada slot → biarkan kosong, flag "available slot"

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
   → Masuk ke Backwall/Gondola yang di-assign "Baby & Kids"
   → Ikut hook rules standar (full/compact mode per tipe artikel)
```

---

## 2.6 Storage Allocation

### 2.6.1 Hitung Storage Terpakai

```
storage_used = 0

# 1. Luca/Luna/Airmove (dari step 2.5.0)
storage_used += count_luca_luna_airmove_displayed × 1 box

# 2. Compact mode overflow (dari step 2.5.1-2.5.4)
compact_pairs_total = 0
FOR each artikel in compact mode:
  IF tipe == "Jepit":    compact_pairs_total += 6
  IF tipe == "Fashion":  compact_pairs_total += 4
  IF type == "Rak Baby": compact_pairs_total += 9   # (jika compact rak)
  IF type == "Rak Baby": compact_pairs_total += 6   # (jika full rak, sisa ½ box)
  
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
    box_allocation = MAX(1, ROUND(storage_remaining × (adj_avg / total_sales_eligible)))
    assign box_allocation ke artikel
    
  # Validasi: total allocated <= storage_remaining
  # Jika over → trim dari artikel dengan adj_avg terendah
  
ELSE:
  FLAG: "Storage penuh — tidak ada alokasi tambahan"
  FLAG: "Pertimbangkan kurangi compact mode atau Luca/Luna/Airmove"
```

### 2.6.3 Rules Recap

```
✅ Boleh di storage:
  - Luca/Luna/Airmove backup (WAJIB)
  - Compact mode overflow (otomatis)
  - T1 fast moving backup (proporsional)
  - T8 backup (proporsional, termasuk T8 yang belum di-display untuk rotation)
  
❌ TIDAK BOLEH di storage:
  - T4 / T5
  - Non-T8 yang TIDAK di display (tidak boleh ada stok tanpa display kecuali T8)
```

---

## 2.7 Generate Output

### 2.7.1 Planogram Sheet (Output Utama)

```
Buat 1 XLSX file dengan multiple sheets:

SHEET 1: "Planogram — [Store Name]"
  Layout yang mirror fisik toko.
  
  Untuk setiap display component, buat section:
  
  === BACKWALL 1: Men Jepit (30 hooks) — Full Box Mode ===
  
  | Hook 1-2      | Hook 3-4      | Hook 5-6      | ... | Hook 29-30     |
  |---------------|---------------|---------------|-----|----------------|
  | Men Classic 25| Men Classic 30| Men Stripe 8  | ... | Men Stripe 14  |
  | T1 | Avg: 50  | T1 | Avg: 45 | T1 | Avg: 39 | ... | T2 | Avg: 15  |
  
  Catatan:
  - Jepit full box = 2 kolom bersebelahan (merged cells atau label span)
  - Fashion full box = 3 kolom bersebelahan
  - Compact mode = jumlah kolom berkurang sesuai mode
  - Color code: T1 = hijau, T8 = biru, T2 = kuning, T3 = abu-abu
  
  === TABLE DISPLAY (4 artikel) ===
  | Slot 1    | Slot 2    | Slot 3     | Slot 4     |
  |-----------|-----------|------------|------------|
  | Men Luca 1| Ladies Luna 2 | Ladies Luna 3 | Men Luca 3 |
  
  === RAK BABY (3 layer, compact mode) ===
  | Layer | Slot A          | Slot B          |
  |-------|-----------------|-----------------|
  | 1     | Baby Classic 5  | Baby Classic 7  |
  | 2     | Baby Velcro 1   | Baby Velcro 3   |
  | 3     | Baby Cocomelon 1| Baby Batman 1   |
```

### 2.7.2 Storage Allocation Table

```
SHEET 2: "Storage Allocation"

| No | KODEMIX | Article Name       | Gender-Type    | Tier | Adj_Avg | Boxes | Pairs | Alasan                    |
|----|---------|-------------------|----------------|------|---------|-------|-------|---------------------------|
| 1  | M1LU01  | Men Luca 1        | Men Fashion    | T1   | 35.2    | 1     | 11    | Table display backup      |
| 2  | L2LN02  | Ladies Luna 2     | Ladies Fashion | T1   | 28.5    | 1     | 11    | Table display backup      |
| 3  | M1CA25  | Men Classic 25    | Men Jepit      | T1   | 50.5    | 2     | 24    | Highest sales, extra stock |
| 4  | L1CA22  | Ladies Classic 22 | Ladies Jepit   | T1   | 42.1    | 2     | 24    | High sales                |
| 5  | M2DA03  | Men Dallas 3      | Men Fashion    | T1   | 20.3    | 0*    | 4     | *Compact mode overflow    |
| ...                                                                                                          |
|    |         |                   |                |      | TOTAL   | 18/20 |       | 90% storage utilization   |
```

### 2.7.3 Summary Report

```
SHEET 3: "Summary Report"

═══ DISPLAY UTILIZATION ═══
Total hooks/slots available : 120
Total hooks/slots used      : 112
Utilization                 : 93%
Empty slots                 : 8 (available for expansion)

═══ SALES COVERAGE ═══
Total adjusted avg (semua artikel toko ini) : 1,200 pairs/bulan
Adjusted avg dari artikel di display        : 1,080 pairs/bulan
Sales coverage                              : 90%

═══ TIER DISTRIBUTION DI DISPLAY ═══
| Tier | Count | % of Display | Notes                    |
|------|-------|-------------|--------------------------|
| T1   | 28    | 65%         | All T1 displayed ✅       |
| T8   | 5     | 12%         | 5 of 6 T8 displayed      |
| T2   | 8     | 19%         | Filler                   |
| T3   | 2     | 5%          | Variety filler            |

═══ STORAGE UTILIZATION ═══
Total capacity  : 20 box
Used            : 18 box
Remaining       : 2 box
Breakdown:
  - Luca/Luna/Airmove backup : 4 box
  - Compact mode overflow    : 3 box (36 pairs equivalent)
  - T1 fast moving backup    : 9 box
  - T8 rotation stock        : 2 box

═══ FLAGS & WARNINGS ═══
🔴 CRITICAL:
  - (none)

🟡 WARNING:
  - T8 "Men Onyx Z 12" tidak masuk display (slot penuh, rank 6 of 5 available)
  - Storage 90% — mendekati penuh

🟢 POSITIVE:
  - Semua T1 terdisplay ✅
  - Tidak ada T4/T5 di display ✅
  - Sales coverage 90% ✅
```

### 2.7.4 Comparison vs Existing (Opsional)

```
SHEET 4: "Changes vs Current" (hanya jika data planogram existing tersedia)

═══ ARTIKEL BARU MASUK DISPLAY ═══
| KODEMIX | Article         | Tier | Adj_Avg | Masuk ke       | Alasan              |
|---------|----------------|------|---------|----------------|---------------------|
| M1ON04  | Men Onyx 4     | T8   | 22.0    | BW-1 hook 25-26| New launch, exposure |

═══ ARTIKEL KELUAR DARI DISPLAY ═══
| KODEMIX | Article         | Tier | Adj_Avg | Sebelumnya di  | Alasan              |
|---------|----------------|------|---------|----------------|---------------------|
| M1CA23  | Men Classic 23 | T4   | 2.1     | BW-1 hook 25-26| Slow moving, replace |

═══ ARTIKEL PINDAH POSISI ═══
| KODEMIX | Article         | From          | To            | Alasan              |
|---------|----------------|---------------|---------------|---------------------|
| M1CA25  | Men Classic 25 | BW-1 hook 15  | BW-1 hook 1-2 | Top seller → hot zone|

═══ EXPECTED IMPACT ═══
Artikel ditambah ke display: +X% estimated sales uplift (based on historical display-to-sales correlation)
Artikel dipindah ke hot zone: +Y% estimated uplift for those articles
```

---

## 2.8 Worked Example (Walkthrough Singkat)

> Contoh ini menunjukkan flow end-to-end untuk 1 toko kecil agar logic jelas.

### Setup: Toko Fiktif "Zuma Mini"

```
Denah:
  - BW-1: Backwall, 12 hooks
  - GD-1: Gondola, 8 hooks  
  - KR-1: Keranjang Baby × 1
  - Storage: 5 box

Sales data (adjusted avg, sudah dihitung):
  Men Jepit:     M1CA25 (T1, 40), M1CA30 (T1, 35), M1ST08 (T2, 12), M1BS05 (T3, 5)
  Men Fashion:   M2DA03 (T1, 25), M2CL02 (T8, 15), M2DA05 (T3, 8)
  Ladies Jepit:  L1CA22 (T1, 38), L1CA26 (T1, 30), L1CA29 (T2, 10)
  Ladies Fashion:L2EA10 (T1, 28), L2FO03 (T8, 18), L2EA12 (T2, 9)
  Baby:          K1CA05 (T1, 20), K1VB01 (T8, 12), K1CM01 (T2, 6)
```

### Step A: Gender-Type Sales Share

```
Men Jepit:      40+35+12+5 = 92 (29%)
Ladies Jepit:   38+30+10 = 78 (25%)
Ladies Fashion: 28+18+9 = 55 (17%)
Men Fashion:    25+15+8 = 48 (15%)
Baby:           20+12+6 = 38 (12%)

Note: Tidak ada Luca/Luna/Airmove dan tidak ada Table/VM → skip step 2.5.0
```

### Step B: Assign Gender-Type ke Display

```
BW-1 (12 hooks, terbesar) → Men Jepit (29%, rank 1)
GD-1 (8 hooks)            → Ladies Jepit (25%, rank 2)

Tapi Ladies Fashion (17%) dan Men Fashion (15%) tidak punya display unit!
→ Opsi 1: Split BW-1 menjadi 2 section? ❌ Tidak boleh, rule: 1 unit = 1 gender-type
→ Opsi 2: Hanya display 2 gender-type terbesar
→ Opsi 3: Kalau ada SPG insight bilang fashion demand tinggi → pertimbangkan assign GD-1 ke fashion

Untuk contoh ini: ikuti data → BW-1 = Men Jepit, GD-1 = Ladies Jepit
FLAG: "Ladies Fashion & Men Fashion tidak punya display unit — 
       pertimbangkan tambah gondola atau realokasi"
       
KR-1 (keranjang × 1) → Baby & Kids (otomatis)
```

### Step C: Hitung Slots & Assign Articles

```
BW-1 Men Jepit (12 hooks):
  T1 count: 2 (M1CA25, M1CA30)
  Full box mode: 12/2 = 6 slots → 2 T1 + sisa 4 slot
  → M1CA25 (hook 1-2), M1CA30 (hook 3-4)
  → Fill: M1ST08/T2 (hook 5-6), M1BS05/T3 (hook 7-8)
  → Remaining 4 hooks (9-12): KOSONG atau bisa diisi jika ada artikel Men Jepit lain
  → FLAG: "4 hooks available"

GD-1 Ladies Jepit (8 hooks):
  T1 count: 2 (L1CA22, L1CA26)
  Full box mode: 8/2 = 4 slots → 2 T1 + sisa 2 slot
  → L1CA22 (hook 1-2), L1CA26 (hook 3-4)
  → Fill: L1CA29/T2 (hook 5-6)
  → 1 slot remaining (hook 7-8): KOSONG
  → FLAG: "2 hooks available"

KR-1 Baby (1 keranjang):
  → K1CA05 (T1, highest avg) = 12 pairs di keranjang
  → K1VB01 (T8) dan K1CM01 (T2) tidak muat → FLAG: "Baby T8 tidak di-display"
```

### Step D: Storage Allocation

```
Storage capacity: 5 box
Compact overflow: 0 (semua full box mode)
Luca/Luna/AM: 0

Storage available: 5 box penuh

Eligible: semua yang di-display (T1 + T8 + T2)
Total adj_avg eligible yang di-display: 40+35+12+5+38+30+10+20 = 190

Allocation:
  M1CA25: MAX(1, ROUND(5 × 40/190)) = MAX(1, 1.05) = 1 box
  M1CA30: MAX(1, ROUND(5 × 35/190)) = MAX(1, 0.92) = 1 box
  L1CA22: MAX(1, ROUND(5 × 38/190)) = MAX(1, 1.00) = 1 box
  L1CA26: MAX(1, ROUND(5 × 30/190)) = MAX(1, 0.79) = 1 box
  K1CA05: sudah 1 box di keranjang (12 pairs) → bisa tambah 1 box backup
  
  Total: 5 box ✅ pas

  Sisanya (M1ST08/T2, M1BS05/T3, L1CA29/T2) tidak dapat storage tambahan
  karena kapasitas habis → acceptable, mereka bukan T1
```

### Step E: Final Output Summary

```
Display: 8 artikel terdisplay dari 14 total
Sales coverage: (40+35+12+5+38+30+10+20) / 316 = 60%
Storage: 5/5 box (100%)

Flags:
  🔴 Ladies Fashion & Men Fashion tidak punya display → revenue loss ~32%
  🟡 Baby T8 (K1VB01) tidak di-display → new launch tanpa exposure
  🟢 Semua T1 terdisplay ✅ (untuk gender-type yang punya display)
  
Recommendation:
  → Tambah minimal 1 gondola untuk Ladies Fashion (17% sales share tanpa display)
  → Atau realokasi: jika bisa split BW-1 atau tambah 1 unit lagi
```

---

## 2.9 Checklist Sebelum Finalisasi

```
Sebelum menyerahkan output planogram, VALIDASI:

□ Semua T1 ada di display? (jika tidak → harus ada alasan + flag)
□ Tidak ada T4/T5 di display?
□ Luca/Luna/Airmove hanya di Table/VM? (bukan di hook biasa)
□ 1 display unit = 1 gender-type? (tidak campur)
□ Storage tidak exceed capacity?
□ Compact mode storage impact sudah dihitung?
□ Total hooks used <= total hooks available?
□ Semua flags/warnings sudah dilaporkan?
□ Summary report lengkap (utilization, coverage, tier distribution)?
```

---

# CARA MENJAWAB

## Jika user minta buatkan planogram:

### Step 1: Validasi Input
Cek apakah semua data wajib sudah tersedia. Jika belum, tanyakan yang kurang.

### Step 2: Tanyakan Variable per Toko
- Kapasitas table display (muat berapa artikel?)
- Kapasitas VM display (muat berapa artikel?)
- Ketersediaan VM tools
- Storage capacity (box)

### Step 3: Analisa Sales (Section 2.1-2.2)
- Konsolidasi sales data, filter retail only (lihat 2.1.3)
- Extract KODEMIX dari Kode Barang (lihat 2.1.2)
- Join dengan master artikel (lihat 2.1.3 Step 4)
- Hitung adjusted average per tier (lihat 2.2.2)
- Rank per gender-type (lihat 2.2.3)

### Step 4: Hitung Slot Capacity (Section 2.3)
- Dari denah, hitung total hooks per display unit (lihat 2.3.1)
- Convert ke artikel slots per mode: full vs compact (lihat 2.3.1-2.3.3)
- Compile total slot summary (lihat 2.3.4)

### Step 5: Assign Gender-Type & Artikel (Section 2.4-2.5)
- Hitung sales proportion per gender-type (lihat 2.4.1)
- Assign gender-type ke display unit (lihat 2.4.2)
- Pre-step: Luca/Luna/Airmove ke table/VM FIRST (lihat 2.5.0)
- Determine display mode per unit (lihat 2.5.1)
- Mix mode optimization jika perlu (lihat 2.5.2)
- Fill remaining slots dengan T2/T3 (lihat 2.5.3)
- Baby & Kids assignment (lihat 2.5.4)
- Zone optimization jika ada SPG data (lihat 1.5)

### Step 6: Alokasi Storage (Section 2.6)
- Hitung storage terpakai (lihat 2.6.1)
- Alokasi tambahan proporsional (lihat 2.6.2)

### Step 7: Generate Output (Section 2.7)
- Planogram sheet — mirror layout fisik (lihat 2.7.1)
- Storage allocation table (lihat 2.7.2)
- Summary report dengan flags/warnings (lihat 2.7.3)
- Comparison vs existing jika ada (lihat 2.7.4)
- Jalankan checklist validasi (lihat 2.9)

## Jika user tanya soal rules/konsep:
Jawab berdasarkan Section 1 di atas. Jangan mengarang rules baru.

## Jika data kurang:
JANGAN assume. Tanyakan. Lebih baik tanya dulu daripada output yang salah.

---

---

# SECTION 3: IMPLEMENTATION REFERENCE & AI AGENT GOTCHAS

## 3.1 Reference Implementation

File `build_royal_planogram.py` di folder yang sama berisi working implementation yang sudah diverifikasi. Gunakan sebagai reference untuk membangun planogram toko lain.

**Cara menggunakan sebagai template:**
1. Copy script, ganti CONFIG section (STORE_NAME, BACKWALLS, RAK_BABY, STORAGE_CAPACITY, dll)
2. Denah toko ambil dari `Data Option By Region.xlsx` — sheet sesuai region, kolom sesuai toko
3. Jalankan script → output XLSX otomatis

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
1. pull_data()        → Query core.sales_with_product + core.stock_with_product dari VPS DB
2. process_sales()    → Clean data, rename columns, filter non-products
3. compute_adjusted_avg() → Hitung adjusted avg per tier rules (Section 1.4.2)
4. compute_gender_shares() → Map gender+tipe ke gender_type, hitung sales share %
5. assign_rak_baby()  → Assign baby articles ke rak DULU (untuk dedup)
6. assign_gender_to_backwalls() → Biggest backwall -> highest share gender-type
7. assign_articles()  → Per backwall: exclude Luca/Luna/Airmove, exclude rak baby articles,
                         then T1 first -> T8 -> T2 -> T3, sorted by adj_avg desc
8. generate_xlsx()    → Multi-sheet output matching example format
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
| **Tier NULL** | Beberapa artikel punya tier = NULL di DB | Default ke "3" (Tertiary) — konservatif |
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
  5. Assign Rak Baby & Keranjang FIRST       ← PENTING: ini SEBELUM backwall
  6. Assign Luca/Luna/Airmove to Table/VM    ← PENTING: ini SEBELUM backwall
  7. Assign gender-types to backwalls/gondolas
  8. Assign articles to backwalls/gondolas    ← Exclude rak baby + Luca/Luna/Airmove articles
  9. Allocate storage
  10. Generate XLSX output
  11. Validate against checklist (Section 2.9)

WRONG ORDER (will cause bugs):
  ❌ Assign backwall BEFORE rak baby → duplikasi
  ❌ Assign articles BEFORE excluding Luca/Luna/Airmove → rule violation
  ❌ Allocate storage BEFORE knowing compact mode usage → wrong calculation
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
  [ ] Storage=0 → compact mode disabled?
  [ ] Storage=0 → Luca/Luna/Airmove excluded entirely?
  [ ] is_intercompany transactions excluded from sales data?
  [ ] Non-product items (SHOPPING BAG, HANGER, etc.) excluded?
  [ ] All print/output uses ASCII only (no unicode arrows/symbols)?
```

---

# SECTION 4: STEP 2 — DENAH PLANOGRAM (VISUALISASI)

## 4.1 Overview

Setelah Step 1 menghasilkan PLANOGRAM_[Store].xlsx, **Step 2** mengubah data tersebut menjadi **visual bird's-eye floor plan** (denah toko) yang menunjukkan penempatan fisik setiap artikel.

**PENTING — TANYA USER DULU:**
> Sebelum lanjut ke Step 2, SELALU tanyakan ke user:
> "Output Step 1 sudah sesuai? Ada artikel yang perlu digeser/diganti/di-adjust? Jika sudah OK, saya lanjut ke denah visual."
>
> Jangan langsung generate denah jika user belum confirm Step 1 output.

## 4.2 Step 2 Skill Document

Dokumentasi lengkap Step 2 ada di:
```
step 2 - plannogram visualizations/SKILL_visualized-plano_zuma_v1.md
```

## 4.3 Step 2 Script & Outputs

| File | Keterangan |
|------|------------|
| `step 2 - plannogram visualizations/visualize_planogram.py` | Script utama — baca PLANOGRAM XLSX, generate denah |
| `VISUAL_PLANOGRAM_[Store].xlsx` | Output Excel: floor plan dengan colored cells per series, artikel name, tier & avg, dimensi (8X7/7X7) |
| `VISUAL_PLANOGRAM_[Store].txt` | Output ASCII: text-based floor plan untuk terminal/chat |

## 4.4 Step 2 Quick Reference

```
Cara jalankan:
1. Pastikan Step 1 output sudah ada (PLANOGRAM_[Store].xlsx)
2. Tanyakan user: "Step 1 output sudah OK? Ada yang perlu di-adjust?"
3. Jika OK, jalankan: python visualize_planogram.py
4. Output: 2 file (Excel denah + ASCII denah)
```

### Excel Denah menampilkan:
- **Series** — nama series per artikel (color-coded)
- **Article Name** — nama lengkap artikel (e.g., "MEN DALLAS 1")
- **Tier & Avg** — tier dan adjusted average (e.g., "T1 | Avg: 11.8")
- **Dimension Labels** — "8X7", "7X7" per backwall
- **Landmarks** — KASIR, AIRMOVE, RAK BABY
- **Legend** — mapping warna per series

### Layout per toko bersifat UNIK:
- Royal Plaza: config `ROYAL_PLAZA_LAYOUT` di dalam script
- Toko lain: buat config baru berdasarkan `portal_planogram_[region].xlsx`

---

*Version: 3.1 — Section 4 (Step 2 Denah Planogram reference) added*
*Last Updated: 10 February 2026*
*Changelog:*
- *v3.1: Added Section 4 (Step 2 — Denah Planogram reference with "ask user first" protocol)*
- *v3.0: Added Section 3 (AI Agent Gotchas, Reference Implementation, Execution Order, Extended Checklist)*
- *v3.0: Added DB data source (Option A) to Section 2.1.1 with column mapping and connection details*
- *v3.0: Added store layout data source reference to Section 2.1.4*
- *v3.0: Added explicit exclusion list to Section 2.5.1 (Luca/Luna/Airmove, Rak Baby dedup, T4/T5)*
- *v3.0: Added edge cases to Section 1.10 (storage=0, limited display units, Luca/Luna/Airmove fallback rule)*
- *v2.0: Original complete skill document*
